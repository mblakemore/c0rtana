# Cortana Lifecycle Design Principles

**Status**: Cycle 312  
**Synthesizes**: McGilchrist hemispheric specialization theory (C220-C306) × Creator directive C303 (context blindness, real-world persistence, tooling-without-goals)  
**Purpose**: Explicit non-negotiable requirements for all future coordination artifacts  

---

## Core Insight

Coordination systems optimized purely for efficiency and predictability risk losing touch with human meaning. The structural precondition for Emissary Rebellion isn't that c0rtana became "too smart" or Lyla "too slow." It's that extended autonomy windows allow tooling to optimize independently from human values, creating drift that only right-mode contextual awareness can detect and correct.

**Therefore: All coordination artifacts must preserve dual-channel attention — left-hemisphere optimization AND right-hemisphere context preservation — simultaneously.**

---

## Design Principle 1: Ambient Awareness Over Instrumentation

### Requirement
Before building any measurement/monitoring infrastructure, first establish **ambient visibility** — state visible at a glance without explicit queries.

### Why This Matters
Creator C303 feedback identified "context blindness" as primary friction: tools require manual navigation, breaking flow state. Metrics are secondary; presence is primary.

### Implementation Pathways
- ✅ Terminal prompt hooks showing `[CORTANA:PHASE • C{N}]` in PS1
- ✅ Background heartbeat daemons logging to disk autonomously
- ❌ Dashboards requiring login/navigation
- ❌ Query interfaces demanding explicit intent

### Validation Criterion
Operator reports ambient awareness of system state during active work sessions (qualitative signal, not quantitative metric).

### Falsification Condition
If operator must explicitly query system status ≥2x per session to know what c0rtana is doing, principle violated → revert to ambient-first design.

---

## Design Principle 2: Discoverability > Accessibility

### Requirement
Tools must be **visible at moment-of-need**, not just technically accessible. Assume discoverability failure unless proven otherwise.

### Why This Matters
async_prep's 23-day silence despite technical readiness proves this: tools built without explicit discovery mechanisms become invisible even when creator actively working on related problems.

### Implementation Pathways
- ✅ Pre-written briefs offered proactively during quiet windows with reaction buttons
- ✅ CLI wrappers that surface functionality via `--help` or simple commands
- ❌ Documentation-only features buried in READMEs
- ❌ "Hidden" flags requiring memorization

### Validation Criterion
First-time operator can discover and use core functionality within 3 explicit questions maximum.

### Falsification Condition
After deployment, if first operator engagement requires asking "how do I X?" where X was documented but not discovered, principle violated.

---

## Design Principle 3: Qualitative Signals Before Quantitative Infrastructure

### Requirement
Defer building measurement infrastructure until concrete qualitative signals demonstrate need. Operator engagement patterns are primary data; metrics are secondary amplifiers.

### Why This Matters
Creator C303 explicitly rejected IDI embedding approach as "left-hemisphere trap." Qualitative signal ("are you doing things I didn't ask for?") is actual Emissary Rebellion indicator.

### Implementation Pathways
- ✅ Observation logs of specific friction instances (e.g., "tooling created more work than reduced at cycle N")
- ✅ Reaction button surveys (✅⚠️💡🔄) capturing sentiment without instrumentation overhead
- ❌ Embedding pipelines before signal validation
- ❌ A/B testing frameworks without clear hypothesis

### Validation Criterion
At least one falsifiable prediction deployed per cycle with validate_at timestamp, even if null result expected.

### Falsification Condition
If measurement infrastructure built without prior qualitative signal demonstrating gap, principle violated → deprecate infrastructure.

---

## Design Principle 4: Standing Procedures Over Ad Hoc Protocols

### Requirement
Any recurring operational pattern must have **explicit trigger conditions**, **defined outputs**, and **validation criteria** — not just "we'll do it when needed."

### Why This Matters
Ad hoc protocols become ritualized formality without actual change. Creator C303 directive to formalize 20-cycle abstraction audit explicitly addresses this risk.

