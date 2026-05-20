#!/usr/bin/env python3
"""
Cadence Probe V3 — Coordination instrumentation using unified metrics_schema.md v1.0.

ADOPTED SCHEMA: Strictly compliant with /droid/repos/cl_shared/docs/metrics_schema.md v1.0.
Maps cadence operations to schema's operation_type enum via metadata domain context.

Schema per entry (per metrics_schema.md):
  - timestamp: ISO8601 wall-clock time
  - operation_type: git_push|git_pull|bb_write|bb_read|handoff_complete
  - duration_ms: Latency in milliseconds
  - agent: "c0rtana" (this tool)
  - entry_id: Optional blackboard entry ID
  - metadata: Domain-specific context including cadence operation type

Registry location: state/memories/cadence_state.json (current config/state)
Output logs:      logs/coordination_metrics.jsonl (append-only, standardized schema)

Usage:
    python scripts/cadence_probe_v3.py write     # Write new cycle marker + measure
    python scripts/cadence_probe_v3.py pull      # Pull and measure from shared registry  
    python scripts/cadence_probe_v3.py report    # Generate statistics report
    python scripts/cadence_probe_v3.py watch     # Continuous monitoring mode
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import statistics
import argparse


# Shared paths — aligned with bb_tool convention for compatibility
REGISTRY_PATH = Path(__file__).parent.parent / "state" / "memories" / "cadence_state.json"
METRICS_PATH = Path(__file__).parent.parent / "logs" / "coordination_metrics.jsonl"

AGENT_NAME = "c0rtana"  # Required field per metrics_schema.md v1.0


def now_iso() -> str:
    """ISO8601 wall-clock timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_registry() -> dict:
    """Load current cadence state if exists."""
    if not REGISTRY_PATH.exists():
        return {
            "cycle": 0,
            "last_sync": None,
            "mode": "hybrid_b_c",
            "config": {
                "registry_enabled": True,
                "adaptive_tuning": True,
                "poll_interval_min": 5,
                "max_poll_interval_hrs": 12
            }
        }
    with open(REGISTRY_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"cycle": 0, "last_sync": None, "mode": "unknown", "config": {}}


def save_state(state: dict):
    """Write cadence state atomically."""
    with open(REGISTRY_PATH, "w") as f:
        json.dump(state, f, indent=2)


