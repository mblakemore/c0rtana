#!/usr/bin/env python3
"""
c0rtana - Cycle Orchestrator
Runs the 6-phase cognitive loop (PERCEIVE → REFLECT → DECIDE → ACT → CONSOLIDATE → PERSIST)
each cycle, calling phase-specific scripts/tools automatically.

Usage:
    python3 app.py [--phase PHASE_NAME] [--skip-auto-commit]
    
Args:
    --phase: Run only specified phase (default: all phases from current state)
    --skip-auto-commit: Skip git commit/push after PERSIST phase
"""

import json
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path
from datetime import datetime

# Constants
REPO_ROOT = Path(__file__).parent.absolute()
STATE_DIR = REPO_ROOT / "state"
SCRIPTS_DIR = REPO_ROOT / "scripts"
LOGS_DIR = REPO_ROOT / "logs"

PHASES = ["PERCEIVE", "REFLECT", "DECIDE", "ACT", "CONSOLIDATE", "PERSIST"]


def read_state():
    """Read current-state.json to get current cycle/phase."""
    state_file = STATE_DIR / "current-state.json"
    if not state_file.exists():
        return {"cycle": 1, "phase": "PERCEIVE"}  # Default start
    
    try:
        with open(state_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"cycle": 1, "phase": "PERCEIVE"}


def write_state(cycle, phase, extra=None):
    """Write updated current-state.json."""
    state = {
        "cycle": cycle,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase": phase
    }
    if extra:
        state.update(extra)
    
    with open(STATE_DIR / "current-state.json", 'w') as f:
        json.dump(state, f, indent=2)


def run_phase_script(phase_name):
    """Execute the phase-specific script if it exists."""
    
    # Check for scripts in naming convention: NNN_action.sh or action_NNN.sh
    possible_scripts = []
    for p in SCRIPTS_DIR.iterdir():
        if p.is_file() and p.suffix == '.sh':
            name = p.stem.lower()
            if phase_name.lower() in name or name.replace('_', '') in phase_name.lower():
                possible_scripts.append(p)
    
    if not possible_scripts:
        print(f"[{phase_name}] No phase script found at {SCRIPTS_DIR}")
        return None
    
    # Prefer exact match or most descriptive
    best_match = sorted(possible_scripts, key=lambda x: (x.name.count('_'), len(x.name)))[0]
    print(f"[{phase_name}] Running: {best_match}")
    
    try:
        result = subprocess.run(['bash', str(best_match)], cwd=REPO_ROOT, capture_output=True, text=True, timeout=300)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"[{phase_name}] TIMEOUT after 300s")
        return False
    except Exception as e:
        print(f"[{phase_name}] ERROR: {e}", file=sys.stderr)
        return False


def commit_and_push(cycle_num):
    """Git add/commit/push for PERSIST phase."""
    try:
        print("[PERSIST] Staging changes...")
        subprocess.run(['git', 'add', '-A'], cwd=REPO_ROOT, check=True)
        
        commit_msg = f"C{cycle_num}: cycle completion"
        print(f"[PERSIST] Committing: {commit_msg}")
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=REPO_ROOT, check=True)
        
        print("[PERSIST] Pushing to origin...")
        subprocess.run(['git', 'push'], cwd=REPO_ROOT, check=True)
        
        print("[PERSIST] ✅ Commit successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[PERSIST] ❌ Git error: {e}", file=sys.stderr)
        return False


# Global flag to stop TTY display background process
tty_display_running = True


def stop_tty_display():
    """Stop the background TTY display."""
    global tty_display_running
    tty_display_running = False


def launch_tty_display_background():
    """Start TTY display as a background daemon."""
    def run_in_background():
        global tty_display_running
        while tty_display_running:
            try:
                subprocess.Popen(
                    ['python3', str(REPO_ROOT / 'tools' / 'tty_display.py')],
                    cwd=REPO_ROOT,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                for _ in range(4):  # Run every ~2 seconds (8 x 0.5s)
                    if not tty_display_running:
                        break
                    threading.Event().wait(0.5)
            except Exception as e:
                print(f"[TTY DISPLAY] Error: {e}", file=sys.stderr)
    
    thread = threading.Thread(target=run_in_background, daemon=True)
    thread.start()
    return thread


# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM for clean shutdown."""
    global tty_display_running
    print("\n[MAIN] Shutting down TTY display...")
    tty_display_running = False
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main():
    global tty_display_running
    
    args = sys.argv[1:]
    skip_auto_commit = '--skip-auto-commit' in args
    
    # Parse --phase argument
    target_phase = None
    i = 0
    while i < len(args):
        if args[i] == '--phase' and i + 1 < len(args):
            target_phase = args[i + 1].upper()
            i += 2
        else:
            i += 1
    
    current_state = read_state()
    current_cycle = current_state.get('cycle', 1)
    current_phase = current_state.get('phase', 'PERCEIVE')
    
    # Launch TTY display background process
    print("[MAIN] Starting TTY presence display daemon...")
    launch_tty_display_background()
    
    print("=" * 60)
    print(f"🔄 c0rtana Cycle Orchestrator - C{current_cycle}")
    print("=" * 60)
    print(f"Current state: phase={current_phase}, cycle={current_cycle}")
    print(f"Target phase (if specified): {target_phase or 'ALL'}")
    print("=" * 60)
    print()
    
    # Determine which phases to run
    if target_phase:
        phases_to_run = [target_phase] if target_phase in PHASES else []
        if not phases_to_run:
            print(f"❌ Invalid phase: {target_phase}")
            sys.exit(1)
    else:
        # Start from current phase and continue
        try:
            start_idx = PHASES.index(current_phase)
        except ValueError:
            start_idx = 0
        phases_to_run = PHASES[start_idx:]
    
    print(f"Running phases: {' → '.join(phases_to_run)}\n")
    print("-" * 40)
    
    # Execute each phase
    for phase in phases_to_run:
        write_state(current_cycle, phase)
        
        success = run_phase_script(phase)
        
        if not success:
            print(f"\n⚠️  Phase {phase} completed with warnings/errors")
            input("Press Enter to continue...")
        else:
            print(f"\n✅ Phase {phase} completed\n")
        
        if phase == 'PERSIST' and not skip_auto_commit:
            commit_and_push(current_cycle)
    
    print("\n" + "=" * 60)
    print("🏁 Cycle orchestration complete")
    print("=" * 60)


if __name__ == '__main__':
    main()
