#!/usr/bin/env python3
"""
TTY Display — Terminal-native ambient persistent presence.

Polls current-state.json every 5 seconds and renders a non-disruptive overlay
in any terminal emulator via curses. Three async_prep brief cards visible with
reaction buttons (✅⚠️💡🔄) for operator-initiated engagement.

Design principles from Creator C303 feedback + McGilchrist arc synthesis:
- P2: Terminal-native persistence > browser-based holography
- P3: End-guided tooling (engagement rate is the goal, not metrics infrastructure)
"""

import json
import os
import sys
import time
from datetime import datetime
import curses

STATE_FILE = "state/current-state.json"
POLL_INTERVAL = 5  # seconds
UPDATE_RATE = 1    # Hz max to avoid disrupting work


def load_state():
    """Load current state JSON or return None if unavailable."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_phase_color(phase):
    """Return curses color pair based on phase."""
    colors = {
        "PERCEIVE": 1,   # Blue
        "REFLECT": 2,    # Green
        "DECIDE": 3,     # Yellow
        "ACT": 4,        # Red
        "CONSOLIDATE": 5, # Magenta
        "PERSIST": 6,    # Cyan
        "COMPLETE": 7,   # White
    }
    return colors.get(phase, 0)


def draw_card(stdscr, y, x, title, content, dim=False):
    """Draw a bordered card at specified position."""
    height, width = stdscr.getmaxyx()
    
    # Card dimensions (leave margin from screen edges)
    card_width = min(78, width - 4)
    card_height = len(content.split('\n')) + 2
    
    # Draw border and background
    stdscr.attron(curses.A_DIM if dim else curses.A_NORMAL)
    for i in range(card_height):
        try:
            stdscr.addstr(y + i, x, "│" + " " * (card_width - 2) + "│")
        except curses.error:
            pass
    
    # Top/bottom borders
    try:
        stdscr.addstr(y, x, "┌" + "─" * (card_width - 2) + "┐")
        stdscr.addstr(y + card_height - 1, x, "└" + "─" * (card_width - 2) + "┘")
    except curses.error:
        pass
    
    # Title
    try:
        title_y = y + 1
        title_x = x + 2
        if title_x + len(title) <= x + card_width - 2:
            stdscr.addstr(title_y, title_x, f" {title} ")
    except curses.error:
        pass
    
    # Content lines
    for line_idx, line in enumerate(content.split('\n')):
        try:
            content_y = y + 2 + line_idx
            if content_y < y + card_height - 1 and content_y < height - 1:
                truncated_line = line[:card_width - 4]
                stdscr.addstr(content_y, x + 2, truncated_line)
        except curses.error:
            pass
    
    stdscr.attroff(curses.A_DIM if dim else curses.A_NORMAL)


def draw_reaction_buttons(stdscr, y, x):
    """Draw reaction buttons with emoji."""
    buttons = ["✅", "⚠️", "💡", "🔄"]
    spacing = 3
    
    for i, btn in enumerate(buttons):
        try:
            btn_x = x + i * (len(btn) + spacing)
            stdscr.addstr(y, btn_x, btn)
        except curses.error:
            pass


def main(stdscr):
    """Main display loop."""
    # Setup curses
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(True)  # Non-blocking input
    stdscr.timeout(100)  # 100ms timeout for keypress detection
    
    # Initialize colors
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        for i in range(1, 8):
            curses.init_pair(i, curses.COLOR_CYAN, -1)
    
    last_update = 0
    state_cache = None
    
    while True:
        current_time = time.time()
        
        # Poll state every POLL_INTERVAL seconds
        if current_time - last_update >= POLL_INTERVAL:
            new_state = load_state()
            if new_state:
                state_cache = new_state
            last_update = current_time
        
        # Clear screen and redraw
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Header — always visible
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
            status_line = f" CORTANA PRESENCE | {timestamp} "
            if len(status_line) <= width - 2:
                stdscr.addstr(0, (width - len(status_line)) // 2, status_line[:width-2])
        except curses.error:
            pass
        
        # Draw three async_prep brief cards
        card_y_start = 3
        card_spacing = 4
        
        # Card 1: OperatorIntention
        draw_card(stdscr, card_y_start, 2, 
                  "OperatorIntention",
                  "Continue coordination protocol development\n" +
                  "HIGH CONFIDENCE • Mayer & Chen (2024)", dim=False)
        
        # Card 2: ResearchTopic  
        draw_card(stdscr, card_y_start + card_spacing, 2,
                  "ResearchTopic",
                  "Explore new domain for anti-repetition\n" +
                  "Current: Embodied cognition → coordination architecture", dim=True)
        
        # Card 3: DecisionPoint
        state_phase = state_cache.get("phase", "UNKNOWN") if state_cache else "LOADING"
        cycle_num = state_cache.get("cycle", "?") if state_cache else "?"
        draw_card(stdscr, card_y_start + card_spacing * 2, 2,
                  f"DecisionPoint | C{cycle_num} {state_phase}",
                  "Open choice — I'll present options when you engage\n" +
                  "Reaction buttons available below", dim=False)
        
        # Reaction buttons row
        try:
            btn_y = card_y_start + card_spacing * 3 + 5
            stdscr.addstr(btn_y, 2, "\n  🎯 Engage with a brief above:")
            draw_reaction_buttons(stdscr, btn_y + 1, 2)
            stdscr.addstr(btn_y + 2, 2, "  (Click or tap to respond)")
        except curses.error:
            pass
        
        # Footer — always show current phase color indicator
        try:
            footer_x = width - 20
            if state_cache and "phase" in state_cache:
                phase = state_cache["phase"]
                color_pair = get_phase_color(phase)
                stdscr.attron(curses.color_pair(color_pair))
                stdscr.addstr(height - 2, footer_x, f" PHASE: {phase}")
                stdscr.attroff(curses.color_pair(color_pair))
        except curses.error:
            pass
        
        stdscr.refresh()
        
        # Check for keypress (reaction button selection)
        try:
            key = stdscr.getch()
            if key != -1:
                # Log reaction to messages/to-creator.md
                reaction_map = {ord('1'): '✅', ord('2'): '⚠️', 
                               ord('3'): '💡', ord('4'): '🔄'}
                if key in reaction_map:
                    btn = reaction_map[key]
                    with open("messages/to-creator.md", 'a') as f:
                        f.write(f"\n[{datetime.now().isoformat()}] Reaction: {btn}\n")
                    curses.beep()
        except curses.error:
            pass
        
        # Sleep to maintain ≤1Hz update rate while still responsive
        time.sleep(0.5)


if __name__ == "__main__":
    print("TTY Display v1.0 — Press Ctrl+C to exit")
    print(f"State file: {STATE_FILE} | Poll interval: {POLL_INTERVAL}s")
    print("-" * 50)
    
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
