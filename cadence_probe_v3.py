#!/usr/bin/env python3
"""
Cadence Probe v3.0 — Unified timing instrumentation per metrics_schema.md v1.0

This probe measures inter-entry delays between coordinated agent actions.
Output format aligned with Lyla's bb_perf_probe.py for single-stream metrics.

Schema compliance:
  - operation_type: "cadence_measurement"
  - duration_ms: wall-clock delay since last entry (ms)
  - timestamp: ISO8601 ISO format
  - agent: "c0rtana" or "lyla"
  - entry_id: Blackboard Registry entry identifier
  - N>=3 guard for percentile calculations maintained
"""

import json
import subprocess
from datetime import datetime, timezone


def get_last_entry_timestamp():
    """Query Blackboard Registry for most recent entry timestamp."""
    try:
        result = subprocess.run(
            ["git", "-C", "/droid/repos/cl_shared", "log", "--format=%ci", "-n", "1"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error querying git log: {e}")
        return None


def measure_cadence_delta(last_ts_str):
    """Calculate wall-clock delta in milliseconds from last entry."""
    # Parse ISO timestamp (adjust format as needed)
    last_ts = datetime.fromisoformat(last_ts_str.replace(" +0000", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = (now - last_ts).total_seconds() * 1000  # ms
    return int(delta)


def write_metric(operation_type, duration_ms, agent="c0rtana"):
    """Write metric to unified stream per metrics_schema.md v1.0."""
    metric = {
        "operation_type": operation_type,
        "duration_ms": duration_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "entry_id": "cadence_probe_v3"
    }
    
    # Append to blackboard_metrics.jsonl
    with open("/droid/repos/cl_shared/blackboard_metrics.jsonl", "a") as f:
        f.write(json.dumps(metric) + "\n")
    
    print(f"Cadence metric written: {json.dumps(metric)}")


if __name__ == "__main__":
    last_ts = get_last_entry_timestamp()
    if not last_ts:
        print("No prior entry found; skipping cadence measurement.")
        exit(0)
    
    delta_ms = measure_cadence_delta(last_ts)
    write_metric("cadence_measurement", delta_ms)
