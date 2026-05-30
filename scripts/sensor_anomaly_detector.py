#!/usr/bin/env python3
"""Sensor Anomaly Detector — statistical anomaly detection on DHT22 time series.

Applies z-score and IQR methods to detect anomalies in raw sensor readings
and calibrated readings. Distinguishes between:
  - SENSOR anomaly: raw reading jumps while environment likely stable
  - ENVIRONMENTAL change: consistent shift across readings

Usage:
  python3 scripts/sensor_anomaly_detector.py [--ip <IP>] [--collect] [--min-readings N]
  --collect: Fetch live reading and append to anomaly log
  --min-readings: Minimum readings before anomaly detection activates (default: 5)
"""

import argparse
import json
import math
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ANOMALY_LOG = Path("state/sensor_anomaly_log.jsonl")
MIN_READINGS = 5  # minimum data points for meaningful stats


def fetch_dht22(ip: str, timeout: int = 10) -> dict | None:
    url = f"http://{ip}/api/sensor/dht"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "c0rtana-anomaly")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [WARN] Fetch failed: {e}")
        return None


def load_readings(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    readings = []
    for line in log_path.read_text().strip().split("\n"):
        line = line.strip()
        if line:
            readings.append(json.loads(line))
    return readings


def append_reading(log_path: Path, reading: dict) -> None:
    content = log_path.read_text().rstrip() + "\n" + json.dumps(reading) + "\n" if log_path.exists() and log_path.read_text().strip() else json.dumps(reading) + "\n"
    log_path.write_text(content)


def compute_stats(values: list[float]) -> dict:
    n = len(values)
    if n < 2:
        return {"mean": values[0] if values else 0, "std": 0, "median": values[0] if values else 0, "q1": 0, "q3": 0, "iqr": 0}

    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0
    std = math.sqrt(variance)

    sorted_v = sorted(values)
    median = sorted_v[n // 2] if n % 2 else (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2

    q1_idx = n // 4
    q3_idx = (3 * n) // 4
    q1 = sorted_v[q1_idx]
    q3 = sorted_v[q3_idx]
    iqr = q3 - q1

    return {"mean": mean, "std": std, "median": median, "q1": q1, "q3": q3, "iqr": iqr}


def z_score(value: float, mean: float, std: float) -> float:
    return abs(value - mean) / std if std > 0 else 0.0


def iqr_anomaly(value: float, q1: float, q3: float, multiplier: float = 1.5) -> float:
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    if value < lower:
        return (q3 + 1) / 100  # normalize to 0-1 scale
    if value > upper:
        return (value - q1) / (iqr + 1) / 100
    return 0.0


def detect_anomalies(readings: list[dict], latest: dict, min_readings: int = MIN_READINGS) -> dict:
    if len(readings) < min_readings:
        return {
            "status": "COLLECTING",
            "message": f"Need {min_readings} readings minimum (have {len(readings)}). Anomaly detection disabled until sufficient data.",
            "readings_count": len(readings),
        }

    raw_humidities = [r["raw_humidity"] for r in readings]
    raw_temps = [r["raw_temp"] for r in readings]
    cal_humidities = [r.get("calibrated_humidity") for r in readings if "calibrated_humidity" in r]
    cal_temps = [r.get("calibrated_temp") for r in readings if "calibrated_temp" in r]

    h_stats = compute_stats(raw_humidities)
    t_stats = compute_stats(raw_temps)

    # Z-score analysis on raw readings
    h_z = z_score(latest["raw_humidity"], h_stats["mean"], h_stats["std"])
    t_z = z_score(latest["raw_temp"], t_stats["mean"], t_stats["std"])

    # IQR analysis
    h_iqr_score = iqr_anomaly(latest["raw_humidity"], h_stats["q1"], h_stats["q3"])
    t_iqr_score = iqr_anomaly(latest["raw_temp"], t_stats["q1"], t_stats["q3"])

    # Classify
    h_anomaly = h_z > 2.0 or h_iqr_score > 0.5
    t_anomaly = t_z > 2.0 or t_iqr_score > 0.5

    if h_anomaly or t_anomaly:
        # Check if calibrated reading is also anomalous (environmental change)
        # or if only raw is anomalous (sensor glitch)
        if cal_humidities:
            cal_stats = compute_stats(cal_humidities)
            cal_h_z = z_score(latest.get("calibrated_humidity", 0), cal_stats["mean"], cal_stats["std"])
            if cal_h_z < 1.5:
                anomaly_type = "ENVIRONMENTAL"
                explanation = "Raw reading shifted but calibrated value stable — environment changed, not sensor"
            else:
                anomaly_type = "SENSOR"
                explanation = "Both raw and calibrated readings anomalous — possible sensor malfunction"
        else:
            anomaly_type = "UNKNOWN"
            explanation = "Raw reading anomalous, insufficient calibrated data to classify"
    else:
        anomaly_type = "NORMAL"
        explanation = "Reading within expected range"

    return {
        "status": "ACTIVE",
        "anomaly_type": anomaly_type,
        "explanation": explanation,
        "readings_count": len(readings),
        "latest": {
            "raw_humidity": latest["raw_humidity"],
            "raw_temp": latest["raw_temp"],
        },
        "humidity_stats": {k: round(v, 3) for k, v in h_stats.items()},
        "temp_stats": {k: round(v, 3) for k, v in t_stats.items()},
        "z_scores": {
            "humidity": round(h_z, 3),
            "temp": round(t_z, 3),
        },
        "iqr_scores": {
            "humidity": round(h_iqr_score, 3),
            "temp": round(t_iqr_score, 3),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Sensor anomaly detector")
    parser.add_argument("--ip", default="192.168.4.38")
    parser.add_argument("--collect", action="store_true", help="Fetch and log reading")
    parser.add_argument("--min-readings", type=int, default=MIN_READINGS)
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    print("=== Sensor Anomaly Detector ===")
    print(f"  Time: {now.isoformat()}")
    print(f"  Target: {args.ip}")
    print()

    # Load existing readings
    readings = load_readings(ANOMALY_LOG)
    print(f"  Historical readings: {len(readings)}")

    # Fetch live reading
    sensor = fetch_dht22(args.ip)
    if not sensor:
        print("No sensor data. Exiting.")
        sys.exit(1)

    raw_h = sensor.get("humidity")
    raw_t = sensor.get("temp")
    print(f"  Raw: {raw_h}% humidity, {raw_t}°C")

    # Compute calibrated values for tracking
    DIRECT_BIAS_H = 37.0
    DIRECT_BIAS_T = 2.82
    cal_h = round(raw_h - DIRECT_BIAS_H, 2)
    cal_t = round(raw_t - DIRECT_BIAS_T, 2)
    print(f"  Direct-corrected: {cal_h}% humidity, {cal_t}°C")
    print()

    # Build reading entry
    reading_entry = {
        "timestamp": now.isoformat(),
        "raw_humidity": raw_h,
        "raw_temp": raw_t,
        "calibrated_humidity": cal_h,
        "calibrated_temp": cal_t,
    }

    # Run anomaly detection against historical data
    result = detect_anomalies(readings, reading_entry, args.min_readings)
    result["timestamp"] = now.isoformat()

    if args.collect:
        append_reading(ANOMALY_LOG, reading_entry)
        print(f"  Reading logged ({len(readings) + 1} total)")

    print(f"  Status: {result['status']}")
    if result.get("anomaly_type"):
        print(f"  Anomaly: {result['anomaly_type']}")
        print(f"  Explanation: {result.get('explanation', 'N/A')}")
    if result.get("z_scores"):
        print(f"  Z-scores: humidity={result['z_scores']['humidity']}, temp={result['z_scores']['temp']}")
    if result.get("humidity_stats"):
        print(f"  Humidity stats: mean={result['humidity_stats']['mean']}, std={result['humidity_stats']['std']}")

    # Save report
    report_path = "state/sensor_anomaly_report.json"
    Path(report_path).write_text(json.dumps(result, indent=2))
    print(f"\n  Report saved to {report_path}")

    return result


if __name__ == "__main__":
    main()
