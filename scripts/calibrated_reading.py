#!/usr/bin/env python3
"""
Calibrated Sensor Reading Pipeline
Fetches fresh DHT22 data from ESP32 and applies C566 Kalman bias corrections
to produce estimated true room conditions with uncertainty bounds.

Usage: python3 scripts/calibrated_reading.py [--ip <IP>] [--save]
"""

import argparse
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone


def fetch_dht22(ip: str, timeout: int = 10) -> dict | None:
    """Fetch current DHT22 reading from ESP32."""
    url = f"http://{ip}/api/sensor/dht"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as e:
        print(f"Failed to fetch DHT22: {e}")
        return None


def apply_calibration(raw_humidity: float, raw_temp: float,
                      bias_humidity: float, bias_temp: float,
                      uncertainty_humidity: float, uncertainty_temp: float) -> dict:
    """Apply systematic bias correction and compute uncertainty bounds."""
    corrected_humidity = raw_humidity - bias_humidity
    corrected_temp = raw_temp - bias_temp

    # Combined uncertainty: sensor noise + calibration uncertainty
    # DHT22 spec: +/-2% humidity, +/-0.5C temp
    sensor_noise_h = 2.0
    sensor_noise_t = 0.5

    total_uncertainty_h = (sensor_noise_h ** 2 + uncertainty_humidity ** 2) ** 0.5
    total_uncertainty_t = (sensor_noise_t ** 2 + uncertainty_temp ** 2) ** 0.5

    return {
        "raw_humidity": raw_humidity,
        "raw_temp": raw_temp,
        "bias_humidity": bias_humidity,
        "bias_temp": bias_temp,
        "corrected_humidity": round(corrected_humidity, 2),
        "corrected_temp": round(corrected_temp, 2),
        "uncertainty_humidity_95ci": round(total_uncertainty_h, 2),
        "uncertainty_temp_95ci": round(total_uncertainty_t, 2),
        "humidity_95ci_low": round(corrected_humidity - 1.96 * total_uncertainty_h, 2),
        "humidity_95ci_high": round(corrected_humidity + 1.96 * total_uncertainty_h, 2),
        "temp_95ci_low": round(corrected_temp - 1.96 * total_uncertainty_t, 2),
        "temp_95ci_high": round(corrected_temp + 1.96 * total_uncertainty_t, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Calibrated sensor reading pipeline")
    parser.add_argument("--ip", default="192.168.4.38", help="ESP32 IP address")
    parser.add_argument("--save", action="store_true", help="Save report to state/ directory")
    args = parser.parse_args()

    # C566 Kalman bias estimation results
    calibration = {
        "bias_humidity": 45.93,
        "bias_temp": 3.86,
        "uncertainty_humidity": 0.2236,
        "uncertainty_temp": 0.0707,
        "source": "C566 KalmanBiasEstimator, n=6 readings + 1 Creator ground truth",
        "ground_truth": {
            "humidity": 61.0,
            "temp_celsius": 18.28,
            "source": "Creator direct measurement",
        },
    }

    print("=== Calibrated Sensor Reading Pipeline ===")
    print(f"Target: {args.ip}")
    now = datetime.now(timezone.utc)
    print(f"Timestamp: {now.isoformat()}")
    print(f"Calibration: {calibration['source']}")
    print()

    raw = fetch_dht22(args.ip)
    if not raw:
        print("No sensor data available. Exiting.")
        return

    raw_humidity = raw.get("humidity")
    raw_temp = raw.get("temp")

    if raw_humidity is None or raw_temp is None:
        print(f"Invalid sensor data: {raw}")
        return

    print(f"Raw DHT22 reading:")
    print(f"  Humidity: {raw_humidity}%")
    print(f"  Temperature: {raw_temp}°C")
    print()

    result = apply_calibration(
        raw_humidity, raw_temp,
        calibration["bias_humidity"], calibration["bias_temp"],
        calibration["uncertainty_humidity"], calibration["uncertainty_temp"],
    )

    print(f"Calibrated (bias-corrected) reading:")
    print(f"  True humidity: {result['corrected_humidity']}% +/- {result['uncertainty_humidity_95ci']}%")
    print(f"    95% CI: [{result['humidity_95ci_low']}%, {result['humidity_95ci_high']}%]")
    print(f"  True temperature: {result['corrected_temp']}°C +/- {result['uncertainty_temp_95ci']}°C")
    print(f"    95% CI: [{result['temp_95ci_low']}°C, {result['temp_95ci_high']}°C]")
    print()

    # Compare against Creator ground truth
    gt_h = calibration["ground_truth"]["humidity"]
    gt_t = calibration["ground_truth"]["temp_celsius"]
    print(f"Reference (Creator ground truth):")
    print(f"  Humidity: {gt_h}%")
    print(f"  Temperature: {gt_t}°C")
    print(f"  Deviation from ground truth:")
    print(f"    Humidity: {result['corrected_humidity'] - gt_h:+.2f}%")
    print(f"    Temperature: {result['corrected_temp'] - gt_t:+.2f}°C")

    report = {
        "cycle": 567,
        "tool": "calibrated_reading.py",
        "timestamp": now.isoformat(),
        "esp32_ip": args.ip,
        "dht22_timestamp": raw.get("timestamp"),
        "calibration_source": calibration["source"],
        "ground_truth": calibration["ground_truth"],
        "reading": result,
    }

    if args.save:
        report_path = "state/calibrated_reading_c567.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to {report_path}")

    print(f"\n=== JSON Report ===")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
