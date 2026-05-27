#!/usr/bin/env python3
"""
ESP32 Sensor Baseline Diagnostic
Uses Lyla's shared hardware_service.py to establish a baseline reading
for P_C524_SENSOR_DRIFT validation.

Checks:
  - All sensor endpoints respond with valid data
  - Humidity trend direction (compared to previous readings)
  - Temperature consistency with room expectations
  - Touch sensor responsiveness
  - Device health (WiFi, NTP sync)
"""

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, '/droid/repos/cl_shared')
from esp32.hardware_service import ESP32Service

STATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'state')
BASELINE_FILE = os.path.join(STATE_DIR, 'sensor_baseline.json')


def load_previous_baseline():
    """Load previous baseline reading for comparison."""
    if os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE, 'r') as f:
            return json.load(f)
    return None


def check_humidity_trend():
    """Check if humidity is drifting upward by examining state file history."""
    # Read recent readings from context
    context_file = os.path.join(STATE_DIR, 'memories', 'context.json')
    if not os.path.exists(context_file):
        return None, "No context data available"

    with open(context_file, 'r') as f:
        ctx = json.load(f)

    sensors = ctx.get('sensors', {})
    humidity = sensors.get('humidity', '')
    # Extract numeric value from "96.1% (possible drift)"
    try:
        historical = float(humidity.split('%')[0])
    except (ValueError, IndexError):
        return None, f"Could not parse historical humidity: {humidity}"

    return historical, f"Previous: {historical}% -> Current reading will be compared"


def run_baseline():
    service = ESP32Service()
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Full diagnostic
    diag = service.diagnose()
    historical_humidity, trend_note = check_humidity_trend()

    report = {
        'cycle': 526,
        'timestamp': timestamp,
        'device_status': diag.get('device', 'unknown'),
        'wifi': {
            'rssi_dbm': diag.get('wifi_rssi'),
            'status': diag.get('wifi_status'),
            'quality': 'good' if diag.get('wifi_rssi', 0) > -70 else 'weak'
        },
        'ntp_synced': diag.get('ntp_synced', False),
        'sensors': {
            'temperature': diag.get('dht', {}).get('temp_c'),
            'humidity': diag.get('dht', {}).get('humidity_pct'),
            'touch_active': diag.get('touch', {}).get('active'),
        },
        'trend': {
            'historical_humidity': historical_humidity,
            'note': trend_note,
        },
        'checks': {}
    }

    # Validation checks
    s = report['sensors']
    report['checks']['temp_valid'] = 15 <= s['temperature'] <= 35
    report['checks']['humidity_valid'] = 0 < s['humidity'] <= 100
    report['checks']['humidity_drift'] = s['humidity'] > 90
    report['checks']['wifi_strong'] = diag.get('wifi_rssi', 0) > -70
    report['checks']['ntp_synced'] = diag.get('ntp_synced', False)

    # Compare with historical if available
    if historical_humidity:
        drift = s['humidity'] - historical_humidity
        report['checks']['humidity_drift_direction'] = drift >= 0
        report['checks']['humidity_drift_amount'] = round(drift, 1)

    # Save baseline
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(BASELINE_FILE, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(f"=== C526 Sensor Baseline Diagnostic ===")
    print(f"Timestamp: {timestamp}")
    print(f"Device: {report['device_status']}")
    print(f"Temp: {s['temperature']}°C | Humidity: {s['humidity']}%")
    print(f"WiFi: {report['wifi']['rssi_dbm']}dBm ({report['wifi']['quality']})")
    print(f"NTP synced: {diag.get('ntp_synced')}")
    print(f"Touch: {'ACTIVE' if s['touch_active'] else 'IDLE'}")
    print()

    passed = sum(report['checks'].values())
    total = len(report['checks'])
    print(f"Checks: {passed}/{total} passed")
    for check, result in report['checks'].items():
        status = 'PASS' if result else 'FAIL'
        print(f"  [{status}] {check}")

    if s['humidity'] > 90:
        print(f"\nNOTE: Humidity at {s['humidity']}% — consistent with DHT22 upward drift hypothesis")
        print(f"P_C524_SENSOR_DRIFT validation date: 2026-06-03")

    return report


if __name__ == '__main__':
    run_baseline()
