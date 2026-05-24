#!/usr/bin/env python3
"""
C0RTANA State Daemon — Continuous State-to-LED Projection System with Sensor Feedback

Continuously monitors current-state.json and projects cognitive state 
onto ESP32 LED rings via HTTP API. Integrates environmental sensors to 
close the cybernetic feedback loop between embodied cognition and internal processing.

Sensor Integration:
  - Light level → modulates LED brightness, shifts color temperature
  - Motion detection → perturbs IDLE→PERCEIVE phase transition
  
Usage:
    sudo python3 state_daemon.py --daemon              # Background daemon
    sudo python3 state_daemon.py --simulate-sensors    # Test with simulated sensors (default)
    sudo python3 state_daemon.py --real-sensors        # Use real ESP32 sensor data
    
    sudo python3 state_daemon.py --once                # One-shot projection
    
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

from worktrees.C352_ESP32_CLIENT.esp32_controller import (
    apply_state_mapping, 
    read_sensors, 
    apply_sensor_feedback
)


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


def run_once(simulate_sensors: bool = True):
    """One-shot projection with sensor feedback loop without looping."""
    state = read_current_state()
    
    if not state:
        log("No valid state to project")
        return False
    
    # Read environmental context via sensors (simulated or real)
    sensors = read_sensors(simulate=simulate_sensors)
    log(f"Sensors: light_level={sensors['light_level']}, motion={sensors['motion_detected']}")
    
    # Modulate internal state based on environmental input
    modulated_state = apply_sensor_feedback(state, sensors)
    log(f"Modulated: {json.dumps({k:v for k,v in modulated_state.items() if k.startswith('_')})}")
    
    log(f"Projecting state: phase={modulated_state.get('phase')}, confidence={modulated_state.get('confidence')}")
    success = apply_state_mapping(STATE_FILE)
    
    if success:
        log("✓ State projected successfully")
    else:
        log("✗ Failed to project state")
    
    return success


def run_daemon(simulate_sensors: bool = True):
    """Continuous monitoring loop with sensor feedback."""
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    
    write_pid()
    log("State daemon started (PID: {})".format(os.getpid()))
    log(f"Monitoring {STATE_FILE} every {LOOP_INTERVAL}s")
    log(f"Sensor simulation mode: {simulate_sensors}")
    
    old_state = {}
    
    try:
        while True:
            new_state = read_current_state()
            
            if state_changed(old_state, new_state):
                log(f"State changed: {json.dumps({k: v for k, v in new_state.items() if k in ['phase', 'confidence']})}")
                
                # Read environmental context via sensors
                sensors = read_sensors(simulate=simulate_sensors)
                log(f"Sensors: light_level={sensors['light_level']}, motion={sensors['motion_detected']}")
                
                # Modulate internal state based on environmental input
                modulated_state = apply_sensor_feedback(new_state, sensors)
                
                # Apply LED projection
                success = apply_state_mapping(STATE_FILE)
                
                if success:
                    log("✓ Projection complete with sensor feedback")
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
    parser = argparse.ArgumentParser(description="C0RTANA State Daemon — Continuous LED Projection System with Sensor Feedback")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no loop)")
    parser.add_argument("--daemon", action="store_true", help="Run as background daemon service")
    parser.add_argument("--real-sensors", action="store_true", help="Use real ESP32 sensors instead of simulation")
    parser.add_argument("--simulate-sensors", action="store_true", default=True, help="Simulate sensors for testing (default: True)")
    
    args = parser.parse_args()
    
    # Determine sensor mode
    simulate_sensors = args.simulate_sensors or not args.real_sensors
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    if args.daemon or RUN_AS_DAEMON:
        run_daemon(simulate_sensors=simulate_sensors)
    elif args.once or not RUN_AS_DAEMON:
        success = run_once(simulate_sensors=simulate_sensors)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
