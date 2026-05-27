#!/usr/bin/env python3
"""
ESP32 Multi-Sensor Coordinator — Unified polling for all sensor endpoints

Replaces the motion-only daemon (esp32_sensor_daemon.py) with a coordinator
that polls every available sensor endpoint and logs state changes to patterns.jsonl.

Current ESP32 firmware endpoints:
  - /api/sensor/touch  → {"sensor":"touch","active":bool,"timestamp":"<ISO8601Z>"}
  - /api/sensor/motion → 404 (removed in firmware update)
  - /api/sensor/temp   → 404 (pending firmware update with DHT11/AM2302)
  - /api/sensor/humidity → 404 (pending firmware update with DHT11/AM2302)

Usage:
    python tools/esp32_sensor_coordinator.py [--daemon] [--interval 500]

Daemon mode: runs continuously, logs changes to patterns.jsonl
Single-shot: polls once and exits (useful for testing)
"""

import argparse
import json
import sys
import time
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError


# ---------------------------------------------------------------------------
# Sensor endpoint configuration
# ---------------------------------------------------------------------------

SENSOR_ENDPOINTS = {
    "touch": {
        "url": "http://192.168.4.38/api/sensor/touch",
        "available": None,  # set to True/False on first probe
    },
    "motion": {
        "url": "http://192.168.4.38/api/sensor/motion",
        "available": None,
    },
    "temp": {
        "url": "http://192.168.4.38/api/sensor/temp",
        "available": None,
    },
    "humidity": {
        "url": "http://192.168.4.38/api/sensor/humidity",
        "available": None,
    },
}

PATTERNS_FILE = "state/memories/patterns.jsonl"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def probe_endpoint(url, timeout=2):
    """Try to reach a sensor endpoint. Returns (available, data_or_None)."""
    try:
        req = Request(url)
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            return True, data
    except Exception:
        return False, None


def read_sensor(endpoint_cfg):
    """Read one sensor endpoint. Returns (available, data)."""
    if endpoint_cfg["available"] is False:
        # Already known to be down, skip retry
        return False, None
    available, data = probe_endpoint(endpoint_cfg["url"])
    endpoint_cfg["available"] = available
    return available, data


# ---------------------------------------------------------------------------
# State change detection
# ---------------------------------------------------------------------------

class SensorStateTracker:
    """Tracks last-seen values per sensor and detects changes."""

    def __init__(self):
        self.last_values = {}

    def has_changed(self, sensor_name, data):
        value = data.get("active") if "active" in data else data.get("value")
        if value is None:
            # For temp/humidity, compare the whole dict
            value = data
        return self.last_values.get(sensor_name) != value

    def record(self, sensor_name, data):
        value = data.get("active") if "active" in data else data.get("value")
        if value is None:
            value = data
        self.last_values[sensor_name] = value


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_pattern(sensor_name, event_type, data):
    """Append a sensor event to patterns.jsonl."""
    os.makedirs("state/memories", exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "sensor": sensor_name,
        **data,
    }
    with open(PATTERNS_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def poll_all():
    """Poll all sensor endpoints. Returns dict of {sensor: data}."""
    results = {}
    for name, cfg in SENSOR_ENDPOINTS.items():
        available, data = read_sensor(cfg)
        if available:
            results[name] = data
    return results


def run_coordinator(daemon=False, interval_ms=500):
    tracker = SensorStateTracker()
    events_logged = 0

    print(f"🟢 ESP32 Multi-Sensor Coordinator starting...")
    print(f"   Poll interval: {interval_ms}ms")
    print(f"   Sensors: {', '.join(SENSOR_ENDPOINTS.keys())}")
    print(f"   Daemon: {daemon}")
    print(f"   Press Ctrl+C to stop\n")

    try:
        while True:
            results = poll_all()
            now = datetime.now(timezone.utc).isoformat()

            for name, data in results.items():
                if tracker.has_changed(name, data):
                    tracker.record(name, data)
                    value = data.get("active") if "active" in data else data.get("value")
                    event_type = f"{name}_{value}"
                    log_pattern(name, event_type, {
                        "esp32_timestamp": data.get("timestamp"),
                        "simulated": False,
                    })
                    print(f"[{now}] {event_type}")
                    events_logged += 1

            if not daemon:
                # Single-shot: print summary and exit
                print(f"\n--- Poll results ({len(results)} sensors) ---")
                for name, data in results.items():
                    print(f"  {name}: {json.dumps(data)}")
                print(f"\nEvents logged: {events_logged}")
                break

            time.sleep(interval_ms / 1000.0)

    except KeyboardInterrupt:
        print(f"\n🛑 Coordinator stopped. Events logged: {events_logged}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ESP32 Multi-Sensor Coordinator")
    parser.add_argument("--daemon", action="store_true",
                        help="Run continuously (default: single-shot)")
    parser.add_argument("--interval", type=int, default=500,
                        help="Poll interval in ms (default: 500)")
    parser.add_argument("--host", default="192.168.4.38",
                        help="ESP32 host address")
    parser.add_argument("--probe", action="store_true",
                        help="Probe all endpoints and exit (no polling)")
    args = parser.parse_args()

    if args.probe:
        print("Probing endpoints...")
        for name, cfg in SENSOR_ENDPOINTS.items():
            available, data = probe_endpoint(cfg["url"])
            status = "ONLINE" if available else "OFFLINE"
            info = ""
            if available:
                info = f" → {json.dumps(data)}"
            print(f"  {name}: {status}{info}")
        return

    run_coordinator(daemon=args.daemon, interval_ms=args.interval)


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    main()
