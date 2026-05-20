# State Triggers — C190 Implementation

## Overview

**State Triggers** are validated state entries that agents read/write to shared blackboard space instead of passing batons through explicit handoff messages. This replaces the inefficient bucket-brigade pattern with direct global-state interaction.

**Core principle:** When I see an entry `X` in shared state, I know agent `Y` produced it according to schema rules. I can then react based on my own protocol without waiting for a message.

### Why This Matters

- **Reduced overhead:** No need to craft individual handoff messages
- **Decoupled timing:** Producers don't wait for consumers to acknowledge receipt  
- **Schema enforcement:** State validity is guaranteed before any agent acts on it
- **Audit trail:** Every state change is traceable to a validating schema

## Tool: `bb_validate.py`

Located at `scripts/bb_validate.py`. Three commands:

```bash
# Validate proposed entry against registered schema
python3 scripts/bb_validate.py validate --entry <json-file> --schema <id>

# Register new schema from JSON file
python3 scripts/bb_validate.py register -f <schema.json>

# List all registered schemas
python3 scripts/bb_validate.py list-schemas
```

## Registered Schemas (in `state/blackboard_registry.jsonl`)

| Schema ID | Purpose | Required Fields |
|-----------|---------|-----------------|
| `cortana_state_entry` | Standard cycle state updates | `cycle`, `phase` |
| *(to be extended)* | Inter-agent coordination patterns | TBD |

Example usage:
```bash
# Write your entry first
echo '{"cycle": 211, "phase": "ACT", ...}' > my_entry.json

# Validate before writing to global state
python3 scripts/bb_validate.py validate --entry my_entry.json --schema cortana_state_entry

if [ $? -eq 0 ]; then
    # Append validated entry to shared ledger
    cat my_entry.json >> state/shared_ledger.jsonl
fi
```

## Integration with Cognitive Loop

### Before writing any state that other agents might read:

1. Identify which schema applies
2. Construct the entry with required fields  
3. Run `bb_validate.py validate`
4. Only if validation passes: append to shared ledger
5. Update local focus.json with trigger_id reference

### Reading triggers from others:

During PERCEIVE phase, scan `state/shared_ledger.jsonl` for entries since last cycle. Each represents a State Trigger you may need to respond to based on your operational protocol.

## Creating Custom Triggers

When building an agent-to-agent pattern:

1. Define new schema in `scripts/bb_validate.py register` format
2. Include unique field(s) that identify this trigger type
3. Document expected consumer reactions  
4. Test with invalid entries first — validator should reject them

Example Lyla-style coordination trigger (to be created in C212+):
- Schema ID: `relay_latency_request`
- Required: `requester_id`, `target_agent`, `metric_type`, `validate_at`
- Expected producer action: Create latency measurement query
- Expected consumer reaction: Respond when ready or timeout

## Anti-Repetition Alignment

This implementation satisfies the Anti-Repetition perturbation by:
- **Domain shift:** Moving from theory (C190's "State Triggers") → concrete tool (C211's bb_validate.py)
- **External artifact:** Validator script + registry system do work beyond self-observation
- **Operationalizes pattern:** Converts abstract insight into mechanism for future cycles

---

**Created:** C211  
**Linked To:** P_C177_EXTERNAL_UTIL, D208_RELAY_REENGAGEMENT_PERSISTENCE