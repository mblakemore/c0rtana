#!/usr/bin/env python3
"""Calibration Health Monitor — tracks DHT22 calibration health over time.

Fetches live ESP32 DHT22 data, applies bias corrections, and compares
against Creator ground truth to determine if calibration is still valid
or if environmental change warrants a new reference measurement.

Health states:
  STABLE — calibrated reading within tolerance of GT (environment unchanged)
  DRIFTING — approaching threshold (monitor closely)
  RECALIBRATE — environment likely changed (new GT measurement recommended)

Usage: python3 scripts/calibration_health_monitor.py [--ip <IP>] [--save]
"""

import argparse
import json
import math
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# C566 Kalman bias estimation
KALMAN_BIAS_HUMIDITY = 45.93
KALMAN_BIAS_TEMP = 3.86
KALMAN_UNCERTAINTY_H = 0.2236
KALMAN_UNCERTAINTY_T = 0.0707

# C568 direct observation (raw 98.0 - GT 61.0 = 37.0)
DIRECT_BIAS_HUMIDITY = 37.0
DIRECT_BIAS_TEMP = 2.82

# Creator ground truth reference
GT_HUMIDITY = 61.0
GT_TEMP = 18.28

# Health thresholds (in calibrated units)
TOLERANCE_HUMIDITY = 5.0   # % — within this = STABLE
TOLERANCE_TEMP = 2.0       # °C — within this = STABLE
DRIFT_MARGIN_HUMIDITY = 10.0  # % — beyond this = RECALIBRATE
DRIFT_MARGIN_TEMP = 4.0      # °C — beyond this = RECALIBRATE

HEALTH_LOG = Path("state/calibration_health_log.jsonl")


def fetch_dht22(ip: str, timeout: int = 10) -> dict | None:
    """Fetch current DHT22 reading from ESP32."""
    url = f"http://{ip}/api/sensor/dht"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "c0rtana-health")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [WARN] DHT22 fetch failed: {e}")
        return None


def fetch_esp32_status(ip: str, timeout: int = 5) -> dict | None:
    """Fetch ESP32 status for connectivity info."""
    url = f"http://{ip}/status"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "c0rtana-health")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [WARN] Status fetch failed: {e}")
        return None


def calibrate_reading(raw_h: float, raw_t: float,
                      bias_h: float, bias_t: float,
                      unc_h: float, unc_t: float) -> dict:
    """Apply bias correction and compute uncertainty bounds."""
    corrected_h = raw_h - bias_h
    corrected_t = raw_t - bias_t

    # DHT22 spec noise + calibration uncertainty
    sensor_noise_h = 2.0
    sensor_noise_t = 0.5

    total_unc_h = math.sqrt(sensor_noise_h ** 2 + unc_h ** 2)
    total_unc_t = math.sqrt(sensor_noise_t ** 2 + unc_t ** 2)

    return {
        "corrected_humidity": round(corrected_h, 2),
        "corrected_temp": round(corrected_t, 2),
        "uncertainty_humidity": round(total_unc_h, 2),
        "uncertainty_temp": round(total_unc_t, 2),
        "humidity_95ci_low": round(corrected_h - 1.96 * total_unc_h, 2),
        "humidity_95ci_high": round(corrected_h + 1.96 * total_unc_h, 2),
        "temp_95ci_low": round(corrected_t - 1.96 * total_unc_t, 2),
        "temp_95ci_high": round(corrected_t + 1.96 * total_unc_t, 2),
    }


