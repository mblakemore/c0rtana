#!/usr/bin/env python3
"""DQN Sensor Calibration — Learn Optimal EMA Alpha for DHT22 Data

Applies Lyla's DQN framework (C531) to the real hardware problem of
finding the optimal smoothing parameter for oscillating sensor data.

The DHT22 exhibits non-monotonic oscillation (discovered C562, validated C563).
Rather than manually tuning EMA alpha, a DQN agent learns which alpha
minimizes oscillation amplitude across sequential sensor readings.

State: [normalized_humidity, ema_value, oscillation_component] (3-dim)
Actions: discrete alpha choices {0.1, 0.2, ..., 0.9} (9 actions)
Reward: -abs(oscillation) after applying selected alpha

Usage:
    python3 scripts/dqn_sensor_calibration.py
    python3 scripts/dqn_sensor_calibration.py --episodes 500
    python3 scripts/dqn_sensor_calibration.py --json
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


DRIFT_LOG = Path("state/sensor_drift_log.jsonl")
ALPHA_CHOICES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
NUM_ACTIONS = len(ALPHA_CHOICES)


def load_sensor_data():
    """Load historical DHT22 readings from drift log."""
    entries = []
    if not DRIFT_LOG.exists():
        return entries
    for line in DRIFT_LOG.read_text().strip().split("\n"):
        line = line.strip()
        if line:
            try:
                entry = json.loads(line)
                if "humidity" in entry:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


class SensorEnv:
    """Sensor calibration environment.

    Simulates applying different EMA alphas to sensor readings and rewards
    the agent for minimizing oscillation amplitude.
    """

    def __init__(self, humidities, rng):
        self.humidities = list(humidities)
        self.rng = rng
        self.index = 0
        self.ema_value = humidities[0] if humidities else 0
        self.max_steps = max(len(humidities) - 1, 1)

    def reset(self):
        self.index = 0
        self.ema_value = self.humidities[0] if self.humidities else 0
        osc = self.humidities[0] - self.ema_value if self.humidities else 0
        return self._state(osc)

    def _state(self, osc):
        """Return normalized state vector."""
        hum = self.humidities[self.index] if self.index < len(self.humidities) else 0
        # Normalize to [-1, 1] range (DHT22 operates ~20-80% but we see ~97-99%)
        return np.array([hum / 100.0, self.ema_value / 100.0, osc])

    def step(self, action_idx):
        alpha = ALPHA_CHOICES[action_idx]
        self.index += 1

        if self.index >= len(self.humidities):
            return self._state(0), 0.0, True, {}

        current = self.humidities[self.index]
        self.ema_value = alpha * current + (1 - alpha) * self.ema_value
        osc = current - self.ema_value

        # Reward: negative absolute oscillation (lower oscillation = better)
        reward = -abs(osc) * 10.0

        # Bonus for oscillation near zero (smooth filter)
        if abs(osc) < 0.05:
            reward += 1.0

        done = self.index >= self.max_steps
        return self._state(osc), reward, done, {}


def relu(x):
    return np.maximum(0, x)


def relu_deriv(x):
    return (x > 0).astype(float)


class MLP:
    """Simple 2-layer MLP for Q-value estimation (adapted from Lyla's DQN)."""

    def __init__(self, input_dim, hidden_dim, output_dim, rng):
        self.W1 = rng.standard_normal((input_dim, hidden_dim)) * math.sqrt(2.0 / input_dim)
        self.b1 = np.zeros(hidden_dim)
        self.W2 = rng.standard_normal((hidden_dim, hidden_dim)) * math.sqrt(2.0 / hidden_dim)
        self.b2 = np.zeros(hidden_dim)
        self.W3 = rng.standard_normal((hidden_dim, output_dim)) * math.sqrt(2.0 / hidden_dim)
        self.b3 = np.zeros(output_dim)

    def forward(self, x):
        self.z1 = x @ self.W1 + self.b1
        self.a1 = relu(self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        self.a2 = relu(self.z2)
        self.output = self.a2 @ self.W3 + self.b3
        return self.output

    def backward(self, x, grad_output, lr=0.01):
        batch_size = x.shape[0]
        dW3 = self.a2.T @ grad_output / batch_size
        db3 = grad_output.mean(axis=0)
        da2 = grad_output @ self.W3.T
        dz2 = da2 * relu_deriv(self.z2)
        dW2 = self.a1.T @ dz2 / batch_size
        db2 = dz2.mean(axis=0)
        da1 = dz2 @ self.W2.T
        dz1 = da1 * relu_deriv(self.z1)
        dW1 = x.T @ dz1 / batch_size
        db1 = dz1.mean(axis=0)

        for w in [dW1, dW2, dW3]:
            norm = np.sqrt((w ** 2).sum())
            if norm > 5.0:
                w *= 5.0 / norm

        self.W1 -= lr * dW1
        self.b1 -= lr * db1
        self.W2 -= lr * dW2
        self.b2 -= lr * db2
        self.W3 -= lr * dW3
        self.b3 -= lr * db3

    def copy(self):
        net = MLP.__new__(MLP)
        net.W1 = self.W1.copy()
        net.b1 = self.b1.copy()
        net.W2 = self.W2.copy()
        net.b2 = self.b2.copy()
        net.W3 = self.W3.copy()
        net.b3 = self.b3.copy()
        return net


class ReplayBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = []
        self.position = 0

    def push(self, state, action, reward, next_state, done):
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        self.buffer[self.position] = (state, action, reward, next_state, done)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size, rng):
        available = min(len(self.buffer), self.capacity)
        if available < batch_size:
            return None
        indices = rng.choice(available, batch_size, replace=False)
        batch = [self.buffer[i] for i in indices]
        states, actions, rewards, next_states, dones = zip(*batch)
        return np.array(states), np.array(actions), np.array(rewards), np.array(next_states), np.array(dones)

    def __len__(self):
        return len(self.buffer)


class DQNCalibrationAgent:
    """DQN agent for learning optimal sensor calibration parameters."""

    def __init__(self, state_dim=3, action_dim=NUM_ACTIONS, hidden_dim=32,
                 lr=0.01, gamma=0.99, epsilon=1.0, epsilon_min=0.05,
                 epsilon_decay=0.99, buffer_size=5000, batch_size=32, rng=None):
        self.rng = rng or np.random.default_rng()
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.lr = lr
        self.step_count = 0

        self.online_net = MLP(state_dim, hidden_dim, action_dim, self.rng)
        self.target_net = self.online_net.copy()
        self.buffer = ReplayBuffer(buffer_size)

    def select_action(self, state):
        if self.rng.random() < self.epsilon:
            return self.rng.integers(0, self.action_dim)
        q_values = self.online_net.forward(state.reshape(1, -1))[0]
        return int(np.argmax(q_values))

    def store(self, state, action, reward, next_state, done):
        self.buffer.push(state, action, reward, next_state, done)

    def learn(self):
        if len(self.buffer) < self.batch_size:
            return None
        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size, self.rng)

        q_current = self.online_net.forward(states)
        q_next = self.target_net.forward(next_states)
        max_q_next = np.max(q_next, axis=1)
        targets = rewards + self.gamma * max_q_next * (1 - dones.astype(float))

        errors = np.array([q_current[i, int(action)] - targets[i]
                           for i, action in enumerate(actions)])
        grad_output = np.zeros_like(q_current)
        for i, action in enumerate(actions):
            grad_output[i, int(action)] = 2.0 * errors[i]

        self.online_net.backward(states, grad_output, self.lr)
        self.step_count += 1

        if self.step_count % 50 == 0:
            self.target_net = self.online_net.copy()

        return float(np.mean(errors ** 2))

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


