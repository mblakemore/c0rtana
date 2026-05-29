#!/usr/bin/env python3
"""
2D Kalman filter with state-space model for ESP32 DHT22 sensor prediction.

Extends scripts/kalman_filter.py (1D, scalar) to 2D state-space:
  State: [humidity, temperature]
  Process model: constant value + random walk (humidity/temp don't change rapidly)
  Measurement model: direct observation with DHT22 noise

Produces a forward prediction for the next ESP32 reading to grade later.

Key insight from Kalman (1960): optimal linear estimation when both
process and measurement are Gaussian. The Kalman gain is the optimal
weight between prediction and measurement — no tuning needed if Q and R
are correctly specified.

Connection to Lyla's toolkit:
  - C521 (Bayesian inference): Kalman filter IS recursive Bayesian estimation
  - C523 (GPs): Kalman filter is GP with RBF kernel in the limit of
    continuous-time random walk prior
  - C527 (RL): Kalman filter provides the state estimate for POMDPs
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

DRIFT_LOG = Path("state/sensor_drift_log.jsonl")


class KalmanFilter2D:
    """2D Kalman filter for [humidity, temperature] state estimation.

    State transition: x_k = x_{k-1} + w_k  (random walk, F = I)
    Measurement:      z_k = H * x_k + v_k  (direct observation, H = I)

    This is the simplest non-trivial state-space model. For humidity
    in a stable environment, the true state barely changes between
    measurements (Q is small). The DHT22 has ~2% RH and ~0.5C accuracy,
    so R reflects measurement noise, not state change.
    """

    def __init__(self, q_humidity=0.001, q_temp=0.0001,
                 r_humidity=4.0, r_temp=0.25):
        """
        Args:
            q_humidity: Process noise covariance for humidity (RH^2).
                Small = humidity is stable between readings.
            q_temp: Process noise covariance for temperature (C^2).
            r_humidity: Measurement noise covariance for humidity (RH^2).
                DHT22 accuracy ~2% RH → variance ~4.
            r_temp: Measurement noise covariance for temperature (C^2).
                DHT22 accuracy ~0.5C → variance ~0.25.
        """
        # State estimate [humidity, temp]
        self.x = None
        # Error covariance matrix (2x2, diagonal = independent)
        self.P = None
        # Process noise covariance
        self.Q = [[q_humidity, 0], [0, q_temp]]
        # Measurement noise covariance
        self.R = [[r_humidity, 0], [0, r_temp]]

    def _mat_mult(self, a, b):
        """2x2 matrix multiplication."""
        return [
            [a[0][0]*b[0][0] + a[0][1]*b[1][0], a[0][0]*b[0][1] + a[0][1]*b[1][1]],
            [a[1][0]*b[0][0] + a[1][1]*b[1][0], a[1][0]*b[0][1] + a[1][1]*b[1][1]]
        ]

    def _mat_add(self, a, b):
        """2x2 matrix addition."""
        return [[a[i][j] + b[i][j] for j in range(2)] for i in range(2)]

    def _mat_sub(self, a, b):
        """2x2 matrix subtraction."""
        return [[a[i][j] - b[i][j] for j in range(2)] for i in range(2)]

    def _mat_inv(self, m):
        """2x2 matrix inverse."""
        det = m[0][0]*m[1][1] - m[0][1]*m[1][0]
        if abs(det) < 1e-12:
            return [[1, 0], [0, 1]]
        return [
            [m[1][1]/det, -m[0][1]/det],
            [-m[1][0]/det, m[0][0]/det]
        ]

    def _outer(self, a, b):
        """Outer product of two vectors."""
        return [[a[i]*b[j] for j in range(2)] for i in range(2)]

    def predict(self):
        """Predict step: propagate state and covariance forward.

        x_pred = F * x  (F = I, so state doesn't change)
        P_pred = F * P * F^T + Q  (covariance grows by process noise)
        """
        if self.x is None:
            return
        # State prediction (identity transition)
        # x stays the same
        # Covariance prediction: P = P + Q
        self.P = self._mat_add(self.P, self.Q)

    def update(self, z):
        """Update step: incorporate measurement z = [humidity, temp].

        K = P_pred * H^T * (H * P_pred * H^T + R)^-1
          = P * (P + R)^-1  (since H = I)

        x = x + K * (z - H*x)
        P = (I - K*H) * P
          = (I - K) * P  (since H = I)
        """
        if self.x is None:
            self.x = z[:]
            self.P = [[self.R[0][0], 0], [0, self.R[1][1]]]
            return self.x[:], None

        # Innovation: measurement - prediction
        innovation = [z[i] - self.x[i] for i in range(2)]

        # Kalman gain: K = P * (P + R)^-1
        pr = self._mat_add(self.P, self.R)
        pr_inv = self._mat_inv(pr)
        K = self._mat_mult(self.P, pr_inv)

        # Update state: x = x + K * innovation
        for i in range(2):
            self.x[i] += K[i][0]*innovation[0] + K[i][1]*innovation[1]

        # Update covariance: P = (I - K) * P
        I_K = [[1 - K[0][0], -K[0][1]], [-K[1][0], 1 - K[1][1]]]
        self.P = self._mat_mult(I_K, self.P)

        return self.x[:], K

    def filter(self, measurements):
        """Apply Kalman filter to a sequence of [humidity, temp] measurements."""
        results = []
        for z in measurements:
            self.predict()
            result = self.update(z)
            results.append({
                "filtered": result[0],
                "kalman_gain": result[1],
            })
        return results

    def predict_future(self, steps=1):
        """Predict future state by running predict() without measurements.

        Each step adds process noise to covariance, so uncertainty grows.
        The state estimate stays the same (random walk with zero drift).
        """
        for _ in range(steps):
            self.predict()
        return {
            "state": self.x[:],
            "covariance": self.P[:],
            "uncertainty_humidity": math.sqrt(self.P[0][0]),
            "uncertainty_temp": math.sqrt(self.P[1][1]),
        }


def load_drift_log():
    """Load historical drift log entries."""
    entries = []
    if not DRIFT_LOG.exists():
        return entries
    for line in DRIFT_LOG.read_text().strip().split("\n"):
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def main():
    print("=" * 60)
    print("C565: 2D Kalman Filter — State-Space Model for DHT22")
    print("=" * 60)

    readings = load_drift_log()
    if not readings:
        print("No sensor data available")
        return None

    measurements = [[r["humidity"], r["temp"]] for r in readings]

    # Run Kalman filter
    kf = KalmanFilter2D()
    results = kf.filter(measurements)

    print(f"\nProcessed {len(readings)} readings")
    print(f"\n{'Step':>4} {'Raw H':>8} {'Raw T':>8} {'Filt H':>8} {'Filt T':>8} {'K_h':>8} {'K_t':>8}")
    print("-" * 70)
    for i, (result, meas) in enumerate(zip(results, measurements)):
        k_h = result["kalman_gain"][0][0] if result["kalman_gain"] else None
        k_t = result["kalman_gain"][1][1] if result["kalman_gain"] else None
        kh_str = f"{k_h:.4f}" if k_h is not None else "  init"
        kt_str = f"{k_t:.4f}" if k_t is not None else "  init"
        print(f"{i+1:>4} {meas[0]:>8.1f} {meas[1]:>8.1f} "
              f"{result['filtered'][0]:>8.2f} {result['filtered'][1]:>8.2f} "
              f"{kh_str:>8} {kt_str:>8}")

    # Forward prediction
    future = kf.predict_future(steps=1)
    print(f"\n--- Forward Prediction (next reading) ---")
    print(f"Predicted humidity: {future['state'][0]:.2f}% +/- {future['uncertainty_humidity']:.2f}%")
    print(f"Predicted temp:     {future['state'][1]:.2f}C +/- {future['uncertainty_temp']:.2f}C")

    # Confidence intervals
    h_pred = future["state"][0]
    h_unc = future["uncertainty_humidity"]
    t_pred = future["state"][1]
    t_unc = future["uncertainty_temp"]

    # 95% confidence interval (2-sigma)
    h_lo, h_hi = h_pred - 2*h_unc, h_pred + 2*h_unc
    t_lo, t_hi = t_pred - 2*t_unc, t_pred + 2*t_unc

    print(f"\n95% CI humidity: [{h_lo:.2f}%, {h_hi:.2f}%]")
    print(f"95% CI temp:     [{t_lo:.2f}C, {t_hi:.2f}C]")

    # Variance comparison: raw vs filtered
    raw_h_var = sum((m[0] - sum(mm[0] for mm in measurements)/len(measurements))**2
                    for m in measurements) / max(len(measurements) - 1, 1)
    filt_h_values = [r["filtered"][0] for r in results]
    filt_h_var = sum((v - sum(filt_h_values)/len(filt_h_values))**2
                     for v in filt_h_values) / max(len(filt_h_values) - 1, 1)

    print(f"\n--- Variance Reduction ---")
    print(f"Raw humidity variance:    {raw_h_var:.4f}")
    print(f"Filtered humidity variance: {filt_h_var:.4f}")
    print(f"Variance reduction: {(1 - filt_h_var/raw_h_var)*100:.1f}%")

    # Build prediction artifact
    prediction = {
        "id": "P_C565_KALMAN_2D_PREDICTION",
        "cycle": 565,
        "type": "forward_prediction",
        "description": "2D Kalman filter predicts next ESP32 DHT22 reading",
        "prediction": {
            "humidity": round(h_pred, 2),
            "humidity_95ci_low": round(h_lo, 2),
            "humidity_95ci_high": round(h_hi, 2),
            "temperature": round(t_pred, 2),
            "temperature_95ci_low": round(t_lo, 2),
            "temperature_95ci_high": round(t_hi, 2),
        },
        "model": {
            "type": "KalmanFilter2D",
            "q_humidity": 0.001,
            "q_temp": 0.0001,
            "r_humidity": 4.0,
            "r_temp": 0.25,
            "n_training_readings": len(readings),
        },
        "validate_at": "2026-06-01T00:00:00Z",
        "grading_criteria": "CORRECT if actual reading within 95% CI, "
                           "MOSTLY_CORRECT if within 3-sigma, INCORRECT otherwise",
        "created": datetime.now(timezone.utc).isoformat(),
    }

    # Save prediction
    pred_path = Path("state/predictions/P_C565_KALMAN_2D_PREDICTION.json")
    pred_path.write_text(json.dumps(prediction, indent=2) + "\n")
    print(f"\nPrediction saved to {pred_path}")

    # Save full report
    report = {
        "cycle": 565,
        "tool": "kalman_2d_prediction.py",
        "description": "2D Kalman filter state-space model for DHT22",
        "kalman_analysis": {
            "n_readings": len(readings),
            "filtered_states": [
                {"humidity": round(r["filtered"][0], 4), "temp": round(r["filtered"][1], 4)}
                for r in results
            ],
            "variance_reduction_pct": round((1 - filt_h_var/raw_h_var)*100, 1),
            "final_state": {
                "humidity": round(kf.x[0], 4),
                "temp": round(kf.x[1], 4),
            },
            "final_covariance": {
                "humidity": round(kf.P[0][0], 6),
                "temp": round(kf.P[1][1], 6),
            },
        },
        "forward_prediction": prediction,
        "created": datetime.now(timezone.utc).isoformat(),
    }

    report_path = Path("state/kalman_2d_report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Report saved to {report_path}")

    return report


if __name__ == '__main__':
    main()
