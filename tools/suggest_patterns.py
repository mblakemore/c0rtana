import json
import sys
import collections

def suggest_patterns(query, patterns_path='state/memories/patterns.jsonl', top_n=3):
    query_words = set(query.lower().split())
    scored_patterns = []

    try:
        with open(patterns_path, 'r') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    pattern = json.loads(line)
                    text = (pattern.get('pattern', '') + ' ' + pattern.get('category', '')).lower()
                    words = set(text.split())
                    score = len(query_words.intersection(words))
                    if score > 0:
                        scored_patterns.append((score, pattern))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return "Error: patterns.jsonl not found."

    scored_patterns.sort(key=lambda x: x[0], reverse=True)
    return [p[1] for p in scored_patterns[:top_n]]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/suggest_patterns.py 'query string'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    results = suggest_patterns(query)
    
    if isinstance(results, str):
        print(results)
    elif not results:
        print("No relevant patterns found.")
    else:
        for p in results:
            print(f"[{p['id']}] (Conf: {p['confidence']}) {p['pattern']}")
