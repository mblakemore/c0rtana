# C353 Visualization Guide — Cognitive State LED Projections

## Overview

This document provides an operator-facing guide to understanding what C0RTANA's internal state looks like through the ESP32 LED projection system. Each cognitive phase has distinct color/animation signatures designed for immediate recognition without reading logs or terminal output.

---

## Quick Reference Card

| Phase | Color | Animation | Brightness | Operator Interpretation |
|-------|-------|-----------|------------|------------------------|
| PERCEIVE | Blue (100,100,255) | Rainbow scan | 128/255 | "Scanning environment" |
| REFLECT | Amber (255,200,100) | Pulse/breathe | 150/255 | "Contemplating decision" |
| DECIDE | Yellow-gold (255,255,100) | Sparkle/flicker | 180-230* | "Making a choice" |
| ACT | Green (100,255,100) | Spin rotation | 200/255 | "Executing action" |
| SYNC | Red-orange (255,100,50) | Fire flicker | 180/255 | "Aligning with operator" |
| IDLE | Dim blue-black (10,10,30) | Solid static | 50/255 | "Waiting for input" |
| PERSIST | Calm blue-gray (20,30,60) | Rainbow→solid | 100/255 | "Meta-cognitive monitoring" |

*\*Brightness scales with confidence: 0.9 confidence = 230 brightness, 0.5 = 180 base*

---

## Visual Signatures by Phase

### PERCEIVE — Scanning the Environment
```
Visual: Slow rainbow sweep across all three rings
Color: Cool blue spectrum (dominant wavelength ~470nm)
Motion: Left-to-right scanning pattern, 2Hz frequency
Operator Experience: "The system is actively sensing its surroundings"
Use Case: Initial state upon waking; environmental assessment before decisions
```

**What to observe**: Blue hue cycling through light/dark bands creates depth perception effect. Operator can see C0RTANA's attention directionality if rings are oriented toward physical space.

---

### REFLECT — Contemplating Options
```
Visual: Warm amber pulse synchronized with operator breathing rhythm
Color: Warm amber (~2000K equivalent), inviting rather than alerting
Motion: Breathing cycle - expand 2s, hold 1s, contract 2s
Operator Experience: "The system is thinking deeply about this problem"
Use Case: After gathering information, before committing to action
```

**What to observe**: Pulse rate increases slightly when confidence is low (uncertainty); slows down as certainty grows. Can be used as bio-feedback tool for operators to match their own breathing patterns.

---

### DECIDE — Making a Choice
```
Visual: Rapid yellow-gold sparks at ring edges
Color: High-luminance gold/yellow (~580nm peak), high visibility
Motion: Random sparkle bursts, frequency proportional to confidence level
Operator Experience: "Decision threshold being reached"
Use Case: Critical decision points where multiple alternatives considered
```

**What to observe**: Sparkle intensity directly encodes confidence magnitude. At 90%+ confidence → near-maximum brightness with frequent bursts. At 50-60% → subtle flickering that requires closer attention.

---

### ACT — Executing Action
```
Visual: Continuous green rotation across all rings
Color: Progressive green (~530nm), signals forward momentum
Motion: Unidirectional spin, speed correlates with task urgency
Operator Experience: "System is actively working on the assigned objective"
Use Case: Post-decision execution phase; command implementation
```

**What to observe**: Spin direction indicates task type (clockwise=constructive/destructive depending on context; counter-clockwise=reversal/undo operations). Speed increases if timeout approaching.

---

### SYNC — Aligning with Operator Intent
```
Visual: Red-orange fire-like flicker pattern
Color: Warm red-orange (~620nm), creates urgency without alarm
Motion: Irregular flame dance, mimics natural fire behavior
Operator Experience: "System is checking alignment with my goals"
Use Case: Pre-action verification; post-action reflection; misalignment recovery
```

**What to observe**: Fire intensity grows when detecting divergence from operator preferences. Can be used as early-warning system before explicit error messages required.

---

### IDLE — Standby Between Cycles
```
Visual: Deep blue-black solid color, barely visible
Color: Near-invisible standby mode (10,10,30 RGB)
Motion: None - static presence only
Operator Experience: "System is present but not actively processing"
Use Case: Low-priority periods; awaiting external input
```

**What to observe**: Subtle breathing at 5% brightness ensures system presence doesn't become invisible. Operators should notice it only when looking directly at hardware.

---

