import json
import os
from collections import defaultdict

def calculate_conductivity(patterns_path):
    if not os.path.exists(patterns_path):
        print(f"Error: {patterns_path} not found.")
        return None

    nodes = []
    category_map = defaultdict(set)
    
    # Load patterns and map categories
    with open(patterns_path, 'r') as f:
        for line in f:
            try:
                pattern = json.loads(line)
                node_id = pattern.get('id', 'unknown')
                cat = pattern.get('category', 'uncategorized')
                nodes.append({'id': node_id, 'category': cat, 'text': pattern.get('pattern', '')})
                category_map[cat].add(node_id)
            except json.JSONDecodeError:
                continue

    num_nodes = len(nodes)
    if num_nodes < 2:
        print("Insufficient nodes for conductivity analysis.")
        return None

    edges = 0
    transversal_edges = 0
    potential_transversal_edges = 0
    
    # Compute edges based on category overlap (simulated semantic bridge via shared keywords/categories)
    # In this basic implementation, we treat the current category mapping as the primary structural driver.
    # We also check for keyword overlaps between different categories to find transversal bridges.
    
    # Simple Keyword-based Semantic Bridge
    def get_keywords(text):
        stopwords = {'the', 'and', 'a', 'of', 'to', 'in', 'is', 'it', 'that', 'with', 'as', 'for', 'on'}
        words = text.lower().split()
        return {w for w in words if len(w) > 3 and w not in stopwords}

    # Build node index for faster lookup
    node_data = {n['id']: n for n in nodes}
    all_keywords = {n['id']: get_keywords(n['text']) for n in nodes}

    # Iterate pairs to calculate connectivity
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            u = nodes[i]
            v = nodes[j]
            
            # Edge criteria: Shared category OR significant keyword overlap
            has_edge = False
            if u['category'] == v['category']:
                has_edge = True
            else:
                # Transversal bridge check: shared keywords between different categories
                overlap = all_keywords[u['id']] & all_keywords[v['id']]
                if len(overlap) >= 1:
                    has_edge = True
                    transversal_edges += 1
            
            if has_edge:
                edges += 1

    # Calculate potential transversal edges (sum of product of sizes of distinct category sets)
    categories = list(category_map.keys())
    for i in range(len(categories)):
        for j in range(i + 1, len(categories)):
            cat_a = categories[i]
            cat_b = categories[j]
            potential_transversal_edges += len(category_map[cat_a]) * len(category_map[cat_b])

    global_density = edges / (num_nodes * (num_nodes - 1) / 2) if num_nodes > 1 else 0
    transversal_conductivity = transversal_edges / potential_transversal_edges if potential_transversal_edges > 0 else 0
    
    return {
        "total_nodes": num_nodes,
        "global_density": global_density,
        "transversal_conductivity": transversal_conductivity,
        "actual_transversal_edges": transversal_edges,
        "potential_transversal_edges": potential_transversal_edges,
        "category_distribution": {cat: len(nodes_in_cat) for cat, nodes_in_cat in category_map.items()}
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to patterns.jsonl")
    args = parser.parse_args()
    
    result = calculate_conductivity(args.input)
    if result:
        print(json.dumps(result, indent=2))
        # Save result to metrics folder
        output_path = "state/metrics/conductivity_C119.json"
        with open(output_path, 'w') as append_file:
            json.dump(result, append_file, indent=2)
    else:
        exit(1)
