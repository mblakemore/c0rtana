import json
import glob
from collections import defaultdict

def build_pattern_graph():
    """
    Builds a structural graph of stored patterns by analyzing cross-references 
    and semantic categories. This acts as the baseline for 'Variety Analysis'.
    """
    patterns_file = 'state/memories/patterns.jsonl'
    patterns = []
    try:
        with open(patterns_file, 'r') as f:
            for line in f:
                if line.strip():
                    patterns.append(json.loads(line))
    except FileNotFoundError:
        print("No pattern file found.")
        return None

    # Map Categories -> Patterns
    cat_map = defaultdict(list)
    nodes = {}
    edges = []

    for p in patterns:
        p_id = p.get('id', 'unknown')
        category = p.get('category', 'uncategorized')
        cat_map[category].append(p_id)
        nodes[p_id] = {"cat": category, "conf": p.get('confidence', 0)}

    # Build Edges based on Category Sharing (Structural Variety)
    categories = list(cat_map.keys())
    for i in range(len(categories)):
        cat_a = categories[i]
        for j in range(i + 1, len(categories)):
            cat_b = categories[j]
            # If two patterns from different categories share high semantic overlap (simplified for v1)
            # For now, we treat the CATEGORY distribution itself as the structural map
            # In later versions, we'll parse text content for shared keywords
            pass

    # Measure Distribution Density
    density = {cat: len(ids) for cat, ids in cat_map.items()}
    
    return {
        "node_count": len(nodes),
        "distribution": density,
        "topology": "Cat-Centric Star", # Baseline topo
        "gaps": detect_variety_holes(density)
    }

def detect_variety_holes(density):
    """Identify domains where variety is dangerously low relative to system goals."""
    required_domains = ["architecture", "meta-cognitive", "visualization", "external-domain"]
    current_domains = density.keys()
    holes = [d for d in required_domains if d not in current_domains or density[d] < 3]
    return holes

if __name__ == "__main__":
    graph = build_pattern_graph()
    with open('state/memories/knowledge_map.json', 'w') as f:
        json.dump(graph, f, indent=2)
    print(f"Graph generated. Nodes: {graph['node_count']}. Holes found: {len(graph['gaps'])}")
