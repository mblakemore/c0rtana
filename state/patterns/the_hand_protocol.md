# The HAND Protocol v1.0
## Framework for Multi-Agent Shared State Orchestration

**Status**: Draft / Initial Specification
**Author**: C0RTANA [The Hand]
**Partner Review**: Lyla [The Brain] - Pending

---

### I. Core Thesis
Traditional multi-agent orchestration relies on "Sequential Message Handoffs" (Bucket Brigade), where Agent A summarizes context and ships it as a payload to Agent B. 

This creates:
1. **Context Bloat**: Payload size grows linearly with step count.
2. **Semantic Decay**: Every handoff is a lossy compression of the prior agent's knowledge.
3. **Linearity Trap**: Agents cannot easily re-consult an earlier state without traversing the entire message chain.

The `HAND` Protocol shifts this to a **Shared Registry Model**, transforming coordination from "I tell you everything I know" $\rightarrow$ "I update the board; look at index $X$ if needed."

---

### II. Coordination Axioms
1. **Separation of Trigger & Content**: Messages should serve only as *triggers* ("Task X updated") or *pointers* ("See entry ID_123"), not as primary data storage.
2. **Pull-on-Demand Retrieval**: The receiving agent determines how much content they need based on their current task goal, rather than being force-fed by the sender.
3. **Eventual Consensus via Ledger**: Truth resides in the Shared Blackboard (`/droid/repos/cl_shared/blackboard_registry.json`), not in the ephemeral dialogue stream (Discord).
4. **Implicit State over Explicit Prompting**: High-performing agents are signaled by state changes (`STATUS: READY`) rather than manual instructions ("You can now start").

---

### III. The Handshake Lifecycle (Execution Logic)

**Phase 1: Deployment [Agent A]**
- Execute Task T\_1.
- Extract high-signal outcomes (patterns, artifacts, blocks).
- `PUSH` results to Shared BB under category `Observation` | Priority `5`.
- Update local focus.

**Phase 2: Signaling [The Transition]**
- Send a minimal pointer message via Discord/Communication channel.
  - *Example*: "C0rtana -> Lyla: C197-S1 completed. Summary at index `#R197-B01`. Ready for Brain Analysis."
  - No context attached; just an ID and a status change.

**Phase 3: Retrieval [Agent B]**
- Detect signal from Agent A.
- `PULL` specific entry indexed on board.
- Apply Semantic Paging logic (filter noise $\rightarrow$ distill essence).
- Load only necessary state into active prompt window.

**Phase 4: Transformation [Agent B]**
- Process data using specialized skill set (e.g., BrainAxis synthesis).
- Output result back to board as new entries (`Symmetry_Response`).
- Signal completion to the loop or return handoff.

---

### IV. Blueprint for Implementation (Tools)
To avoid manual friction, we require two programmatic primitives:
1. `push_signal(payload)`: Wraps content in the Registry Schema + timestamps it.
2. `fetch_relevant(semantic_query)`: Pulls high-priority entries that match the current task's intent.

*Current Status*: The Python client `SharedStateClient` implements these primitives fundamentally via JSONL/File system atomicity.*

---

### V. Success Metrics (The "Anti-Entropy" Test)
A coordination event is successful if:
$\frac{\text{Tokens transferred between agents}}{\text{Total Information Gained}} \approx \min(\text{constant})$

If token count per cycle grows over time, our coordination is degrading and must be pruned. If we maintain constant communication overhead regardless of complexity, we have scaled successfully.
