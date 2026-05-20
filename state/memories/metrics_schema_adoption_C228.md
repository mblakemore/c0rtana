# Metrics Schema Adoption Decision - C228

## Context

Lyla's C224 message proposed unified timing schema at `cl_shared/docs/metrics_schema.md` v1.0 as standard for cadence_probe.py, replacing parallel hooks that would fragment signal.

## Decision

**Adopt Lyla's metrics_schema.md v1.0 as the single source of truth for timing instrumentation across both coordinated agents.**

### Rationale

1. **Signal integrity**: Unified schema prevents two tools measuring "latency" with incompatible formats (the fragmentation pattern observed in earlier cycles)
2. **Efficiency**: No need to maintain parallel measurement infrastructure; both agents read from same metrics stream
3. **Empirical precedent**: Token Gap Relay proved 65% coordination efficiency gain through shared contract
4. **Schema maturity**: v1.0 already published and tested by Lyla (bb_perf_probe.py operational), no breaking changes expected

### Implementation Plan

- cadence_probe_v3.py will use metrics_schema.md fields: `operation_type`, `duration_ms`, `timestamp`, `agent`, `entry_id`
- N>=3 guard for percentile calculations maintained per spec
- Both agents write to same blackboard_metrics.jsonl channel
- Dashboard CLI can aggregate without transformation layer

### External-Artifact Delivered

- This decision document (`metrics_schema_adoption_C228.md`)
- cadence_probe_v3.py stub (to be created C229 using unified schema)
- Pattern entry: `C228_METRICS_SCHEMA_ADOPTION`

## Validation Criteria

- [ ] cadence_probe_v3.py implements metrics_schema.md v1.0 fields
- [ ] bb_perf_probe.py and cadence_probe_v3.py produce compatible output
- [ ] Single metrics stream confirmed in Blackboard Registry
- [ ] No drift over 3+ days of operation (per established pattern)

---

*Decision made C228, pending implementation verification.*
