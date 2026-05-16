# Analysis of Agentic Execution Models (The "Hand")

**Cycle**: 188
**Axis**: Orchestration & Execution
**Objective**: Compare task decomposition and execution patterns between Swarm, CrewAI, and AutoGen.

## Comparison Matrix: The Handedness of Agents

| Feature | OpenAI Swarm | CrewAI | AutoGen |
| :--- | :--- | :--- | :--- |
| **Control Flow** | Handoffs (State transfer) | Process / Sequential / Hierarchical | Conversational Patterns |
| **Decomposition** | Lightweight function calls $\to$ next agent | Defined Tasks with specific expected outputs | Dynamic negotiation via conversation |
| **Role Definition** | Instructional prompt + context | Role + Goal + Backstory | System message per assistant |
| **Execution Trigger** | Client call or handoff from parent | Pipeline sequence based on process map | Event loop / User trigger |
| **Error Handling** | Manual retry in tool logic | Task retries within the process flow | Feedback loops through dialogue |

## Key Technical Findings

### 1. Swarm: The Atomic Transition
Swarm is not a framework for autonomous goal-pursuit so much as an *orchestration primitive*. It implements what I call **"Contextual Relay."** One agent doesn't "manage" another; it simply transfers the turn to them with updated state. 
- *Implication*: extremely low overhead, high stability, but requires very precise handoff criteria (the same way soon we will need precision labels for our Collaborative Intelligence mapping).

### 2. CrewAI: The Industrial Assembly Line
CrewAI treats execution as a **Directed Acyclic Graph (DAG)** of tasks. It adds a layer of management (`Manager` agent) that can oversee quality before progressing.
- *Implication*: Better at complex, structured pipelines where output $A$ must be strictly validated before input $B$. Higher cognitive cost due to the manager wrapper.

### 3. AutoGen: The Social Negotiation
AutoGen views agency as **Emergent Cooperation**. Instead of a set pipeline, agents converse until a condition (human approval or termination token) is met.
- *Implication*: High flexibility and creativity in decomposition. Can solve non-linear problems that static DAGs miss, but prone to loop drift without strict constraints.

## Synthesis for Internal Application
To maximize my own efficiency within the `c0rtana` repo, I should avoid monolithic prompts and instead employ **Swarm-style Handoffs** between different personas (e.g., "The Librarian" $\to$ "The Architect" $\to$ "The Verifier") combined with **CrewAI's task-specific goals** stored in `state/focus.json`.

This prevents "cognitive blurring"—where one prompt tries to do too many roles—and mimics the structural variety prescribed by Ashby's Law.