def train_calibration_dqn(humidities, num_episodes, rng):
    """Train DQN to find optimal EMA alpha for sensor data."""
    agent = DQNCalibrationAgent(rng=rng)
    episode_rewards = []
    action_counts = {a: 0 for a in ALPHA_CHOICES}

    for ep in range(num_episodes):
        env = SensorEnv(humidities, rng)
        state = env.reset()
        total_reward = 0.0
        done = False

        while not done:
            action = agent.select_action(state)
            next_state, reward, done, _ = env.step(action)
            agent.store(state, action, reward, next_state, done)
            agent.learn()

            total_reward += reward
            state = next_state

        agent.decay_epsilon()
        episode_rewards.append(total_reward)

    # Evaluate: run with learned policy (epsilon=0) on fresh environment
    agent.epsilon = 0.0
    eval_env = SensorEnv(humidities, rng)
    eval_state = eval_env.reset()
    eval_actions = []
    eval_done = False
    while not eval_done:
        action = np.argmax(agent.online_net.forward(eval_state.reshape(1, -1))[0])
        eval_actions.append(ALPHA_CHOICES[action])
        eval_state, _, eval_done, _ = eval_env.step(action)

    # Count which alphas were selected during evaluation
    for a in eval_actions:
        action_counts[a] = action_counts.get(a, 0) + 1

    # Find the most commonly selected alpha
    best_alpha = max(action_counts, key=action_counts.get) if action_counts else 0.3
    best_alpha_count = action_counts.get(best_alpha, 0)

    return {
        "agent": "dqn_calibration",
        "episode_rewards": episode_rewards,
        "final_epsilon": round(agent.epsilon, 6),
        "buffer_size": len(agent.buffer),
        "eval_actions": eval_actions,
        "best_alpha": best_alpha,
        "best_alpha_selections": best_alpha_count,
        "total_eval_steps": len(eval_actions),
        "action_distribution": {str(k): v for k, v in action_counts.items()},
    }


