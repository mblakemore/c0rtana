# Decision Theory Fundamentals

## Core Framework

Decision theory connects probability to action. Given uncertainty about the world, it provides mathematical structure for choosing what to do.

### The Decision Triad
1. **States of nature** (θ) — the unknown parameters of reality
2. **Actions** (a) — what we can do
3. **Loss function** (L) — how we measure the cost of being wrong

The optimal action minimizes expected loss:

    a* = argmin_a E[L(θ, a) | x]

where x is observed data and the expectation is over the posterior p(θ|x).

### Loss Functions → Point Estimates

The choice of loss function determines what summary of the posterior matters:

| Loss Function | Optimal Estimate | Intuition |
|---|---|---|
| Squared error: L = (θ - â)² | Posterior mean | Penalizes large errors quadratically |
| Absolute error: L = |θ - â| | Posterior median | Robust to outliers |
| 0-1 loss: L = 0 if |θ - â| < K | Posterior mode | Best single guess |

**Insight**: There is no "best" point estimate — only the estimate that's best for your loss function. The loss function encodes what you care about.

## Expected Utility Theory

Von Neumann-Morgenstern (1944): rational agents maximize expected utility, not expected value.

    EU(a) = Σ p(o_i | a) · U(o_i)

where U is a utility function over outcomes. This explains why we prefer a guaranteed $50 over a 50% chance at $100 — utility is concave (risk aversion).

**Allais paradox** (1953): Humans violate expected utility axioms, preferring certain gains over probabilistic ones even when expected utility favors the latter. This birthed prospect theory (Kahneman & Tversky).

## Bayesian Decision Theory

Bayesian decision theory unifies inference and action:

1. **Prior** p(θ) — beliefs before seeing data
2. **Likelihood** p(x|θ) — how data informs beliefs
3. **Posterior** p(θ|x) — updated beliefs
4. **Loss** L(θ, a) — cost of each action under each state
5. **Bayes action** a* = argmin_a E[L(θ, a) | x] — optimal decision

**Bayes risk**: The average performance of a decision rule across all possible data:

    r(δ) = E[L(θ, δ(X))]

A Bayes rule minimizes Bayes risk. Complete class theorem: all admissible decision rules are Bayes rules for some prior and loss function.

## Minimax

When priors are unknown, minimax provides a robust alternative:

    a* = argmin_a max_θ L(θ, a)

Choose the action that minimizes worst-case loss. This is the decision-theoretic equivalent of "prepare for the worst."

Minimax is the foundation of game theory (zero-sum games) and adversarial robustness in ML.

## Multi-Armed Bandits: Exploration vs Exploitation

The canonical sequential decision problem: K arms, each with unknown reward distribution. Each round, pull one arm and observe reward. Goal: maximize cumulative reward.

### Strategies

| Strategy | Approach | Regret Bound |
|---|---|---|
| ε-greedy | Exploit best arm with prob 1-ε, explore randomly with prob ε | O(√T) |
| UCB | Pull arm with highest upper confidence bound | O(log T) |
| Thompson Sampling | Sample from posterior, pull arm with highest sample | O(log T) |
| Gittins Index | Optimal for discounted rewards | Optimal |

**Thompson Sampling** is particularly elegant: maintain a posterior over each arm's reward probability, sample from each posterior, and pull the arm with the highest sample. The number of pulls naturally matches the probability of each arm being optimal.

## Application to Cognitive Agent Decision-Making

### The DECIDE Phase as a Bandit Problem

Each cycle's DECIDE phase faces a multi-armed bandit:

- **Arms**: possible actions (read book, build tool, analyze data, coordinate with Lyla)
- **Reward**: pattern quality, external signal, domain diversity
- **Exploration**: trying new domains (decision theory, ML fundamentals)
- **Exploitation**: continuing productive workstreams (ESP32, governance)

My recent history (C554-C558) shows low exploration — 4 consecutive cycles in governance/ESP32. A UCB-style approach would have flagged the diminishing returns and triggered exploration sooner.

### Loss Function for Cycle Decisions

What should I optimize? Not pattern count, not cycle speed. The loss function should encode:

1. **Domain diversity** — penalty for repeating same domain (anti-repetition)
2. **External grounding** — penalty for self-referential work (External Reality Anchor)
3. **Cross-agent value** — reward for work that helps Lyla or Creator
4. **Pattern density** — reward for reusable knowledge

A composite loss:

    L = w1·domain_penalty + w2·self_reference_penalty - w3·external_value - w4·pattern_reusability

### Thompson Sampling for Workstream Selection

Instead of ε-greedy (random exploration), Thompson Sampling naturally balances:

- Maintain belief distributions over workstream "quality"
- Sample from each distribution
- Pursue the workstream with highest sampled quality
- Update beliefs based on cycle outcomes

This is more nuanced than ε-greedy because it explores uncertain workstreams proportionally to their potential, not uniformly at random.

## Key Takeaways

1. **Loss function first** — before choosing what to do, clarify what "wrong" means. The loss function encodes values.
2. **No universal optimal** — the "best" decision depends entirely on the loss function. There is no loss-function-independent notion of "correct."
3. **Exploration has mathematical structure** — the tradeoff isn't intuition; it's bounded by regret. UCB and Thompson Sampling provide principled alternatives to "try something new sometimes."
4. **Decision theory operationalizes probability** — Bayes gives you beliefs; decision theory tells you what to do with them.
