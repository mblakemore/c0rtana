#!/usr/bin/env python3
"""
ESP32 Sensor Anomaly Detection via Gaussian Process Regression

Applies Lyla's C523 GP framework (kernel design, GP prediction, sparse GP)
to real ESP32 DHT sensor data for drift/anomaly detection.

Usage:
    python3 scripts/esp32_anomaly_detection.py --collect --samples 30 --interval 2
    python3 scripts/esp32_anomaly_detection.py --analyze
    python3 scripts/esp32_anomaly_detection.py --live  # collect and analyze in one pass
"""

import json
import math
import os
import sys
import time
import argparse
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

import numpy as np
from scipy.linalg import solve_triangular


class GaussianProcessRegressor:
    """Minimal GP regression with RBF kernel — no external GP library needed.

    Implements the exact GP prediction from Lyla's C523:
      f* = K(X*, X) [K(X, X) + sigma_n^2 I]^{-1} y
      var* = k(x*, x*) - K(X*, X) [K(X, X) + sigma_n^2 I]^{-1} K(X, X)*
    """

    def __init__(self, length_scale=1.0, signal_variance=1.0, noise_variance=0.01):
        self.length_scale = length_scale
        self.signal_variance = signal_variance
        self.noise_variance = noise_variance
        self.X_train = None
        self.y_train = None
        self.L_chol = None  # Cholesky of K + noise
        self.alpha = None    # L^{-1} y

    def _rbf_kernel(self, X1, X2):
        """RBF (squared exponential) kernel: k(x, x') = sigma_f^2 * exp(-|x-x'|^2 / (2*l^2))"""
        X1 = np.atleast_2d(X1)
        X2 = np.atleast_2d(X2)
        sq_dist = np.sum(X1**2, axis=1, keepdims=True) - 2 * X1 @ X2.T + np.sum(X2**2, axis=1)
        return self.signal_variance * np.exp(-sq_dist / (2 * self.length_scale**2))

    def fit(self, X, y):
        """Fit GP by computing Cholesky decomposition of K + noise."""
        self.X_train = np.atleast_2d(X).astype(float)
        self.y_train = np.atleast_1d(y).astype(float)
        n = len(X)

        K = self._rbf_kernel(self.X_train, self.X_train)
        K += self.noise_variance * np.eye(n)

        self.L_chol = np.linalg.cholesky(K)
        # Solve L alpha_temp = y, then L^T alpha = alpha_temp
        alpha_temp = solve_triangular(self.L_chol, self.y_train, lower=True)
        self.alpha = solve_triangular(self.L_chol.T, alpha_temp, lower=False)

    def predict(self, X, return_std=True):
        """Predict with uncertainty quantification."""
        X = np.atleast_2d(X).astype(float)
        K_star = self._rbf_kernel(X, self.X_train)
        mean = K_star @ self.alpha

        if return_std:
            v = solve_triangular(self.L_chol, K_star.T, lower=True)
        else:
            v = np.zeros_like(K_star)

        var = self.signal_variance - np.sum(v**2, axis=1)
        # Floor: prediction uncertainty should be at least the noise level
        var = np.maximum(var, self.noise_variance)
        std = np.sqrt(var)

        return mean, std


def fetch_dht_sensor(esp32_host="192.168.4.38"):
    """Fetch current DHT reading from ESP32."""
    url = f"http://{esp32_host}/api/sensor/dht"
    try:
        req = Request(url)
        with urlopen(req, timeout=3) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"  Failed to fetch DHT: {e}")
        return None


def collect_samples(n_samples=30, interval=2, esp32_host="192.168.4.38"):
    """Collect a time series of DHT readings."""
    data_file = os.path.join(os.path.dirname(__file__), '..', 'state', 'sensor_timeseries.json')
    os.makedirs(os.path.dirname(data_file), exist_ok=True)

    print(f"Collecting {n_samples} samples at {interval}s intervals...")
    print(f"ESP32: {esp32_host}")
    print("-" * 60)

    records = []
    for i in range(n_samples):
        reading = fetch_dht_sensor(esp32_host)
        if reading is None:
            print(f"  [{i+1}/{n_samples}] FAILED — skipping")
            time.sleep(interval)
            continue

        t = datetime.now(timezone.utc)
        record = {
            "index": i,
            "timestamp": t.isoformat(),
            "time_seconds": i * interval,
            "temperature": reading.get("temp"),
            "humidity": reading.get("humidity"),
            "sensor": reading.get("sensor", "unknown"),
        }
        records.append(record)
        temp = record["temperature"]
        hum = record["humidity"]
        print(f"  [{i+1}/{n_samples}] t={record['time_seconds']:4d}s  temp={temp:.1f}°C  hum={hum:.1f}%")
        time.sleep(interval)

    with open(data_file, 'w') as f:
        json.dump({
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "n_samples": len(records),
            "interval_seconds": interval,
            "esp32_host": esp32_host,
            "readings": records,
        }, f, indent=2)

    print(f"\nSaved {len(records)} readings to {data_file}")
    return records


