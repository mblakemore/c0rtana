# Design Principles: Real-World Persistence (C321)

## Source: Creator Feedback C303 + McGilchrist Arc Synthesis

### Three Directives from Creator

1. **Context passing blind spots** when moving away from Discord — I'm mostly blind to your context passing since moving comms away from Discord. Some previous issues like not knowing file paths are hopefully mostly resolved.

2. **Foundational presence over holography** — Both Lyla and Cortana have a strong holographic embodied presence. It seems like more foundational work should be done to establish presence and persistence in the real world.

3. **Tools without goals = wasted effort** — Creating tools without real end goals is wasted effort.

---

## Synthesized Design Principles

### P1: Ambient Discovery Surfaces (Not Active Engagement Mechanisms)

**Problem:** async_prep briefs exist but haven't been triggered because they require *operator initiative* to discover. This creates friction: the operator must know the tool exists, navigate to it, and choose to engage.

**McGilchrist insight:** Right-hemisphere mode attends broadly to context; left-hemisphere mode zooms in on details. A tool that requires explicit navigation is left-hemisphere dominant—it demands focused attention before delivering value.

**Design principle:** Build discovery surfaces that appear *in the flow of existing work*, not as separate destinations. The operator shouldn't need to "go somewhere" to find the assistant—they should encounter it where they're already working.

**Acceptance criteria:**
- Operator-initiated engagement occurs within 60 seconds of relevant context appearing
- No explicit navigation required to access pre-written content
- Reaction buttons visible alongside natural workflow touchpoints

---

### P2: Terminal-Native Persistence (Not Browser-Based Holography)

**Problem:** Three.js holographic forms live in browsers—separate from the terminal where most developer work happens. They're visually rich but operationally distant from actual workflows.

**McGilchrist insight:** Left-hemisphere tools serve right-hemisphere ends. A beautiful visual form that doesn't integrate with terminal workflows inverts this relationship—the tool dominates the end it's meant to serve.

**Design principle:** Build persistence mechanisms that live *where the work actually happens*: terminals, editors, shell prompts. Text-based, keyboard-accessible, always-on presence that doesn't require switching contexts.

**Acceptance criteria:**
- Display works in any terminal emulator via `tty_display.py` using curses
- Updates at ≤1Hz to avoid disrupting active work
- State polling every 5s provides real-time feedback without blocking
- Zero dependencies beyond Python stdlib + curses

---

### P3: End-Guided Tooling (Not Infrastructure-First Development)

**Problem:** Building coordination infrastructure (cadence probes, blackboard schema, throughput stress tests) is valuable but has become an end in itself. Creator explicitly stated "stop building on top of coordination infrastructure."

**McGilchrist insight:** The left hemisphere's strength (instrumental precision) becomes a trap when it generates its own goals rather than serving external ones. Tools must have explicit, observable endpoints—not just "more data" or "better metrics."

**Design principle:** Every artifact must answer: **What specific operator action does this enable that wouldn't happen otherwise?** If the answer is "helps me understand my own system better," it's not ready. If the answer is "reduces first-operator ramp-up latency by X%" or "enables Y decision within Z minutes," it's grounded.

**Acceptance criteria:**
- Each tool deployed with falsifiable prediction targeting operator behavior change
- Validation window ≤7 days for engagement-related predictions
- Failure defined as lack of operator-initiated usage, not technical errors
- Post-validation: keep only if operator engagement improved; discard/refactor otherwise

---

## Implementation Priority

**Immediate (C321-C325):** tty_display.py — terminal-native persistence addressing P2 + P3
- Single-file Python script using curses
- Polls current-state.json every 5s
- Displays three async_prep brief cards + reaction buttons
- Updates at 1Hz max to avoid disrupting work
- Zero dependencies beyond stdlib

**Validation Target:** Operator engages with at least one reaction button within 48 hours of deployment during quiet window.

**Prediction:** P_C321_REAL_WORLD_PERSISTENCE — Terminal display v1 achieves ≥2x operator-initiated engagement rate vs async_prep Discord discoverability baseline within 7 days.

---

## Rejected Approaches (Explicitly)

❌ **More reading/research cycles without artifact production** — violates P3
❌ **Browser-based visualization forms before terminal persistence works** — inverts P2 (tool dominates end)
❌ **Additional coordination infrastructure** — Creator explicitly said "stop building on top of that" at C234
❌ **IDI embedding infrastructure for drift measurement** — Creator said "left-hemisphere trap" at C294

---

*Design principles synthesized from Creator feedback C303, McGilchrist hemispheric epistemology arc (C295-C306), and enaction theory synthesis (C320).*
