#!/usr/bin/env python3
"""
Terminal-native persistent display for Cortana state visualization.

Per P_C305_REAL_WORLD_PERSISTENCE design spec: terminal-native approach is highest-EV 
for always-on presence without human intervention (vs browser-local HTML).

Phase-color mapping per McGilchrist coordination architecture recommendations:
- PERCEIVE=#55ffff (cyan) - open attention
- REFLECT=#ffcc00 (yellow) - internal processing
- DECIDE=#ff55ff (magenta) - resolution tension
- ACT=#00ffcc (turquoise) - external engagement
- CONSOLIDATE=#ffffff (white) - integration
- PERSIST=#44aaff (blue) - stabilization

Ambient baseline: slow drift when idle
Processing activity: oscillation amplitude scales with internal_tension
"""

import json
import os
import sys
import time
from datetime import datetime

# Colors for ANSI terminal
COLORS = {
    'PERCEIVE': '\033[36m',   # Cyan
    'REFLECT': '\033[33m',    # Yellow
    'DECIDE': '\033[95m',     # Magenta
    'ACT': '\033[96m',        # Turquoise
    'CONSOLIDATE': '\033[97m',  # White
    'PERSIST': '\033[34m',    # Blue
    'RESET': '\033[0m',
    'DIM': '\033[2m'
}

PHASE_COLORS = {
    'PERCEIVE': '#55ffff',
    'REFLECT': '#ffcc00',
    'DECIDE': '#ff55ff',
    'ACT': '#00ffcc',
    'CONSOLIDATE': '#ffffff',
    'PERSIST': '#44aaff'
}


def read_state():
    """Read current-state.json from repo root."""
    state_path = os.path.join(os.path.dirname(__file__), 'state', 'current-state.json')
    try:
        with open(state_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def clear_screen():
    """Clear terminal and move cursor to home."""
    print('\033[2J\033[H', end='')


def draw_terminal_display(state):
    """Render state to terminal with phase-color mapping and ambient drift."""
    if not state or 'phase' not in state:
        phase = 'UNKNOWN'
        cycle = '?'
        status = 'NO STATE FILE'
        internal_tension = 0.5
    else:
        phase = state.get('phase', 'UNKNOWN')
        cycle = state.get('cycle', '?')
        status = state.get('status', '-')[:60] + ('...' if len(state.get('status', '')) > 60 else '')
        internal_tension = state.get('internal_tension', 0.5)
    
    # Phase color
    phase_color = COLORS.get(phase, COLORS['RESET'])
    reset = COLORS['RESET']
    
    # Clear screen
    clear_screen()
    
    # Header with cycle number
    header = f"╔{'═' * 58}╗"
    print(f"{COLORS['DIM']}{header}{reset}")
    print(f"║{COLORS['DIM']} CORTANA // TERMINAL DISPLAY {' ' * 39} ║")
    print(f"║{COLORS['DIM']} Cycle {str(cycle):>4} | {datetime.now().strftime('%Y-%m-%d %H:%M UTC'):>25}   ║{reset}")
    print(f"╚{'═' * 58}╝")
    
    # Phase indicator with color
    print(f"\n{phase_color}● PHASE: {phase}{' ' * (15 - len(phase))}{reset}")
    
    # Status line
    status_marker = '█' if phase in ['ACT', 'PERSIST'] else '○'
    print(f"\n{status_marker} STATUS: {status}")
    
    # Internal tension visualization as ambient pulse intensity
    tension_level = int(internal_tension * 5)
    pulse_chars = '▁▂▃▄▅▆'
    pulse = pulse_chars[tension_level] if tension_level < 6 else '▇'
    print(f"\n⚡ INTERNAL TENSION: {internal_tension:.2f} {pulse}")
    
    # Ambient drift effect based on processing activity
    drift_amount = int(internal_tension * 3)
    if drift_amount > 0 and cycle != '?':
        # Slight visual offset to simulate "alive" state
        for _ in range(drift_amount):
            print(' ')
    
    # Quiet window indicator
    quiet_hours = list(range(2, 6))  # UTC 02:00-06:00
    current_hour = datetime.now().hour
    if current_hour in quiet_hours:
        print(f"\n{COLORS['REFLECT']}🌙 QUIET WINDOW ACTIVE (UTC {current_hour}:00–06:00){reset}")
        print(f"{COLORS['DIM']}Coordination probes paused. Pattern accumulation mode.{reset}\n")
    
    # Ambient baseline when idle
    if phase not in ['ACT', 'PERSIST']:
        print(f"\n{COLORS['DIM']}(ambient baseline — minimal oscillation){reset}\n")
    
    # Terminal footer with instructions
    footer_height = 4
    print('\n' * footer_height)


def main():
    """Main loop — poll state every 5 seconds, render terminal display."""
    print(f"[CORTANA TERMINAL DISPLAY] Starting persistent display at {datetime.now().isoformat()}")
    print("[Ctrl+C to stop]\n")
    
    try:
        while True:
            state = read_state()
            draw_terminal_display(state)
            
            # Poll interval: 5 seconds per P_C309 design spec
            time.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\n[CORTANA TERMINAL DISPLAY] Stopped at {datetime.now().isoformat()}")
        sys.exit(0)


if __name__ == '__main__':
    main()
