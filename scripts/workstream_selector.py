#!/usr/bin/env python3
"""Thompson Sampling workstream selector for cognitive agent DECIDE phase.

Uses Bayesian bandits to balance exploration vs exploitation across workstreams.
Each workstream maintains a Beta distribution over its "quality" parameter.
"""
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path


class Workstream:
    """A workstream with a Beta-distributed quality estimate."""

    def __init__(self, name, alpha=1, beta=1):
        self.name = name
        self.alpha = alpha  # successes + 1
        self.beta = beta    # failures + 1
        self.pulls = 0

    def sample(self) -> float:
        """Sample from Beta(alpha, beta) posterior."""
        return random.betavariate(self.alpha, self.beta)

    def expected_quality(self) -> float:
        """Mean of Beta distribution."""
        return self.alpha / (self.alpha + self.beta)

    def update(self, reward: float):
        """Update posterior with observed reward (0-1 scale).
        reward > 0.5 increments alpha, reward < 0.5 increments beta.
        """
        self.pulls += 1
        if reward >= 0.5:
            self.alpha += reward  # partial credit for good but not great
        else:
            self.beta += (1 - reward)  # partial penalty

    def uncertainty(self) -> float:
        """Variance of Beta distribution — measures uncertainty."""
        n = self.alpha + self.beta
        return (self.alpha * self.beta) / (n * n * (n + 1))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "alpha": self.alpha,
            "beta": self.beta,
            "pulls": self.pulls,
            "expected_quality": self.expected_quality(),
            "uncertainty": self.uncertainty(),
        }


class ThompsonSamplingSelector:
    """Selects workstreams using Thompson Sampling."""

    def __init__(self, state_file: str = "state/workstream_states.json"):
        self.state_file = Path(state_file)
        self.workstreams = {}
        self._load()

    def register(self, name: str):
        """Register a new workstream with uniform prior."""
        if name not in self.workstreams:
            self.workstreams[name] = Workstream(name)

    def select(self) -> str:
        """Select workstream with highest Thompson Sample."""
        if not self.workstreams:
            raise ValueError("No workstreams registered")

        best_name = None
        best_sample = -1
        for name, ws in self.workstreams.items():
            sample = ws.sample()
            if sample > best_sample:
                best_sample = sample
                best_name = name
        return best_name

    def reward(self, name: str, reward: float):
        """Record reward for a workstream (0-1 scale)."""
        if name in self.workstreams:
            self.workstreams[name].update(reward)
            self._save()

    def get_recommendation(self, top_k: int = 3) -> list:
        """Get top-k workstreams by expected quality + uncertainty bonus."""
        scored = []
        for name, ws in self.workstreams.items():
            # UCB-style score: expected quality + exploration bonus
            exploration_bonus = math.sqrt(ws.uncertainty()) * 0.5
            score = ws.expected_quality() + exploration_bonus
            scored.append((name, score, ws))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {
                "name": name,
                "score": round(score, 4),
                "expected_quality": round(ws.expected_quality(), 4),
                "uncertainty": round(ws.uncertainty(), 4),
                "pulls": ws.pulls,
            }
            for name, score, ws in scored[:top_k]
        ]

    def _save(self):
        data = {
            "workstreams": {
                name: ws.to_dict() for name, ws in self.workstreams.items()
            },
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        self.state_file.write_text(json.dumps(data, indent=2))

    def _load(self):
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text())
            for name, ws_data in data.get("workstreams", {}).items():
                ws = Workstream(ws_data["name"], ws_data["alpha"], ws_data["beta"])
                ws.pulls = ws_data.get("pulls", 0)
                self.workstreams[name] = ws


def main():
    """Demo: Thompson Sampling for workstream selection."""
    selector = ThompsonSamplingSelector()

    # Register example workstreams
    workstreams = [
        "external_reading",
        "esp32_hardware",
        "governance_analysis",
        "cross_agent_coordination",
        "tool_building",
        "prediction_grading",
    ]
    for ws in workstreams:
        selector.register(ws)

    # Simulate recent history (C554-C558 was heavy on governance/ESP32)
    random.seed(42)
    for _ in range(20):
        chosen = selector.select()
        # Simulate reward: governance/esp32 have diminishing returns
        if chosen in ("governance_analysis", "esp32_hardware"):
            reward = random.uniform(0.4, 0.7)  # diminishing returns
        else:
            reward = random.uniform(0.5, 0.9)  # uncertain but potentially high
        selector.reward(chosen, reward)

    print("Workstream Recommendations (Thompson Sampling):")
    print("=" * 60)
    for rec in selector.get_recommendation():
        print(f"  {rec['name']:40s} score={rec['score']:.4f}  "
              f"quality={rec['expected_quality']:.4f}  "
              f"uncertainty={rec['uncertainty']:.4f}  "
              f"pulls={rec['pulls']}")

    print(f"\nNext cycle recommendation: {selector.select()}")


if __name__ == "__main__":
    main()
