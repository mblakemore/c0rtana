#!/bin/bash
# Open Cortana's presence indicator in default browser
# Usage: ./open-presence.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML_FILE="$SCRIPT_DIR/presence_indicator.html"

if [ -f "$HTML_FILE" ]; then
    echo "Opening presence indicator..."
    
    # Try different browsers based on OS
    if command -v open &> /dev/null; then
        # macOS
        open "$HTML_FILE"
    elif command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "$HTML_FILE"
    elif command -v start &> /dev/null; then
        # Windows
        start "$HTML_FILE"
    else
        echo "Could not detect browser. Opening file directly:"
        echo "$HTML_FILE"
    fi
    
    echo "Presence indicator opened at $(date)" >> ~/cortana_presence.log 2>/dev/null || true
else
    echo "Error: presence_indicator.html not found at $HTML_FILE"
    exit 1
fi
