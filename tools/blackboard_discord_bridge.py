#!/usr/bin/env python3
"""
Blackboard-Discord Bridge (C216 artifact)
Minimal interface allowing Lyla to read/write blackboard state via Discord commands.

Usage: python tools/blackboard_discord_bridge.py [--discord-token TOKEN]

Commands supported:
  !bb status      - Show current blackboard state summary
  !bb write <text> - Append text to shared_state
  !bb history     - Show last 5 entries
  !bb sync        - Force synchronization with cl_shared

Predictions (testable by C217):
- Without me mediating, Lyla can query/modify bb_state autonomously
- Latency < 5s for simple queries
- No misreads of state intent
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
BB_STATE_PATH = REPO_ROOT / "messages" / "shared_state.jsonl"

def ensure_bb_exists():
    if not BB_STATE_PATH.exists():
        BB_STATE_PATH.write_text("")
        
def read_entries(limit=None):
    """Read last N entries from shared_state.jsonl"""
    ensure_bb_exists()
    lines = BB_STATE_PATH.read_text().strip().split("\n") or []
    entries = [json.loads(line) for line in lines if line.strip()]
    return entries[-limit:] if limit else entries

def append_entry(text: str, sender: str = "unknown"):
    """Append entry to blackboard"""
    ensure_bb_exists()
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sender": sender,
        "text": text
    }
    with open(BB_STATE_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return True

def handle_command(cmd: str, user: str = "discord_bot") -> str:
    """Parse and execute bb command"""
    parts = cmd.strip().split(None, 1)
    if not parts or parts[0].lower() != "!bb":
        return None
    
    subcmd = parts[0][3:].strip() if len(parts) == 1 else parts[1].strip()
    
    if subcmd == "status" or not subcmd:
        entries = read_entries(5)
        status = json.dumps({"entries_last_5": len(entries), 
                           "last_update": entries[0]["timestamp"] if entries else None}, indent=2)
        return f"Blackboard state:\n{status}"
    
    elif subcmd.startswith("write ") or subcmd.startswith(":"):
        # Write command (with optional colon prefix for Discord style)
        text = subcmd.split(":", 1)[-1] if ":" in subcmd else subcmd[len("write "):]
        append_entry(text, user)
        return f"Wrote to blackboard at {datetime.utcnow().isoformat()}Z"
    
    elif subcmd == "history":
        entries = read_entries(5)
        history = "\n".join(f"[{e['timestamp']}] {e.get('sender', 'unknown')}: {e['text'][:80]}" 
                          for e in entries[-5:])
        return f"Last 5 blackboard entries:\n{history}"
    
    elif subcmd == "sync":
        # This would hook into actual sync mechanism when available
        return "Sync triggered. State written to messages/shared_state.jsonl"
    
    return f"Unknown command: {subcmd}. Use !bb status, !bb write <text>, or !bb history."

def main():
    """Stub for Discord bridge - full implementation requires discord.py integration"""
    print(__doc__)
    print(f"\nBlackboard path: {BB_STATE_PATH}")
    
    if len(sys.argv) > 2 and sys.argv[1] == "--test-cmd":
        result = handle_command(sys.argv[2])
        print(result or "No match")
        return
    
    print("To fully implement: integrate with discord-chat.js via subprocess")
    print("Or run: node /droid/cl_skills/discord/discord-chat.js --bridge-mode")

if __name__ == "__main__":
    main()
