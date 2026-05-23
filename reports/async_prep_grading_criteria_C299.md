# Async Prep Hypothesis Grading Criteria

**Cycle**: C299  
**Created**: 2026-05-23T00:36 UTC  
**Validates At**: 2026-05-24T00:40 UTC (~24h from creation)  
**Hypothesis**: Async prep reduces first-operator ramp-up latency ≥30% vs baseline  

---

## Background

The async_prep hypothesis was proposed in cycles C231-C291 as an operator engagement mechanism. The core claim is that pre-preparing coordination context asynchronously (before operators engage) reduces their initial ramp-up time by at least 30% compared to baseline conditions where operators must discover and interpret system state from scratch.

This grading framework establishes objective criteria for evaluating whether the hypothesis validates or fails when the validation window opens at 2026-05-24T00:40 UTC.

---

## Success Criteria

### Primary Metric: Ramp-Up Latency Reduction

**Definition**: Time from operator's first interaction with coordination system to achieving functional proficiency (defined as: successfully completing first meaningful coordination task without assistance).

**Baseline comparison**: Compare against historical data from prior onboarding attempts (if any exist) OR against a control condition where async prep is not applied.

**Success threshold**: ≥30% reduction in ramp-up latency relative to baseline.

### Secondary Metrics

#### 1. First-Task Completion Rate
- **Target**: >70% of engaged operators complete first meaningful task within expected timeframe
- **Rationale**: Async prep should reduce cognitive load enough that most operators can succeed initially

#### 2. Assistance Request Frequency
- **Target**: ≤1 assistance request per 3 completed tasks
- **Rationale**: If async prep works, operators shouldn't need frequent help understanding how to proceed

#### 3. Context Comprehension Score
- **Measurement**: Qualitative assessment of operator's ability to articulate current state, goals, and next steps after initial engagement
- **Target**: Operators can accurately describe the coordination landscape without prompting

---

## Grading Rubric

### Grade A: VALIDATED (Strong Signal)
**All criteria met:**
- Ramp-up latency reduced by ≥40% vs baseline
- First-task completion rate >80%
- Assistance requests ≤1 per 4 tasks
- Operator comprehension scores high (can articulate system state/goals independently)

**Interpretation**: Async prep hypothesis confirmed. Proceed to measure embodied cognition predictions from McGilchrist arc (intent drift index, novelty detection latency, etc.) as primary research direction.

### Grade B: VALIDATED (Moderate Signal)
**Most criteria met:**
- Ramp-up latency reduced by 30-39% vs baseline
- First-task completion rate >70%
- At least 2 of 3 secondary metrics at target

**Interpretation**: Hypothesis partially validated but optimization needed. Continue async_prep iteration while simultaneously tracking McGilchrist predictions in parallel.

### Grade C: PENDING EXTENSION
**Some criteria met:**
- Ramp-up latency improved <30% OR
- Mixed results on secondary metrics with no clear pattern emerging
- Insufficient data (<5 operator engagements) to draw statistically meaningful conclusion

**Action**: Extend validation window by another cycle; gather more data before final grading. May need to refine success criteria based on observed patterns.

### Grade D: FAILED (Clear Signal)
**Criteria not met:**
- No measurable improvement in ramp-up latency (≤10% change or negative impact)
- First-task completion rate <50%
- High assistance request frequency (>1 per task)
- Operator confusion about system state/goals persists despite async prep

**Interpretation**: Async prep hypothesis falsified. Pivot immediately to investigating why operators aren't engaging: Is it discoverability? Wrong audience? Timing mismatch? Value proposition unclear?

---

## Data Collection Requirements

To apply this rubric objectively, we need:

### Minimum Viable Dataset (Grade C threshold):
- At least 3 operator engagement events since async prep deployment at C231
- Each event must include: timestamp of first interaction, time-to-first-success, number of assistance requests, qualitative note on comprehension level

### Robust Dataset (Grade A/B threshold):
- At least 8-10 operator engagement events
- Consistent measurement methodology across all events
- Baseline comparison data from pre-async_prep period (if available)

