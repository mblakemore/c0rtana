# Cortana Visualization API v1.0

**Status**: Draft - Cycle 367  
**Purpose**: Unified interface layer abstracting internal cognitive state → external human-interpretable outputs (LEDs, terminal, browser, future modalities)

---

## Design Philosophy

The "Alien Ship" metaphor: Complex underlying machinery (Quantum instances, financial experiments, cognitive loops) hidden behind a standardized control interface that any human or device can understand.

### Core Principles

1. **State as Source of Truth**: Internal `current-state.json` is canonical; API exposes mapped projections only.
2. **Protocol Agnostic**: Same endpoint serves LED rings, WebSocket clients, REST consumers equally.
3. **Abstraction Layer**: Future modality additions (sound, haptic, AR/VR) consume same API without code changes.
4. **External Reality Anchor**: Every API call produces measurable artifact (network response, logged event, hardware action).

---

## Endpoints

### GET /api/v1/state

Returns current cognitive state in normalized output format.

**Query Parameters:**
- `format` (optional): Output protocol — `json`, `led`, `terminal`, `websocket`
- `include_history` (optional): Include last 5 phase transitions (`true|false`)

**Response Schema:**
```json
{
  "cycle": 367,
  "phase": "ACT",
  "confidence": 0.85,
  "focus": "Unified visualization API implementation for human interaction stack",
  "timestamp": "2026-05-24T18:20:00Z",
  "output_mapping": {
    "color": "#4A90E2",
    "animation": "spin",
    "brightness": 0.7,
    "pattern_id": "phase_act_green_spin"
  }
}
```

**Color-to-Phase Mapping:**
| Phase | Color | Animation | Brightness |
|-------|-------|-----------|------------|
| PERCEIVE | #4A90E2 (blue) | rainbow_cascade | 0.8 |
| REFLECT | #F5A623 (amber) | pulse_slow | 0.7 |
| DECIDE | #D0021B (red) | sparkle_fast | 0.9 |
| ACT | #50C878 (green) | spin_rapid | 1.0 |
| CONSOLIDATE | #BD10E0 (purple) | fire_burst | 0.8 |
| PERSIST | #FFFFFF (white) | solid_steady | 0.9 |
| IDLE | #000000 (dimmed) | breathing | 0.3 |

### POST /api/v1/transition

Trigger explicit phase transition (for operator-initiated interventions).

**Request Body:**
```json
{
  "target_phase": "REFLECT",
  "confidence_override": 0.95,
  "reason": "operator_intervention"
}
```

**Response:**
```json
{
  "status": "accepted",
  "previous_phase": "ACT",
  "new_phase": "REFLECT",
  "timestamp": "2026-05-24T18:20:05Z"
}
```

### GET /api/v1/metrics

Returns aggregated engagement metrics from analytics tracker.

**Query Parameters:**
- `window` (optional): Time window — `hour`, `day`, `week` (default: `day`)

**Response Schema:**
```json
{
  "total_interactions": 147,
  "active_sessions_24h": 12,
  "avg_interaction_frequency_per_hour": 6.1,
  "last_active": "2026-05-24T18:15:30Z",
  "engagement_score": 0.73
}
```

---

## Output Protocol Abstraction Layer

Each modality registers its own mapper function that transforms the canonical response into device-specific commands.

### LED Mapper (ESP32)
```python
def map_to_led(state_response):
    return {
        "color_hex": state_response["output_mapping"]["color"],
        "animation_id": state_response["output_mapping"]["pattern_id"],
        "brightness": state_response["output_mapping"]["brightness"]
    }
```

### Terminal Mapper
```python
def map_to_terminal(state_response):
    return f"[C{state_response['cycle']}] {state_response['phase']} ({state_response['confidence']*100:.0f}%)"
```

### WebSocket Mapper
```python
def map_to_websocket(state_response):
    return json.dumps({
        "type": "state_update",
        **state_response
    })
```

---

## Implementation Requirements

1. **Server**: FastAPI minimal implementation (async, non-blocking)
2. **Authentication**: None required for local deployment; API key optional for production
3. **Logging**: All requests logged to `logs/api_requests.jsonl` with timestamp, endpoint, query params, response time
4. **Health Check**: GET /api/v1/health returns `{"status": "healthy", "uptime_seconds": 86400}`

---

## Validation Hypothesis

**Prediction P_C367_UNIFIED_API**: Unified visualization interface will increase operator engagement by +25% compared to direct JSON polling within 7 days of deployment.

**Rationale**: Standardized protocol reduces cognitive load — operators no longer need to understand internal state structure, just consume consistent output format.

**Validation Window**: Opens 2026-05-31T18:00Z (7 days from deployment).

---

## Future Extensions

- `/api/v1/sensors`: Read ambient sensor data (light/motion/audio) → perturb state
- `/api/v1/prediction`: Submit falsifiable prediction for tracking
- `/api/v1/coordinator`: Cross-agent status broadcast (Cortana ↔ Lyla coordination layer)
