#!/usr/bin/env python3
"""
Cortana Visualization API Server v1.0
Unified interface layer for human interaction tech stack.

Endpoints:
  GET  /api/v1/state       - Current cognitive state projection
  POST /api/v1/transition  - Operator-initiated phase transition  
  GET  /api/v1/metrics     - Engagement metrics from analytics tracker
  GET  /api/v1/health      - Health check endpoint

Usage:
  python3 viz_server.py [--port 8080] [--sim]
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Configuration
STATE_FILE = Path("/droid/repos/c0rtana/state/current-state.json")
LOG_FILE = Path("/droid/repos/c0rtana/logs/api_requests.jsonl")

# Parse command line args properly
_args = __import__("sys").argv[1:]
PORT = 8080
SIM_MODE = False
for arg in _args:
    if arg.startswith("--port"):
        PORT = int(arg.split("=")[1] if "=" in arg else _args[_args.index(arg)+1])
    elif arg == "--sim":
        SIM_MODE = True

app = FastAPI(
    title="Cortana Visualization API",
    version="1.0.0",
    description="Unified interface layer for human interaction tech stack"
)

# Phase-to-output mapping (canonical color/animation/brightness per phase)
PHASE_MAPPINGS = {
    "PERCEIVE": {"color": "#4A90E2", "animation": "rainbow_cascade", "brightness": 0.8},
    "REFLECT": {"color": "#F5A623", "animation": "pulse_slow", "brightness": 0.7},
    "DECIDE": {"color": "#D0021B", "animation": "sparkle_fast", "brightness": 0.9},
    "ACT": {"color": "#50C878", "animation": "spin_rapid", "brightness": 1.0},
    "CONSOLIDATE": {"color": "#BD10E0", "animation": "fire_burst", "brightness": 0.8},
    "PERSIST": {"color": "#FFFFFF", "animation": "solid_steady", "brightness": 0.9},
    "IDLE": {"color": "#000000", "animation": "breathing", "brightness": 0.3}
}

class PhaseTransition(BaseModel):
    target_phase: str
    confidence_override: float | None = None
    reason: str = "operator_intervention"


def log_request(endpoint: str, query_params: dict, response_time_ms: float):
    """Append request to JSONL log file."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "query_params": query_params,
        "response_time_ms": round(response_time_ms, 2)
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_current_state() -> dict | None:
    """Read current-state.json from disk."""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read state: {e}")
    return None


@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    """Log all requests to JSONL file."""
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    log_request(request.url.path, dict(request.query_params), duration)
    return response


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    uptime = time.time() - getattr(app, "start_time", time.time())
    return {"status": "healthy", "uptime_seconds": round(uptime)}


@app.on_event("startup")
async def startup_event():
    """Record server start time."""
    app.start_time = time.time()
    print(f"[INFO] Cortana Visualization API v1.0 starting on port {PORT}")
    if SIM_MODE:
        print("[SIM] Simulation mode — no real state file access")


@app.get("/api/v1/state")
async def get_state(format: str = Query(default="json"), include_history: bool = Query(default=False)):
    """Return current cognitive state with output mapping."""
    if SIM_MODE:
        # Return simulated state for testing without hardware
        return {
            "cycle": 367,
            "phase": "ACT",
            "confidence": 0.85,
            "focus": "Unified visualization API implementation (simulation)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output_mapping": PHASE_MAPPINGS["ACT"]
        }
    
    state = read_current_state()
    if not state:
        return JSONResponse(status_code=404, content={"error": "state_file_not_found"})
    
    phase = state.get("phase", "IDLE")
    mapping = PHASE_MAPPINGS.get(phase, PHASE_MAPPINGS["IDLE"])
    
    response = {
        "cycle": state.get("cycle", 0),
        "phase": phase,
        "confidence": state.get("confidence", 0.5),
        "focus": state.get("focus", ""),
        "next_focus": state.get("next_focus", ""),
        "timestamp": datetime.fromisoformat(state.get("timestamp", datetime.now(timezone.utc).isoformat())).isoformat(),
        "output_mapping": mapping
    }
    
    if include_history and "history" in state:
        response["phase_history"] = state["history"][-5:]
    
    return response


@app.post("/api/v1/transition")
async def trigger_transition(transition: PhaseTransition):
    """Operator-initiated phase transition (metadata only — doesn't modify actual state)."""
    # In production, this would validate operator auth and potentially invoke state daemon
    # For now, just log the intent as an external artifact
    print(f"[TRANSITION] {transition.target_phase} requested via API — reason: {transition.reason}")
    return {
        "status": "accepted",
        "target_phase": transition.target_phase,
        "requested_at": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/v1/metrics")
async def get_metrics(window: str = Query(default="day")):
    """Return engagement metrics from analytics tracker."""
    try:
        interactions_file = Path("/droid/repos/c0rtana/state/interactions.jsonl")
        if not interactions_file.exists():
            return {"total_interactions": 0, "active_sessions_24h": 0, "engagement_score": 0.0}
        
        # Count events in window (simplified — full implementation reads JSONL)
        with open(interactions_file) as f:
            events = [json.loads(line) for line in f if line.strip()]
        
        total_events = len(events)
        unique_users = len(set(e.get("user_id", "anonymous") for e in events))
        
        # Simple engagement score heuristic
        engagement_score = min(1.0, total_events / 100)
        
        return {
            "total_interactions": total_events,
            "active_sessions_24h": unique_users,
            "avg_interaction_frequency_per_hour": round(total_events / max(1, window_hours[window]), 2),
            "last_active": datetime.now(timezone.utc).isoformat(),
            "engagement_score": round(engagement_score, 3)
        }
    except Exception as e:
        print(f"[ERROR] Failed to read metrics: {e}")
        return {"error": "metrics_unavailable"}


# Helper dict for window calculations
window_hours = {"hour": 1, "day": 24, "week": 168}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