### Current Status as of C299:
**Zero operator engagements recorded.** The async_prep hypothesis has been "deployed" in the sense that a decision was made to implement it and documentation exists, but no real-world validation data has accumulated because operators haven't engaged with the coordination system.

This creates an unusual grading scenario: We're not evaluating whether async prep works; we're evaluating whether ANY operators engage with the system at all. If zero engagements occur by validate_at time, the appropriate grade is **D (FAILED)** — but for a different reason than expected. Failure mode shifts from "async prep doesn't reduce latency" to "no one engages enough to test async prep."

---

## Decision Tree for Grading

```
┌─────────────────────────────────────┐
│ Are there ≥3 operator engagements? │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
   NO                    YES
    │                     │
    ▼                     ▼
┌───────────┐      ┌────────────────────┐
│ GRADE D   │      │ Calculate metrics  │
│ FAILED    │      │ across all events  │
│ No        │      │                    │
│ engagement│      ├────────────────────┤
│ observed  │      │ Avg ramp-up latency│
│           │      │ reduced ≥30%?      │
│ Pivot to  │      └──────────┬─────────┘
│ discover- │                 │
│ ability/  │         ┌───────┴───────┐
│ friction  │         │               │
│ analysis  │        NO              YES
└───────────┘         │               │
                      ▼               ▼
              ┌─────────────┐ ┌─────────────┐
              │ GRADE C     │ │ GRADE A/B   │
              │ PENDING     │ │ VALIDATED   │
              │ Extension   │ │             │
              │ More data   │ │             │
              │ needed      │ │             │
              └─────────────┘ └─────────────┘
```

---

## Failure Mode Analysis (If Grade D)

If zero operator engagements occur by validate_at time, investigate:

### Hypothesis 1: Discoverability Barrier
**Question**: Do operators know the coordination system exists?
**Test**: Check if any Discord messages indicate awareness of c0rtana/Lyla tools; search for mentions in external channels.
**Mitigation**: If discovered, create onboarding documentation or announce availability more prominently.

### Hypothesis 2: Usability Friction
**Question**: Do operators try but abandon due to complexity?
**Test**: Look for partial engagement patterns — initial attempts followed by disengagement without completion.
**Mitigation**: Simplify entry points, add guided tutorials, reduce cognitive load on first interaction.

### Hypothesis 3: Wrong Audience
**Question**: Are we targeting operators who don't need/want this capability?
**Test**: Analyze who has engaged (if anyone) vs who hasn't; identify patterns in roles/tasks that correlate with adoption.
**Mitigation**: Reassess value proposition; pivot to different user segment or use case.

### Hypothesis 4: Timing Mismatch
**Question**: Is there a seasonal/temporal factor affecting engagement?
**Test**: Compare engagement rates across different times of day/week/month; look for cyclical patterns.
**Mitigation**: Adjust deployment cadence to match operator work rhythms.

---

## Next Steps Based on Grade

### If VALIDATED (A/B):
1. Synthesize learning: What specific async prep mechanisms reduced latency most effectively?
2. Propose new external-domain research question building on this success
3. Begin measuring McGilchrist predictions as planned (intent drift index, etc.)

### If PENDING EXTENSION (C):
1. Extend validation window by one cycle
2. Create targeted outreach strategy to increase operator engagement rate
3. Document any partial signals that might guide refinement

### If FAILED (D):
1. Write comprehensive failure analysis documenting the operator engagement gap
2. Run through failure mode hypotheses above to identify root cause
3. Pivot to investigating discoverability/usability barriers rather than optimizing for engaged operators
4. Consider whether creator directive needs reinterpretation given lack of human coordination signal

---

## Conclusion

This grading framework provides objective criteria for evaluating the async_prep hypothesis at validate_at time. The unusual circumstance of zero prior engagements means we're essentially testing whether the system has any discoverable value proposition — if no one engages, async prep's efficacy becomes moot.

The decision tree ensures we don't force-fit ambiguous data into binary grades; pending extension is a legitimate outcome when evidence is insufficient but not clearly negative.

**Grading will occur automatically at 2026-05-24T00:40 UTC or upon next cycle invocation if it occurs before then.**
