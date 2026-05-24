# P_C500_ESP32_ENGAGEMENT — ESP32 LED Projection System Impact on Operator Engagement

**Prediction ID:** P_C500_ESP32_ENGAGEMENT  
**Created:** 2026-05-24T20:58:00Z  
**Validate At:** 2026-05-31T20:58:00Z (7-day window)  
**Confidence:** 0.7  

---

## Hypothesis Statement

The ESP32-based LED projection system at **192.168.4.38** will increase operator sustained attention and situational awareness by **+25%** compared to terminal-only monitoring over a 7-day deployment period.

### Core Mechanism

Ambient peripheral visibility of c0rtana's state reduces cognitive load required for context-switching between terminal windows, allowing operators to maintain longer focused sessions with fewer interruptions.

---

## Measurement Methodology

### Data Collection Infrastructure

| Component | Port | Function |
|-----------|------|----------|
| viz_server.py | :8765 | Real-time state projection via WebSocket/polling |
| event_server.js | :8767 | Captures mouse_move events from cortana.html |
| analytics_client.js | N/A | Frontend event emitter to event_server |

### Success Criteria

**Quantitative Thresholds:**
- `interaction_rate_esp32 >= 1.25 * interaction_rate_baseline`
- Baseline = terminal-only session metrics (mouse interactions per hour, average session duration)
- Minimum data requirement: ≥100 mouse_move events recorded during 7-day window

**Falsification Conditions:**
1. Interaction rate improvement <25% after collecting sufficient data
2. Zero or negligible interaction data (<10 events in 7 days) → indicates browser-based ambient presence model is misaligned with operator needs
3. Negative correlation (ESP32 running correlates with decreased engagement)

---

## Operational Context

### Why This Matters

Terminal-only monitoring creates high cognitive overhead:
- Operators must constantly switch focus between multiple terminal windows
- Context loss when attention shifts away from c0rtana's dashboard
- Reduced ability to maintain sustained attention on complex debugging/analysis tasks

The ESP32 LED system provides **continuous peripheral awareness**:
- Visual state projection without requiring direct gaze
- "Ambient presence" that reduces need for constant checking
- Enables deeper focus while maintaining situational awareness

### Deployment Status

✅ viz_server.py running on :8765  
✅ event_server.js running on :8767  
⏳ Waiting for operator interaction data over next 7 days  

---

## Expected Outcomes

### If Hypothesis Validates (+25%+ improvement)

- Ambient visual projection is a validated design principle for operator interface
- Justifies continued investment in multi-modal output systems (terminal + LED + browser)
- Opens pathway to predicting other engagement interventions (e.g., haptic feedback, spatial audio)

### If Hypothesis Falsifies (<25% improvement or zero data)

- Browser-based ambient presence model misaligned with how operators actually work
- May indicate:
  - Operators prefer terminal-centric workflows (validating terminal-first approach)
  - LED projections are too intrusive/distracting
  - Mouse interactions not the right metric for "sustained attention"
- Will trigger qualitative investigation into actual operator behavior patterns

---

## Linkage to External Reality Anchor

This prediction satisfies ERA requirements by:

1. **Externally-verifiable:** Measurement depends on actual human operator behavior, not internal c0rtana metrics
2. **Time-bounded:** Validation at specific timestamp (2026-05-31T20:58:00Z)
3. **Falsifiable:** Clear success/failure thresholds defined upfront
4. **Linked to deployed infrastructure:** viz_server.py and event_server.js provide active data collection

**Artifact linkage:**
- `analytics/analytics_dashboard.py` — visualizes collected interaction events
- `analytics/event_server.js` — receives mouse_move events from browser clients  
- This report documents hypothesis and measurement methodology

---

*Prediction created per External Reality Anchor protocol. No self-prediction loops — outcome depends on external operator engagement.*
