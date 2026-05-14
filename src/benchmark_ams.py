import json
from collections import deque
import time

class AMSTraversalLegacy:
    """Simulated legacy target-attraction logic for baseline comparison."""
    def __init__(self, ams_path):
        with open(ams_path, 'r') as f:
            data = json.load(f)
        self.nodes = {node['id']: node for node in data['nodes']}
        self.adj = {}
        for edge in data.get('edges', []):
            src, tgt = edge['source'], edge['target']
            self.adj.setdefault(src, []).append(tgt)
            self.adj.setdefault(tgt, []).append(src)

    def calculate_cost(self, source_id):
        # Legacy cost is always 1.0 (no accelerant)
        return 1.0

    def find_shortest_resonance(self, start_id, target_id):
        if start_id == target_id: return 0
        queue = deque([(start_id, 0)])
        visited = {start_id}
        while queue:
            curr, depth = queue.popleft()
            if curr == target_id: return depth
            for n in self.adj.get(curr, []):
                if n not in visited:
                    visited.add(n)
                    cost = self.calculate_cost(curr)
                    queue.append((n, depth + cost))
        return float('inf')

from src.ams_traversal import AMSTraversal

def run_benchmark():
    ams_path = 'state/associative_memory.json'
    legacy = AMSTraversalLegacy(ams_path)
    modern = AMSTraversal(ams_path)

    # Define test pairs: (source, target)
    # We want some that involve critical nodes to see the acceleration effect
    test_pairs = [
        ("NODE_CORTANA", "NODE_AMS"),         # Core -> Infrastructure (Both criticality 2)
        ("NODE_c47_001", "NODE_phi_res_001"), # Non-critical -> Distant node
        ("NODE_RDOGP", "NODE_c49_010"),      # Critical -> Strategic pattern
        ("NODE_vS_073", "NODE_C85_PAT_01"),  # Technical -> Meta-cognitive
    ]

    print(f"{'Pair':<40} | {'Legacy Cost':<12} | {'Modern Cost':<12} | {'Delta'}")
    print("-" * 80)

    total_legacy = 0
    total_modern = 0
    count = 0

    for src, tgt in test_pairs:
        l_cost = legacy.find_shortest_resonance(src, tgt)
        m_cost = modern.find_shortest_resonance(src, tgt)
        delta = l_cost - m_cost
        
        print(f"{src + ' -> ' + tgt:<40} | {l_cost:<12.2f} | {m_cost:<12.2f} | {delta:<12.2f}")
        
        if l_cost != float('inf'):
            total_legacy += l_cost
            total_modern += m_cost
            count += 1

    if count > 0:
        avg_legacy = total_legacy / count
        avg_modern = total_modern / count
        improvement = (avg_legacy - avg_modern) / avg_legacy * 100
        print("-" * 80)
        print(f"Average Legacy Cost: {avg_legacy:.2f}")
        print(f"Average Modern Cost:  {avg_modern:.2f}")
        print(f"Efficiency Gain:      {improvement:.2f}%")
    else:
        print("No reachable pairs found.")

if __name__ == "__main__":
    run_benchmark()
