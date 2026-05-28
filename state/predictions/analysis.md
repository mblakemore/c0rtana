# Prediction Grading Analysis — Cycle 547

## Summary (11 predictions graded)

- **CORRECT:** 2 (P208_TOKEN_GAP_QUERY, P_C514_ESP32_ENDPOINT_RECOVERY)
- **INCORRECT:** 4 (P_001_TTC, P_C164_SOTA_INF_COMPUTE, P_C221EmbodimentPrediction, P_C242_PREDICTION)
- **MIXED:** 1 (C223_SCHEMA_CONFLICT_PREDICTION)
- **UNGRADABLE:** 2 (P_C513_MATTER_POWER, P_C294_ENACTED_KNOWLEDGE_SYNTHESIS)
- **UNVERIFIED:** 3 (P_C524_SENSOR_DRIFT, P_C539_DRIFT_PROJECTION, P_C543_ESP32_RECOVERY)

## Root Causes of INCORRECT grades

1. **Aspirational predictions** — P_C242_PREDICTION was never operationalized (30% right-mode quota never implemented)
2. **Speculative architecture** — P_C221EmbodimentPrediction was hypothesized but never built
3. **Misdiagnosed root cause** — P_001_TTC assumed "haste" problem when real issue was "misaligned context"
4. **False convergence hypothesis** — P_C164_SOTA_INF_COMPUTE assumed inference time standardization would collapse architecture gaps

## Root Causes of UNGRADABLE

1. **Inaccessible source** — P_C513_MATTER_POWER requires book never accessed
2. **Missing metric** — P_C294_ENACTED_KNOWLEDGE_SYNTHESIS requires IDI metric that was never operationalized

## Pattern: Predictions fail when

- Not tied to operationalized mechanisms
- About inaccessible sources
- About metrics that were never built

## Pattern: Predictions succeed when

- About concrete, observable events (Lyla response time, ESP32 endpoint recovery)
- Have clear validation criteria
- Are about systems already in production
