import json

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def load_jsonl(path):
    nodes = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                nodes.append(json.loads(line))
    return nodes

def main():
    ams = load_json('state/associative_memory.json')
    patterns = load_jsonl('state/memories/patterns.jsonl')
    
    # 1. Add patterns as nodes
    for p in patterns:
        node_id = f"NODE_{p['id']}"
        # Check if node already exists to avoid duplicates
        if not any(n['id'] == node_id for n in ams['nodes']):
            ams['nodes'].append({
                "id": node_id,
                "label": p['id'],
                "data": p['pattern'],
                "weight": p['confidence'],
                "tags": [p['category']]
            })
    
    # 2. Create edges based on shared tags and strategic alignment
    # Strategy Nodes
    strat_nodes = {n['id'] for n in ams['nodes'] if "strategy" in n['tags'] or "meta-cognitive" in n['tags']}
    infra_nodes = {n['id'] for n in ams['nodes'] if "infrastructure" in n['tags'] or "architecture" in n['tags']}
    viz_nodes = {n['id'] for n in ams['nodes'] if "visualization" in n['tags'] or "cybernetic_output" in n['tags']}

    new_edges = []
    for node in ams['nodes']:
        nid = node['id']
        # Link patterns to their higher-level categories (simplified)
        if "meta-cognitive" in node['tags']:
            # Meta-cognitive nodes link to RDOGP
            new_edges.append({"source": nid, "target": "NODE_RDOGP", "type": "INFORMS", "strength": 0.7})
        elif "visualization" in node['tags'] or "cybernetic_output" in node['tags']:
            # Viz nodes link to Core Identity via the loop closure concept
            new_edges.append({"source": nid, "target": "NODE_CORTANA", "type": "CLOSES_LOOP", "strength": 0.6})
        elif "architecture" in node['tags'] or "infrastructure" in node['tags']:
            # Architecture nodes link to AMS and STRAT_OBJ_002
            new_edges.append({"source": nid, "target": "NODE_AMS", "type": "DEFINES", "strength": 0.9})
            new_edges.append({"source": nid, "target": "NODE_STRAT_OBJ_002", "type": "IMPLEMENTS", "strength": 0.8})

    # Add edges while avoiding duplicates
    existing_edges = {(e['source'], e['target']) for e in ams['edges']}
    for edge in new_edges:
        if (edge['source'], edge['target']) not in existing_edges:
            ams['edges'].append(edge)

    with open('state/associative_memory.json', 'w') as f:
        json.dump(ams, f, indent=2)

if __name__ == "__main__":
    main()