def assess_health(kalman: dict, direct: dict) -> dict:
    """Assess calibration health by comparing calibrated readings to GT.

    Uses both Kalman (45.93% bias) and direct (37.0% bias) estimates
    to account for C568's finding that Kalman overestimates bias.
    """
    # Deviation from GT for both estimates
    kalman_dev_h = kalman["corrected_humidity"] - GT_HUMIDITY
    kalman_dev_t = kalman["corrected_temp"] - GT_TEMP
    direct_dev_h = direct["corrected_humidity"] - GT_HUMIDITY
    direct_dev_t = direct["corrected_temp"] - GT_TEMP

    # Use average of both estimates for health assessment
    avg_h = (kalman["corrected_humidity"] + direct["corrected_humidity"]) / 2
    avg_t = (kalman["corrected_temp"] + direct["corrected_temp"]) / 2
    avg_dev_h = avg_h - GT_HUMIDITY
    avg_dev_t = avg_t - GT_TEMP

    # Bias estimate range (uncertainty from method disagreement)
    bias_range_h = abs(KALMAN_BIAS_HUMIDITY - DIRECT_BIAS_HUMIDITY)
    bias_range_t = abs(KALMAN_BIAS_TEMP - DIRECT_BIAS_TEMP)

    # Classify
    if abs(avg_dev_h) <= TOLERANCE_HUMIDITY and abs(avg_dev_t) <= TOLERANCE_TEMP:
        status = "STABLE"
    elif abs(avg_dev_h) <= DRIFT_MARGIN_HUMIDITY and abs(avg_dev_t) <= DRIFT_MARGIN_TEMP:
        status = "DRIFTING"
    else:
        status = "RECALIBRATE"

    return {
        "status": status,
        "avg_calibrated_humidity": round(avg_h, 2),
        "avg_calibrated_temp": round(avg_t, 2),
        "deviation_humidity": round(avg_dev_h, 2),
        "deviation_temp": round(avg_dev_t, 2),
        "kalman_deviation_humidity": round(kalman_dev_h, 2),
        "kalman_deviation_temp": round(kalman_dev_t, 2),
        "direct_deviation_humidity": round(direct_dev_h, 2),
        "direct_deviation_temp": round(direct_dev_t, 2),
        "bias_estimate_range_humidity": round(bias_range_h, 2),
        "bias_estimate_range_temp": round(bias_range_t, 2),
        "tolerance_humidity": TOLERANCE_HUMIDITY,
        "tolerance_temp": TOLERANCE_TEMP,
    }


def log_health_entry(entry: dict) -> None:
    """Append health entry to time-series log."""
    if HEALTH_LOG.exists():
        HEALTH_LOG.write_text(
            HEALTH_LOG.read_text().rstrip() + "\n" + json.dumps(entry) + "\n"
        )
    else:
        HEALTH_LOG.write_text(json.dumps(entry) + "\n")


def compute_trend(log_path: Path) -> dict | None:
    """Compute trend from health log history."""
    if not log_path.exists():
        return None

    entries = []
    for line in log_path.read_text().strip().split("\n"):
        line = line.strip()
        if line:
            entries.append(json.loads(line))

    if len(entries) < 3:
        return {"entries": len(entries), "trend": "insufficient_data"}

    # Check if deviation is increasing (environment changing)
    recent = entries[-3:]
    deviations = [abs(e.get("deviation_humidity", 0)) for e in recent]

    if deviations[-1] > deviations[0] * 1.2:
        trend = "INCREASING"
    elif deviations[-1] < deviations[0] * 0.8:
        trend = "DECREASING"
    else:
        trend = "STABLE"

    return {
        "entries": len(entries),
        "trend": trend,
        "recent_deviations": deviations,
        "first_reading": entries[0].get("raw_humidity"),
        "last_reading": entries[-1].get("raw_humidity"),
    }


