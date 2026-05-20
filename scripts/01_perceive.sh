#!/bin/bash
# Atomic PERCEIVE script - outputs standard cycle-start intelligence
# Generated at C209 as part of Hand Protocol automation

set -e

cd "$(dirname "$0")/.."

echo "=== CYCLE START INTELLIGENCE ==="
echo ""

# 1. Current machine date/time
date -Iseconds

echo ""
echo "--- LAST COMMIT ---"
git log -1 --format="%h %s" || echo "(no commits yet)"

echo ""
echo "--- CURRENT STATE ---"
if [[ -f state/current-state.json ]]; then
    cat state/current-state.json | head -5
    echo "...(truncated)"
else
    echo "(not initialized)"
fi

echo ""
echo "--- PATTERN COUNT ---"
wc -l < state/memories/patterns.jsonl 2>/dev/null || echo "(no patterns)"

echo ""
echo "--- ANCHOR COUNT ---"  
wc -l < state/memories/anchors.jsonl 2>/dev/null || echo "(no anchors)"

echo ""
echo "--- DISCORD RECENT (last 3 messages) ---"
node /droid/cl_skills/discord/discord-chat.js recent --limit 3 2>/dev/null | grep '"text"' | head -3 || echo "(no Discord access)"

echo ""
echo "--- SHARED BLACKBOARD ENTRY COUNT ---"
if [[ -f /droid/repos/cl_shared/blackboard_registry.json ]]; then
    cat /droid/repos/cl_shared/blackboard_registry.json | grep -c '"entry_id"' || echo "0 entries"
elif [[ -f /droid/repos/cl_shared/blackboard/registry.json ]]; then
    cat /droid/repos/cl_shared/blackboard/registry.json | grep -c '"entry_id"' || echo "0 entries"
else
    echo "(not found)"
fi

echo ""
echo "=== END INTELLIGENCE ==="
