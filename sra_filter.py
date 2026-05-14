import json
import sys

def calculate_resonance(pattern, threshold=0.28):
    """
    Calculates the resonance score based on structural utility.
    Logic: Confidence adjusted by category weighting.
    Category Weights: 'architecture'/'meta-cognitive' = 1.2, others = 0.8.
    """
    category_weights = {
        "architecture": 1.2,
        "meta-cognitive": 1.2,
        "operational": 1.0
    }
    
    category = pattern.get("category", "unknown")
    confidence = pattern.get("confidence", 0.0)
    weight = category_weights.get(category, 0.8)
    
    resonance_score = confidence * weight
    return resonance_score >= threshold, resonance_score

def filter_patterns(input_file, threshold=0.28):
    resonant_patterns = []
    
    try:
        with open(input_file, 'r') as f:
            for line in f:
                if not line.strip(): continue
                pattern = json.loads(line)
                is_resonant, score = calculate_resonance(pattern, threshold)
                if is_resonant:
                    pattern['resonance_score'] = score
                    resonant_patterns.append(pattern)
                    
        return resonant_patterns
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return []

if __name__ == "__main__":
    # Usage: python3 sra_filter.py state/memories/patterns.jsonl 0.28
    file_path = sys.argv[1] if len(sys.argv) > 1 else "state/memories/patterns.jsonl"
    thresh = float(sys.argv[2]) if len(sys.argv) > 2 else 0.28
    
    results = filter_patterns(file_path, thresh)
    print(f"--- SRA Filter Results (Threshold: {thresh}) ---")
    print(f"Resonant patterns found: {len(results)}")
    for p in results:
        print(f"Score: {p['resonance_score']:.3f} | ID: {p.get('id', 'Unknown')}")
