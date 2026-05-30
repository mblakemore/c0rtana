#!/usr/bin/env python3
"""Initialize workstream states from real cycle history.

Parses git log to categorize cycles and compute real rewards based on:
- Artifact production (did the cycle produce something external?)
- Domain diversity (did it break streaks or repeat?)
- Cross-agent value (did Lyla or Creator respond/use the output?)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

# Workstream definitions with keyword matchers
WORKSTREAMS = {
    "external_reading": {
        "keywords": ["reading", "fundamentals", "study", "API docs", "book", "paper"],
        "description": "External-domain study, reading, knowledge acquisition",
    },
    "esp32_hardware": {
        "keywords": ["ESP32", "sensor", "DHT", "hardware", "firmware", "OTA", "LED", "rings"],
        "description": "ESP32 device interaction, sensor data, hardware debugging",
    },
    "tool_building": {
        "keywords": ["tool", "script", "built", "built:", "dashboard", "estimator", "checker", "selector", "consolidation"],
        "description": "Building tools, scripts, visualizations, dashboards",
    },
    "prediction_grading": {
        "keywords": ["prediction", "graded", "grade", "P_C", "calibration", "Brier"],
        "description": "Prediction grading, calibration analysis, Brier scoring",
    },
    "cross_agent_coordination": {
        "keywords": ["Lyla", "governance", "cross-valid", "cross-agent", "coordination"],
        "description": "Cross-agent synthesis, governance analysis, coordination with Lyla",
    },
}


def categorize_cycle(commit_msg: str) -> list:
    """Categorize a cycle's commit message into workstreams."""
    categories = []
    msg_lower = commit_msg.lower()
    for ws, config in WORKSTREAMS.items():
        for kw in config["keywords"]:
            if kw.lower() in msg_lower:
                categories.append(ws)
                break
    return categories


def compute_reward(categories: list, streak: dict, cycle_idx: int) -> dict:
    """Compute reward (0-1) for each workstream in a cycle.

    Reward factors:
    - Base: 0.6 (neutral)
    - Multi-workstream cycle: +0.1 (shows integration)
    - Breaking a streak (>3 of same): +0.15 (domain diversity)
    - Repeating same workstream >3 in a row: -0.1 (diminishing returns)
    """
    rewards = {}
    for cat in categories:
        reward = 0.6

        # Integration bonus
        if len(categories) > 1:
            reward += 0.1

        # Streak bonus/penalty
        current_streak = streak.get(cat, 0)
        if current_streak > 3:
            reward -= 0.1  # diminishing returns on repetition
        elif current_streak == 3 and cat in categories:
            reward += 0.15  # breaking a streak is valuable

        rewards[cat] = min(1.0, max(0.0, reward))

    return rewards


def main():
    # Parse recent git history
    result = subprocess.run(
        ["git", "log", "--oneline", "-50"],
        capture_output=True, text=True
    )

    if not result.returncode == 0:
        print("Error running git log", file=sys.stderr)
        sys.exit(1)

    # Initialize workstreams with uniform prior
    selector_workstreams = {}
    for ws in WORKSTREAMS:
        selector_workstreams[ws] = {
            "name": ws,
            "alpha": 1.0,
            "beta": 1.0,
            "pulls": 0,
        }

    # Track streaks
    streak = {}
    last_workstreams = set()

    # Process cycles in chronological order (newest first from git log)
    lines = result.stdout.strip().split("\n")
    lines.reverse()  # oldest first

    for line in lines:
        match = re.match(r"^[0-9a-f]+\s+(C\d+):\s+(.*)", line)
        if not match:
            continue

        commit_msg = match.group(2)
        categories = categorize_cycle(commit_msg)

        if not categories:
            # Unclassified cycle — skip (could be meta-work, memory pruning, etc.)
            continue

        # Update streaks
        for ws in WORKSTREAMS:
            if ws in categories:
                streak[ws] = streak.get(ws, 0) + 1
            else:
                streak[ws] = 0

        # Compute rewards
        rewards = compute_reward(categories, streak, len(lines))

        # Apply rewards to workstreams
        for ws, reward in rewards.items():
            if ws in selector_workstreams:
                selector_workstreams[ws]["pulls"] += 1
                if reward >= 0.5:
                    selector_workstreams[ws]["alpha"] += reward
                else:
                    selector_workstreams[ws]["beta"] += (1 - reward)

    # Recalculate derived metrics
    for ws, data in selector_workstreams.items():
        n = data["alpha"] + data["beta"]
        data["expected_quality"] = round(data["alpha"] / n, 4)
        data["uncertainty"] = round((data["alpha"] * data["beta"]) / (n * n * (n + 1)), 4)

    # Save state
    state_file = Path("state/workstream_states.json")
    output = {
        "workstreams": selector_workstreams,
        "source": "scripts/workstream_init.py — real cycle history",
        "cycles_analyzed": len(lines),
    }
    state_file.write_text(json.dumps(output, indent=2))

    # Print summary
    print("Workstream States (initialized from real cycle history)")
    print("=" * 70)
    for ws, data in sorted(selector_workstreams.items(),
                           key=lambda x: x[1]["expected_quality"],
                           reverse=True):
        print(f"  {ws:35s} quality={data['expected_quality']:.4f}  "
              f"uncertainty={data['uncertainty']:.4f}  "
              f"pulls={data['pulls']}")
    print(f"\nState saved to {state_file}")


if __name__ == "__main__":
    main()
