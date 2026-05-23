#!/usr/bin/env python3
"""
priority_reset.py — Explicit operator focus selection tool

Presents creator with three choices:
  A) Embodied cognition deep-dive (theory + coordination applications)
  B) Anomaly detection tooling (pattern-based alerting)  
  C) Custom directive (free-form direction)

Captures stdin, validates input, logs JSONL record to state/memories/focus_decisions.jsonl
"""

import json
from datetime import datetime
from pathlib import Path

FOCUS_DECISIONS_LOG = Path(__file__).parent.parent / "state" / "memories" / "focus_decisions.jsonl"

OPTIONS = {
    "A": ("embodied_cognition_deep_dive", "Embodied cognition deep-dive"),
    "B": ("anomaly_detection_tooling", "Anomaly detection tooling"),
    "C": ("custom_directive", "Custom directive")
}


def display_menu():
    """Display choice menu."""
    print("\n" + "=" * 60)
    print("CORTANA FOCUS SELECTION")
    print("=" * 60)
    print("\nChoose your current priority:")
    print()
    print(f"  [A] {OPTIONS['A'][1]}")
    print(f"      → Theory synthesis, enaction theory, McGilchrist hemispheric division")
    print()
    print(f"  [B] {OPTIONS['B'][1]}")  
    print(f"      → Pattern-based anomaly detection, alerting mechanisms")
    print()
    print(f"  [C] {OPTIONS['C'][1]}")
    print(f"      → Free-form custom direction (type after pressing C)")
    print()
    print("-" * 60)
    print("Enter A/B/C: ", end="", flush=True)


def capture_choice():
    """Capture and validate operator choice."""
    try:
        choice = input().strip().upper()
        
        if choice not in OPTIONS:
            print(f"\nInvalid selection '{choice}'. Must be A, B, or C.")
            return None
            
        return choice
        
    except EOFError:
        print("\nNo input received. Aborting.")
        return None


def log_decision(choice):
    """Log decision to JSONL file with cycle context."""
    # Read last cycle from current-state.json
    state_file = Path(__file__).parent.parent / "state" / "current-state.json"
    
    if state_file.exists():
        import json as j
        with open(state_file) as f:
            state = j.load(f)
        cycle = state.get("cycle", "unknown")
    else:
        cycle = "unknown"
    
    choice_key, choice_label = OPTIONS[choice]
    
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "cycle": cycle,
        "decision_type": "focus_priority_reset",
        "selection": choice_key,
        "label": choice_label,
        "source": "priority_reset.py CLI"
    }
    
    FOCUS_DECISIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    with open(FOCUS_DECISIONS_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")
    
    print(f"\n✓ Logged: {choice_label}")
    print(f"  Decision recorded for cycle {cycle}")


def main():
    """Main entry point."""
    display_menu()
    choice = capture_choice()
    
    if not choice:
        return 1
    
    log_decision(choice)
    print("\nPriority reset complete.")
    print("=" * 60 + "\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