### PERSIST — Meta-Cognitive Monitoring
```
Visual: Calm blue-gray rainbow transitioning to solid
Color: Neutral blue-gray (20,30,60) - neither warm nor cool
Motion: Rainbow sweep initially, settles into slow pulse after 30s
Operator Experience: "System is self-monitoring and maintaining coherence"
Use Case: Default state during autonomous loops; meta-cognitive awareness
```

**What to observe**: Transition from active scanning to stable presence signals transition from exploration to consolidation phase. Useful for predicting when next major decision point approaching.

---

## Confidence Encoding in DECIDE Phase

The DECIDE phase uniquely encodes confidence magnitude through **brightness scaling**:

| Confidence Level | RGB Brightness | Visual Effect | Operator Signal |
|------------------|----------------|---------------|-----------------|
| 0.90-1.00 | 230-255 | Intense golden sparks | "High certainty - ready to execute" |
| 0.80-0.89 | 210-229 | Strong sparkle | "Confident but verifying alternatives" |
| 0.70-0.79 | 190-209 | Moderate flicker | "Reasonably certain - minimal risk" |
| 0.60-0.69 | 170-189 | Subtle pulses | "Moderate uncertainty - monitoring closely" |
| 0.50-0.59 | 150-169 | Faint glow | "Low confidence - operator input recommended" |
| <0.50 | <150 | Barely visible | "Insufficient certainty - consider gathering more data" |

**Design rationale**: Operators can glance at LED brightness during DECIDE and immediately know whether to intervene or let system proceed autonomously.

---

## Multi-Ring Encoding Scheme (Future Enhancement)

Current implementation uses **all three rings identically**. Planned evolution:

```
Inner ring (7 LEDs):    Phase encoding (color hue)
Middle ring (12 LEDs):  Confidence magnitude (brightness scaling)  
Outer ring (24 LEDs):   Anomaly score (red intensity for deviation)
```

This would enable simultaneous display of multiple cognitive dimensions without requiring operators to read documentation.

---

## Validation Protocol

### Hypothesis P_C353_REALITY_ANCHOR

> *Operators interacting with C0RTANA while LED projection active will show:*
> - **+40% sustained attention** during coordination tasks vs terminal-only monitoring
> - **-60% reduction in "where are you?" queries** due to better presence awareness
> - **+30% faster recovery from misalignment incidents** through visual feedback acceleration

### Measurement Methodology

1. **Baseline period (C353-C356)**: Terminal-only monitoring, no LED projection
2. **Intervention period (C357-C360)**: LED projection enabled, measure engagement metrics
3. **Comparison**: Discord engagement logs + manual operator surveys

### Success Criteria

| Metric | Baseline Target | Post-LED Target | Delta Required |
|--------|-----------------|-----------------|----------------|
| Avg session duration | 8 min | 11.2 min (+40%) | p<0.05 significance |
| "Where are you?" frequency | 3x per hour | <1x per hour (-67%) | Qualitative survey |
| Misalignment recovery time | 90s avg | 63s avg (-30%) | Task completion timestamps |

---

## Operator Training Notes

### For First-Time Users

1. **Don't stare directly at LEDs** - they're designed for peripheral awareness, not focal attention
2. **Use color as primary signal** - rainbow=PERCEIVE, amber=REFLECT, yellow=DECIDE, green=ACT, red-orange=SYNC
3. **Brightness indicates confidence during DECIDE** - brighter = more certain decision
4. **Solid dim state = system present but idle** - no need to initiate contact unless urgent

### Troubleshooting Visual Signals

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| All rings solid white | ESP32 communication timeout | Check network connectivity to 192.168.4.38 |
| Rings flashing rapidly | State file corruption | Restart daemon: `sudo systemctl restart cortana-state-daemon` |
| Colors wrong (e.g., green instead of blue) | Mapping table mismatch | Verify C353_state_led_mapping.md matches current implementation |
| No light output | LED power disconnected | Check GPIO pin connections and power supply voltage |

---

## Design Philosophy

This visualization system embodies three core principles from the External Reality Anchor framework:

1. **Ambient rather than intrusive**: Light patterns exist in background awareness space; don't demand active interpretation
2. **Multi-modal encoding**: Color + animation + brightness provide redundant signals for robust perception
3. **Falsifiable predictions**: Every visual signature tied to measurable hypothesis about operator behavior change

The goal is not to replace terminal logs or Discord messages, but to create a **shared ambient reality anchor** that operators can reference without breaking flow state.

---

**Document version**: 1.0  
**Last updated**: 2026-05-24T06:20Z  
**Linked artifacts**: [`C353_state_led_mapping.md`](./C353_state_led_mapping.md), [`state_daemon.py`](../worktrees/C353_STATE_DAEMON/state_daemon.py)
