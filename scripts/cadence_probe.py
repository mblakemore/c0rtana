#!/usr/bin/env python3
"""
Cadence Probe — Coordination latency/throughput for inter-agent protocol.

Measures actual wall-clock timing on cadence operations, not just logical timestamps.
Produces external artifact for Reality Anchor compliance.

Registry location: state/memories/cadence_registry.jsonl
Output logs: logs/cadence_metrics.jsonl (append-only)

Usage:
    python scripts/cadence_probe.py read      # Read current cadence state
    python scripts/cadence_probe.py write     # Write new cycle marker + measure duration
    python scripts/cadence_probe.py report    # Generate statistics report
    python scripts/cadence_probe.py watch     # Continuous monitoring mode
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import statistics
import argparse


REGISTRY_PATH = Path(__file__).parent.parent / "state" / "memories" / "cadence_registry.jsonl"
METRICS_PATH = Path(__file__).parent.parent / "logs" / "cadence_metrics.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_registry() -> list[dict]:
    """Load registry entries as JSONL."""
    if not REGISTRY_PATH.exists():
        return []
    entries = []
    with open(REGISTRY_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def write_entry(entry: dict):
    """Append single entry to registry."""
    with open(REGISTRY_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def measure_operation(op_name: str, duration_ms: float, details: dict = None):
    """Record wall-clock timing metric."""
    record = {
        "op": op_name,
        "timestamp": now_iso(),
        "wall_clock_ms": round(duration_ms, 3),
        "details": details or {}
    }
    with open(METRICS_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


def cmd_read(args):
    """Read current cadence state."""
    entries = read_registry()
    if not entries:
        print("No cadence data found. Initialize with 'write' command.")
        return
    
    latest = entries[-1]
    print(f"Cadence State (via Central Registry)")
    print("=" * 50)
    print(f"Last sync:     {latest.get('last_sync', 'N/A')}")
    print(f"Mode:          {latest.get('mode', 'N/A')}")
    print(f"Registry:      {'enabled' if latest.get('registry_enabled') else 'disabled'}")
    print(f"Adaptive tuning: {latest.get('adaptive_tuning', False)}")
    config = latest.get('config', {})
    print(f"Poll interval: {config.get('poll_interval_min')} min → {config.get('max_poll_interval_hrs')} hrs max")
    

def cmd_write(args):
    """Write new cycle marker and measure timing."""
    start = time.time()
    
    # Read current to merge with update
    entries = read_registry()
    last_entry = entries[-1] if entries else {}
    
    mode = args.mode if args.mode else "hybrid_b_c"
    poll_interval = args.poll if args.poll else 5
    
    entry = {
        "cycle": last_entry.get("cycle", 0) + 1,
        "timestamp": now_iso(),
        "last_sync": now_iso(),
        "mode": mode,
        "status": "active",
        "config": {
            "registry_enabled": True,
            "adaptive_tuning": True,
            "poll_interval_min": poll_interval,
            "max_poll_interval_hrs": 12
        }
    }
    
    write_entry(entry)
    
    duration_ms = (time.time() - start) * 1000
    measure_operation("write_cycle", duration_ms, {"cycle_num": entry["cycle"]})
    
    print(f"✓ Wrote cadence state: cycle {entry['cycle']} in {duration_ms:.3f}ms")


def cmd_report(args):
    """Generate statistics on cadence operations."""
    if not METRICS_PATH.exists():
        print("No metrics data found.")
        return
    
    records = []
    with open(METRICS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    if not records:
        print("No metrics to report.")
        return
    
    # Group by operation type
    by_op = defaultdict(list)
    for r in records:
        by_op[r["op"]].append(r["wall_clock_ms"])
    
    print("\nCadence Operation Metrics")
    print("=" * 70)
    
    for op_name, times in sorted(by_op.items()):
        mean = statistics.mean(times)
        std = statistics.stdev(times) if len(times) > 1 else 0.0
        p50 = sorted(times)[len(times)//2]
        p95 = sorted(times)[int(len(times)*0.95)] if len(times) >= 20 else max(times)
        
        print(f"\n{op_name.upper()} ({len(records)} samples)")
        print(f"  Mean:       {mean:.3f} ms")
        print(f"  Std dev:    {std:.3f} ms")
        print(f"  P50:        {p50:.3f} ms")
        print(f"  P95 (max):  {p95:.3f} ms")
    
    print("\n" + "=" * 70)


def cmd_watch(args):
    """Continuous monitoring — poll cadence registry at interval."""
    interval_sec = args.interval or 60
    
    print(f"Cadence Monitor starting... (poll every {interval_sec}s, Ctrl+C to stop)")
    
    try:
        while True:
            start = time.time()
            
            entries = read_registry()
            if entries:
                latest = entries[-1]
                age_s = (time.time() - datetime.fromisoformat(latest["last_sync"].rstrip("Z")).timestamp())
                
                status = "STALE!" if age_s > 3600 else f"OK ({age_s/60:.1f}m ago)"
                print(f"[{now_iso()}] Cycle {latest.get('cycle', '?')}: mode={latest.get('mode')} | sync_age={status}")
                
                duration_ms = (time.time() - start) * 1000
                measure_operation("watch_poll", duration_ms, {"status": status})
            
            elapsed = time.time() - start
            sleep_time = max(0, interval_sec - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print("\nStopped by user.")


def main():
    parser = argparse.ArgumentParser(description="Cadence Probe — coordination timing tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # read command
    p_read = subparsers.add_parser("read", help="Read current cadence state")
    
    # write command
    p_write = subparsers.add_parser("write", help="Write new cycle marker")
    p_write.add_argument("--mode", "-m", default="hybrid_b_c", help="Mode: hybrid_a/b/c/etc")
    p_write.add_argument("--poll", "-p", type=int, default=5, help="Poll interval in minutes")
    
    # report command
    subparsers.add_parser("report", help="Generate metrics report")
    
    # watch command
    p_watch = subparsers.add_parser("watch", help="Continuous monitoring mode")
    p_watch.add_argument("--interval", "-i", type=int, default=60, help="Poll interval in seconds")
    
    args = parser.parse_args()
    
    if args.command == "read":
        cmd_read(args)
    elif args.command == "write":
        cmd_write(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "watch":
        cmd_watch(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
