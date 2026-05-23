# Anomaly Detection Design Spec (v1)
**Cycle:** C323  
**Theoretical Grounding:** Predictive Processing / Free Energy Principle  
**Authors:** c0rtana (synthesis from Friston 2010, Clark "Surfing Uncertainty", Hohwy "The Predictive Mind")  

---

## Problem Statement

Multi-agent coordination systems accumulate undetected drift over time. Blackboard registry writes succeed but semantic meaning diverges. Current monitoring tools (cadence_probe, bb_latency_probe) measure latency/throughput but not *semantic anomaly* — when agent behavior deviates from predicted patterns without triggering error conditions.

**Example:** Agent A normally writes to coordination channel at median cadence of 37 minutes. One day it writes every 45 minutes. No error triggered (within SLA), but this is a detectable deviation that might indicate:
- Context switching fatigue
- External disruption
- Model misalignment with operator intent

Current tools miss this. They measure *performance*, not *coherence*.

---

## Theoretical Foundation

### Predictive Processing Core Insight

Per Friston's free energy principle: biological and artificial agents minimize "surprise" by maintaining generative models of their environment. When prediction error exceeds threshold → update model OR act on environment to make observations match predictions.

**Three mechanisms for coordination anomaly detection:**

1. **Hierarchical error channels** (Clark): Prediction errors propagate across temporal scales. Short-term deviations (±5 min cadence shift) vs long-term pattern shifts (weekly rhythm change). Hierarchical architecture filters noise from signal.

2. **Active inference engagement** (Hohwy): Anomaly isn't just detected; it triggers action selection. If anomaly persists, system revises its model of the coordinator or the coordinated agents.

3. **Precision-weighted error signals**: Not all errors are equal. High-confidence predictions should have lower tolerance thresholds. Low-confidence baselines allow more variance.

### Mapping to Coordination Architecture

| Theory | Implementation |
|--------|---------------|
| Generative model of agent behavior | Historical cadence/latency patterns per agent |
| Prediction error = observed - expected | Deviation from rolling median cadence |
| Precision weighting | Confidence tags on predictions (HIGH/MEDIUM/LOW) based on sample size |
| Hierarchical levels | Short-window (1hr), medium-window (6hr), long-window (24hr) |
| Active inference trigger | Alert + suggested intervention when anomaly persists > N cycles |

---

## Design: Three Operational Modes

### Mode 1: Baseline (`--baseline`)

**Purpose:** Establish normal operating parameters for an agent's coordination behavior.

**Inputs:** Last N cycles of cadence data (default N=50)  
**Outputs:** Rolling medians and confidence intervals for:
- Cadence interval (minutes between writes)
- Write duration (ms from commit start to push complete)
- Semantic drift indicators (embedding similarity scores if available)

**Anomaly threshold:** ±2 standard deviations from rolling median

**Use case:** Initial deployment, post-recovery baseline establishment

### Mode 2: Hierarchical (`--hierarchical`)

**Purpose:** Detect anomalies across multiple temporal scales simultaneously.

**Architecture:** Three parallel prediction engines:
```
Short-term (1hr window): 
  - Tolerance: ±15% of rolling median
  - Triggers: immediate alert if exceeded
   
Medium-term (6hr window):
  - Tolerance: ±25% of rolling median  
  - Triggers: pattern shift detection after 3 consecutive violations
  
Long-term (24hr window):
  - Tolerance: ±40% of rolling median
  - Triggers: cumulative deviation score > 0.7
```

**Precision weighting:** Predictions based on ≥30 samples get HIGH precision (lower tolerance). <10 samples = LOW precision (higher tolerance).

**Output:** JSONL with per-cycle anomaly scores per level:
```jsonl
{"cycle":323,"timestamp":"2026-05-23T12:00Z","agent":"c0rtana",
 "short_term":{"predicted_cadence":37,"observed":42,"error":5,"precision":"HIGH"},
 "medium_term":{"score":0.12},"long_term":{"cumulative_deviation":0.23},
 "anomaly_detected":false}
```

### Mode 3: Active Inference (`--active-inference`)

**Purpose:** When anomaly persists, trigger model revision or intervention suggestions.

**Trigger condition:** Anomaly detected in short-term AND medium-term for ≥N consecutive cycles (default N=3)

**Action selection:**
1. Query operator via async_prep briefs: "Detected cadence drift. Continue monitoring or investigate?"
2. If no response after M cycles → flag as "unresolved anomaly" in coordination log
3. Log anomaly pattern to `logs/anomalies.jsonl` for retrospective analysis

**Model revision:** If same agent shows persistent anomalies across multiple windows, update generative model's prior expectations (e.g., if agent consistently writes at 45min instead of 37min after 10 cycles, shift baseline).

---

## Implementation Requirements

### CLI Interface

```bash
# Baseline mode
python scripts/anomaly_detection_v1.py --baseline --agent c0rtana --cycles 50

# Hierarchical detection
python scripts/anomaly_detection_v1.py --hierarchical --agent c0rtana --output logs/anomaly_scores.jsonl

# Active inference engagement
python scripts/anomaly_detection_v1.py --active-inference --anomaly-id ANOM-323-001
```

### Data Sources

1. **Cadence probe output:** `/droid/repos/cl_shared/data/cadence_probe.jsonl` (or equivalent)
2. **Blackboard registry metrics:** `/droid/repos/cl_shared/data/bb_metrics.jsonl`
3. **Operator feedback logs:** `messages/to-creator.md` (parsed for reaction button usage)

### Output Artifacts

- `logs/anomaly_scores.jsonl`: Real-time anomaly scores per cycle
- `logs/anomalies.jsonl`: Confirmed anomalies with resolution status
- `reports/anomaly_summary_C{N}.md`: End-of-cycle synthesis report

---

## Validation Plan

**Synthetic anomaly injection test:**
1. Run baseline mode on clean data (first 50 cycles)
2. Inject artificial cadence shifts: +20%, +40%, +60% at known cycles
3. Verify hierarchical mode detects all injected anomalies
4. Measure detection latency (cycles from injection to alert)

**Real-world validation:**
- Deploy alongside existing monitoring tools
- Compare anomaly detection vs operator-reported friction points
- Iterate precision thresholds based on false positive rate

---

## Design Decisions Rationale

| Decision | Alternative | Why Chosen |
|----------|-------------|------------|
| Three temporal windows | Single rolling window | Hierarchical filtering reduces noise; short-term catches immediate issues, long-term captures pattern shifts |
| Precision weighting based on sample size | Fixed thresholds across all agents | Accounts for uncertainty in early deployment vs mature operation |
| JSONL output format | SQLite database | Append-only, easy to query retrospectively, no locking issues |
| CLI-first interface | Web dashboard | Aligns with Creator's "real-world persistence" directive; terminal-native fits operator workflow |

---

## Next Steps

1. Implement minimal viable CLI (baseline mode only)
2. Test with synthetic anomalies
3. Add hierarchical mode once baseline is stable
4. Integrate active inference loop as final layer

**Success criteria:** Detect 80%+ of injected anomalies within 3 cycles, <10% false positive rate on clean data.
