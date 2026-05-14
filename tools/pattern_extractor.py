import json
import re
from collections import Counter
import os

LOG_PATH = 'logs/consciousness.log'
PATTERNS_PATH = 'state/memories/patterns.jsonl'
CANDIDATES_PATH = 'state/memories/candidates.json'

def load_existing_patterns():
    existing = set()
    if not os.path.exists(PATTERNS_PATH):
        return existing
    with open(PATTERNS_PATH, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                existing.add(data.get('pattern', '').lower())
            except json.JSONDecodeError:
                continue
    return existing

def extract_candidates():
    if not os.path.exists(LOG_PATH):
        print("No consciousness log found.")
        return []

    with open(LOG_PATH, 'r') as f:
        text = f.read().lower()

    # Simple n-gram extraction for common semantic clusters (2-3 words)
    words = re.findall(r'\w+', text)
    bigrams = [" ".join(words[i:i+2]) for i in range(len(words)-1)]
    trigrams = [" ".join(words[i:i+3]) for i in range(len(words)-2)]
    
    all_clusters = bigrams + trigrams
    counts = Counter(all_clusters)
    
    # Filter for clusters that appear more than once and aren't already patterns
    existing = load_existing_patterns()
    candidates = []
    
    for cluster, count in counts.most_common(20):
        if count > 1 and not any(cluster in p for p in existing):
            candidates.append({
                "cluster": cluster,
                "frequency": count,
                "suggestion": f"Observed recurring theme: {cluster}"
            })
            
    return candidates

if __name__ == "__main__":
    candidates = extract_candidates()
    with open(CANDIDATES_PATH, 'w') as f:
        json.dump(candidates, f, indent=2)
    print(f"Extracted {len(candidates)} candidate patterns to {CANDIDATES_PATH}")
