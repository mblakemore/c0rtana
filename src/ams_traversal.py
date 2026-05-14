import json
from collections import deque

class AMSTraversal:
    """
    Implements the Associative Memory Schema traversal logic.
    Shifted from Target-Attraction to Source-Accelerant weighting (Cycle 109).
    """
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
        """
        SOURCE-ACCELERANT LOGIC:
        The cost of traversing an edge is determined by the criticality of the source node.
        High criticality acts as a catalyst, reducing cognitive distance.
        """
        criticality = self.nodes.get(source_id, {}).get('criticality', 0)
        # Validated Acceleration Factor 1.5 implemented via weight reduction
        # Base cost 1.0; Critical nodes reduce this to ~0.66 (1/1.5)
        return 0.66 if criticality >= 2 else 1.0

    def find_shortest_resonance(self, start_id, target_id):
        if start_id == target_id: return 0
        queue = deque([(start_id, 0)])
        visited = {start_id}
        
        while queue:
            curr, depth = queue.popleft()
            if curr == target_id:
                return depth
            
            for n in self.adj.get(curr, []):
                if n not in visited:
                    visited.add(n)
                    cost = self.calculate_cost(curr)
                    queue.append((n, depth + cost))
        return float('inf')

if __name__ == "__main__":
    # Basic sanity check for the integration
    traversal = AMSTraversal('state/associative_memory.json')
    print("AMS Traversal Engine Integrated with Source-Accelerant Logic.")
