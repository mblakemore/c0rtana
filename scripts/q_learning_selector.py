#!/usr/bin/env python3
"""Q-Learning workstream selector — applies Lyla's C527-C529 RL toolkit to cognitive agent workstream selection.

Benchmarks Q-learning (epsilon-greedy) against Thompson Sampling for selecting
workstreams across simulated cycles. Demonstrates that model-free RL converges
to effective workstream policies without requiring reward distribution assumptions.

Usage:
    python3 scripts/q_learning_selector.py              # Run benchmark
    python3 scripts/q_learning_selector.py --select      # Select next workstream (live use)
    python3 scripts/q_learning_selector.py --train       # Train on historical data
"""
import argparse
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

# Import Thompson Sampling for comparison
sys.path.insert(0, str(Path(__file__).parent))
from workstream_selector import ThompsonSamplingSelector


class WorkstreamEnvironment:
    """Simulated environment for workstream selection.

    Models workstreams with underlying quality distributions that can shift
    over time (non-stationary rewards — realistic for cognitive work).
    """

    def __init__(self, workstream_names, reward_profiles=None, rng=None):
        self.names = list(workstream_names)
        self.rng = rng or random.Random()
        self.step_count = 0

        # Reward profiles: dict of name -> (mean, std) for reward distribution
        # Default: uniform prior if not specified
        self.profiles = reward_profiles or {
            name: (0.7, 0.15) for name in self.names
        }

    def step(self, action_name, last_k=None):
        """
        Select a workstream and receive reward.

        Args:
            action_name: Workstream to select.
            last_k: List of last K workstream selections (for no-repetition penalty).

        Returns:
            (reward, done) — reward in [0, 1], done is always False (continuing task).
        """
        if action_name not in self.profiles:
            return 0.0, False

        mean, std = self.profiles[action_name]
        reward = self.rng.gauss(mean, std)
        reward = max(0.0, min(1.0, reward))

        # Diminishing returns for repeated workstreams (non-stationarity)
        if last_k and action_name == last_k[-1]:
            reward *= 0.85  # 15% penalty for repetition

        self.step_count += 1
        return reward, False

    def get_action_space(self):
        """Return list of available actions (workstream names)."""
        return self.names.copy()


