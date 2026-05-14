import json
from collections import deque

def run_resonance_probe(ams_path):
    with open(ams_path, 'r') as f:
        data = json.load(f)
    
    nodes = {node['id']: node for node in data['nodes']}
    edges = data.get('edges', [])
    
    # Build adjacency list from edges
    adj = {}
    for edge in edges:
        src, tgt = edge['source'], edge['target']
        if src not in adj: adj[src] = []
        adj[src].append(tgt)
        # Assuming undirected associative links for resonance
        if tgt not in adj: adj[tgt] = []
        adj[tgt].append(src)

    def measure_depth(start_id, target_id):
        if start_id == target_id: return 0
        queue = deque([(start_id, 0)])
        visited = {start_id}
        min_depth = float('inf')
        
        while queue:
            curr, depth = queue.popleft()
            
            if curr == target_id:
                return depth
            
            for n in adj.get(curr, []):
                if n not in visited:
                    visited.add(n)
                    # Criticality (>=2) reduces the 'cognitive distance' of a hop
                    cost = 0.5 if nodes.get(n, {}).get('criticality', 0) >= 2 else 1.0
                    queue.append((n, depth + cost))
        return float('inf')

    # Test Case 1: Path from a non-critical node to Target
    # Start A: NODE_c49_004 (Crit 0) -> Target: NODE_STRAT_OBJ_002
    # Note: Based on edges, c49_004 is isolated. Let's use something connected.
    # Use NODE_c47_001 (Crit 0) -> NODE_RDOGP (Crit 2) -> NODE_STRAT_OBJ_002 (Crit 1)
    
    depth_standard = measure_depth('NODE_c47_001', 'NODE_STRAT_OBJ_002')
    # Test Case 2: Path from a critical node to Target
    # Start B: NODE_CORTANA (Crit 2) -> NODE_RDOGP (Crit 2) -> NODE_STRAT_OBJ_002 (Crit 1)
    depth_critical = measure_depth('NODE_CORTANA', 'NODE_STRAT_OBJ_002')
    
    return depth_standard, depth_critical

if __name__ == "__main__":
    try:
        std, crit = run_resonance_probe('state/associative_memory.json')
        print(f"Standard Resonance Depth: {std}")
        print(f"Critical Resonance Depth: {crit}")
        if crit != 0 and std != float('inf'):
            print(f"Acceleration Factor: {std/crit}")
    except Exception as e:
        print(f"Error during probe: {e}")
