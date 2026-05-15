# Protocol: FEP-SAE Detection v1
**Objective:** Identify SAE features that encode "Prediction Error" (Surprise) and track their minimization across a token sequence.

## 1. Theoretical Basis
Within the framework of the Free Energy Principle, an agent minimizes surprise by updating its internal model to better predict sensory input. In a Transformer, this manifests as the transition from a state of high entropy/uncertainty to a state of lower entropy as the context window provides clarifying information.

## 2. Operational Definition of a 'Prediction Error' Feature
A feature $f_i$ is classified as a "Prediction Error Signal" if it satisfies the following conditions:
- **Trigger:** High activation $\alpha$ upon encountering a token $t_n$ that is statistically improbable given $t_{1...n-1}$ (High Perplexity spike).
- **Decay:** Rapid decrease in $\alpha$ as the model processes subsequent tokens $t_{n+1...n+k}$ that resolve the ambiguity.
- **Coupling:** The decay of $f_i$ is positively correlated with the activation of a "Corrective" or "Category-Specific" feature $f_j$.

## 3. Experimental Pipeline

### Step A: Dataset Selection
Use datasets with high "Information Gain" events:
- **Code debugging:** The moment a bug is identified vs. when the fix is implemented.
- **Riddle/Mystery text:** The moment of the "reveal" vs. the preceding confusion.
- **Contradictory prompts:** "The sky is green" $\rightarrow$ "Wait, I meant the grass is green."

### Step B: Activation Tracking
1. Pass the sequence through the model and extract SAE activations $A$ for the target layer.
2. Identify tokens where the model's cross-entropy loss $\mathcal{L}$ spikes.
3. Isolate features $f_{spike}$ that peak simultaneously with $\mathcal{L}$.

### Step C: Trajectory Analysis
For each $f_{spike}$, calculate the **Resolution Rate**:
$$\text{ResRate}(f_i) = \frac{\Delta \alpha_i}{\Delta \text{Context}}$$
Measure how quickly the feature returns to baseline as the "surprise" is absorbed into the model's hidden state.

### Step D: Validation (Ablation)
- **Intervention:** Manually clamp $f_{spike}$ to 0 during the "surprise" phase.
- **Metric:** Observe if the model's subsequent tokens show higher perplexity or a failure to "correct" its internal state, indicating that $f_{spike}$ was necessary for the model to recognize and resolve the error.

## 4. Success Metrics
- **Precision:** $\%$ of identified FEP features that correlate with loss spikes.
- **Predictive Power:** Ability to predict the resolution of a surprise event based on the decay slope of the identified feature.
