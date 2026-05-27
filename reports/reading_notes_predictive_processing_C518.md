# C518: Predictive Processing — Reading Notes

## Sources
- Wikipedia: Predictive coding, Free energy principle
- Topic: Karl Friston's framework, Andy Clark's "Whatever Next?" (2013), Rao & Ballard (1999)

## Core Theory

Predictive coding inverts the traditional view of perception. Instead of the brain receiving passive sensory data and building up a model bottom-up, the brain generates top-down predictions and only passes upward what *doesn't* match — prediction errors.

Key concepts:
1. **Hierarchical prediction**: Each level of the cortex predicts the level below; only residuals propagate up.
2. **Precision weighting**: The brain weights prediction errors by their reliability — this is what attention *is*, under this theory.
3. **Active inference**: The same machinery that updates beliefs also drives action. You move your body to make your sensory predictions come true.
4. **Free energy principle**: A mathematical unification — systems minimize variational free energy (an upper bound on surprise). Minimizing free energy w.r.t. internal states = Bayesian belief updating. Minimizing w.r.t. actions = active inference.

## Connection to McGilchrist

McGilchrist's book argues the left hemisphere (LH) is specialized for abstract, decontextualized, reductionist representation, while the right hemisphere (RH) is specialized for embodied, holistic, context-sensitive perception.

The predictive coding framework maps onto this:

- **LH as high-precision prior**: The left hemisphere is the source of strong, rigid predictions — categories, rules, abstractions. It's the "model" that has been trained and now runs on autopilot.
- **RH as precision-weighting mechanism**: The right hemisphere is what detects when the model is wrong, what reweights priors in light of novel evidence, what keeps the model honest. Its slow processing speed is a *feature*: it gathers more information before allowing predictions to update.
- **Creative insight = RH loosening LH priors**: The moment of insight occurs when the right hemisphere's precision weighting allows a previously suppressed prediction error to update the left hemisphere's model.

## Key Insight

This is a genuine synthesis, not just a mapping. McGilchrist described *what* the hemispheres do; predictive coding provides a *mechanism* for how the right hemisphere might keep the left's predictions honest. The "right hemisphere hypothesis of depression" — that depression is an over-weighting of negative priors — is a concrete example where predictive coding explains McGilchrist's clinical observations.

## Current State of the Theory

The theory remains controversial. Key open questions:
- How does the brain actually implement prediction errors? No consensus.
- What is an error signal in neural terms?
- The framework is computationally tractable in some domains but disputed in others.
- ERP/EEG evidence is suggestive but not definitive.

## My Prediction

Given that predictive processing provides a mechanistic account of how priors and evidence interact, and given McGilchrist's claim that the RH's slower processing is what keeps the LH's abstractions from running away, I predict that:

**P_C518_RH_LOOSENING**: The creative insight phenomenon (Gestalt "Aha!" moments) will be empirically distinguishable from routine pattern recognition by a measurable shift in precision weighting — specifically, a temporary *decrease* in the precision assigned to prior expectations (allowing novel prediction errors to propagate) followed by a *rebound* in precision as the new model consolidates. This predicts a U-shaped temporal profile of precision during insight, with the insight moment at the nadir.

This is testable via EEG (alpha-band power as a proxy for precision) during tasks that elicit insight vs. routine problem-solving.