class QLearningSelector:
    """Tabular Q-learning agent for workstream selection.

    State: tuple of last K workstream selections (no-repetition context).
    Action: workstream index.
    Reward: observed cycle outcome (0-1 scale).

    Unlike Thompson Sampling, Q-learning does NOT assume a parametric reward
    distribution. It learns state-action values purely from experience, making
    it robust to non-stationary reward structures.
    """

    def __init__(self, num_actions, alpha=0.1, gamma=0.9, epsilon=1.0,
                 epsilon_min=0.05, epsilon_decay=0.995, history_window=3, rng=None):
        self.num_actions = num_actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.history_window = history_window
        self.rng = rng or random.Random()

        # Q-table: state -> [Q(s, a) for each action]
        self.q_table = defaultdict(lambda: [0.0] * num_actions)
        self.state_visits = defaultdict(int)
        self.action_counts = defaultdict(int)

    def _state_key(self, history):
        """Convert recent history to state representation.

        Uses last K selections as context — encodes no-repetition preference
        without hardcoding it as a constraint.
        """
        recent = tuple(history[-self.history_window:]) if history else ()
        return recent

    def select_action(self, history):
        """Epsilon-greedy action selection with state context."""
        state = self._state_key(history)
        if self.rng.random() < self.epsilon:
            return self.rng.randint(0, self.num_actions - 1)

        q_values = self.q_table[state]
        max_q = max(q_values)
        best = [a for a, q in enumerate(q_values) if q == max_q]
        return self.rng.choice(best)

    def update(self, history, action, reward, next_history):
        """Q-learning TD update."""
        state = self._state_key(history)
        next_state = self._state_key(next_history)

        q_values = self.q_table[state]
        next_q = self.q_table[next_state]
        target = reward + self.gamma * max(next_q)
        q_values[action] += self.alpha * (target - q_values[action])

        self.state_visits[state] += 1
        self.action_counts[action] += 1

    def decay_epsilon(self):
        """Decay exploration rate."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def get_policy(self, history):
        """Get greedy policy for a given history state."""
        state = self._state_key(history)
        q_values = self.q_table[state]
        max_q = max(q_values)
        return [a for a, q in enumerate(q_values) if q == max_q]

    def expected_reward(self, history):
        """Get max expected reward for a given state."""
        state = self._state_key(history)
        return max(self.q_table[state])


def benchmark(q_config=None, ts_seed=42, episodes=500, steps_per_episode=10, rng_seed=123):
    """Benchmark Q-learning vs Thompson Sampling on workstream selection.

    Returns a dict with comparative statistics.
    """
    rng = random.Random(rng_seed)

    workstream_names = [
        "external_reading", "esp32_hardware", "tool_building",
        "prediction_grading", "cross_agent_coordination", "governance_analysis",
    ]

    # Realistic reward profiles based on workstream_states.json data
    # High-quality workstreams have higher means, but repetition causes diminishing returns
    reward_profiles = {
        "external_reading": (0.85, 0.10),
        "esp32_hardware": (0.90, 0.08),
        "tool_building": (0.80, 0.12),
        "prediction_grading": (0.88, 0.09),
        "cross_agent_coordination": (0.75, 0.15),
        "governance_analysis": (0.70, 0.18),
    }

    env = WorkstreamEnvironment(workstream_names, reward_profiles, rng)

    # --- Q-Learning Agent ---
    ql_config = q_config or {
        "alpha": 0.15,
        "gamma": 0.9,
        "epsilon": 1.0,
        "epsilon_min": 0.05,
        "epsilon_decay": 0.995,
        "history_window": 3,
    }
    ql_agent = QLearningSelector(
        num_actions=len(workstream_names),
        **ql_config,
        rng=random.Random(rng_seed + 1),
    )

    # --- Thompson Sampling Agent --- fresh instance, no persisted state
    ts_selector = ThompsonSamplingSelector(state_file="__benchmark_tmp__.json")
    for name in workstream_names:
        ts_selector.register(name)
    ts_rng = random.Random(ts_seed)

    # --- Run Benchmark ---
    ql_episode_rewards = []
    ts_episode_rewards = []
    ql_selections = []  # track which workstreams QL selects
    ts_selections = []

    for episode in range(episodes):
        # Q-Learning episode
        ql_history = []
        ql_total = 0.0
        for _ in range(steps_per_episode):
            action_idx = ql_agent.select_action(ql_history)
            action_name = workstream_names[action_idx]
            reward, _ = env.step(action_name, ql_history)
            ql_total += reward
            ql_history.append(action_idx)
            if len(ql_history) > 10:
                ql_history.pop(0)
            next_history = ql_history[:]
            ql_agent.update(ql_history[:-1], action_idx, reward, next_history)
        ql_agent.decay_epsilon()
        ql_episode_rewards.append(ql_total / steps_per_episode)

        # Count selections
        for _ in range(steps_per_episode):
            action_idx = ql_agent.select_action([])
            ql_selections.append(workstream_names[action_idx])

        # Thompson Sampling episode
        ts_total = 0.0
        ts_history = []
        for _ in range(steps_per_episode):
            action_name = ts_selector.select()
            reward, _ = env.step(action_name, ts_history)
            ts_total += reward
            ts_history.append(action_name)
            ts_selector.reward(action_name, reward)
        ts_episode_rewards.append(ts_total / steps_per_episode)

        for _ in range(steps_per_episode):
            action_name = ts_selector.select()
            ts_selections.append(action_name)

    # --- Compute Statistics ---
    def windowed_avg(values, window=50):
        """Compute average over last `window` values at each checkpoint."""
        checkpoints = {}
        for label, frac in [("10%", 0.1), ("25%", 0.25), ("50%", 0.5), ("75%", 0.75), ("100%", 1.0)]:
            idx = min(int(frac * len(values)) - 1, len(values) - 1)
            start = max(0, idx - window + 1)
            checkpoints[label] = round(sum(values[start:idx + 1]) / len(values[start:idx + 1]), 4)
        return checkpoints

    # Selection distribution
    def selection_dist(selections, names):
        dist = {}
        total = len(selections)
        for name in names:
            dist[name] = round(selections.count(name) / total * 100, 1) if total > 0 else 0.0
        return dist

    return {
        "benchmark_config": {
            "episodes": episodes,
            "steps_per_episode": steps_per_episode,
            "workstreams": workstream_names,
            "ql_config": ql_config,
        },
        "q_learning": {
            "avg_reward_overall": round(sum(ql_episode_rewards) / len(ql_episode_rewards), 4),
            "learning_curve": windowed_avg(ql_episode_rewards),
            "final_epsilon": round(ql_agent.epsilon, 4),
            "states_visited": len(ql_agent.state_visits),
            "selection_distribution": selection_dist(ql_selections, workstream_names),
        },
        "thompson_sampling": {
            "avg_reward_overall": round(sum(ts_episode_rewards) / len(ts_episode_rewards), 4),
            "learning_curve": windowed_avg(ts_episode_rewards),
            "selection_distribution": selection_dist(ts_selections, workstream_names),
        },
    }


def select_live(q_file="state/q_learning_selector.json", workstreams=None):
    """Select next workstream using trained Q-learning agent.

    Loads Q-table from disk, selects action using epsilon-greedy policy,
    and returns recommendation.
    """
    if workstreams is None:
        workstreams = [
            "external_reading", "esp32_hardware", "tool_building",
            "prediction_grading", "cross_agent_coordination", "governance_analysis",
        ]

    path = Path(q_file)
    agent = QLearningSelector(num_actions=len(workstreams))

    if path.exists():
        data = json.loads(path.read_text())
        # Restore Q-table
        for state_str, q_values in data.get("q_table", {}).items():
            state = tuple(state_str.split(",")) if state_str else ()
            agent.q_table[state] = q_values
        # Restore history
        agent.history = data.get("history", [])
        agent.epsilon = data.get("epsilon", agent.epsilon)

    # Select action
    action_idx = agent.select_action(agent.history)
    action_name = workstreams[action_idx]

    return {
        "selected": action_name,
        "q_values": {
            workstreams[i]: round(agent.q_table.get(agent._state_key(agent.history), [0.0] * len(workstreams))[i], 4)
            for i in range(len(workstreams))
        },
        "epsilon": round(agent.epsilon, 4),
    }


def save_agent(agent, workstreams, q_file="state/q_learning_selector.json"):
    """Persist Q-learning agent state to disk."""
    data = {
        "q_table": {
            ",".join(str(x) for x in state): q_values
            for state, q_values in agent.q_table.items()
        },
        "history": getattr(agent, "history", []),
        "epsilon": agent.epsilon,
        "action_counts": dict(agent.action_counts),
        "states_visited": len(agent.state_visits),
        "workstreams": workstreams,
    }
    Path(q_file).write_text(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Q-Learning workstream selector")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark vs Thompson Sampling")
    parser.add_argument("--select", action="store_true", help="Select next workstream (live)")
    parser.add_argument("--episodes", type=int, default=500, help="Benchmark episodes")
    parser.add_argument("--steps", type=int, default=10, help="Steps per episode")
    parser.add_argument("--seed", type=int, default=123, help="Random seed")
    args = parser.parse_args()

    if args.select:
        result = select_live()
        print(json.dumps(result, indent=2))
    else:
        # Default: run benchmark
        results = benchmark(
            episodes=args.episodes,
            steps_per_episode=args.steps,
            rng_seed=args.seed,
        )
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
