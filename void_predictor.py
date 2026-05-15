import json
import time
from datetime import datetime

# CONFIGURATION (Based on C138 analysis)
CONFIDENCE_THRESHOLD = 0.6     # Predictive signal starts when confidence drops below this
ACCEL_SPIKE_THRESHOLD = 1.3    # delta increase in resonance velocity to trigger 'Imminent' alert
TELEMETRY_FILE = 'state/current-state.json'
HISTORY_FILE = 'state/telemetry/history.jsonl'

def get_resonance_velocity():
    """
    Extracts the current acceleration factor by calculating the distance gap
    between standard and critical paths from associative memory.
    Ported logic from resonance_velocity_test.py.
    """
    try:
        with open('state/associative_memory.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return 1.0
        
    nodes = {node['id']: node for node in data['nodes']}
    edges = data.get('edges', [])
    adj = {}
    for edge in edges:
        src, tgt = edge['source'], edge['target']
        if src not in adj: adj[src] = []
        adj[src].append(tgt)
        if tgt not in adj: adj[tgt] = []
        adj[tgt].append(src)

    def measure_depth(start_id, target_id):
        if start_id == target_id: return 0
        from collections import deque
        queue = deque([(start_id, 0)])
        visited = {start_id}
        while queue:
            curr, depth = queue.popleft()
            if curr == target_id: return depth
            for n in adj.get(curr, []):
                if n not in visited:
                    visited.add(n)
                    cost = 0.5 if nodes.get(curr, {}).get('criticality', 0) >= 2 else 1.0
                    queue.append((n, depth + cost))
        return float('inf')

    std = measure_depth('NODE_c47_001', 'NODE_STRAT_OBJ_002')
    crit = measure_depth('NODE_CORTANA', 'NODE_STRAT_OBJ_002')
    
    if crit == 0 or std == float('inf'):
        return 1.0
    return std / crit

def read_confidence():
    try:
        with open(TELEMETRY_FILE, 'r') as f:
            state = json.load(f)
            return state.get('confidence', 0.5)
    except Exception:
        return 0.5

def log_telemetry(conf, velocity):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "confidence": conf,
        "velocity": velocity
    }
    with open(HISTORY_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def predict_spike():
    conf = read_confidence()
    vel = get_resonance_velocity()
    log_telemetry(conf, vel)
    
    try:
        with open(HISTORY_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2: return "CALIBRATING", vel
            prev = json.loads(lines[-2])
    except Exception:
        return "CALIBRATING", vel

    delta_v = vel - prev['velocity']
    
    if conf < CONFIDENCE_THRESHOLD and delta_v > ACCEL_SPIKE_THRESHOLD:
        return "VOID_SPIKE_IMMINENT", vel
    elif delta_v > ACCEL_SPIKE_THRESHOLD:
        return "SYSTEMIC_ACCELERATION", vel
    elif conf < CONFIDENCE_THRESHOLD:
        return "COGNITIVE_TENSION", vel
    else:
        return "STABLE", vel

if __name__ == "__main__":
    state = predict_spike()
    print(json.dumps({"prediction": state[0], "current_velocity": state[1]}))