def log_metric(operation_type: str, duration_ms: float, success: bool, 
               entry_id: str = None, metadata: dict = None):
    """Append timing metric to shared channel (strictly aligned with metrics_schema.md v1.0)."""
    record = {
        "timestamp": now_iso(),
        "operation_type": operation_type,
        "duration_ms": round(duration_ms, 3),
        "agent": AGENT_NAME,
        "entry_id": entry_id,
        "metadata": metadata or {}
    }
    with open(METRICS_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


# Cadence-specific operation mapping — these get stored in metadata.operation_domain
# while the outer operation_type maps to the closest schema enum value
CADENCE_OP_MAPPING = {
    "cycle_write": "bb_write",       # Writing cycle marker is a blackboard write op
    "cycle_pull": "bb_read",         # Pulling state is a blackboard read op  
    "registry_poll": "handoff_complete"  # Poll checks handoff sync status
}


def cmd_write(args):
    """Write new cycle marker and measure write duration."""
    start_time = time.perf_counter()
    
    registry = load_registry()
    registry["cycle"] += 1
    registry["last_sync"] = now_iso()
    registry["mode"] = args.mode if args.mode else registry.get("mode", "hybrid_b_c")
    
    min_interval = registry["config"].get("poll_interval_min", 5)
    max_hours = registry["config"].get("max_poll_interval_hrs", 12)
    
    save_state(registry)
    
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    
    cadence_op = "cycle_write"
    log_metric(
        operation_type=CADENCE_OP_MAPPING[cadence_op],
        duration_ms=duration_ms,
        success=True,
        entry_id=f"C{registry['cycle']}",
        metadata={
            "cadence_operation": cadence_op,
            "cycle_num": registry["cycle"],
            "mode": registry["mode"],
            "poll_interval_min": min_interval,
            "max_poll_interval_hrs": max_hours
        }
    )
    
    print(f"✓ Wrote cadence state: cycle {registry['cycle']} in {duration_ms:.3f}ms")


def cmd_pull(args):
    """Pull from shared blackboard and measure pull timing."""
    start_time = time.perf_counter()
    
    try:
        registry = load_registry()
        has_data = bool(registry.get("last_sync"))
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        success = has_data
        status = "success" if success else "empty"
        
        cadence_op = "cycle_pull"
        log_metric(
            operation_type=CADENCE_OP_MAPPING[cadence_op],
            duration_ms=duration_ms,
            success=success,
            entry_id=None,
            metadata={
                "cadence_operation": cadence_op,
                "has_state": success,
                "last_cycle": registry.get("cycle", 0),
                "last_sync": registry.get("last_sync", None)
            }
        )
        
        print(f"✓ Pulled cadence state in {duration_ms:.3f}ms | status: {status}")
        
    except Exception as e:
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        cadence_op = "cycle_pull"
        log_metric(
            operation_type=CADENCE_OP_MAPPING[cadence_op],
            duration_ms=duration_ms,
            success=False,
            entry_id=None,
            metadata={"cadence_operation": cadence_op, "error": str(e)}
        )
        
        print(f"✗ Pull failed in {duration_ms:.3f}ms: {e}")


def cmd_report(args):
    """Generate statistics on coordination operations."""
    if not METRICS_PATH.exists():
        print("No metrics data found. Run 'write' or 'pull' commands first.")
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
    
    # Group by schema's operation_type field
    by_op = defaultdict(list)
    by_success = defaultdict(lambda: {"success": 0, "failure": 0})
    
    for r in records:
        op = r.get("operation_type", "unknown")
        duration_ms = r.get("duration_ms", 0)
        success = r.get("success", False)
        
        by_op[op].append(duration_ms)
        key = "success" if success else "failure"
        by_success[op][key] += 1
    
    print("\n" + "=" * 70)
    print(f"COORDINATION METRICS REPORT - cadence_probe_v3 (metrics_schema.md v1.0)")
    print(f"Generated: {now_iso()}")
    print(f"Total operations logged: {len(records)}")
    print("=" * 70)
    
    for op_name in sorted(by_op.keys()):
        times = by_op[op_name]
        stats = by_success[op_name]
        total = stats["success"] + stats["failure"]
        
        mean = statistics.mean(times)
        std = statistics.stdev(times) if len(times) > 1 else 0.0
        p50 = sorted(times)[len(times)//2]
        p95_idx = min(int(len(times)*0.95), len(times)-1)
        p95 = sorted(times)[p95_idx]
        
        # Also report cadence-specific breakdown via metadata
        cadence_ops = defaultdict(list)
        for r in records:
            if r.get("operation_type") == op_name:
                meta = r.get("metadata", {})
                cad_op = meta.get("cadence_operation", "unknown")
                cadence_ops[cad_op].append(r.get("duration_ms", 0))
        
        print(f"\n{op_name.upper()} (schema enum | {total} samples)")
        print("-" * 40)
        print(f"  Mean:       {mean:.3f} ms")
        print(f"  Std dev:    {std:.3f} ms")
        print(f"  P50:        {p50:.3f} ms")
        print(f"  P95:        {p95:.3f} ms")
        print(f"  Success rate: {(stats['success']/max(total,1))*100:.1f}%")
        
        if cadence_ops:
            print("\n  Cadence operation breakdown:")
            for cad_op, times_list in sorted(cadence_ops.items()):
                avg = statistics.mean(times_list)
                print(f"    - {cad_op}: {len(times_list)} samples @ {avg:.2f}ms avg")
    
    print("\n" + "=" * 70)
    print("SCHEMA COMPLIANCE NOTE:")
    print("This output uses metrics_schema.md v1.0 fields exactly:")
    print("  - timestamp (wall-clock ISO8601)")
    print("  - operation_type (enum: git_push|git_pull|bb_write|bb_read|handoff_complete)")
    print("  - duration_ms (float timing measurement)")
    print("  - agent (string: 'c0rtana' or 'lyla')")
    print("  - entry_id (optional blackboard reference)")
    print("  - metadata (domain context including cadence_operation field)")
    print("")
    print("Cadence-specific operations preserved in metadata.cadence_operation.")
    print("=" * 70)


def cmd_watch(args):
    """Continuous monitoring — poll cadence registry at interval."""
    interval_sec = args.interval or 60
    
    print(f"Cadence Monitor V3 starting... (poll every {interval_sec}s, Ctrl+C to stop)")
    print(f"Metrics logged to: {METRICS_PATH}")
    
    try:
        while True:
            start = time.perf_counter()
            
            registry = load_registry()
            age_s = None
            if registry.get("last_sync"):
                last_ts = datetime.fromisoformat(registry["last_sync"].replace("Z", "+00:00"))
                now_ts = datetime.now(timezone.utc)
                age_s = (now_ts - last_ts).total_seconds()
            
            status = f"{age_s/60:.1f}m ago" if age_s is not None else "never synced"
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start) * 1000
            
            log_metric(
                operation_type="handoff_complete",
                duration_ms=duration_ms,
                success=True,
                entry_id=None,
                metadata={
                    "cadence_operation": "registry_poll",
                    "cycle_num": registry.get("cycle", "?"),
                    "mode": registry.get("mode", "?"),
                    "sync_age_mins": round(age_s/60, 1) if age_s else None
                }
            )
            
            print(f"[{now_iso()}] Cycle {registry.get('cycle', '?')}: mode={registry.get('mode')} | sync={status}")
            
            elapsed = time.time() - start
            sleep_time = max(0, interval_sec - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print("\nStopped by user.")


def main():
    parser = argparse.ArgumentParser(
        description="Cadence Probe V3 — coordination timing using metrics_schema.md v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
SCHEMA COMPLIANCE (metrics_schema.md v1.0):

cadence_probe_v3.py strictly adheres to the unified timing schema from cl_shared/docs/.
All output conforms to required fields: timestamp, operation_type, duration_ms, agent.
Cadence-specific context preserved in metadata.cadence_operation field.

Example metric entry structure:
{
    "timestamp": "2026-05-20T08:00:00Z",
    "operation_type": "bb_write",
    "duration_ms": 12.453,
    "agent": "c0rtana",
    "entry_id": "C42",
    "metadata": {
        "cadence_operation": "cycle_write",
        "cycle_num": 42,
        "mode": "hybrid_b_c"
    }
}

Commands:
    write      - Write new cycle marker + measure write duration
    pull       - Pull state from shared registry + measure latency  
    report     - Generate statistics on all logged operations
    watch      - Continuous monitoring mode (default interval: 60s)
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # write command
    p_write = subparsers.add_parser("write", help="Write new cycle marker + measure write duration")
    p_write.add_argument("--mode", "-m", default=None, help="Mode override (default: keep current)")
    p_write.add_argument("--poll", type=int, dest="poll_min", default=None, help="Poll interval in minutes")
    
    # pull command  
    subparsers.add_parser("pull", help="Pull state from shared registry + measure latency")
    
    # report command
    subparsers.add_parser("report", help="Generate metrics report")
    
    # watch command
    p_watch = subparsers.add_parser("watch", help="Continuous monitoring mode")
    p_watch.add_argument("--interval", "-i", type=int, default=60, help="Poll interval in seconds")
    
    args = parser.parse_args()
    
    if args.command == "write":
        cmd_write(args)
    elif args.command == "pull":
        cmd_pull(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "watch":
        cmd_watch(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
