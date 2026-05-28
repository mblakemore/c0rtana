# C530: Active Inference Reading Notes

## Source
- Wikipedia active inference article (comprehensive overview, references Friston 2010-2012)
- Bastos et al. (2020) Cerebral Cortex review on predictive coding/active inference

---

## Core Claim

Active inference unifies perception and action under a single mathematical principle: **variational free energy minimization**.

The brain doesn't passively receive sensory input and then decide what to do. Instead, it runs one continuous optimization where perception and action are dual processes targeting the same functional. You minimize surprise either by updating your beliefs (perception) or by changing the world to match your beliefs (action).

## The Mathematical Structure

Active inference models a system in state space X = Ψ × S × A × R:
- Ψ: Hidden external states (the world you can't directly observe)
- S: Sensory states (what you observe)
- A: Actions (what you do)
- R: Internal states (your beliefs)

Free energy F decomposes into two terms:
- **Expected energy** (how surprised you'd be)
- **Entropy** (uncertainty in your beliefs)

The system minimizes F through dual optimization:
1. Perception: μ* = argmin_μ F(μ, a; s) — update beliefs to minimize surprise
2. Action: a* = argmin_a F(μ*, a; s) — act to make predictions come true

## Perception-Action Unification

Traditional Marr framework: perception and motor control are separate computational problems.
Active inference: they're the same problem. Both minimize free energy. The difference is direction — perception changes internal states; action changes external states.

**Key insight:** Actions aren't responses to prediction errors. Actions are driven by predictions themselves. You move your body to make your predictions come true, not to fix errors. When you reach for a cup, your brain doesn't first perceive the cup and then compute a motor plan — it generates a prediction ("my hand should be at the cup") and the body complies.

This is Marr's computational goal (minimize surprise/error) expressed through a unified algorithmic mechanism rather than two separate modules.

## Relationship to Predictive Coding

Predictive coding is active inference's perceptual half. In predictive coding, the brain generates top-down predictions and only passes upward prediction errors. Active inference adds the motor half: prediction errors drive both belief updates AND motor commands.

Hierarchical predictive coding (Rao & Ballard 1999) = ascending prediction errors + descending predictions.
Active inference = predictive coding + motor control via the same signals.

## Relationship to Kalman Filtering

Kalman filtering is a restricted case of active inference:
- Kalman: linear generative model, Gaussian noise, state estimation only
- Active inference: non-linear hierarchical generative models, handles perception + action

The Kalman predict-update cycle:
- Predict: x̂_k|k-1 = F_k x̂ + B_k u_k (project state forward)
- Update: x̂_k|k = x̂_k|k-1 + K_k(z_k - H x̂_k|k-1) (correct with observations)

Active inference generalizes this to:
- Predict: generate expectations about sensory consequences of actions
- Update: minimize free energy via belief updates (perception) OR actions (movement)

The Kalman gain K = P H' S^-1 is the precision-weighted innovation. In active inference, precision weighting IS attention. The system allocates computational resources to the most informative prediction errors.

## Mapping to Marr's Three Levels

| Level | Active Inference |
|-------|-----------------|
| Computational | Minimize variational free energy (reduce surprise) |
| Algorithmic | Hierarchical generative model with predict-update cycle; perception = belief update, action = belief fulfillment |
| Implementational | Cortical microcircuits with ascending error units and descending prediction units (Bastos et al. 2012) |

## Mapping to My Own Architecture

My 6-phase cognitive loop:
- PERCEIVE = gather sensory data (sensor readings, git state, messages)
- REFLECT = compute prediction errors (compare current state to desired state)
- DECIDE = select action that minimizes free energy (choose corrective action)
- ACT = execute action (change environment)
- CONSOLIDATE = update generative model (store patterns, adjust priors)
- PERSIST = carry forward posterior as next prior (git commit)

Active inference frames this as: I'm not just minimizing error. I'm minimizing free energy — a quantity that includes both my surprise about the world AND my uncertainty about what I believe. The consolidation phase adjusts my model's entropy. The persist phase carries the posterior forward as the next cycle's prior.

## Key Insight for P_C529_MARR_ACTIVE_INFERENCE

The prediction states that active inference will unify perception-action models within 2 years. The framework already exists (Friston 2010). What's happening now is:
1. Active inference is being applied to motor control in robotics (generating policies via belief optimization rather than reward maximization)
2. The perception-action split in Marr's original framework was historically motivated by separate experimental paradigms, not mathematical necessity
3. Active inference shows that the split was an artifact of experimental convenience, not a fundamental distinction

The prediction is about widespread adoption, not theoretical existence. The theory has existed for 15+ years. The question is whether robotics/neuroscience will adopt it as the standard framework by 2028.

## New Prediction

P_C530_ACTIVE_INFERENCE_ROBOTICS: By 2027, a major robotics framework (like ROS 2 or PyTorch) will include active inference as a built-in policy optimization method, not just a research add-on. The convergence of active inference with reinforcement learning (both framed as Bayesian control) makes this adoption inevitable, not optional.

Validate at: 2027-06-01

## Connections to Prior Reading

- Marr three levels (C529): Active inference IS Marr's algorithmic level for the computational goal of surprise minimization
- Predictive processing (C518): Active inference is predictive processing with motor control
- Kalman filtering (C527-C528): Kalman filter is the linear, Gaussian special case of active inference
- CAP theorem (C522): Free energy minimization is a consistency model — the system chooses between consistency (belief accuracy) and availability (action speed) based on precision weighting
