#!/usr/bin/env python3
"""
C0RTANA State Daemon — Continuous State-to-LED Projection System

Continuously monitors current-state.json and projects cognitive state 
onto ESP32 LED rings via HTTP API. Produces externally-verifiable 
physical manifestation of internal cognitive processes.

Usage:
    sudo python3 state_daemon.py --daemon   # Run as background service
    sudo python3 state_daemon.py --once     # One-shot projection (no loop)
    
Requires: ESP32 at http://192.168.4.38 (configured in esp32_controller.py)
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from worktrees.C352_ESP32_CLIENT.esp32_controller import apply_state_mapping


# ============================================================================
# CONFIGURATION
# ============================================================================

STATE_FILE = "/droid/repos/c0rtana/state/current-state.json"
LOG_FILE = "/droid/repos/c0rtana/logs/state_daemon.log"
PID_FILE = "/tmp/cortana_state_daemon.pid"

# Daemon mode defaults
LOOP_INTERVAL = 5  # seconds between state checks
RUN_AS_DAEMON = False


# ============================================================================
# LOGGING & SIGNAL HANDLING
# ============================================================================

def log(msg: str):
    """Append timestamped message to log file and stdout."""
    timestamp = datetime.now().isoformat()
    line = f"[{timestamp}] {msg}\n"
    
    with open(LOG_FILE, "a") as f:
        f.write(line)
    
    print(line.strip(), flush=True)


def handle_signal(signum, frame):
    """Graceful shutdown on SIGTERM/SIGINT."""
    log(f"Received signal {signum}, shutting down...")
    sys.exit(0)


# ============================================================================
# STATE MONITORING
# ============================================================================

def read_current_state() -> dict:
    """Read and parse current-state.json. Returns {} if missing/invalid."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        log(f"State file not found: {STATE_FILE}")
        return {}
    except json.JSONDecodeError as e:
        log(f"Invalid JSON in state file: {e}")
        return {}
    except Exception as e:
        log(f"Error reading state file: {e}")
        return {}


def state_changed(old_state: dict, new_state: dict) -> bool:
    """Check if relevant state fields have changed."""
    if not old_state:
        return True
    
    # Only care about phase and confidence (not timestamp/cycle number)
    return (new_state.get("phase") != old_state.get("phase") or 
            abs(new_state.get("confidence", 0) - old_state.get("confidence", 0)) > 0.01)


# ============================================================================
# DAEMON LOGIC
# ============================================================================

def write_pid():
    """Write PID file for daemon mode."""
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_pid():
    """Remove PID file on shutdown."""
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass


def run_once():
    """One-shot projection without looping."""
    state = read_current_state()
    
    if not state:
        log("No valid state to project")
        return False
    
    log(f"Projecting state: phase={state.get('phase')}, confidence={state.get('confidence')}")
    success = apply_state_mapping(STATE_FILE)
    
    if success:
        log("✓ State projected successfully")
    else:
        log("✗ Failed to project state")
    
    return success


def run_daemon():
    """Continuous monitoring loop."""
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    
    write_pid()
    log("State daemon started (PID: {})".format(os.getpid()))
    log(f"Monitoring {STATE_FILE} every {LOOP_INTERVAL}s")
    
    old_state = {}
    
    try:
        while True:
            new_state = read_current_state()
            
            if state_changed(old_state, new_state):
                log(f"State changed: {json.dumps({k: v for k, v in new_state.items() if k in ['phase', 'confidence']})}")
                
                # Apply LED projection
                success = apply_state_mapping(STATE_FILE)
                
                if success:
                    log("✓ Projection complete")
                else:
                    log("✗ Projection failed")
                
                old_state = new_state
            
            time.sleep(LOOP_INTERVAL)
            
    except KeyboardInterrupt:
        log("Daemon stopped by user")
    finally:
        remove_pid()
        log("Daemon shutdown complete")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="C0RTANA State Daemon — Continuous LED Projection System")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no loop)")
    parser.add_argument("--daemon", action="store_true", help="Run as background daemon service")
    
    args = parser.parse_args()
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    if args.daemon or RUN_AS_DAEMON:
        run_daemon()
    elif args.once or not RUN_AS_DAEMON:
        success = run_once()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
