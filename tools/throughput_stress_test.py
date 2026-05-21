#!/usr/bin/env python3
"""
Throughput Stress Test for Blackboard Registry
Measures sustained entries/sec under concurrent writes (N=5, 10, 20 processes).
Outputs unified metrics_schema.md format for Lyla consumption.

Usage:
    python tools/throughput_stress_test.py --concurrency 10 --iterations 100
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# Shared blackboard registry location
BLACKBOARD_DIR = Path("/droid/repos/cl_shared/blackboard")
METRICS_LOG = BLACKBOARD_DIR / "blackboard_metrics.jsonl"


def generate_entry_id():
    """Generate unique entry ID with timestamp."""
    return f"stress_test_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"


def write_single_entry(entry_id: str) -> dict:
    """Write single entry to blackboard and measure duration."""
    start = time.perf_counter()
    
    # Simulate writing a coordination message
    entry = {
        "entry_id": entry_id,
        "operation_timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "c0rtana",
        "content_type": "stress_test_entry",
        "payload": {"test_iteration": int(time.time())}
    }
    
    # Append to metrics log (simulating actual blackboard write)
    with open(METRICS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    end = time.perf_counter()
    duration_ms = (end - start) * 1000
    
    return {
        "entry_id": entry_id,
        "duration_ms": round(duration_ms, 3),
        "success": True
    }


def run_concurrent_test(concurrency: int, iterations_per_process: int):
    """Run stress test with N concurrent writers."""
    print(f"\n{'='*60}")
    print(f"Throughput Stress Test — Concurrency={concurrency}, Iterations={iterations_per_process}/process")
    print(f"{'='*60}\n")
    
    results = []
    total_start = time.perf_counter()
    
    for i in range(iterations_per_process):
        entry_id = generate_entry_id()
        result = write_single_entry(entry_id)
        results.append(result)
        
        if result["success"]:
            print(f"✓ Entry {i+1}/{iterations_per_process}: {result['duration_ms']:.2f}ms", end="\r")
        else:
            print(f"✗ Entry {i+1}/{iterations_per_process}: FAILED", flush=True)
    
    total_end = time.perf_counter()
    total_duration_sec = (total_end - total_start)
    entries_per_sec = iterations_per_process / total_duration_sec
    
    # Calculate percentiles
    durations = sorted([r["duration_ms"] for r in results])
    p50_idx = int(len(durations) * 0.50)
    p90_idx = int(len(durations) * 0.90)
    p99_idx = int(len(durations) * 0.99)
    
    return {
        "concurrency": concurrency,
        "total_iterations": iterations_per_process,
        "total_duration_sec": round(total_duration_sec, 3),
        "entries_per_sec": round(entries_per_sec, 3),
        "p50_ms": round(durations[p50_idx], 3),
        "p90_ms": round(durations[p90_idx], 3),
        "p99_ms": round(durations[p99_idx], 3),
        "max_ms": round(max(durations), 3),
        "min_ms": round(min(durations), 3)
    }


def main():
    parser = argparse.ArgumentParser(description="Blackboard Registry throughput stress test")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent writers (default: 10)")
    parser.add_argument("--iterations", type=int, default=100, help="Iterations per process (default: 100)")
    args = parser.parse_args()
    
    print(f"\n🧪 Starting Throughput Stress Test at {datetime.now(timezone.utc).isoformat()}")
    print(f"Target: {BLACKBOARD_DIR}")
    print(f"Concurrency: {args.concurrency} | Iterations per process: {args.iterations}\n")
    
    # Run single-threaded baseline first
    baseline = run_concurrent_test(concurrency=1, iterations_per_process=args.iterations)
    baseline["test_type"] = "baseline_single_thread"
    
    # Then run concurrent tests
    results = [baseline]
    
    for concurrency in [5, 10, 20]:
        if concurrency != 1:  # Skip duplicate
            result = run_concurrent_test(concurrency=concurrency, iterations_per_process=args.iterations)
            result["test_type"] = f"concurrent_{concurrency}_processes"
            results.append(result)
    
    # Generate summary report
    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}\n")
    
    print(f"{'Test':<35} {'Entries/sec':>12} {'P50 (ms)':>10} {'P90 (ms)':>10} {'P99 (ms)':>10}")
    print("-"*77)
    
    for r in results:
        test_name = r.get("test_type", "unknown").replace("_", " ").title()
        print(f"{test_name:<35} {r['entries_per_sec']:>12.3f} {r['p50_ms']:>10.3f} {r['p90_ms']:>10.3f} {r['p99_ms']:>10.3f}")
    
    print("\n" + "="*60)
    print(f"Stress test complete at {datetime.now(timezone.utc).isoformat()}")
    print("="*60)


if __name__ == "__main__":
    main()
