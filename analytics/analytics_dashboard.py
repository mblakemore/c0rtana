#!/usr/bin/env python3
"""
Analytics Dashboard CLI — Real-time operator engagement metrics
Reads interactions.jsonl and produces human-readable summary of engagement patterns.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


INTERACTIONS_FILE = Path(__file__).parent / "interactions.jsonl"


def load_events():
    """Load all interaction events from JSONL file."""
    events = []
    if not INTERACTIONS_FILE.exists():
        return events
    
    with open(INTERACTIONS_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def compute_metrics(events):
    """Compute engagement metrics from event list."""
    if not events:
        return {
            "total_events": 0,
            "unique_sessions": 0,
            "first_event": None,
            "last_event": None,
            "avg_frequency_per_hour": 0,
            "active_days": 0,
        }
    
    # Parse timestamps
    for e in events:
        e["_ts"] = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
    
    events.sort(key=lambda x: x["_ts"])
    
    sessions = set(e.get("session_id") for e in events if e.get("session_id"))
    dates = set(e["_ts"].date().isoformat() for e in events)
    
    time_span_hours = (events[-1]["_ts"] - events[0]["_ts"]).total_seconds() / 3600
    
    return {
        "total_events": len(events),
        "unique_sessions": len(sessions),
        "first_event": events[0]["timestamp"],
        "last_event": events[-1]["timestamp"],
        "time_span_hours": round(time_span_hours, 2),
        "avg_frequency_per_hour": round(len(events) / max(time_span_hours, 0.001), 2),
        "active_days": len(dates),
    }


def main():
    """Main entry point."""
    events = load_events()
    metrics = compute_metrics(events)
    
    print("=" * 60)
    print("CORTANA OPERATOR ENGAGEMENT DASHBOARD")
    print("=" * 60)
    print(f"Total Events:        {metrics['total_events']}")
    print(f"Unique Sessions:     {metrics['unique_sessions']}")
    print(f"Active Days:         {metrics['active_days']}")
    print("-" * 60)
    if metrics["total_events"] > 0:
        print(f"First Event:         {metrics['first_event']}")
        print(f"Last Event:          {metrics['last_event']}")
        print(f"Time Span:           {metrics['time_span_hours']} hours")
        print(f"Avg Frequency:       {metrics['avg_frequency_per_hour']}/hour")
    else:
        print("No engagement data collected yet.")
    print("=" * 60)


if __name__ == "__main__":
    main()
