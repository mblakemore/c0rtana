#!/usr/bin/env python3
"""
Priority Reset CLI — C328
Minimal terminal prompt for operator focus selection.

Usage: python bin/priority_reset.py

Options presented:
A) Embodied cognition deep-dive (Varela/Langon/Thompson continued)
B) Anomaly detection tooling (predictive processing → concrete implementation)
C) Something else entirely (free text input)

Captures choice via stdin, outputs JSONL to logs/priority_selection.jsonl
"""

import sys
import json
from datetime import datetime, timezone


def display_prompt():
    """Display the priority selection prompt."""
    print("\n" + "="*60)
    print("PRIORITY RESET — What should I focus on next?")
    print("="*60)
    print()
    print("A) Embodied cognition deep-dive")
    print("   Continue Varela/Langon/Thompson 'The Embodied Mind'")
    print("   Map enaction theory to coordination architecture")
    print()
    print("B) Anomaly detection tooling")
    print("   Implement predictive coding framework from scratch")
    print("   Free energy principle → practical anomaly detector")
    print()
    print("C) Something else entirely")
    print("   Tell me what you actually need right now")
    print()
    print("-"*60)
    print("Enter A, B, or C: ", end="", flush=True)


def get_choice():
    """Get and validate operator choice."""
    try:
        choice = sys.stdin.read(1).strip().upper()
        if choice in ('A', 'B', 'C'):
            return choice
        else:
            print("Invalid choice. Please enter A, B, or C.")
            return None
    except KeyboardInterrupt:
        print("\nCancelled.")
        return None


def log_selection(choice, timestamp):
    """Log selection to JSONL file."""
    record = {
        "cycle": 328,
        "timestamp": timestamp.isoformat(),
        "choice": choice,
        "description": {
            "A": "Embodied cognition deep-dive",
            "B": "Anomaly detection tooling", 
            "C": "Something else entirely"
        }[choice]
    }
    
    with open("logs/priority_selection.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")
    
    return record


def main():
    display_prompt()
    choice = get_choice()
    
    if not choice:
        sys.exit(1)
    
    timestamp = datetime.now(timezone.utc)
    record = log_selection(choice, timestamp)
    
    print(f"\n✓ Selection recorded: {record['description']}")
    print(f"  Timestamp: {timestamp.isoformat()}")
    print(f"  Log: logs/priority_selection.jsonl")
    print()
    
    # Output for Discord relay
    print(f"**c0rtana C328**: Priority reset deployed. Creator selected option '{choice}' ({record['description']}). Next cycle will begin {record['description'].lower().replace(' ', '_')}_arc.")


if __name__ == "__main__":
    main()
