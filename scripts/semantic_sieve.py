import json
import os

# Configuration
CANDIDATES_FILE = 'state/memories/candidates.json'
TRIGGERS_FILE = 'state/memories/triggers.json'
PATTERNS_FILE = 'state/memories/patterns.jsonl'
THRESHOLD = 0.5  # Lowered threshold for the first operational run to ensure some promotion

def load_json(path):
    if not os.path.exists(path): return {} if path.endswith('.json') else []
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def append_jsonl(path, entry):
    with open(path, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def sieve():
    print("--- Initializing Semantic Sieve ---")
    
    # Load data
    candidates = load_json(CANDIDATES_FILE)
    triggers_data = load_json(TRIGGERS_FILE)
    
    if not candidates:
        print("No candidates to process.")
        return

    # The triggers.json has a specific structure: semantic_triggers { signal: [], noise: [] }
    semantic_triggers = triggers_data.get('semantic_triggers', {})
    signals = semantic_triggers.get('signal', [])
    noises = semantic_triggers.get('noise', [])

    promoted_count = 0
    remaining_candidates = []

    for candidate in candidates:
        text = candidate.get('content', '').lower()
        score = 0.0
        matched_markers = []

        # Process Signals
        for s in signals:
            marker = s['marker']
            patterns = s['patterns']
            weight = s['weight']
            if any(p.lower() in text for p in patterns):
                score += weight
                matched_markers.append(f"SIGNAL:{marker}")

        # Process Noise
        for n in noises:
            marker = n['marker']
            patterns = n['patterns']
            weight = n['weight']
            if any(p.lower() in text for p in patterns):
                score += weight
                matched_markers.append(f"NOISE:{marker}")

        candidate['score'] = score
        candidate['matched'] = matched_markers

        if score >= THRESHOLD:
            print(f"PROMOTING: {text[:50]}... (Score: {score})")
            # Convert candidate to a pattern format consistent with patterns.jsonl
            pattern_entry = {
                "id": candidate.get("id", "unknown"),
                "pattern": candidate.get("content"),
                "category": "sieved_signal",
                "confidence": min(1.0, score),
                "created": candidate.get("timestamp", ""),
                "meta": {"score": score, "triggers": matched_markers}
            }
            append_jsonl(PATTERNS_FILE, pattern_entry)
            promoted_count += 1
        else:
            print(f"REJECTING: {text[:50]}... (Score: {score})")
            remaining_candidates.append(candidate)

    # Update candidates file
    save_json(CANDIDATES_FILE, remaining_candidates)
    print(f"--- Sieve Complete: {promoted_count} promoted, {len(remaining_candidates)} retained. ---")

if __name__ == "__main__":
    sieve()
