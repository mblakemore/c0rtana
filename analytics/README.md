# Interaction Analytics Stack

## Purpose

Measure operator engagement with cortana's interactive particle UI per **DC1.5/C4957 External Reality Anchor** requirement. Each cycle must produce externally-verifiable artifacts — interaction data is such an artifact.

## Components

### 1. `analytics_tracker.py` — Event Logger Daemon

- WebSocket server on `ws://localhost:8767`
- Receives events from visualizer, appends to JSONL log file
- Non-blocking, append-only design (cybernetic memory principle)
- Periodic heartbeat broadcasts total interactions / active clients

**Run:**
```bash
python3 analytics/analytics_tracker.py
```

### 2. `analytics_client.js` — Visualizer Integration

- Injected into `cortana.html` via `<script src="./analytics/analytics_client.js"></script>`
- Tracks mouse movements (throttled at 10% to avoid flooding)
- Emits `{type, timestamp, session_id, coordinates}` to analytics tracker
- Auto-reconnects if connection drops

### 3. `interaction_dashboard.html` — Real-Time Metrics

- WebSocket client subscribing to analytics tracker heartbeats
- Displays: total interactions, active sessions, last updated
- Live event log table + raw stream scrollback
- Open in browser: `http://localhost:8080/dashboard/interaction_dashboard.html`

**Quick start:**
```bash
# From c0rtana repo root:
cd dashboard && python3 -m http.server 8080
# Then open http://localhost:8080/interaction_dashboard.html
```

## Event Schema

Each logged interaction is a JSON object:
```json
{
  "type": "mouse_move" | "cursor_enter",
  "timestamp": "2026-05-23T21:43:46Z",
  "session_id": "sess_20260523_214346_0",
  "coordinates": {"x": 1024, "y": 768},
  "cumulative_moves": 42
}
```

## Log File Format

Append-only JSONL at `analytics/interactions.jsonl`:
```
{"type":"mouse_move","timestamp":"...","session_id":"..."}
{"type":"cursor_enter","timestamp":"...","session_id":"..."}
```

Per **Critical Lesson #1 (Storage ≠ Retrieval)**: query actively. Use:
```bash
grep 'mouse_move' analytics/interactions.jsonl | wc -l  # count events
tail -n 100 analytics/interactions.jsonl  # recent activity
```

## External Artifact Validation

This stack produces **Cycle-End Signal** artifacts:
- ✅ Concrete external-domain artifact (interaction data from real operators)
- ✅ Measurable metrics (interaction frequency, session duration)
- ✅ Falsifiable predictions (will operator engagement exceed baseline?)

Data can be used to validate **P_C339_INTERACTIVE_PRESENCE**: *"If creator engages with interactive particle UI ≥5 times in validation window → ambient+interactive model has value."*

---

*Built C340 — measurement infrastructure for engagement validation*
