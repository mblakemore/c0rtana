#!/usr/bin/env python3
"""Unified workstream scheduler — Thompson Sampling + Q-Learning hybrid.

Combines TS diversity (native exploration without epsilon decay) with QL's
context-aware reward learning (no-repetition penalty from state history).

Architecture:
  - TS provides base quality signal per workstream (Beta posterior sampling)
  - QL provides context adjustment: how good is workstream X given recent history?
  - Final score = TS_sample * (1 + QL_context_bonus)

Usage:
    python3 scripts/workstream_scheduler.py --select    # Live recommendation
    python3 scripts/workstream_scheduler.py --reward <name> <0-1>  # Record outcome
    python3 scripts/workstream_scheduler.py --status     # Show all workstreams
"""
import argparse
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = "state/workstream_scheduler.json"


class UnifiedScheduler:
    """Hybrid scheduler: TS for diversity, QL for context-aware reward."""

    def __init__(self, state_file=STATE_FILE):
        self.state_file = Path(state_file)
        self.workstreams = {}  # name -> {"alpha": float, "beta": float}
        self.q_adjustments = defaultdict(float)  # (last_ws, candidate_ws) -> adjustment
        self.history = []  # recent workstream selections
        self.history_window = 3
        self.load()

    def register(self, name):
        """Register a workstream with uniform Beta(1,1) prior."""
        if name not in self.workstreams:
            self.workstreams[name] = {"alpha": 1.0, "beta": 1.0}

    def ts_sample(self, name):
        """Draw from Beta posterior for a workstream."""
        ws = self.workstreams[name]
        return random.betavariate(ws["alpha"], ws["beta"])

    def ts_expected(self, name):
        """Mean of Beta posterior."""
        ws = self.workstreams[name]
        return ws["alpha"] / (ws["alpha"] + ws["beta"])

    def ts_uncertainty(self, name):
        """Variance of Beta posterior."""
        ws = self.workstreams[name]
        n = ws["alpha"] + ws["beta"]
        return (ws["alpha"] * ws["beta"]) / (n * n * (n + 1))

    def ql_context_bonus(self, candidate):
        """Get Q-learning context adjustment for candidate given recent history.

        If the last workstream was the same as candidate, bonus is negative
        (diminishing returns from repetition). If we just did a different
        workstream, bonus reflects observed transition quality.
        """
        if not self.history:
            return 0.0

        last = self.history[-1]
        if last == candidate:
            return self.q_adjustments.get((last, candidate), -0.15)

        return self.q_adjustments.get((last, candidate), 0.0)

    def score(self, name):
        """Compute hybrid score: TS sample modulated by QL context."""
        base = self.ts_sample(name)
        context = self.ql_context_bonus(name)
        # Context bonus modulates TS sample multiplicatively
        # Negative bonus = penalty for repetition, positive = synergy
        return base * (1.0 + context)

    def select(self):
        """Select workstream with highest hybrid score."""
        if not self.workstreams:
            raise ValueError("No workstreams registered")

        best_name = None
        best_score = -1
        scores = {}

        for name in self.workstreams:
            s = self.score(name)
            scores[name] = round(s, 4)
            if s > best_score:
                best_score = s
                best_name = name

        return best_name, scores

    def reward(self, name, reward):
        """Record outcome and update both TS posterior and QL context.

        reward: float in [0, 1] — higher = better cycle outcome
        """
        if name not in self.workstreams:
            self.register(name)

        # Update TS posterior
        ws = self.workstreams[name]
        if reward >= 0.5:
            ws["alpha"] += reward
        else:
            ws["beta"] += (1.0 - reward)

        # Update QL context: learn transition quality
        if self.history:
            last = self.history[-1]
            key = (last, name)
            # Exponential moving average of reward for this transition
            old = self.q_adjustments.get(key, 0.0)
            alpha_ql = 0.2  # learning rate for context adjustments
            self.q_adjustments[key] = old + alpha_ql * (reward - old)

            # If same workstream repeated, learn diminishing returns
            if last == name and reward < 0.7:
                self.q_adjustments[key] = self.q_adjustments.get(key, 0.0) - 0.05

        # Update history
        self.history.append(name)
        if len(self.history) > self.history_window:
            self.history.pop(0)

        self.save()

    def get_status(self):
        """Get status of all workstreams."""
        result = {}
        for name, ws in self.workstreams.items():
            result[name] = {
                "expected_quality": round(self.ts_expected(name), 4),
                "uncertainty": round(self.ts_uncertainty(name), 6),
                "samples": round(ws["alpha"] + ws["beta"] - 2, 1),
            }
        return result

    def save(self):
        data = {
            "workstreams": dict(self.workstreams),
            "q_adjustments": {
                f"{k[0]}->{k[1]}": v for k, v in self.q_adjustments.items()
            },
            "history": self.history,
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        self.state_file.write_text(json.dumps(data, indent=2))

    def load(self):
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text())
            self.workstreams = data.get("workstreams", {})
            raw_adjustments = data.get("q_adjustments", {})
            for key_str, val in raw_adjustments.items():
                parts = key_str.split("->")
                if len(parts) == 2:
                    self.q_adjustments[(parts[0], parts[1])] = val
            self.history = data.get("history", [])


def migrate_from_existing(scheduler):
    """Migrate TS state from workstream_states.json into the unified scheduler."""
    src = Path("state/workstream_states.json")
    if not src.exists():
        return

    data = json.loads(src.read_text())
    for name, ws_data in data.get("workstreams", {}).items():
        scheduler.register(name)
        # Transfer TS posterior parameters
        scheduler.workstreams[name]["alpha"] = ws_data.get("alpha", 1.0)
        scheduler.workstreams[name]["beta"] = ws_data.get("beta", 1.0)


def main():
    parser = argparse.ArgumentParser(description="Unified workstream scheduler")
    parser.add_argument("--select", action="store_true", help="Select next workstream")
    parser.add_argument("--reward", nargs=2, metavar=("NAME", "VALUE"),
                        help="Record reward for a workstream")
    parser.add_argument("--status", action="store_true", help="Show workstream status")
    parser.add_argument("--migrate", action="store_true",
                        help="Migrate from workstream_states.json")
    args = parser.parse_args()

    scheduler = UnifiedScheduler()

    if args.migrate:
        migrate_from_existing(scheduler)
        scheduler.save()
        print("Migrated existing TS state into unified scheduler.")
        return

    if args.select:
        name, scores = scheduler.select()
        print(f"\nUnified Scheduler Recommendation:")
        print(f"  Selected: {name}")
        print(f"\n  Scores (TS * QL context):")
        for ws, s in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            expected = scheduler.ts_expected(ws)
            uncertainty = scheduler.ts_uncertainty(ws)
            context = scheduler.ql_context_bonus(ws)
            print(f"    {ws:40s} score={s:.4f}  "
                  f"ts_expected={expected:.4f}  "
                  f"uncertainty={uncertainty:.6f}  "
                  f"ql_context={context:+.2f}")
        print(f"\n  Recent history: {scheduler.history}")

    elif args.reward:
        name, value = args.reward
        scheduler.reward(name, float(value))
        print(f"Recorded reward {value} for {name}")

    elif args.status:
        status = scheduler.get_status()
        print(json.dumps(status, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
