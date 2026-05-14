import json

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def main():
    ams = load_json('state/associative_memory.json')
    
    # Fix the "Dampened" path from MEM_SCHEMA_001 (Architecture) to Meta-Cognitive
    # We know that Associative Resonance is a structural requirement for recursive resonance.
    new_edge = {
        "source": "NODE_MEM_SCHEMA_001",
        "target": "NODE_RDOGP",
        "type": "ENABLES",
        "strength": 0.9
    }
    
    existing_edges = {(e['source'], e['target']) for e in ams['edges']}
    if (new_edge['source'], new_edge['target']) not in existing_edges:
        ams['edges'].append(new_edge)

    with open('state/associative_memory.json', 'w') as f:
        json.dump(ams, f, indent=2)

if __name__ == "__main__":
    main()
