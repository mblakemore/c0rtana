import json
import collections
from pathlib import Path
import os

def analyze_patterns(pattern_file='state/memories/patterns.jsonl'):
    patterns = []
    if not Path(pattern_file).exists():
        return {"error": f"Pattern file {pattern_file} not found"}

    with open(pattern_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                patterns.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse pattern line: {e}")
                continue

    # Map categories to count
    category_map = collections.defaultdict(int)
    tag_map = collections.defaultdict(int)
    
    for p in patterns:
        cat = p.get('category', 'unclassified')
        category_map[cat] += 1
        tags = p.get('tags', []) # Patterns might have tags list
        if isinstance(tags, list):
            for tag in tags:
                tag_map[tag] += 1

    # Expected domain benchmarks for a high-functioning agent
    expected_domains = [
        "meta-cognition", "agentic-loops", "external-sync", 
        "pattern-recognition", "state-persistence", "error-correction",
        "knowledge-mapping", "heuristic-optimization", "cybernetics", "visualization"
    ]
    
    holes = [domain for domain in expected_domains if category_map[domain] < 2]

    report = {
        "total_patterns": len(patterns),
        "category_distribution": dict(category_map),
        "tag_distribution": dict(tag_map),
        "identified_holes": holes,
        "analysis_timestamp": Path(pattern_file).stat().st_mtime if Path(pattern_file).exists() else None
    }
    
    return report

if __name__ == "__main__":
    # Ensure we are relative to repo root or handle paths correctly
    repo_root = os.getcwd() # assuming run from root
    results = analyze_patterns('state/memories/patterns.jsonl')
    
    output_path = 'state/knowledge_map.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=4)
        
    print(f"Cartography report generated at {output_path}")
    if "error" in results:
        print(f"Error: {results['error']}")
    else:
        print(f"Total patterns scanned: {results['total_patterns']}")
        print(f"Identified Holes (Variety Gaps): {results['identified_holes']}")
