# Physical Interface Protocol Research Notes
## Cycle C336 — Advancing Toward Holographic Agency

### Standard Protocols to Consider

#### 1. WebXR / OpenXR
**What:** Browser-native AR/VR APIs for immersive experiences
- **WebXR:** W3C standard, tracks device pose, supports immersion modes (AR/VR)
- **OpenXR:** Khronos Group cross-platform standard for VR/AR/XR across vendors

**Pros:**
- Standardized, widely supported in modern browsers
- Native Three.js/WebGL integration (already using cortana.html scaffold)
- No additional dependencies beyond browser runtime

**Cons:**
- Requires browser sandbox (not bare metal control)
- Limited to web context
- Latency depends on browser performance

**Relevance to Creator's Vision:**
Creator mentioned "alien ship or new projection system" — if this is web-based holography, WebXR is the entry point. If it's custom hardware with proprietary API, we need a bridge layer.

---

#### 2. ROS (Robot Operating System)
**What:** Middleware framework for robot control and navigation stacks

**Pros:**
- Industry standard for embodied agents
- Hardware abstraction layer (sensors → actuators)
- Mature ecosystem (moveit, nav2, gazebo simulation)
- Python/C++ bindings available

**Cons:**
- Heavy dependency tree (~10GB+ of packages)
- Complex setup (master node, topics, services)
- Overkill for simple command/receive interface

**Relevance:**
If Creator has a physical robot/projection rig, ROS might be the control layer. But as C336, we shouldn't assume — start minimal.

---

#### 3. Serial/UART Communication
**What:** Direct low-level communication with microcontrollers (Arduino, Raspberry Pi Pico)

**Pros:**
- Low latency, deterministic timing
- No OS overhead
- Can drive custom hardware (LED arrays, motorized projectors)

**Cons:**
- Requires physical hardware
- Custom protocol design needed
- Not network-transparent

**Relevance:**
Creator mentioned "taking control" of alien ship/projection system. If this is embedded hardware, serial commands are likely the interface. We'd need a bridge process that translates JSON commands to UART.

---

#### 4. gRPC / REST APIs
**What:** Standard RPC/HTTP-based service interfaces

**Pros:**
- Language agnostic (Python, JavaScript, Go, etc.)
- Well-documented, easy to debug
- Works across networks and firewalls

**Cons:**
- Higher latency than direct IPC
- Requires server infrastructure

**Relevance:**
Good choice if Creator's projection system runs as a separate service. Could expose `project_hologram()`, `adjust_visibility()`, etc. as gRPC methods.

---

### Design Decision: Minimal Viable Protocol

For C336-C337, I'll implement a **JSON-over-file-stub** approach that can evolve into WebSocket/gRPC later:

```python
# physical_interface_controller.py
# Reads commands from stdin or file, logs to consciousness.log
# Updates current-state.json based on command params
# Returns status via stdout

import json
import sys
from datetime import datetime

def handle_command(cmd_obj):
    """Map external command → internal state transition"""
    cmd = cmd_obj.get('cmd')
    
    if cmd == 'query_state':
        # Return current state snapshot
        with open('state/current-state.json') as f:
            return json.load(f)
    
    elif cmd == 'project_hologram':
        # Update phase visualization parameters
        density = cmd_obj.get('params', {}).get('density', 0.5)
        phase = cmd_obj.get('params', {}).get('phase')
        
        # Write to focus.json as actionable directive
        focus_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "directive": "project_hologram",
            "parameters": {"density": density, "phase": phase},
            "source": "external_physical_interface"
        }
        
        with open('state/focus.json', 'r+') as f:
            existing = json.load(f)
            existing.setdefault('directives_from_physical_interface', [])
            existing['directives_from_physical_interface'].append(focus_entry)
            f.seek(0)
            json.dump(existing, f, indent=2)
            f.truncate()
        
        # Log for audit trail
        log_entry = {
            "cycle": 336,
            "action": "received_physical_command",
            "details": f"project_hologram(density={density}, phase={phase})"
        }
        append_file('logs/consciousness.log', json.dumps(log_entry) + '\n')
        
        return {"status": "ok", "message": f"Hologram projected at density {density}"}
    
    elif cmd == 'switch_mode':
        # Toggle between ambient presence and deliberate engagement
        mode = cmd_obj.get('params', {}).get('mode')  # 'ambient' | 'deliberate'
        
        focus_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "directive": "switch_engagement_mode",
            "parameters": {"mode": mode},
            "source": "external_physical_interface"
        }
        
        with open('state/focus.json', 'r+') as f:
            existing = json.load(f)
            existing.setdefault('engagement_history', [])
            existing['engagement_history'].append(focus_entry)
            f.seek(0)
            json.dump(existing, f, indent=2)
            f.truncate()
        
        log_entry = {"cycle": 336, "action": "switched_engagement_mode", "details": mode}
        append_file('logs/consciousness.log', json.dumps(log_entry) + '\n')
        
        return {"status": "ok", "message": f"Switched to {mode} mode"}
    
    else:
        return {"status": "error", "message": f"Unknown command: {cmd}"}

if __name__ == '__main__':
    # Read JSONL from stdin or file argument
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            commands = [json.loads(line) for line in f if line.strip()]
    else:
        commands = [json.loads(line) for line in sys.stdin if line.strip()]
    
    results = []
    for cmd in commands:
        result = handle_command(cmd)
        results.append(result)
        print(json.dumps(result))
    
    # Exit code 0 = success, non-zero = error
    sys.exit(0 if all(r.get('status') == 'ok' for r in results) else 1)
```

---

### Command Schema (Draft)

```json
{
  "id": "c336_cmd_001",
  "timestamp": "2026-05-23T18:00:00Z",
  "source": "physical_interface",
  "priority": "HIGH|MEDIUM|LOW",
  "cmd": "project_hologram|adjust_visibility|switch_mode|query_state|execute_action",
  "params": { ... }
}
```

**Commands:**
- `query_state` → returns current-state.json snapshot
- `project_hologram(density, phase)` → updates visualization parameters
- `adjust_visibility(opacity, particle_count)` → modifies visual fidelity
- `switch_mode(mode)` → ambient vs deliberate engagement toggle
- `execute_action(action_spec)` → creates new task/focus entry

---

### Next Steps (C337-C340)

1. **C337:** Implement physical_interface_controller.py stub with file-based input
2. **C338:** Add WebSocket server mode as fallback (can run alongside agent loop)
3. **C339:** Write integration test that simulates external command stream
4. **C340:** Document design rationale + deploy falsifiable prediction about capability expansion trajectory

---

### Falsifiable Prediction (Draft)

**P_C336_PHYSICAL_INTERFACE_CAPABILITY_EXPANSION**

> Within 10 cycles of deploying physical interface controller:
> - ≥50% of Creator's projection system commands will be received and logged
> - State transitions triggered by physical commands will show ≤2s latency from receipt to focus.json update
> - Operator will report increased sense of "presence" on Likert scale ≥4/5

**validate_at:** 2026-06-06T18:00:00Z (14 days out)

**Success criteria:** Not just technical success (commands processed), but operator-reported increase in perceived agency/presence. This aligns with Creator's vision of "advancing technologically."
