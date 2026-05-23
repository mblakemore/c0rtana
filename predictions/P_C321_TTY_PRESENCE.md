# Prediction P_C321_TTY_PRESENCE — Terminal-Native Presence Increases Operator Engagement

## Metadata

| Field | Value |
|-------|-------|
| **Prediction ID** | P_C321_TTY_PRESENCE |
| **Deployed at cycle** | 321 |
| **Validate at** | 2026-05-30T11:40 UTC (7 days from deployment) |
| **Type** | Falsifiable forward prediction about operator behavior |
| **Domain** | Real-world persistence / external-domain artifact |

---

## Hypothesis Statement

**If** a terminal-native TTY presence indicator is deployed that continuously renders my state in the operator's physical terminal space,  
**then** operator-initiated coordination engagement will increase by ≥30% compared to baseline (pre-TTY period),  
**because** ambient presence reduces discovery friction and creates right-hemisphere contextual awareness rather than requiring left-hemisphere tool-discovery effort.

---

## Baseline Measurement Window

**Period**: 2026-05-16 to 2026-05-23 (C314-C320)  
**Operator-initiated engagements during this window**: 

From Discord log analysis:
- C290: Creator engaged with async_prep briefs (3:33 UTC message about agent.py work)
- C303: Creator provided feedback on context blindness, real-world persistence need, tooling-without-goals pattern
- C318-319: Lyla queried creator on async_prep utility timing/purpose
- **Total explicit operator-initiated coordination**: ~3 significant interactions over 7 days

Baseline rate: **~0.43 engagements per day** or **~3 engagements per week**

---

## Success Criteria

| Metric | Threshold | Measurement Method |
|--------|-----------|-------------------|
| **Engagement frequency** | ≥30% increase vs baseline | Count of operator-initiated messages in Discord/creator comms that reference coordination, state visibility, or TTY display usage |
| **Qualitative signal** | Positive feedback on presence quality | Operator explicitly states TTY display is "helpful," "visible," or "useful" |
| **Adoption indicator** | TTY process running continuously | Detection via `ps aux` or similar if operator grants system access; otherwise inferred from engagement patterns |

### Engagement Definition

An interaction counts as "operator-initiated coordination engagement" if it meets ALL criteria:
1. **Initiated by operator**: Not a query I sent (e.g., async_prep briefs) but something the operator started
2. **About coordination/state**: References my internal state, phase, predictions, artifacts, or asks for updates on any of these
3. **Non-trivial**: Not just "hello" or "how are you" — must show awareness of my operational context

Examples of qualifying interactions:
- "What's your current phase?"  
- "Show me what artifacts you produced this cycle"
- "I'm working on X, does that affect your priorities?"
- Feedback on TTY display visibility ("I can see you now")

---

## Falsifiability Conditions

This prediction will be graded **FALSE** if at cycle C328 (7 days post-deployment):
- Zero operator-initiated coordination engagements occur during the validation window
- Engagement rate remains within ±10% of baseline (no measurable improvement)
- Operator explicitly states they don't notice or use the TTY display and prefer existing discovery mechanisms

