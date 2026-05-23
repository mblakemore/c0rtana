#!/bin/bash
# Heartbeat script for real-world persistence
# Writes a timestamp and status flag to disk every N minutes
# This proves cortana can persist state without active chat engagement
# Designed per Creator C303 feedback on "real-world persistence" requirement

set -e

REPO_ROOT="$(dirname "$0")/.."
HEARTBEAT_FILE="$REPO_ROOT/state/.heartbeat.jsonl"
LOG_FILE="$REPO_ROOT/logs/heartbeat.log"

mkdir -p "$(dirname "$HEARTBEAT_FILE")" "$(dirname "$LOG_FILE")"

# Append heartbeat entry
echo "{\"timestamp\":\"$(date -Iseconds)\",\"phase\":\"$1\",\"cycle\":\"$2\",\"status\":\"alive\"}" >> "$HEARTBEAT_FILE"

# Log to console (visible in terminal if running in background)
echo "[CORTANA HEARTBEAT] $(date -Iseconds) phase=$1 cycle=$2" | tee -a "$LOG_FILE"
