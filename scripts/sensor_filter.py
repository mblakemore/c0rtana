#!/usr/bin/env python3
"""
Exponential Moving Average (EMA) low-pass filter for DHT22 sensor data.

Separates oscillation from underlying drift trend to validate
the C562 non-monotonic humidity hypothesis.

Usage:
    python3 scripts/sensor_filter.py [--live] [--alpha ALPHA]

--live: Fetch fresh reading from ESP32 before analysis
--alpha: EMA smoothing factor (default 0.3, lower = more smoothing)
"""

import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DRIFT_LOG = Path("state/sensor_drift_log.jsonl")
ESP32_URL = "http://192.168.4.38/api/sensor/dht"


def ema_filter(values, alpha=0.3):
    """Apply exponential moving average smoothing."""
    if not values:
        return []
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return result


def high_pass(values, alpha=0.3):
    """Extract oscillation component by subtracting low-pass from raw."""
    low = ema_filter(values, alpha)
    return [round(raw - smooth, 4) for raw, smooth in zip(values, low)]


def monotonic_test(values):
    """Check if series is monotonically increasing/decreasing."""
    if len(values) < 2:
        return "insufficient data"
    diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
    increasing = all(d >= 0 for d in diffs)
    decreasing = all(d <= 0 for d in diffs)
    if increasing:
        return "monotonically increasing"
    if decreasing:
        return "monotonically decreasing"
    sign_changes = sum(1 for i in range(len(diffs)-1)
                       if diffs[i] * diffs[i+1] < 0)
    return f"non-monotonic ({sign_changes} direction changes)"


def fetch_live_reading():
    """Fetch current DHT22 reading from ESP32."""
    try:
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "5", ESP32_URL],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "humidity": data.get("humidity"),
                "temp": data.get("temp"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "raw_timestamp": data.get("timestamp", ""),
                "source": "live"
            }
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def load_drift_log():
    """Load historical drift log entries."""
    entries = []
    if not DRIFT_LOG.exists():
        return entries
    for line in DRIFT_LOG.read_text().strip().split("\n"):
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def analyze(readings, alpha=0.3):
    """Run full analysis on sensor readings."""
    if not readings:
        return {"error": "no readings"}

    humidities = [r["humidity"] for r in readings]
    temps = [r["temp"] for r in readings]
    timestamps = [r.get("raw_timestamp", r.get("timestamp", "")) for r in readings]

    # EMA smoothing
    humidity_ema = ema_filter(humidities, alpha)
    temp_ema = ema_filter(temps, alpha)

    # Oscillation component
    humidity_osc = high_pass(humidities, alpha)
    temp_osc = high_pass(temps, alpha)

    # Monotonicity
    humidity_mono = monotonic_test(humidities)
    temp_mono = monotonic_test(temps)
    humidity_ema_mono = monotonic_test(humidity_ema)
    temp_ema_mono = monotonic_test(temp_ema)

    # Oscillation amplitude (peak-to-peak of oscillation component)
    if humidity_osc:
        humidity_osc_amp = max(humidity_osc) - min(humidity_osc)
    else:
        humidity_osc_amp = 0

    # Trend from EMA endpoints
    humidity_trend = humidity_ema[-1] - humidity_ema[0] if len(humidity_ema) > 1 else 0
    temp_trend = temp_ema[-1] - temp_ema[0] if len(temp_ema) > 1 else 0

    # Time span
    time_span = f"{len(readings)} readings"
    if len(readings) >= 2:
        first_ts = readings[0].get("raw_timestamp", readings[0].get("timestamp", ""))
        last_ts = readings[-1].get("raw_timestamp", readings[-1].get("timestamp", ""))
        time_span += f" ({first_ts} to {last_ts})"

    return {
        "tool": "sensor_filter.py",
        "description": "EMA low-pass filter for DHT22 oscillation analysis",
        "alpha": alpha,
        "n_readings": len(readings),
        "time_span": time_span,
        "humidity": {
            "raw": humidities,
            "ema_smoothed": [round(v, 4) for v in humidity_ema],
            "oscillation_component": humidity_osc,
            "oscillation_amplitude": round(humidity_osc_amp, 4),
            "monotonicity_raw": humidity_mono,
            "monotonicity_ema": humidity_ema_mono,
            "trend_ema": round(humidity_trend, 4),
            "range": round(max(humidities) - min(humidities), 4),
        },
        "temperature": {
            "raw": temps,
            "ema_smoothed": [round(v, 4) for v in temp_ema],
            "oscillation_component": temp_osc,
            "monotonicity_raw": temp_mono,
            "monotonicity_ema": temp_ema_mono,
            "trend_ema": round(temp_trend, 4),
            "range": round(max(temps) - min(temps), 4),
        },
        "per_reading_detail": [
            {
                "timestamp": ts,
                "humidity_raw": h,
                "humidity_ema": round(ema_h, 4),
                "humidity_osc": round(osc_h, 4),
                "temp_raw": t,
                "temp_ema": round(ema_t, 4),
            }
            for ts, h, ema_h, osc_h, t, ema_t in zip(
                timestamps, humidities, humidity_ema, humidity_osc,
                temps, temp_ema
            )
        ],
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="DHT22 sensor EMA filter")
    parser.add_argument("--live", action="store_true",
                        help="Fetch fresh ESP32 reading before analysis")
    parser.add_argument("--alpha", type=float, default=0.3,
                        help="EMA smoothing factor (default 0.3)")
    args = parser.parse_args()

    # Load historical data
    readings = load_drift_log()

    # Optionally fetch live reading
    if args.live:
        live = fetch_live_reading()
        if live:
            readings.append(live)
            # Append to drift log
            DRIFT_LOG.write_text(
                DRIFT_LOG.read_text().rstrip() + "\n" +
                json.dumps(live, indent=None) + "\n"
            )
            print(f"Live reading: humidity={live['humidity']}%, temp={live['temp']}C")
        else:
            print("Warning: could not fetch live reading from ESP32")

    if not readings:
        print("No sensor data available")
        sys.exit(1)

    # Run analysis
    report = analyze(readings, args.alpha)

    # Print summary
    print(f"\n{'='*60}")
    print(f"DHT22 Sensor Filter Analysis")
    print(f"{'='*60}")
    print(f"Readings: {report['n_readings']}")
    print(f"Alpha (smoothing): {report['alpha']}")
    print(f"\nHumidity:")
    print(f"  Raw range: {report['humidity']['range']}%")
    print(f"  Raw monotonicity: {report['humidity']['monotonicity_raw']}")
    print(f"  EMA monotonicity: {report['humidity']['monotonicity_ema']}")
    print(f"  Oscillation amplitude: {report['humidity']['oscillation_amplitude']}%")
    print(f"  EMA trend: {report['humidity']['trend_ema']}%")
    print(f"\nTemperature:")
    print(f"  Raw range: {report['temperature']['range']}C")
    print(f"  Raw monotonicity: {report['temperature']['monotonicity_raw']}")
    print(f"  EMA monotonicity: {report['temperature']['monotonicity_ema']}")
    print(f"  EMA trend: {report['temperature']['trend_ema']}C")

    # Write report
    report_path = Path("state/sensor_filter_report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nReport written to {report_path}")

    return report


if __name__ == "__main__":
    main()
