#!/bin/bash
# C316: TTY presence display runner
# Polls tty_display.py every 2 seconds during this phase

set -e

echo "[TTY PRESENCE] Starting real-time terminal feedback loop..."
echo "[TTY PRESENCE] Press Ctrl+C to stop"

# Run curses-based TTY display (non-blocking via subshell)
cd /droid/repos/c0rtana
while true; do
    python3 tools/tty_display.py &
    DISPLAY_PID=$!
    
    # Wait 2 seconds then kill and restart (keeps curses fresh)
    sleep 2
    kill $DISPLAY_PID 2>/dev/null || true
done
