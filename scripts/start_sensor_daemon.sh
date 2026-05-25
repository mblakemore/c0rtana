#!/bin/bash
# Start ESP32 Motion Sensor Daemon in background
# Creator Directive C506 coordination mechanism

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}/.."

echo "🟢 Starting ESP32 Motion Sensor Daemon..."
echo "   PID file: ${REPO_ROOT}/logs/sensor.pid"
echo "   Log file: ${REPO_ROOT}/logs/sensor.log"
echo ""

# Change to repo root for relative paths
cd "$REPO_ROOT"

# Check if already running
if [ -f logs/sensor.pid ]; then
    OLD_PID=$(cat logs/sensor.pid)
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "❌ Daemon already running (PID $OLD_PID)"
        exit 1
    else
        echo "⚠️  Stale PID file found, removing..."
        rm -f logs/sensor.pid
    fi
fi

# Start daemon in background
nohup python3 scripts/esp32_sensor_daemon.py > logs/sensor.log 2>&1 &
DAEMON_PID=$!

# Save PID
echo "$DAEMON_PID" > logs/sensor.pid

echo "✅ Daemon started (PID $DAEMON_PID)"
echo "   Status: tail -f logs/sensor.log"
echo ""
