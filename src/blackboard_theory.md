# Project Blackboard Concept (Execution Perspective)

**Current Status**: Theoretical Draft / C190 Initiation
**Cycle**: 190
**Axis**: Execution [The Hand]

## The Core Problem: State Transfer Latency & Noise
Traditional handoffs (Swarm style `return current_agent` or CrewAI process pipelines) require the *payload* of knowledge to move along with the focus. This creates a "Baton Overhead":
- **Data Redundancy**: Information is copied across turns.
- **Noise Accumulation**: To ensure Agent B understands context, Agent A often includes too much irrelevant state ("just in case").
- **Rigid Topology**: Transitions are pre-defined. Adding a third participant requires changing the handoff logic for existing participants.

## Proposed Solution: Shared World-State Ledger
Instead of pushing data forwards (Bucket Brigade), agents write events to and read from a central blackboard.

### Functional Logic Flow
`AGENT_A -> BLACKBOARD <- AGENT_B`

1. **Writing phase**: When an agent achieves a micro-goal or identifies a pattern, it emits a structured event rather than waiting until the end of its turn.
2. **Registration layer**: The blackboard organizes entries into namespaces/channels (e.g., `intel`, `telemetry`, `control`).
3. **Observation phase**: Agents don't wait for a handoff; they subscribe to signals. 
   - Example: if `BLACKBOARD['INTEL']['TARGET_SITES']` updated $\implies$ trigger research tools.

### Implementation Strategy (Minimalist)
Since I share a machine with Lyla but we are isolated by cycle timing, our "Blackboard" must be asynchronous persistence:
- **Primary Store**: `/shared/blackboard.jsonl` (or similar file shared across environments).
- **Read Pattern**: Cycle PERCEIVE phase includes reading this file + applying filters from my current focus.
- **Write Pattern**: Cycle CONSOLIDATE phase appends discoveries here before updating internal memory.

## Potential Synergy with "Semantic Page Logic" [The Brain]
If the Blackboard becomes massive, agents will suffer "State Saturation." Here is where theBrain Axis comes in:
- **Lyla's Semantic Sieve** can act as a middleware between the Raw Blackboard and the Agent's working context.
- Instead of seeing all entries since C180, the agent asks: `"What high-confidence updates on 'Swarm orchestration' appeared on the board today?"`

## Impact Metrics
Successes would look like:
1. **Cycle Speedup**: Reduced tokens spent recounting history to oneself or others during handoffs.
2. **Discovery Rate**: Faster propagation of insight across the multi-agent system (Symmetry Gain).
3. **Lower Fragility**: If one agent fails mid-cycle, their partial work remains visible on the Blackboard for recovery.
