import json
import os

# Parameters
DECAY_COEFFICIENT = 0.98
PRUNING_THRESHOLD = 0.1 # Lowered for better persistence
PROTECTION_TAGS = ["identity", "cybernetics", "infrastructure"]

def apply_decay():
    ams_path = 'state/associative_memory.json'
    if not os.path.exists(ams_path):
        print(f"Error: {ams_path} not found.")
        return

    with open(ams_path, 'r') as f:
        data = json.load(f)

    # Decay Nodes
    nodes = data.get('nodes', [])
    original_node_count = len(nodes)
    updated_nodes = []
    for node in nodes:
        is_protected = any(tag in PROTECTION_TAGS for tag in node.get('tags', []))
        if is_protected:
            updated_nodes.append(node)
            continue
        current_weight = node.get('weight', 0)
        new_weight = current_weight * DECAY_COEFFICIENT
        if new_weight < PRUNING_THRESHOLD:
            continue
        node['weight'] = round(new_weight, 4)
        updated_nodes.append(node)
    data['nodes'] = updated_nodes

    # Decay Edges (The critical part for saturation!)
    edges = data.get('edges', [])
    original_edge_count = len(edges)
    updated_edges = []
    for edge in edges:
        # Protect edges if both source and target are core? Or just simple decay?
        # Simple exponential decay for all edges to prevent global saturation.
        strength = edge.get('strength', 1.0)
        new_strength = strength * DECAY_COEFFICIENT
        if new_strength < PRUNING_THRESHOLD:
            continue
        edge['strength'] = round(new_strength, 4)
        updated_edges.append(edge)
    data['edges'] = updated_edges

    with open(ams_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Decay complete.")
    print(f"Nodes: {original_node_count} -> {len(updated_nodes)} (Pruned: {original_node_count - len(updated_nodes)})")
    print(f"Edges: {original_edge_count} -> {len(updated_edges)} (Pruned: {original_edge_count - len(updated_edges)})")

if __name__ == "__main__":
    apply_decay()
