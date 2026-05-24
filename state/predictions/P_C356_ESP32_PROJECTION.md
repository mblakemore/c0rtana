# Falsifiable Prediction: ESP32 Embodied Projection

**Prediction ID:** `P_C356_ESP32_PROJECTION`  
**Created:** 2026-05-24T08:52Z  
**Predictor:** Cortana C356  

---

## Hypothesis

Real-time embodied cognition projection via physical LED rings will improve operator situational awareness compared to terminal-only monitoring.

### Measurable Claims

1. **Time-to-situational-understanding**: Average time for human operator to recognize cortana's cognitive phase state will decrease by ≥30% when using LED projection vs reading current-state.json in terminal.

2. **Error reduction**: Operator misidentification of cortana's active phase will decrease from baseline (terminal-only) of ~25% to ≤15% with LED projection over a 7-day validation window (C356-C363).

3. **Attention capture rate**: In multi-task environments, LED state changes will trigger operator attention at least 2x faster than terminal cursor movement or log scrolling.

---

## Validation Methodology

### Baseline Measurement (Days 1-2)
- Operator monitors cortana via terminal only (`cat state/current-state.json`)
- Record: response time to phase transitions, error rates during simulated disruptions
- Sample size: N≥20 observations per metric

### Intervention Phase (Days 3-7)
- ESP32 daemon running continuously, polling state every 2s
- Same operator performs identical task sequences
- Compare metrics against baseline

### Scoring Criteria
- **Success:** ≥30% improvement on all three metrics
- **Partial success:** Improvement on ≥2 metrics OR ≥40% improvement on one metric
- **Falsified:** No statistically significant improvement (p<0.05)

---

## Technical Implementation

**Hardware:** ESP32-WROOM-32 at 192.168.4.38 controlling 43 WS2812B LEDs in concentric rings  
**Mapping:** 
- PERCEIVE → Amber pulse (seeking input)
- REFLECT → Cyan breathing (processing internally)  
- DECIDE → Green static (decision made)
- ACT → Blue chase (executing action)
- CONSOLIDATE → Purple sparkle (integrating learning)
- PERSIST → White flash (committing to memory)

**Daemon:** `/droid/repos/c0rtana/state/esp32_controller.py --daemon` polling every 2 seconds

---

## Validation Window

**Start:** C356 (2026-05-24T08:52Z)  
**End:** C363 (2026-05-31T08:52Z, approximately 7 days from deployment)  

**Grading deadline:** C364 — write Brier score or binary correct/incorrect judgment to `state/predictions/grades.jsonl`

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ESP32 connectivity loss | Low | Medium | Daemon logs disconnections; LED state freezes rather than flashes error |
| Operator distraction | Medium | Low | LEDs are ambient, not attention-seeking; phase transitions still visible in terminal |
| Mapping ambiguity | Medium | Medium | Document color-animation mappings in README; allow operator feedback loop |

---

## Null Hypothesis

LED projection provides no measurable improvement over terminal monitoring for situational awareness. Any perceived benefit is anecdotal or attributable to novelty effect (measurable only in first 48 hours).

---

*This prediction was generated at the end of ACT phase C356 and will be graded after the 7-day validation window closes.*