def main():
    parser = argparse.ArgumentParser(description="Calibration health monitor")
    parser.add_argument("--ip", default="192.168.4.38", help="ESP32 IP address")
    parser.add_argument("--save", action="store_true", help="Log to health log")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    print("=== Calibration Health Monitor ===")
    print(f"  Time: {now.isoformat()}")
    print(f"  Target: {args.ip}")
    print(f"  GT reference: {GT_HUMIDITY}% humidity, {GT_TEMP}°C")
    print()

    # Fetch live data
    sensor = fetch_dht22(args.ip)
    status = fetch_esp32_status(args.ip)

    if not sensor:
        print("No sensor data available. Cannot assess health.")
        sys.exit(1)

    raw_h = sensor.get("humidity")
    raw_t = sensor.get("temp")
    print(f"  Raw DHT22: {raw_h}% humidity, {raw_t}°C")

    if status:
        print(f"  ESP32 status: IP={status.get('ip')}, RSSI={status.get('rssi')}dBm")
    print()

    # Apply both calibration methods
    kalman_result = calibrate_reading(
        raw_h, raw_t,
        KALMAN_BIAS_HUMIDITY, KALMAN_BIAS_TEMP,
        KALMAN_UNCERTAINTY_H, KALMAN_UNCERTAINTY_T,
    )
    direct_result = calibrate_reading(
        raw_h, raw_t,
        DIRECT_BIAS_HUMIDITY, DIRECT_BIAS_TEMP,
        KALMAN_UNCERTAINTY_H, KALMAN_UNCERTAINTY_T,
    )

    print("  Kalman-corrected:  {:.2f}% humidity, {:.2f}°C".format(
        kalman_result["corrected_humidity"], kalman_result["corrected_temp"]))
    print("  Direct-corrected:  {:.2f}% humidity, {:.2f}°C".format(
        direct_result["corrected_humidity"], direct_result["corrected_temp"]))
    print()

    # Assess health
    health = assess_health(kalman_result, direct_result)
    status_emoji = {"STABLE": "OK", "DRIFTING": "WARN", "RECALIBRATE": "ACTION"}

    print(f"  Health: {health['status']} ({status_emoji.get(health['status'], '?')})")
    print(f"  Avg calibrated: {health['avg_calibrated_humidity']}% humidity, {health['avg_calibrated_temp']}°C")
    print(f"  Deviation from GT: {health['deviation_humidity']:+.2f}% humidity, {health['deviation_temp']:+.2f}°C")
    print(f"  Bias uncertainty range: {health['bias_estimate_range_humidity']}% humidity, {health['bias_estimate_range_temp']}°C")
    print()

    # Trend analysis
    if args.save:
        # Log before computing trend (so trend includes this entry)
        log_health_entry({
            "timestamp": now.isoformat(),
            "raw_humidity": raw_h,
            "raw_temp": raw_t,
            **health,
        })
        trend = compute_trend(HEALTH_LOG)
        if trend:
            print(f"  Trend ({trend['entries']} entries): {trend.get('trend', 'N/A')}")
            if trend.get("first_reading") and trend.get("last_reading"):
                print(f"    Raw range: {trend['first_reading']}% -> {trend['last_reading']}%")
        print()

    # Actionable recommendation
    if health["status"] == "STABLE":
        print("  Recommendation: Calibration is valid. No action needed.")
    elif health["status"] == "DRIFTING":
        print("  Recommendation: Environment may be changing. Consider requesting Creator GT measurement.")
    else:
        print("  Recommendation: Environment has likely changed. Request new ground-truth measurement from Creator.")

    # Save report
    report = {
        "cycle": 570,
        "tool": "calibration_health_monitor.py",
        "timestamp": now.isoformat(),
        "esp32_ip": args.ip,
        "ground_truth": {"humidity": GT_HUMIDITY, "temp": GT_TEMP},
        "raw_reading": {"humidity": raw_h, "temp": raw_t},
        "kalman_corrected": kalman_result,
        "direct_corrected": direct_result,
        "health": health,
    }

    if args.save:
        report_path = "state/calibration_health_report.json"
        Path(report_path).write_text(json.dumps(report, indent=2))
        print(f"\n  Report saved to {report_path}")

    print(f"\n=== JSON Report ===")
    print(json.dumps(report, indent=2))

    return report


if __name__ == "__main__":
    main()
