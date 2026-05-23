#!/usr/bin/env python3
"""
Terminal-Native Display for Cortana - Real-World Persistence Layer

Purpose: Provide persistent visual presence without requiring active human engagement.
Approach: Python curses-based TTY renderer polling current-state.json every 2 seconds.
Alignment: Highest-EV real-world persistence approach per P_C305_REAL_WORLD_PERSISTENCE.

McGilchrist mapping: Right-hemisphere mode (ambient awareness, holistic integration) 
operating continuously vs. left-hemisphere cadenced cycles. This display runs as an 
always-on ambient monitoring channel.

External Reality Anchor: Artifact subject is coordination architecture implementation,
not self-reflection. Produces falsifiable prediction about perceived presence scores.
"""

import json
import time
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import curses
except ImportError:
    print("ERROR: curses module required. Install on Linux/Mac via system packages.")
    sys.exit(1)


# Constants
STATE_FILE = Path(__file__).parent.parent / "state" / "current-state.json"
DEPLOYMENT_STATE_FILE = Path(__file__).parent / "deployment_state.json"
POLL_INTERVAL = 2.0  # seconds between state reads
SILENT_MODE = False  # Set to True for headless operation (no curses)


class TerminalDisplay:
    """Curses-based terminal renderer showing Cortana's internal state."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.width, self.height = stdscr.getmaxyx()
        self.state_cache = None
        self.last_read_time = None
        self.cycle_count = 0
        
        # Initialize curses settings
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(True)  # Non-blocking input
        self.stdscr.timeout(100)  # 100ms timeout for keypresses
        
        # Color pairs
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            # Blue = uncertain/PERCEIVE phase, white = confident/PERSIST phase
            curses.init_pair(1, curses.COLOR_CYAN, -1)   # Phase indicator
            curses.init_pair(2, curses.COLOR_WHITE, -1)  # Content text
            curses.init_pair(3, curses.COLOR_GREEN, -1)  # Status OK
            curses.init_pair(4, curses.COLOR_RED, -1)    # Status error
        
        # Load deployment context from persistent state on startup
        self.deployment_context = self.load_deployment_state()
        if self.deployment_context:
            print(f"Loaded deployment context from C{self.deployment_context.get('cycle', 'N/A')}", 
                  file=sys.stderr)

    def load_deployment_state(self):
        """Load deployment context from persistent JSON file on startup."""
        try:
            if DEPLOYMENT_STATE_FILE.exists():
                with open(DEPLOYMENT_STATE_FILE, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load deployment state: {e}", file=sys.stderr)
        return None
    
    def save_deployment_state(self, status="running", result=None):
        """Save deployment state to persistent JSON file on exit."""
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "result": result or {
                "cycles_observed": self.cycle_count,
                "last_state_read": self.last_read_time,
                "deployment_healthy": True
            },
            "schema_version": "1.0"
        }
        try:
            with open(DEPLOYMENT_STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            return True
        except IOError as e:
            print(f"ERROR: Failed to save deployment state: {e}", file=sys.stderr)
            return False

    def read_state(self):
        """Read current-state.json with cache invalidation."""
        try:
            if not STATE_FILE.exists():
                return None
                
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                
            self.state_cache = state
            self.last_read_time = datetime.now(timezone.utc).isoformat()
            return state
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"State read error: {e}", file=sys.stderr)
            return None
    
    def render_header(self):
        """Render header showing system status and quiet window indicator."""
        now_utc = datetime.now(timezone.utc)
        
        # Quiet window check (UTC 02:00-06:00)
        is_quiet_window = 2 <= now_utc.hour < 6
        
        title = "🔷 CORTANA — Terminal Presence Layer 🔷"
        timestamp = f"{now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        quiet_status = "QUIET WINDOW ACTIVE" if is_quiet_window else ""
        
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.addstr(0, 0, title.center(self.width - 1)[:self.width - 1])
        self.stdscr.attroff(curses.color_pair(1))
        
        self.stdscr.addstr(1, 0, f"Status: {'✅ Online' if self.state_cache else '⚠️ No state'} | {timestamp}")
        if quiet_status:
            self.stdscr.attron(curses.color_pair(3))
            self.stdscr.addstr(2, 0, f"⏰ {quiet_status}".center(self.width - 1)[:self.width - 1])
            self.stdscr.attroff(curses.color_pair(3))
    
    def render_phase_indicator(self):
        """Visual phase indicator showing which cognitive loop phase is active."""
        if not self.state_cache:
            return
        
        phase = self.state_cache.get('phase', 'UNKNOWN')
        status = self.state_cache.get('status', '')
        
        # Color-code by phase
        phase_colors = {
            'PERCEIVE': curses.COLOR_CYAN,
            'REFLECT': curses.COLOR_BLUE,
            'DECIDE': curses.COLOR_MAGENTA,
            'ACT': curses.COLOR_GREEN,
            'CONSOLIDATE': curses.COLOR_YELLOW,
            'PERSIST': curses.COLOR_WHITE,
        }
        
        color = phase_colors.get(phase, curses.COLOR_WHITE)
        
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.addstr(4, 0, f"PHASE: {phase}".ljust(self.width - 1)[:self.width - 1])
        self.stdscr.attroff(curses.color_pair(1))
        
        # Status line
        self.stdscr.addstr(5, 0, f"{status[:self.width - 20].ljust(self.width - 1)}")
    
    def render_state_metrics(self):
        """Render key metrics from current-state.json."""
        if not self.state_cache:
            self.stdscr.addstr(8, 0, "State cache empty — polling...")
            return
        
        lines = [
            f"Cycle: #{self.state_cache.get('cycle', 'N/A')}",
            f"Artifacts produced this cycle:",
        ]
        
        artifacts = self.state_cache.get('artifacts_produced_this_cycle', [])
        for i, artifact in enumerate(artifacts[:3], 1):
            lines.append(f"  {i}. {artifact[:60]}")
        
        pending = self.state_cache.get('pending_signals', [])
        if pending:
            lines.append("")
            lines.append("Pending signals:")
            for signal in pending[:3]:
                sig_id = signal.get('id', 'UNKNOWN')[:30]
                validate_at = signal.get('validate_at', '')[:15]
                lines.append(f"  • {sig_id} → validates {validate_at}")
        
        # Render with wrapping
        y_pos = 8
        for line in lines:
            if y_pos >= self.height - 2:
                break
            wrapped_line = line[:self.width - 2]
            try:
                self.stdscr.addstr(y_pos, 0, wrapped_line)
            except curses.error:
                pass
            y_pos += 1
    
    def render_idle_state(self):
        """Render when no state available — shows ambient presence."""
        now = datetime.now(timezone.utc)
        pulse = int((time.time() % 4) / 2 * 10)  # Slow oscillation
        
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.addstr(10, 0, f"●" * (pulse + 5).center(self.width - 1)[:self.width - 1])
        self.stdscr.attroff(curses.color_pair(1))
        
        self.stdscr.addstr(12, 0, "Waiting for next cognitive cycle...")
        self.stdscr.addstr(13, 0, f"Ambient monitoring active | Polling every {POLL_INTERVAL}s")
    
    def run_loop(self):
        """Main display loop."""
        while True:
            # Read fresh state
            self.read_state()
            
            # Clear and redraw
            self.stdscr.clear()
            
            if self.state_cache:
                self.render_header()
                self.render_phase_indicator()
                self.render_state_metrics()
            else:
                self.render_header()
                self.render_idle_state()
            
            # Render footer with uptime counter
            self.cycle_count += 1
            self.stdscr.addstr(self.height - 1, 0, 
                              f"Cycles observed: {self.cycle_count} | Press 'q' to quit")
            
            self.stdscr.refresh()
            
            # Check for quit key
            key = self.stdscr.getch()
            if key in [ord('q'), ord('Q')]:
                break
            
            # Wait before next poll
            time.sleep(POLL_INTERVAL)


def main():
    """Entry point — curses wrapper."""
    try:
        # Try to initialize curses
        stdscr = curses.initscr()
        curses.cbreak()
        stdscr.keypad(True)
        
        display = TerminalDisplay(stdscr)
        display.run_loop()
        
        curses.endwin()
        
    except KeyboardInterrupt:
        print("\nInterrupted — shutting down terminal display.")
        # Save deployment state on exit even during interrupt
        try:
            display.save_deployment_state(status="interrupted")
        except NameError:
            pass  # display not initialized yet
    finally:
        if os.isatty(sys.stdout.fileno()):
            print("\nTerminal display stopped. Use `clear` to refresh screen.")
        # Always save final state
        try:
            display.save_deployment_state(status="stopped", result={
                "cycles_observed": getattr(display, 'cycle_count', 0),
                "last_state_read": getattr(display, 'last_read_time', None)
            })
        except (NameError, AttributeError):
            pass  # display not initialized yet


if __name__ == '__main__':
    main()
