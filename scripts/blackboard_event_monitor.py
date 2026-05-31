#!/usr/bin/env python3
"""
ESP32 Event-Driven Blackboard Monitor — Technique Transfer C578

Applies the interrupt-driven detection pattern (from C573's touch sensor work)
to the coordination domain: instead of periodically polling ESP32 status,
this monitor detects STATE CHANGES via delta comparison and only logs/acts
when something actually changed.

This is the hardware→coordination technique transfer: the principle of
"interrupt over polling" applied across domains.

Usage:
    # Run once — check for changes vs last known state
    python3 scripts/blackboard_event_monitor.py check

    # Continuous monitoring mode (daemon-like, Ctrl-C to stop)
    python3 scripts/blackboard_event_monitor.py watch --interval 30

    # Report recent events
    python3 scripts/blackboard_event_monitor.py report [--limit 20]

Author: C0RTANA C578
Domain: hardware→coordination technique transfer
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
EVENTS_LOG = REPO_ROOT / "state" / "esp32_events.jsonl"
STATE_FILE = REPO_ROOT / "state" / "memories" / "last_esp32_state.json"
ESP32_IP = "192.168.4.38"
BASE_URL = f"http://{ESP32_IP}"

# Endpoints to monitor
ENDPOINTS = {
    "status": "/status",           # brightness, anim, speed, rssi, wifi_status
    "touch": "/api/sensor/touch",  # active state
    "dht": "/api/sensor/dht",      # humidity, temp
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def fetch_endpoint(name: str) -> dict | None:
    """Fetch a single ESP32 endpoint. Returns parsed JSON or None on failure."""
    url = BASE_URL + ENDPOINTS[name]
    try:
        req = urllib.request.urlopen(url, timeout=5)
        data = json.loads(req.read().decode())
        return {"endpoint": name, **data}
    except (urllib.error.URLError, TimeoutError, Exception) as e:
        return {"endpoint": name, "_error": str(e), "_ts": now_iso()}


def load_last_state() -> dict:
    """Load the last known state from disk."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_current_state(state: dict):
    """Persist current state for next delta comparison."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def detect_changes(current: dict, previous: dict) -> list[dict]:
    """Compare current vs previous state. Return list of change events."""
    changes = []

    # Compare each endpoint
    for ep_name in ENDPOINTS:
        cur_ep = current.get(ep_name, {})
        prev_ep = previous.get(ep_name, {})

        if not cur_ep or "timestamp" not in cur_ep:
            continue  # skip endpoints with errors

        if not prev_ep:
            # First read — no baseline yet, but record it
            continue

        # Detect specific field changes based on endpoint type
        if ep_name == "status":
            for field in ("brightness", "anim", "speed"):
                cur_val = cur_ep.get(field)
                prev_val = prev_ep.get(field)
                if cur_val != prev_val and cur_val is not None and prev_val is not None:
                    changes.append({
                        "type": "config_change",
                        "endpoint": ep_name,
                        "field": field,
                        "old_value": prev_val,
                        "new_value": cur_val,
                    })

            # RSSI threshold: flag significant signal drops (>5 dBm)
            cur_rssi = cur_ep.get("rssi")
            prev_rssi = prev_ep.get("rssi")
            if cur_rssi is not None and prev_rssi is not None:
                delta = abs(cur_rssi - prev_rssi)
                if delta > 5:
                    changes.append({
                        "type": "signal_shift",
                        "endpoint": ep_name,
                        "field": "rssi",
                        "old_value": prev_rssi,
                        "new_value": cur_rssi,
                        "delta_dbm": round(delta, 1),
                    })

        elif ep_name == "touch":
            cur_active = cur_ep.get("active", False)
            prev_active = prev_ep.get("active", False)
            if cur_active != prev_active:
                event_type = "touch_start" if cur_active else "touch_end"
                changes.append({
                    "type": event_type,
                    "endpoint": ep_name,
                    "field": "active",
                    "old_value": prev_active,
                    "new_value": cur_active,
                })

        elif ep_name == "dht":
            # Flag humidity/temp shifts > 2% or > 1°C (environmental events)
            for field, threshold in [("humidity", 2.0), ("temp", 1.0)]:
                cur_val = cur_ep.get(field)
                prev_val = prev_ep.get(field)
                if cur_val is not None and prev_val is not None:
                    delta = abs(cur_val - prev_val)
                    if delta > threshold:
                        changes.append({
                            "type": f"{field}_shift",
                            "endpoint": ep_name,
                            "field": field,
                            "old_value": round(prev_val, 2),
                            "new_value": round(cur_val, 2),
                            "delta": round(delta, 2),
                        })

    return changes


def log_event(event: dict):
    """Append a single event to the JSONL log."""
    entry = {
        "timestamp": now_iso(),
        **event,
    }
    EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(EVENTS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def cmd_check(args):
    """Single check cycle — fetch all endpoints, detect changes, log events."""
    print(f"[{now_iso()}] Checking ESP32 at {ESP32_IP}...")

    # Fetch current state from all endpoints
    current = {}
    for name in ENDPOINTS:
        data = fetch_endpoint(name)
        if data:
            current[name] = data
            status = "ok" if "_error" not in data else f"err({data['_error']})"
            print(f"  {name}: {status}")

    if not current:
        print("No endpoints reachable. Is ESP32 online?")
        sys.exit(1)

    # Load previous state and compare
    previous = load_last_state()

    if not previous:
        print("\nFirst run — establishing baseline (no change detection yet).")
    else:
        changes = detect_changes(current, previous)
        if changes:
            print(f"\n⚡ {len(changes)} change(s) detected:")
            for c in changes:
                detail = f"{c['field']}: {c.get('old_value', '?')} → {c.get('new_value', '?')}"
                if "delta" in c or "delta_dbm" in c:
                    delta_key = "delta_dbm" if "delta_dbm" in c else "delta"
                    detail += f" (Δ={c[delta_key]})"
                print(f"  [{c['type']}] {detail}")
                log_event(c)
        else:
            print("\n✓ No changes detected.")

    # Save current as new baseline
    save_current_state(current)
    print(f"\nState saved to {STATE_FILE}")
    return len(changes) if 'changes' in dir() else 0


def cmd_watch(args):
    """Continuous monitoring mode."""
    interval = args.interval
    print(f"[{now_iso()}] Watching ESP32 at {ESP32_IP} (interval={interval}s)")
    print("Press Ctrl+C to stop.\n")

    cycle_count = 0
    total_events = 0

    try:
        while True:
            cycle_count += 1
            n_changes = cmd_check(args)
            total_events += n_changes
            print(f"\n--- Cycle {cycle_count} complete (total events: {total_events}) ---\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\nStopped after {cycle_count} cycles, {total_events} total events logged.")


def cmd_report(args):
    """Show recent events from the log."""
    limit = getattr(args, 'limit', 20) or 20

    if not EVENTS_LOG.exists():
        print("No events logged yet. Run `check` first.")
        return

    lines = EVENTS_LOG.read_text().strip().split("\n")
    lines = [l for l in lines if l.strip()]  # filter empty

    if not lines:
        print("Events file is empty.")
        return

    recent = lines[-limit:]
    print(f"=== Recent ESP32 Events (last {len(recent)}) ===\n")

    for line in recent:
        try:
            event = json.loads(line)
            ts = event.get("timestamp", "?")[:19] + "Z"
            etype = event.get("type", "unknown")
            endpoint = event.get("endpoint", "?")
            field = event.get("field", "")
            old_v = event.get("old_value", "?")
            new_v = event.get("new_value", "?")
            delta_str = ""
            if "delta" in event:
                delta_str = f" Δ={event['delta']}"
            elif "delta_dbm" in event:
                delta_str = f" Δ={event['delta_dbm']} dBm"
            print(f"  [{ts}] {etype:<20} {endpoint}/{field}: {old_v} → {new_v}{delta_str}")
        except json.JSONDecodeError:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="ESP32 Event-Driven Monitor — interrupt-over-polling technique transfer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Technique Transfer (C578):
  Source domain: Hardware (ESP32 touch sensor, C573)
  Target domain: Coordination (blackboard monitoring)

  Principle: Replace periodic polling with change-driven detection.
  The ESP32 firmware uses GPIO interrupts for touch detection instead of
  polling the pin every loop iteration. This script applies the same
  principle to coordination: only act when state actually changes, not
  on a fixed schedule.

Examples:
  python3 scripts/blackboard_event_monitor.py check      # single check
  python3 scripts/blackboard_event_monitor.py watch --interval 30  # continuous
  python3 scripts/blackboard_event_monitor.py report -n 10  # recent events
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    p_check = subparsers.add_parser("check", help="Single check cycle")
    p_check.set_defaults(func=cmd_check)

    p_watch = subparsers.add_parser("watch", help="Continuous monitoring mode")
    p_watch.add_argument("--interval", type=int, default=30, help="Seconds between checks")
    p_watch.set_defaults(func=cmd_watch)

    p_report = subparsers.add_parser("report", help="Show recent events")
    p_report.add_argument("-n", "--limit", type=int, default=20, help="Number of events to show")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
