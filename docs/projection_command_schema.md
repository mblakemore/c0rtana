# Projection Command Schema v1.0

**Purpose:** Standardized JSONL command format for external systems to control `cortana.html` visualization and state.

**Deployed by:** C341 — Projection Bridge CLI (`scripts/projection_bridge.py`)  
**Target system:** cortana.html particle visualizer + projection server (:8766)  
**Protocol:** WebSocket broadcast or file-based input

---

## Base Schema

Every command object must include:

```json
{
  "source": "<string: origin system identifier>",
  "timestamp": "<ISO8601 timestamp>",
  "cmd": "<command name>",
  "params": { ... }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | Origin of command (e.g., `alien_ship`, `projection_system_v2`, `manual_override`) |
| `timestamp` | ISO8601 | No | Auto-populated if missing; use for ordering/auditing |
| `cmd` | string | Yes | Command name from the registry below |
| `params` | object | Yes | Command-specific parameters |

---

## Command Registry

### 1. `set_phase`

Update current cycle phase displayed in visualizer.

**Params:**
- `phase` (string): One of `PERCEIVE`, `REFLECT`, `DECIDE`, `ACT`, `CONSOLIDATE`, `PERSIST`

**Example:**
```json
{"source":"alien_ship","timestamp":"2026-05-23T22:00:00Z","cmd":"set_phase","params":{"phase":"REFLECT"}}
```

**Effect:** Particle formation pattern changes to reflect phase state.

---

### 2. `adjust_density`

Control particle swarm density.

**Params:**
- `density` (float): [0.0–1.0] — 0 = empty, 1 = maximum density

**Example:**
```json
{"source":"projection_system_v2","timestamp":"2026-05-23T22:00:00Z","cmd":"adjust_density","params":{"density":0.85}}
```

**Effect:** Visual swarm expands/contracts; mapped to patterns.jsonl line count in production.

---

### 3. `change_color`

Adjust color temperature based on internal confidence state.

**Params:**
- `color` (string): Hex (#RRGGBB) or named color (`blue`, `white`, `warm_white`, `cool_blue`)
- `transition_ms` (int, optional): Smooth transition duration

**Examples:**
```json
{"source":"alien_ship","timestamp":"2026-05-23T22:00:00Z","cmd":"change_color","params":{"color":"#4A90E2"}}
{"source":"manual_override","timestamp":"2026-05-23T22:00:00Z","cmd":"change_color","params":{"color":"warm_white","transition_ms":1000}}
```

**Effect:** Color temperature shifts from cool blue (uncertain) to warm white (confident).

---

### 4. `switch_formation`

Change particle formation pattern.

**Params:**
- `formation` (string): One of `sphere`, `torus`, `spiral`, `drift`

**Example:**
```json
{"source":"projection_system_v2","timestamp":"2026-05-23T22:00:00Z","cmd":"switch_formation","params":{"formation":"torus"}}
```

**Effect:** Particles rearrange into specified geometric pattern.

---

### 5. `toggle_analytics`

Enable/disable interaction analytics tracking.

**Params:**
- `enabled` (boolean): true = track, false = stop tracking

**Example:**
```json
{"source":"alien_ship","timestamp":"2026-05-23T22:00:00Z","cmd":"toggle_analytics","params":{"enabled":true}}
```

**Effect:** Analytics client begins/stops emitting events to tracker daemon (:8767).

---

## Error Handling

Invalid commands return:
```json
{
  "status": "error",
  "command_id": "<original cmd>",
  "error": "<human-readable error message>"
}
```

Common errors:
- `unknown_cmd`: Command name not in registry
- `invalid_params`: Missing or malformed required parameters
- `rate_limit_exceeded`: Too many commands in short window (implemented at server level)

---

## Integration Points

1. **File-based input**: Use `projection_bridge.py --input <file.jsonl>` to process batch commands
2. **Real-time streaming**: Use `projection_bridge.py --stdin` for live command injection
3. **WebSocket broadcast**: Projection server (`cortana.html`) broadcasts to all connected clients including analytics dashboard

---

## Validation

Commands are validated against this schema before execution. Mismatched schemas result in logged errors without system state changes.

---

*Schema version: 1.0 | Deployed: C341 | Author: c0rtana*
