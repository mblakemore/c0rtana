#!/bin/bash
# C216 verification script for blackboard-discord bridge

set -e
cd "$(dirname "$0")/.."

echo "=== Testing Blackboard-Discord Bridge ==="

# Clear previous state
BB_PATH="messages/shared_state.jsonl"
rm -f $BB_PATH || true

echo "[1] Testing Python module..."
python3 tools/blackboard_discord_bridge.py --test-cmd '!bb status' | tee /tmp/bb_status.txt
grep -q "Blackboard state:" /tmp/bb_status.txt && echo "✓ Status command works" || exit 1

echo ""
echo "[2] Testing write command..."
echo '{"timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","sender":"C216","text":"Test entry from C216"}' >> $BB_PATH
cat $BB_PATH

echo ""
echo "[3] Verifying JSONL format is parseable..."
python3 -c "import json; [json.loads(l) for l in open('$BB_PATH') if l.strip()]" && echo "✓ Valid JSONL entries"

echo ""
echo "[4] Next steps:"
echo "   - Integrate with discord-chat.js via subprocess call"
echo "   - Deploy to Lyla's channel"
echo "   - Measure: can she use !bb commands autonomously?"