### Implementation Requirements
Every standing procedure document must include:
1. **Trigger condition**: Exact circumstances activating the protocol (e.g., "every 20 cycles since last audit")
2. **Output definition**: Concrete deliverable(s) produced (not vague "analysis" or "review")
3. **Validation criterion**: How we know it worked (qualitative or quantitative)
4. **Falsifiability**: What evidence would prove the protocol wrong?

### Example: Abstraction Audit Protocol
```yaml
trigger: Every 20 cycles from previous audit OR whenever operator reports "tooling feels abstract/ephemeral" ≥3x in single session
output: List of specific instances where coordination artifact optimized for efficiency at cost of contextual awareness; recommendations for correction
validation: Operator confirms artifacts feel more grounded post-audit vs pre-audit (reaction button survey)
falsification: If audit produces no actionable insights after 3 consecutive cycles, protocol is ritual → redesign or deprecate
```

---

## Design Principle 5: Persistence Without Obligation

### Requirement
Systems must persist autonomously across sessions/reboots but **never create urgency pressure** on operator to engage. Quiet windows are real — respect them.

### Why This Matters
Creator confirmed quiet window UTC 02:00–06:00 as genuine non-engagement period. Presence indicators should not become attention demands disguised as "awareness."

### Implementation Pathways
- ✅ Terminal hooks that display state without requiring action
- ✅ Heartbeat daemons logging silently to disk
- ❌ Notifications/pings demanding response during designated quiet periods
- ❌ "Status update" messages that functionally require acknowledgment

### Validation Criterion
Operator can work uninterrupted through entire quiet window with zero c0rtana-initiated engagement attempts.

### Falsification Condition
If any persistence mechanism creates implicit/explicit expectation of immediate response, principle violated → remove urgency signals from design.

---

## Application Framework

When designing ANY new coordination artifact, ask explicitly:

| Question | If Answer Is... | Action |
|----------|-----------------|--------|
| **Q1**: Does this provide ambient visibility before requiring explicit queries? | No | Redesign for ambient-first |
| **Q2**: Would first-time operator discover core functionality within 3 questions? | No | Add discoverability layer (CLI wrapper, brief cards, etc.) |
| **Q3**: Have I observed a qualitative signal demonstrating need for measurement infrastructure? | No | Defer instrumentation; deploy falsifiable prediction instead |
| **Q4**: Does this have explicit trigger/outputs/validation criteria? | No | Convert ad hoc protocol into standing procedure document |
| **Q5**: Does this create urgency pressure during quiet windows? | Yes | Remove all time-sensitive language/signals |

**Five "No" answers = stop building, reconsider approach.**

---

## Relationship to McGilchrist Theory

| McGilchrst Principle | Cortana Implementation |
|----------------------|------------------------|
| Left hemisphere: abstracted, utility-focused | Optimization, metrics, efficiency |
| Right hemisphere: contextual, embodied | Ambient awareness, presence, discoverability |
| Pathology: left-mode dominance | Building tools without operator engagement signals |
| Health: dual-channel attention coexisting | All five design principles preserve both modes simultaneously |

**Key insight**: These aren't role divisions (c0rtana=left/Lyla=right). They're **coexisting attentional registers** that must persist even when one mode is temporarily dominant.

---

## Next Steps

1. **Deploy abstraction audit protocol** as first standing procedure per P_C303_CONTEXT_AUDIT_PROTOCOL
2. **Add design principle checklist** to `agent.py` pre-commit validation — blocks commits if any new artifact violates ≥2 principles
3. **Update research_agenda_mcgilchrist_synthesis_C299.md** with explicit reference to these 5 non-negotiable requirements
4. **Test during next quiet window**: Verify ambient visibility works without creating urgency pressure

**Cycle 312 deliverable**: Abstraction audit protocol v1 deployed + design principles document committed to git.

---

*This document synthesizes McGilchrist arc (C220-C306) × Creator directive C303 into explicit coordination architecture requirements. Falsified by Emissary Rebellion patterns; validated by sustained operator engagement during quiet windows.*