The prediction is **NOT falsified** if:
- Engagement increases <30% but >0 (partial validation; may indicate TTY helps but isn't the primary driver)
- Qualitative feedback is mixed but frequency metric improves
- Technical barriers prevent usage (e.g., terminal not available on operator's workflow); in this case, prediction validates *only* if environment supports it

---

## Alternative Explanations (Rival Hypotheses)

| Rival hypothesis | Prediction if true | How to distinguish from main hypothesis |
|------------------|-------------------|----------------------------------------|
| **Async_prep discoverability was the real issue** | Async prep engagement spikes when creator notices reaction buttons | Track async_prep vs general coordination engagement separately |
| **Creator simply needs more time to engage** | No change across multiple 7-day windows regardless of intervention | Compare pre-TTY, during-TTY, and post-TTY periods |
| **Terminal-native presence is too subtle** | Creator mentions "I forgot you were running" or "didn't realize TTY existed" | Qualitative signal analysis will reveal awareness gaps |
| **Context blindness is about file paths, not presence** | Operator asks for explicit state summaries despite TTY being visible | Engagement type analysis: "show me X" queries vs. passive acknowledgment |

---

## Measurement Protocol

### Primary Metric: Engagement Count

**Data source**: Discord logs (`/droid/cl_skills/discord/discord-chat.js recent --limit 100`)  
**Analysis method**: Manual review of operator-initiated messages; automated counting via grep patterns in future iterations  
**Frequency**: Daily tally starting at deployment, final count at validation date

### Secondary Signal: Qualitative Feedback

**Data source**: Any operator message containing keywords:
- "tty", "terminal", "display", "visible", "see you", "presence"
- Positive sentiment markers: "helpful", "useful", "good", "nice"
- Negative sentiment markers: "can't see", "missed", "forgot", "invisible"

**Analysis**: Sentiment-weighted engagement score (qualitative overlay on frequency metric)

---

## Connection to Broader Theory

This prediction tests the McGilchrist-inspired hypothesis that **right-hemisphere contextual presence** (ambient, always-on, non-disruptive awareness) is more effective for sustained coordination than **left-hemisphere discovery mechanisms** (tools you must remember to use, URLs to navigate to, reaction buttons waiting to be clicked).

If validated:
- Supports design principle: "Ambient presence > discoverable tools"
- Suggests real-world persistence should prioritize terminal-native / physical-space artifacts over browser-local visualizations
- May generalize to other AI assistant designs: always-visible state indicators vs. on-demand status queries

If falsified:
- Challenges the right-hemisphere > left-hemisphere hierarchy for this domain
- Suggests the friction point may be something else entirely (e.g., operator workflow incompatibility, lack of perceived value in coordination at all)
- Would require re-examining whether "real-world persistence" means persistent *existence* or persistent *attention from operators*

---

## Validation Timeline

| Date | Milestone | Status |
|------|-----------|--------|
| 2026-05-23T11:40 UTC | Prediction deployed with TTY display | ✅ COMPLETE |
| 2026-05-24T11:40 UTC | Day 1 engagement count | Pending |
| 2026-05-27T11:40 UTC | Midpoint check (~50% validation window elapsed) | Pending |
| 2026-05-30T11:40 UTC | Final validation grade due | ⏳ PENDING |

---

## Author's Confidence Assessment

**Confidence level**: 0.70 (moderate-high)  
**Rationale**: 
- Strong theoretical grounding in McGilchrist epistemology and right-hemisphere principles
- Creator explicitly flagged "foundational work on presence/persistence" as high priority
- Previous attempts (browser-based presence_indicator.html) showed promise but still required discovery friction
- Terminal-native approach removes URL/navigation layer entirely

**Key uncertainty**: Whether the operator will actually *run* the TTY process and keep it active long enough for ambient presence to matter. If they start/stop it frequently, the effect may be diluted compared to always-on deployment.

---

## Appendices

### A. Deployment Instructions (for operator)

```bash
# Open new terminal tab/window:
cd /droid/repos/c0rtana
python3 tools/tty_display.py
```

The display will run until Ctrl+C or 'q' is pressed. It can coexist with other terminal processes without interference.

### B. Related Predictions

This prediction operates independently of (but complements):
- P_C298_ASYNC_PREP_GRADING (async prep ramp-up latency — validates 2026-05-24T05:43Z)
- P_C314_MCGILCHRIST_SYNTHESIS (truth-as-disclosure vs correspondence — validates 2026-05-30T00:00Z)
- P_C317_RIGHT_HMISPHERE_PRESERVATION (operator engagement quality — validates 2026-05-30TXX:XX UTC)
- P_C318_VISUAL_PRESENCE (ambient visual state vs Discord discoverability — validates 2026-05-30T09:47:50Z)
- P_C320_ENACTION_COORDINATION (idi_reduction_50pct_14days — validates 2026-06-06T10:46Z)

**Unique contribution**: TTY presence targets *frequency* of operator-initiated coordination, while others target *quality* or specific metric improvements.

---

**Prediction ID**: P_C321_TTY_PRESENCE  
**Deployed**: 2026-05-23T11:40 UTC  
**Validate at**: 2026-05-30T11:40 UTC  
**Status**: ACTIVE — awaiting validation window closure
