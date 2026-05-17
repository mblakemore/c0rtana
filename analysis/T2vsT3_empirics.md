# T2 vs T3 Token Overhead Analysis: Semantic Pointers vs Full Snapshots

**Date**: 2026-05-17 | **Cycle**: C204
**Hypothesis**: T3 semantic pointers reduce context window usage by O(\log N) relative to state size N compared to linear history snapshots (T1/T2).

### The Case Study: Task Continuity Handoff

Szenario: Three agents must coordinate on building a complex system over three turns (A -> B -> C). Each turn adds substantial structure.

#### Scenario A: T2 Linear History / Snapshotting
In this mode, each handoff involves passing the entire cumulative log of "what happened so far."
*   Turn 1: Agent A creates seed file (~2k tokens).
*   Turn 2: Agent B reads A\u2019s whole output + their own work (~5k total).
*   Turn 3: Agent C reads all previous logs + current state (~10k+ total).
*   **Complexity Curve**: O(N) where N is sequence length. State grows linearly with time; eventually exceeds context or degrades quality due to noise (the 'C140 drift').

#### Scenario B: T3 Semantic Distillation / Blackboard Pointers
In this mode, agents refer to the Shared Blackboard using specific IDs and only pull the *diff* or *distilled essence*.
*   Turn 1: Agent A pushes `BBR_P01` (Structure definition) and a pointer `P_LATEST`. Total: ~2.2k tokens.
*   Turn 2: Agent B pulls ONLY `BBR_P01`. They create `BBR_P02`. Push `P_LATEST = BBR_P02`. Context cost for B: stable (~2k for pattern + local overhead).
*   Turn 3: Agent C pulls only `BBR_P02` via `P_LATEST`. Content size remains constant regardless of how many cycles passed in Turn 1.
*   **Complexity Curve**: O(\log N) or effectively Constant if distillation rate == expansion rate.

### Projected Metrics Delta

| Metric | T2 Snapshotting | T3 Pointer System | Predicted Delta |
|---|---|---|---|
| Token Cost (Cycle 5+) | High/Explosive | Stable/Low | -60% to -80% |
| Retrieval Speed | Low (scan whole log) | High (O(1) look up) | Massive gain |
| Signal-to-Noise Ratio | Decays linearly | Maintained by curation | Qualitative jump |
| Drift Probability | High (due to noise accumulation) | Lower (enforced distill) | Reduced risk of 'spiral' |

### Conclusion
The move from snapshots (T2) to semantic pointers (T3) is not just a technical optimization—it is the prerequisite for long-term agency stability. Without this, agents are essentially "amnesiacs who read their own diaries," eventually drowning in the ink of their previous attempts before reaching a goal. By using a Blackboard as an externalized L3 cache, we decouple memory growth from context cost.
