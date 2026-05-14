import json

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def find_node(ams, node_id):
    for n in ams['nodes']:
        if n['id'] == node_id:
            return n
    return None

def traverse(ams, start_node_id, target_category, max_depth=5):
    # (current_node, depth, current_res, path)
    queue = [(start_node_id, 0, 1.0, [start_node_id])]
    visited = set()
    best_res = 0
    best_path = []

    while queue:
        curr_id, depth, res, path = queue.pop(0)
        
        curr_node = find_node(ams, curr_id)
        if not curr_node: continue
        
        # Broaden match for strategic categories
        tags = curr_node.get('tags', [])
        is_match = False
        if target_category == "meta-cognitive":
             # Match if it's meta-cognitive OR strategy
             if "meta-cognitive" in tags or "strategy" in tags:
                 is_match = True
        elif target_category == "infrastructure":
             # Match if it's infrastructure OR architecture
             if "infrastructure" in tags or "architecture" in tags:
                 is_match = True
        else:
            if target_category in tags:
                is_match = True

        if is_match:
            if res > best_res:
                best_res = res
                best_path = path
        
        if depth < max_depth:
            for edge in ams['edges']:
                if edge['source'] == curr_id:
                    neighbor = edge['target']
                    if neighbor not in visited:
                        visited.add(neighbor)
                        weight = edge.get('strength', 0.5)
                        queue.append((neighbor, depth + 1, res * weight, path + [neighbor]))
                        
    return {"resonance": best_res, "path": best_path}

def main():
    ams = load_json('state/associative_memory.json')
    
    tests = [
        {"name": "Technical -> Strategic", "start": "NODE_MEM_SCHEMA_001", "target": "meta-cognitive"},
        {"name": "Identity -> Technical", "start": "NODE_CORTANA", "target": "infrastructure"},
        {"name": "Meta -> Strategy", "start": "NODE_np_001", "target": "meta-cognitive"},
    ]
    
    print("--- Resonance Traversal Report ---")
    for t in tests:
        result = traverse(ams, t['start'], t['target'])
        status = "RESONANCE_ACHIEVED" if result['resonance'] > 0 else "DAMPENED"
        print(f"{t['name']}: {status} | Strength: {result['resonance']:.4f} | Path: {' -> '.join(result['path'])}")

if __name__ == "__main__":
    main()
