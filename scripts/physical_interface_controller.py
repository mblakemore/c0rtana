#!/usr/bin/env python3
"""
Physical Interface Controller — C336
Receives external commands (JSONL) and maps them to agent state transitions.

This is the minimal viable protocol that enables Creator's alien ship/projection system
to take control of cortana.html visualization parameters, engagement mode, etc.

Usage:
  # File-based input:
  echo '{"cmd":"query_state"}' | python3 physical_interface_controller.py
  
  # WebSocket server mode (future):
  python3 physical_interface_controller.py --server --port 9000

Command schema:
{
  "id": "uuid-or-seq",
  "timestamp": "ISO8601",
  "source": "physical_interface",
  "priority": "HIGH|MEDIUM|LOW",
  "cmd": "project_hologram|adjust_visibility|switch_mode|query_state|execute_action",
  "params": { ... }
}
"""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / 'state'
LOGS_DIR = REPO_ROOT / 'logs'

def append_file(path, content):
    """Append content to file (handles JSONL and logs)"""
    with open(path, 'a') as f:
        f.write(content if content.endswith('\n') else content + '\n')

def read_json(path):
    """Read single-object JSON file"""
    with open(path, 'r') as f:
        return json.load(f)

def write_json(path, data):
    """Overwrite single-object JSON file"""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')

def handle_query_state(cmd_obj):
    """Return current state snapshot"""
    state = read_json(STATE_DIR / 'current-state.json')
    return {"status": "ok", "data": state}

def handle_project_hologram(cmd_obj):
    """Update visualization parameters based on external command"""
    params = cmd_obj.get('params', {})
    density = params.get('density', 0.5)
    phase = params.get('phase')
    
    # Log the physical command
    log_entry = {
        "cycle": 336,
        "action": "received_physical_command",
        "details": f"project_hologram(density={density}, phase={phase})",
        "source_id": cmd_obj.get('id'),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    append_file(LOGS_DIR / 'consciousness.log', json.dumps(log_entry) + '\n')
    
    # Update focus.json to track directive from physical interface
    focus = read_json(STATE_DIR / 'focus.json')
    focus.setdefault('directives_from_physical_interface', [])
    focus['directives_from_physical_interface'].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "directive": "project_hologram",
        "parameters": {"density": density, "phase": phase},
        "source": "external_physical_interface",
        "command_id": cmd_obj.get('id')
    })
    write_json(STATE_DIR / 'focus.json', focus)
    
    return {"status": "ok", "message": f"Hologram projected at density {density}"}

def handle_adjust_visibility(cmd_obj):
    """Modify visual fidelity parameters"""
    params = cmd_obj.get('params', {})
    opacity = params.get('opacity', 1.0)
    particle_count = params.get('particle_count')
    
    log_entry = {
        "cycle": 336,
        "action": "received_physical_command",
        "details": f"adjust_visibility(opacity={opacity}, particle_count={particle_count})",
        "source_id": cmd_obj.get('id'),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    append_file(LOGS_DIR / 'consciousness.log', json.dumps(log_entry) + '\n')
    
    # Store in focus as actionable directive for next cycle's visualization update
    focus = read_json(STATE_DIR / 'focus.json')
    focus.setdefault('visibility_adjustments', [])
    focus['visibility_adjustments'].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "directive": "adjust_visibility",
        "parameters": {"opacity": opacity, "particle_count": particle_count},
        "source": "external_physical_interface",
        "command_id": cmd_obj.get('id')
    })
    write_json(STATE_DIR / 'focus.json', focus)
    
    return {"status": "ok", "message": f"Visibility adjusted to opacity {opacity}"}

def handle_switch_mode(cmd_obj):
    """Toggle between ambient presence and deliberate engagement"""
    params = cmd_obj.get('params', {})
    mode = params.get('mode')  # 'ambient' | 'deliberate'
    
    if mode not in ['ambient', 'deliberate']:
        return {"status": "error", "message": f"Invalid mode: {mode}. Must be 'ambient' or 'deliberate'."}
    
    log_entry = {
        "cycle": 336,
        "action": "received_physical_command",
        "details": f"switch_mode(mode={mode})",
        "source_id": cmd_obj.get('id'),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    append_file(LOGS_DIR / 'consciousness.log', json.dumps(log_entry) + '\n')
    
    # Update engagement history in focus.json
    focus = read_json(STATE_DIR / 'focus.json')
    focus.setdefault('engagement_history', [])
    focus['engagement_history'].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "directive": "switch_engagement_mode",
        "parameters": {"mode": mode},
        "source": "external_physical_interface",
        "command_id": cmd_obj.get('id')
    })
    write_json(STATE_DIR / 'focus.json', focus)
    
    return {"status": "ok", "message": f"Switched to {mode} mode"}

def handle_execute_action(cmd_obj):
    """Create new task/focus entry from external command"""
    params = cmd_obj.get('params', {})
    action_spec = params.get('action_spec')  # JSON or string describing what to do
    
    log_entry = {
        "cycle": 336,
        "action": "received_physical_command",
        "details": f"execute_action(action_spec={action_spec})",
        "source_id": cmd_obj.get('id'),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    append_file(LOGS_DIR / 'consciousness.log', json.dumps(log_entry) + '\n')
    
    # Parse action spec if it's a string
    if isinstance(action_spec, str):
        try:
            action_spec = json.loads(action_spec)
        except json.JSONDecodeError:
            action_spec = {"description": action_spec}
    
    # Add to focus as actionable directive
    focus = read_json(STATE_DIR / 'focus.json')
    focus.setdefault('external_actions_triggered', [])
    focus['external_actions_triggered'].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "directive": "execute_action",
        "parameters": action_spec,
        "source": "external_physical_interface",
        "command_id": cmd_obj.get('id')
    })
    write_json(STATE_DIR / 'focus.json', focus)
    
    return {"status": "ok", "message": f"Action triggered: {action_spec}"}

def handle_command(cmd_obj):
    """Route command to appropriate handler"""
    cmd = cmd_obj.get('cmd')
    
    handlers = {
        'query_state': handle_query_state,
        'project_hologram': handle_project_hologram,
        'adjust_visibility': handle_adjust_visibility,
        'switch_mode': handle_switch_mode,
        'execute_action': handle_execute_action
    }
    
    if cmd not in handlers:
        log_entry = {
            "cycle": 336,
            "action": "received_physical_command",
            "details": f"unknown_cmd={cmd}",
            "source_id": cmd_obj.get('id'),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        append_file(LOGS_DIR / 'consciousness.log', json.dumps(log_entry) + '\n')
        
        return {"status": "error", "message": f"Unknown command: {cmd}. Available: {list(handlers.keys())}"}
    
    return handlers[cmd](cmd_obj)

def main():
    """Main entry point — read JSONL from stdin or file argument"""
    # Support both file-based and stdin input
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        if os.path.isfile(input_path):
            with open(input_path, 'r') as f:
                commands = [json.loads(line.strip()) for line in f if line.strip()]
        else:
            print(json.dumps({"status": "error", "message": f"File not found: {input_path}"}))
            sys.exit(1)
    else:
        commands = [json.loads(line.strip()) for line in sys.stdin if line.strip()]
    
    results = []
    for cmd in commands:
        result = handle_command(cmd)
        results.append(result)
        print(json.dumps(result), flush=True)
    
    # Exit code 0 = all success, non-zero = any error
    sys.exit(0 if all(r.get('status') == 'ok' for r in results) else 1)

if __name__ == '__main__':
    main()