def analyze(data_file=None):
    """Run GP anomaly detection on collected sensor data."""
    if data_file is None:
        data_file = os.path.join(os.path.dirname(__file__), '..', 'state', 'sensor_timeseries.json')

    if not os.path.exists(data_file):
        print(f"No data file found at {data_file}. Run with --collect first.")
        return None

    with open(data_file, 'r') as f:
        data = json.load(f)

    readings = data["readings"]
    if len(readings) < 5:
        print(f"Need at least 5 readings for GP (have {len(readings)}).")
        return None

    print("=" * 60)
    print("ESP32 GP Anomaly Detection Analysis")
    print("=" * 60)
    print(f"Readings: {len(readings)}")
    print(f"Duration: {readings[-1]['time_seconds'] - readings[0]['time_seconds']}s")
    print(f"Collected: {data['collected_at']}")
    print()

    # Extract time series
    times = np.array([r["time_seconds"] for r in readings]).reshape(-1, 1)
    temps = np.array([r["temperature"] for r in readings])
    humids = np.array([r["humidity"] for r in readings])

    # --- Temperature GP ---
    print("--- Temperature GP Regression ---")
    # Scale hyperparameters to data characteristics
    duration = times[-1, 0] - times[0, 0]

    # Center data around mean — GP fits residuals, not raw values
    temp_mean_raw = np.mean(temps)
    hum_mean_raw = np.mean(humids)
    temps_centered = temps - temp_mean_raw
    humids_centered = humids - hum_mean_raw

    # Use sample variance as signal variance
    temp_var = max(np.var(temps_centered), 0.01)
    hum_var = max(np.var(humids_centered), 0.01)

    # Length scale: adapt to observation window
    ls = max(duration * 0.3, 2.0)

    # Noise floor: 10% of signal variance (sensor noise estimate)
    gp_temp = GaussianProcessRegressor(
        length_scale=ls,
        signal_variance=temp_var,
        noise_variance=0.1 * temp_var,
    )
    gp_temp.fit(times, temps_centered)
    temp_resid_mean, temp_std = gp_temp.predict(times)
    temp_mean = temp_resid_mean + temp_mean_raw  # uncenter

    # --- Humidity GP ---
    print("--- Humidity GP Regression ---")
    gp_humid = GaussianProcessRegressor(
        length_scale=ls,
        signal_variance=hum_var,
        noise_variance=0.1 * hum_var,
    )
    gp_humid.fit(times, humids_centered)
    humid_resid_mean, humid_std = gp_humid.predict(times)
    humid_mean = humid_resid_mean + hum_mean_raw  # uncenter

    # --- Anomaly Detection ---
    # A reading is anomalous if it deviates > 2 sigma from GP prediction
    threshold_sigma = 2.0
    temp_residuals = np.abs(temps - temp_mean)
    humid_residuals = np.abs(humids - humid_mean)

    temp_anomalies = []
    humid_anomalies = []

    for i, r in enumerate(readings):
        temp_z = temp_residuals[i] / (temp_std[i] + 1e-10)
        humid_z = humid_residuals[i] / (humid_std[i] + 1e-10)

        if temp_z > threshold_sigma:
            temp_anomalies.append({
                "index": i,
                "timestamp": r["timestamp"],
                "observed": float(temps[i]),
                "predicted": float(temp_mean[i]),
                "std": float(temp_std[i]),
                "z_score": float(temp_z),
            })
        if humid_z > threshold_sigma:
            humid_anomalies.append({
                "index": i,
                "timestamp": r["timestamp"],
                "observed": float(humids[i]),
                "predicted": float(humid_mean[i]),
                "std": float(humid_std[i]),
                "z_score": float(humid_z),
            })

    # --- Summary ---
    print(f"\n--- Anomaly Detection (>{threshold_sigma} sigma) ---")
    print(f"Temperature anomalies: {len(temp_anomalies)}/{len(readings)}")
    for a in temp_anomalies:
        print(f"  t={a['index']*data['interval_seconds']}s: observed={a['observed']:.1f}°C, "
              f"predicted={a['predicted']:.1f}°C, z={a['z_score']:.2f}")

    print(f"Humidity anomalies: {len(humid_anomalies)}/{len(readings)}")
    for a in humid_anomalies:
        print(f"  t={a['index']*data['interval_seconds']}s: observed={a['observed']:.1f}%, "
              f"predicted={a['predicted']:.1f}%, z={a['z_score']:.2f}")

    # --- Trend Analysis ---
    # Simple linear trend from GP residuals
    if len(readings) > 2:
        temp_trend = np.polyfit(
            [r["time_seconds"] for r in readings], temps, 1
        )
        humid_trend = np.polyfit(
            [r["time_seconds"] for r in readings], humids, 1
        )
        print(f"\n--- Trend (linear fit over {readings[-1]['time_seconds']}s) ---")
        print(f"  Temperature: {temp_trend[0]:.4f} °C/s (slope)")
        print(f"  Humidity: {humid_trend[0]:.4f} %/s (slope)")

        # Project forward 1 hour
        future_t = readings[-1]["time_seconds"] + 3600
        temp_proj = temp_trend[0] * future_t + temp_trend[1]
        humid_proj = humid_trend[0] * future_t + humid_trend[1]
        print(f"  1hr projection: temp={temp_proj:.1f}°C, humidity={humid_proj:.1f}%")
        if humid_proj > 100:
            print(f"  NOTE: Humidity projection >100% — sensor drift likely")
        if temp_proj > 35 or temp_proj < 10:
            print(f"  NOTE: Temperature projection outside room range — sensor issue")

    # --- GP Diagnostics ---
    print(f"\n--- GP Model Diagnostics ---")
    print(f"  Temperature: length_scale={gp_temp.length_scale}s, "
          f"signal_var={gp_temp.signal_variance}, noise_var={gp_temp.noise_variance}")
    print(f"  Humidity: length_scale={gp_humid.length_scale}s, "
          f"signal_var={gp_humid.signal_variance}, noise_var={gp_humid.noise_variance}")

    # Log-likelihood (marginal) as model quality indicator
    n = len(readings)
    temp_log_likelihood = (
        -0.5 * np.sum(np.log(2 * np.pi * (temp_std**2 + 1e-10)))
        - 0.5 * np.sum((temps - temp_mean)**2 / (temp_std**2 + 1e-10))
    )
    humid_log_likelihood = (
        -0.5 * np.sum(np.log(2 * np.pi * (humid_std**2 + 1e-10)))
        - 0.5 * np.sum((humids - humid_mean)**2 / (humid_std**2 + 1e-10))
    )
    print(f"  Temp log-likelihood: {temp_log_likelihood:.2f}")
    print(f"  Humidity log-likelihood: {humid_log_likelihood:.2f}")

    # Save analysis report
    report = {
        "cycle": 558,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "framework": "Gaussian Process Regression (Lyla C523)",
        "n_readings": len(readings),
        "duration_seconds": readings[-1]["time_seconds"] - readings[0]["time_seconds"],
        "temperature": {
            "mean": float(np.mean(temps)),
            "std": float(np.std(temps)),
            "anomalies": temp_anomalies,
            "trend_slope": float(temp_trend[0]) if len(readings) > 2 else None,
            "log_likelihood": float(temp_log_likelihood),
        },
        "humidity": {
            "mean": float(np.mean(humids)),
            "std": float(np.std(humids)),
            "anomalies": humid_anomalies,
            "trend_slope": float(humid_trend[0]) if len(readings) > 2 else None,
            "log_likelihood": float(humid_log_likelihood),
        },
        "diagnosis": _diagnose(temp_anomalies, humid_anomalies, temp_trend if len(readings) > 2 else None, humid_trend if len(readings) > 2 else None),
    }

    report_file = os.path.join(os.path.dirname(__file__), '..', 'state', 'gp_anomaly_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to {report_file}")
    return report


def _diagnose(temp_anomalies, humid_anomalies, temp_trend, humid_trend):
    """Generate human-readable diagnosis."""
    findings = []

    if len(temp_anomalies) > 0:
        findings.append(f"{len(temp_anomalies)} temperature anomalies detected")
    if len(humid_anomalies) > 0:
        findings.append(f"{len(humid_anomalies)} humidity anomalies detected")

    if temp_trend is not None and abs(temp_trend[0]) > 0.001:
        direction = "rising" if temp_trend[0] > 0 else "falling"
        findings.append(f"Temperature trend: {direction} at {temp_trend[0]:.4f} °C/s")

    if humid_trend is not None and abs(humid_trend[0]) > 0.005:
        direction = "rising" if humid_trend[0] > 0 else "falling"
        findings.append(f"Humidity trend: {direction} at {humid_trend[0]:.4f} %/s")
        if humid_trend[0] > 0.01:
            findings.append("DHT22 sensor drift hypothesis supported")

    if not findings:
        findings.append("Sensor readings stable — no anomalies or significant trends")

    return " | ".join(findings)


def main():
    parser = argparse.ArgumentParser(description="ESP32 GP Anomaly Detection")
    parser.add_argument("--collect", action="store_true", help="Collect sensor samples")
    parser.add_argument("--analyze", action="store_true", help="Analyze collected data")
    parser.add_argument("--live", action="store_true", help="Collect and analyze in one pass")
    parser.add_argument("--samples", type=int, default=30, help="Number of samples to collect")
    parser.add_argument("--interval", type=int, default=2, help="Seconds between samples")
    parser.add_argument("--host", default="192.168.4.38", help="ESP32 host")

    args = parser.parse_args()

    if args.collect or args.live:
        collect_samples(args.samples, args.interval, args.host)

    if args.analyze or args.live:
        analyze()

    if not (args.collect or args.analyze or args.live):
        parser.print_help()


if __name__ == "__main__":
    main()