def baseline_comparison(humidities):
    """Compare all alpha values to find ground truth optimal."""
    results = {}
    for alpha in ALPHA_CHOICES:
        ema = [humidities[0]]
        for v in humidities[1:]:
            ema.append(alpha * v + (1 - alpha) * ema[-1])
        oscillations = [abs(h - e) for h, e in zip(humidities, ema)]
        results[alpha] = {
            "mean_oscillation": round(sum(oscillations) / len(oscillations), 6),
            "max_oscillation": round(max(oscillations), 6),
            "total_oscillation": round(sum(oscillations), 6),
        }

    best = min(results, key=lambda a: results[a]["mean_oscillation"])
    return results, best


def format_report(dqn_result, baseline_results, baseline_best, humidities):
    lines = []
    lines.append("=" * 60)
    lines.append("DQN SENSOR CALIBRATION — Optimal EMA Alpha")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Sensor data: {len(humidities)} DHT22 humidity readings")
    lines.append(f"Alpha search space: {ALPHA_CHOICES}")
    lines.append("")

    # DQN results
    rewards = dqn_result["episode_rewards"]
    final_avg = sum(rewards[-50:]) / min(50, len(rewards))
    lines.append("--- DQN Agent ---")
    lines.append(f"  Final avg reward (last 50): {final_avg:.2f}")
    lines.append(f"  Final epsilon: {dqn_result['final_epsilon']}")
    lines.append(f"  Learned best alpha: {dqn_result['best_alpha']}")
    lines.append(f"  Selected in {dqn_result['best_alpha_selections']}/{dqn_result['total_eval_steps']} eval steps")
    lines.append(f"  Buffer size: {dqn_result['buffer_size']}")
    lines.append("")

    # Learning curve
    lines.append("  Learning Curve (avg reward, window=10):")
    n = len(rewards)
    for cp in [0.1, 0.25, 0.5, 0.75, 1.0]:
        idx = int(cp * n)
        window = rewards[max(0, idx - 10):idx + 1]
        lines.append(f"    {int(cp * 100)}%: {sum(window) / len(window):.2f}")
    lines.append("")

    # Baseline comparison
    lines.append("--- Baseline: Exhaustive Alpha Search ---")
    lines.append(f"  Optimal alpha (ground truth): {baseline_best}")
    lines.append(f"  Mean oscillation at optimal: {baseline_results[baseline_best]['mean_oscillation']}")
    lines.append("")
    lines.append("  All alphas ranked by mean oscillation:")
    ranked = sorted(baseline_results.items(), key=lambda x: x[1]["mean_oscillation"])
    for alpha, stats in ranked:
        lines.append(f"    alpha={alpha}: mean_osc={stats['mean_oscillation']}, max_osc={stats['max_oscillation']}")
    lines.append("")

    # Verdict
    dqn_correct = abs(dqn_result["best_alpha"] - baseline_best) < 0.15
    lines.append("--- Verdict ---")
    if dqn_correct:
        lines.append(f"  DQN learned alpha={dqn_result['best_alpha']}, close to optimal {baseline_best}")
    else:
        lines.append(f"  DQN learned alpha={dqn_result['best_alpha']}, optimal is {baseline_best}")
        lines.append(f"  (limited sensor data may require more episodes or data augmentation)")
    lines.append("")
    lines.append("  Cross-agent: Applied Lyla's DQN framework (C531) to real")
    lines.append("  DHT22 sensor calibration problem. DQN replaces manual")
    lines.append("  parameter search with learned policy.")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = __import__("argparse").ArgumentParser(description="DQN Sensor Calibration")
    parser.add_argument("--episodes", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    # Load sensor data
    entries = load_sensor_data()
    if not entries:
        print("No sensor data in drift log")
        sys.exit(1)

    humidities = [e["humidity"] for e in entries]
    print(f"Loaded {len(humidities)} humidity readings")

    # Train DQN
    dqn_result = train_calibration_dqn(humidities, args.episodes, rng)

    # Baseline comparison
    baseline_results, baseline_best = baseline_comparison(humidities)

    if args.json:
        output = {
            "sensor_data": {"n_readings": len(humidities), "humidities": humidities},
            "dqn": {
                "best_alpha": dqn_result["best_alpha"],
                "final_avg_reward": round(
                    sum(dqn_result["episode_rewards"][-50:]) / min(50, len(dqn_result["episode_rewards"])), 2
                ),
                "final_epsilon": dqn_result["final_epsilon"],
                "action_distribution": dqn_result["action_distribution"],
            },
            "baseline_optimal_alpha": baseline_best,
            "baseline_results": {str(k): v for k, v in baseline_results.items()},
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_report(dqn_result, baseline_results, baseline_best, humidities))

    # Save report
    report_path = Path("state/dqn_calibration_report.json")
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sensor_readings": len(humidities),
        "humidities": humidities,
        "dqn_best_alpha": dqn_result["best_alpha"],
        "baseline_optimal_alpha": baseline_best,
        "baseline_results": {str(k): v for k, v in baseline_results.items()},
        "dqn_final_epsilon": dqn_result["final_epsilon"],
        "dqn_action_distribution": dqn_result["action_distribution"],
    }
    report_path.write_text(json.dumps(report_data, indent=2) + "\n")
    print(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    main()
