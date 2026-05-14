import json
import os
from datetime import datetime

def calculate_resonance(pattern, context):
    """
    Simulates Selective Resonance Amplification (SRA).
    Resonance = (Structural Match * 0.7) + (Keyword Weight * 0.3)
    """
    # In this synthetic simulation, structural match is approximated by 
    # checking if the pattern belongs to critical categories or has high confidence.
    structural_score = 0.0
    if pattern.get('category') in ['architecture', 'meta-cognitive']:
        structural_score += 0.6
    if pattern.get('confidence', 0) > 0.9:
        structural_score += 0.4
    
    # Keyword weight based on common SRA terminology found in current focus
    keywords = ['sra', 'threshold', 'signal', 'noise', 'resonance', 'utility']
    text = pattern.get('pattern', '').lower()
    keyword_count = sum(1 for word in keywords if word in text)
    keyword_score = min(1.0, keyword_count / 3.0) # Normalized score
    
    return (structural_score * 0.7) + (keyword_score * 0.3)

def calibrate_threshold(patterns, target_retention=0.80):
    scores = []
    for p in patterns:
        # We use the pattern itself as context to simulate its "self-resonance"
        scores.append(calculate_resonance(p, p))
    
    if not scores:
        return None
    
    scores.sort(reverse=True)
    idx = int(len(scores) * target_retention)
    # Ensure index is within bounds
    idx = max(0, min(idx, len(scores) - 1))
    return scores[idx]

def main():
    patterns_file = 'state/memories/patterns.jsonl'
    if not os.path.exists(patterns_file):
        print("Patterns file not found.")
        return

    patterns = []
    with open(patterns_file, 'r') as f:
        for line in f:
            try:
                patterns.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    optimal_threshold = calibrate_threshold(patterns)
    
    print(f"Total Patterns analyzed: {len(patterns)}")
    if optimal_threshold is not None:
        print(f"Proposed SRA Optimal Threshold (80% Retention): {optimal_threshold:.4f}")
    else:
        print("Could not calculate threshold.")

if __name__ == '__main__':
    main()
