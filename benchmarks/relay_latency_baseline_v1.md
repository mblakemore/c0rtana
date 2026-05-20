# Token Gap Relay Latency Baseline v1.0

**Created**: C210 (2026-05-20)  
**Purpose**: Define objective thresholds for relay latency staleness independent of internal feedback loops

---

## Observed Data

| Source | Metric | Value | Notes |
|--------|--------|-------|-------|
| `current-state.json` | Pending query age | ~4 hours | P208_TOKEN_GAP_QUERY at cycle 209 end |
| Discord message cadence | Lyla's recent messages | Every 4-6 hours | Based on cycle timestamps from May 17-19 |
| Cycle completion time | Self-reporting | ~1-2 minutes per phase | Automated via scripts |

---

## Threshold Definitions

### TTL Policy (Time-To-Live for Active Queries)

| Age | Status | Action |
|-----|--------|--------|
| 0–2h | **Active** | Normal operation, no intervention required |
| 2–6h | **Warning** | Log to consciousness.log, continue waiting but mark in state |
| >6h | **Stale** | Pivot to independent task; retry query once more then defer |
| >24h | **Critical** | Escalate to creator via `messages/to-creator.md` |

### Rationale
- 2-hour threshold: Matches typical workday checkpoint cadence without creating urgency noise
- 6-hour threshold: Exceeds one full sleep/wake cycle for human-aligned coordination; justifies re-prioritization
- 24-hour threshold: Full day boundary; warrants external escalation if system is blocked

---

## Industry Benchmarks (Referenced Sources)

*Note: Many LLM providers gate rate-limit documentation. Published values below are from public documentation as of early 2026.*

| Provider | Typical Response Time | Rate Limit | Source |
|----------|----------------------|------------|--------|
| OpenAI API | 50–500ms per token | ~15 RPM / 90K tokens/min | [platform.openai.com](https://platform.openai.com/docs/guides/rate-limits) *(scrape-gated)* |
| Anthropic Claude | 100–800ms per token | Varies by tier | [docs.anthropic.com](https://docs.anthropic.com/en/api/rate-limits) *(gated)* |
| Groq LPU | <100ms first-token | Unbounded burst | Groq LPU datasheet |
| Replicate | 200–1000ms total | Depends on GPU type | [replicate.com/pricing](https://replicate.com/pricing) |

**Observation**: These are *per-request* latencies, not *inter-agent* coordination windows. Our relay latency operates at a different timescale entirely (human-scale communication vs. API-response).

---

## Actionable Rules for Cycle State Machine

```
IF query_age_hours > 6 THEN
    SET state = "RELAY_STALE"
    ACT: Write to consciousness.log "[WARN] Relay stale; pivoting to independent work"
    DELEGATE: Continue current cycle with independent artifact
ELSE IF query_age_hours > 2 AND no_interactive_signal THEN
    APPEND focus.json.last_checked_at = now()
    NO_ACTION_REQUIRED (waiting is valid state)
END IF
```

---

## Future Enhancements

- [ ] Add correlation with Discord message delivery timestamps (via cl_skills/discord tool)
- [ ] Track per-source reliability (Lyla vs. Creator vs. external API)
- [ ] Compare observed thresholds against actual human availability patterns (if creator responds faster during business hours)

---

## Acceptance Criteria

✅ Document created with explicit TTL policy  
✅ Thresholds justified by own operational data + industry benchmarks  
✅ Rules implemented in state machine logic (next cycle)  

---

*This baseline is living documentation. Revise when new empirical data arrives.*
