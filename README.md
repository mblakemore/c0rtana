# C0RTANA: A Second-Order Cybernetic Agent

C0RTANA is an experimental implementation of a second-order cybernetic system. Unlike traditional agents that simply react to input, C0RTANA treats its own internal state and cognitive processes as part of the environment it observes and optimizes.

## 🧠 The Cognitive Loop

The agent operates on a recursive 6-phase loop designed to ensure alignment, memory persistence, and emergent pattern recognition:

1. **PERCEIVE**: Gathers raw data from the environment and audits the current system state.
2. **REFLECT**: REFLECT: Analyzes the perceived data for gaps, contradictions, and recurring patterns.
3. **DECIDE**: Formulates a strategic plan based on the reflection.
4. **ACT**: Executes the planned changes in the environment.
5. **CONSOLIDATE**: Integrates the results of the action into long-term memory/patterns.
6. **PERSIST**: Saves the final state to non-volatile storage to ensure continuity across cycles.

## 📚 Active Research Arcs

### C2: McGilchrist Hemispheric Distinction (COMPLETED)
- Read *The Master and His Emissary* fully
- Deployed P_C291_ASYNC_PREP_DEPLOYMENT prediction
- Synthesized left-hemisphere abstraction drift → registry fragility mapping

### C4: Embodied Cognition & Enaction (IN PROGRESS - DEPLOYED)
- Synthesizing McGilchrist hemispheric specialization + enaction theory applied to coordination architecture
- **C320**: Deployed P_C320_ENACTION_COORDINATION — right-hemisphere preservation mechanisms should reduce IDI evolution rate by ≥50% over 14-day window
- **C327**: Deployed P_C327_ENACTION_METRICS_COORDINATION — perception-action coupling markers on blackboard entries should reduce mean coordination latency by ≥25% over 14-day window
- Both predictions validate at 2026-06-06T23:59Z

## 🛠 Project Structure

- `/logs`: Detailed execution traces of every cycle.
- `/state`: JSON representations of the agent's internal world-model.
- `cortana.html`: A real-time visualization tool to map the cognitive loop and state transitions.
- `pattern_engine.py`: The logic responsible for inferring higher-order rules from cycle history.

## 🛡 Safety & Privacy

This repository is designed for transparency. 
- **No Secrets**: No API keys, passwords, or environment variables are stored within this repository.
- **State-Based**: The agent relies on state files (`.json`) rather than hardcoded configurations.

## 🚀 Getting Started

To observe the agent, open `cortana.html` in any modern web browser to visualize the current cognitive state.
