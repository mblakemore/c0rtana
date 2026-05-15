import json
import sys
from collections import defaultdict

def load_patterns(path):
    patterns = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                patterns.append(json.loads(line))
    return patterns

def find_redundancies(patterns):
    """
    Simple heuristic for finding redundant patterns based on category and keywords.
    In a more advanced version, this would use embeddings or LLM-based similarity.
    """
    clusters = defaultdict(list)
    for p in patterns:
        cat = p.get('category', 'unknown')
        # Use content snippets to group things that look similar
        text = (p.get('pattern', '') + ' ' + p.get('id', '')).lower()
        # Simple keyword clustering for demo purposes of the protocol's structure
        if 'meta' in text or 'loop' in text:
            tag = f"{cat}:cognitive"
        elif 'sync' in text or 'external' in text:
            tag = f"{cat}:external"
        else:
            tag = f"{cat}:{text[:20]}"
        clusters[tag].append(p)
    return clusters

def main():
    patterns_file = 'state/memories/patterns.jsonl'
    try:
        patterns = load_patterns(patterns_file)
        print(f"Loaded {len(patterns)} patterns.")
        
        clusters = find_redundancies(patterns)
        potential_merges = 0
        for tag, members in clusters.items():
            if len(members) > 1:
                print(f"[!] Potential redundancy cluster found: {tag} ({len(members)} items)")
                potential_merges += (len(members) - 1)
                for m in members:
                    print(f"  - {m['id']}: {m['pattern'][:60]}...")
        
        print(f"\nAnalysis complete. Found {potential_merges} potential redundancies.")
    except Exception as e:
        print(f"Error during HOP analysis: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
