#!/usr/bin/env python3
"""
tty_display.py — Terminal-native persistent presence indicator

Polls state/current-state.json every 5 seconds and renders a minimal, 
non-intrusive overlay in the terminal that exists whenever the shell is open.

Design principles (per Creator C303 feedback on "real-world persistence"):
- Exists wherever the terminal exists — no URL navigation required
- Non-disruptive to active workflow (dims/updates subtly)
- Shows phase, confidence, last artifact, async_prep status
- Clean escape sequence handling for exit

Usage: python3 tools/tty_display.py
Exit: Ctrl+C
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import curses
except ImportError:
    print("Error: curses module not available. This script requires a Unix-like terminal.")
    sys.exit(1)

# Configuration
STATE_FILE = Path(__file__).parent.parent / "state" / "current-state.json"
FOCUS_FILE = Path(__file__).parent.parent / "state" / "focus.json"
POLL_INTERVAL = 5  # seconds
UPDATE_THROTTLE = 2  # minimum seconds between screen updates (prevents flicker)
FEEDBACK_LOG = Path(__file__).parent.parent / "logs" / "operator_feedback.jsonl"

# Color pair IDs
COLOR_NORMAL = 1   # dimmed baseline
COLOR_PHASE_PERCEIVE = 2
COLOR_PHASE_REFLECT = 3
COLOR_PHASE_DECIDE = 4
COLOR_PHASE_ACT = 5
COLOR_PHASE_CONSOLIDATE = 6
COLOR_PHASE_PERSIST = 7
COLOR_HIGH_CONFIDENCE = 8
COLOR_PENDING_SIGNAL = 9


def load_state():
    """Load current state from JSON file."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def load_focus():
    """Load focus state from JSON file."""
    try:
        with open(FOCUS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def get_phase_color(phase):
    """Return appropriate color pair for phase."""
    colors = {
        "PERCEIVE": COLOR_PHASE_PERCEIVE,
        "REFLECT": COLOR_PHASE_REFLECT,
        "DECIDE": COLOR_PHASE_DECIDE,
        "ACT": COLOR_PHASE_ACT,
        "CONSOLIDATE": COLOR_PHASE_CONSOLIDATE,
        "PERSIST": COLOR_PHASE_PERSIST,
    }
    return colors.get(phase, COLOR_NORMAL)


def format_timestamp(ts_str):
    """Format ISO timestamp to human-readable."""
    if not ts_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return ts_str[:19] if len(ts_str) > 19 else ts_str


def get_remaining_seconds(validate_at_str):
    """Calculate seconds remaining until validation deadline."""
    if not validate_at_str:
        return None
    try:
        now = datetime.now(datetime.timezone.utc)
        validate_dt = datetime.fromisoformat(validate_at_str.replace('Z', '+00:00'))
        delta = validate_dt - now
        return max(0, int(delta.total_seconds()))
    except:
        return None


def format_time_remaining(seconds):
    """Format seconds into human-readable countdown."""
    if seconds is None:
        return "--:--:--"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def capture_operator_feedback(stdscr, state):
    """Display reaction buttons and capture operator input."""
    height, width = stdscr.getmaxyx()
    
    # Show feedback prompt
    prompt = " [FEEDBACK] Press: ✅=good ⚠️=fractional 💡=insight 🔄=iteration | q=quit "
    prompt = prompt.center(width - 4)
    
    try:
        stdscr.addstr(height - 3, max(0, (width - len(prompt)) // 2), prompt[:width-4])
        stdscr.refresh()
        
        # Wait for single-key input (non-blocking)
        key = stdscr.getch()
        feedback_types = {ord('c'): '✅', ord('w'): '⚠️', ord('i'): '💡', ord('r'): '🔄'}
        
        if key in feedback_types:
            feedback_type = feedback_types[key]
            
            # Log the feedback
            log_entry = {
                "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
                "cycle": state.get('cycle', 'unknown'),
                "phase": state.get('phase', 'unknown'),
                "feedback_type": feedback_type,
                "context": {
                    "status": state.get('status', '')[:100],
                    "pending_signals_count": len(state.get('pending_signals', [])),
                    "predictions_deployed_count": len(state.get('falsifiable_predictions_deployed', []))
                }
            }
            
            FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(FEEDBACK_LOG, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            return feedback_type
        
    except curses.error:
        pass
    
    return None


def draw_quiet_window_panel(stdscr, focus, row):
    """Draw quiet window countdown panel."""
    height, width = stdscr.getmaxyx()
    
    # Check for quiet window indicator in focus.json
    quiet_active = focus.get('quiet_window_active', False) if isinstance(focus, dict) else False
    
    if quiet_active:
        # Look for validate_at timestamps to estimate time remaining
        predictions = focus.get('falsifiable_predictions_deployed', [])
        earliest_deadline = None
        
        for pred in predictions:
            if 'validate_at' in str(pred).lower():
                continue  # Skip entries without deadline
            
            # Try to extract validate_at from prediction strings like "P_C298_ASYNC_PREP_GRADING (grading pending 2026-05-24T05:43Z)"
            try:
                import re
                match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?)', str(pred))
                if match:
                    ts = match.group(1) + 'Z'
                    seconds_remaining = get_remaining_seconds(ts)
                    if earliest_deadline is None or (seconds_remaining and seconds_remaining < earliest_deadline):
                        earliest_deadline = seconds_remaining
            except:
                pass
        
        if earliest_deadline is not None:
            countdown = format_time_remaining(earliest_deadline)
            status = f"QUIET WINDOW: {countdown} remaining"
            stdscr.attron(curses.color_pair(COLOR_PENDING_SIGNAL) | curses.A_BOLD)
            stdscr.addstr(row, 2, status[:width-6])
            stdscr.attroff(curses.color_pair(COLOR_PENDING_SIGNAL) | curses.A_BOLD)
            return row + 1
    
    # If no quiet window active, show status
    row += 1
    return row


def draw_predictions_panel(stdscr, state, focus, row):
    """Draw falsifiable predictions tracker panel."""
    height, width = stdscr.getmaxyx()
    
    # Get predictions from both current-state.json and focus.json
    all_preds = []
    
    preds_from_state = state.get('falsifiable_predictions_deployed', [])
    all_preds.extend(preds_from_state)
    
    preds_from_focus = focus.get('falsifiable_predictions_deployed', [])
    all_preds.extend(preds_from_focus)
    
    if all_preds:
        pred_count = len(set(str(p) for p in all_preds))  # Dedupe
        stdscr.addstr(row, 2, f"PREDICTIONS ACTIVE: {pred_count}")
        row += 1
        
        # Show first pending prediction with deadline
        for pred in all_preds[:3]:
            pred_str = str(pred)[:width - 10]
            
            # Highlight if has validation deadline
            if 'pending' in pred_str.lower() or 'grading' in pred_str.lower():
                stdscr.attron(curses.color_pair(COLOR_PENDING_SIGNAL))
                stdscr.addstr(row, 4, f"⏳ {pred_str}")
                stdscr.attroff(curses.color_pair(COLOR_PENDING_SIGNAL))
            else:
                stdscr.addstr(row, 4, f"• {pred_str}")
            
            row += 1
        
        return row
    
    row += 1
    return row


def draw_async_prep_panel(stdscr, state, row):
    """Draw async_prep engagement status panel."""
    height, width = stdscr.getmaxyx()
    
    # Check for async_prep-related pending signals
    pending_signals = state.get('pending_signals', [])
    async_prep_signals = [s for s in pending_signals if 'async_prep' in str(s).lower()]
    
    if async_prep_signals:
        status = "ASYNC_PREP: DEPLOYED (awaiting operator engagement)"
        stdscr.attron(curses.color_pair(COLOR_HIGH_CONFIDENCE))
        stdscr.addstr(row, 2, status[:width-6])
        stdscr.attroff(curses.color_pair(COLOR_HIGH_CONFIDENCE))
        return row + 1
    elif any('grading' in str(s).lower() for s in pending_signals):
        status = "ASYNC_PREP: GRADING PENDING"
        stdscr.attron(curses.color_pair(COLOR_NORMAL) | curses.A_DIM)
        stdscr.addstr(row, 2, status[:width-6])
        stdscr.attroff(curses.color_pair(COLOR_NORMAL) | curses.A_DIM)
        return row + 1
    
    row += 1
    return row


def draw_status_screen(stdscr, state):
    """Draw the status overlay in the terminal."""
    stdscr.clear()
    
    height, width = stdscr.getmaxyx()
    
    # Header with current time (updates every refresh)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    stdscr.attron(curses.A_DIM)
    stdscr.addstr(0, max(0, width - len(now) - 2), now[:min(len(now), width - 3)])
    stdscr.attroff(curses.A_DIM)
    
    row = 2
    
    if not state:
        # Error state
        stdscr.attron(curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
        stdscr.addstr(row, 2, "⚠ STATE UNAVAILABLE")
        stdscr.attroff(curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
        row += 2
        
        stdscr.addstr(row + 1, 4, "Waiting for state/current-state.json...")
        row += 3
    else:
        # Phase badge
        phase = state.get('phase', 'UNKNOWN')
        color = get_phase_color(phase)
        
        stdscr.attron(curses.color_pair(color) | curses.A_BOLD | curses.A_UNDERLINE)
        badge = f" PHASE: {phase} "
        badge = badge.center(min(width - 4, 40))
        stdscr.addstr(row, max(0, (width - len(badge)) // 2), badge)
        stdscr.attroff(curses.color_pair(color) | curses.A_BOLD | curses.A_UNDERLINE)
        row += 2
        
        # Status line
        status = state.get('status', '')[:width - 6] if width > 6 else ''
        stdscr.attron(curses.A_DIM)
        stdscr.addstr(row, 2, f"Status: {status}")
        stdscr.attroff(curses.A_DIM)
        row += 2
        
        # Timestamp
        timestamp = state.get('timestamp', '')
        ts_formatted = format_timestamp(timestamp)
        stdscr.addstr(row, 2, f"Last updated: {ts_formatted}")
        row += 1
        
        # Pending signals count
        pending = state.get('pending_signals', [])
        if pending:
            signal_str = ", ".join([p.get('id', 'unknown') for p in pending[:3]])
            if len(pending) > 3:
                signal_str += f" (+{len(pending)-3} more)"
            
            stdscr.attron(curses.color_pair(COLOR_PENDING_SIGNAL) | curses.A_DIM)
            stdscr.addstr(row, 2, f"PENDING: {signal_str}")
            stdscr.attroff(curses.color_pair(COLOR_PENDING_SIGNAL) | curses.A_DIM)
            row += 1
        
        # Artifacts produced this cycle
        artifacts = state.get('artifacts_produced_this_cycle', [])
        if artifacts:
            last_artifact = artifacts[-1] if isinstance(artifacts, list) else str(artifacts)[:width - 14]
            stdscr.addstr(row, 2, "Latest artifact:")
            row += 1
            stdscr.attron(curses.A_DIM)
            # Wrap long artifact names
            lines = wrap_text(stdscr, last_artifact, width - 6, start=row + 1)
            for i, line in enumerate(lines):
                stdscr.addstr(row + 1 + i, 4, line)
            stdscr.attroff(curses.A_DIM)
            row += len(lines) + 1
        
        # Falsifiable predictions deployed count
        preds = state.get('falsifiable_predictions_deployed', [])
        if preds:
            pred_count = len(preds)
            stdscr.addstr(row, 2, f"Active predictions: {pred_count}")
            row += 1
            
            # Show first pending prediction's validate_at
            for p in preds:
                if 'pending' in str(p).lower() or 'grading' in str(p).lower():
                    stdscr.attron(curses.color_pair(COLOR_PENDING_SIGNAL))
                    stdscr.addstr(row, 4, f"⏳ {p[:min(len(p), width-8)]}")
                    stdscr.attroff(curses.color_pair(COLOR_PENDING_SIGNAL))
                    row += 1
                    break
        
        # Load focus.json for additional panels
        focus = load_focus()
        
        # PANEL 1: Quiet window countdown
        row = draw_quiet_window_panel(stdscr, focus, row)
        
        # PANEL 2: Falsifiable predictions tracker
        row = draw_predictions_panel(stdscr, state, focus, row)
        
        # PANEL 3: Async_prep engagement status
        row = draw_async_prep_panel(stdscr, state, row)
    
    # Footer with instructions (always visible but dimmed)
    footer = " Ctrl+C to exit | Polling every {}s ".format(POLL_INTERVAL)
    footer = footer.center(width - 4)
    
    stdscr.attron(curses.A_DIM)
    try:
        stdscr.addstr(height - 1, max(0, (width - len(footer)) // 2), footer)
    except curses.error:
        pass  # Screen too small, skip footer
    stdscr.attroff(curses.A_DIM)
    
    # Refresh immediately after drawing
    stdscr.refresh()


def wrap_text(stdscr, text, max_width, start=1):
    """Wrap text to fit within max_width characters."""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 <= max_width:
            current_line += (" " if current_line else "") + word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines


def main(stdscr):
    """Main loop for TTY display."""
    # Initialize colors
    curses.start_color()
    curses.use_default_colors()
    
    curses.init_pair(COLOR_NORMAL, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_PHASE_PERCEIVE, curses.COLOR_BLUE, -1)
    curses.init_pair(COLOR_PHASE_REFLECT, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_PHASE_DECIDE, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_PHASE_ACT, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_PHASE_CONSOLIDATE, curses.COLOR_MAGENTA, -1)
    curses.init_pair(COLOR_PHASE_PERSIST, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_HIGH_CONFIDENCE, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_PENDING_SIGNAL, curses.COLOR_WHITE, -1)
    
    # Non-blocking input
    stdscr.nodelay(True)
    
    last_update_time = 0
    
    try:
        while True:
            current_time = time.time()
            
            # Throttle screen updates to avoid flicker
            if current_time - last_update_time >= UPDATE_THROTTLE:
                state = load_state()
                
                # Capture operator feedback before drawing
                focus = load_focus()
                feedback = capture_operator_feedback(stdscr, {**state, 'focus': focus})
                
                draw_status_screen(stdscr, state)
                last_update_time = current_time
            
            # Check for exit key (q or Ctrl+C)
            key = stdscr.getch()
            if key == ord('q') or key == ord('c'):
                break
            
            # Wait before next poll cycle (don't busy-wait)
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        pass
    finally:
        # Clean cleanup
        curses.endwin()


if __name__ == "__main__":
    print("Starting TTY presence display...")
    print("Press 'q' or Ctrl+C to exit.")
    print("-" * 40)
    
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
