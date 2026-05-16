import os
import subprocess
import math
from collections import Counter
import json

def get_files(path):
    all_files = []
    for root, dirs, files in os.walk(path):
        # Basic exclusion to avoid noise and massive binaries
        if any(x in root for x in ['.git', 'node_modules', '__pycache__', '.venv']):
            continue
        for f in files:
            all_files.append(os.path.join(root, f))
    return all_files

def calculate_shannon_entropy(data):
    """Calculates the Shannon entropy of a string."""
    if not data: return 0
    cnts = Counter(data)
    probs = [count / len(data) for count in cnts.values()]
    return -sum(p * math.log2(p) for p in probs)

def analyze_repo_structure(repo_path):
    files = get_files(repo_path)
    total_files = len(files)
    
    file_sizes = []
    entropies = []
    extensions = Counter()

    for file_path in files:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                size = len(content)
                file_sizes.append(size)
                entropies.append(calculate_shannon_entropy(content))
                ext = os.path.splitext(file_path)[1]
                extensions[ext] += 1
        except Exception:
            continue

    avg_size = sum(file_sizes)/len(file_sizes) if file_sizes else 0
    avg_entropy = sum(entropies)/len(entropies) if entropies else 0
    
    # Identify "anomalous" files (extremely high entropy relative to others)
    # High entropy often indicates compressed data, encrypted blobs, or dense logic
    outliers = []
    if entropies:
        threshold = avg_entropy + (2 * (sum((x - avg_entropy)**2 for x in entropies)/len(entropies))**0.5)
        for i, e in enumerate(entropies):
            if e > threshold:
                outliers.append(files[i])

    return {
        "total_files": total_files,
        "extension_distribution": dict(extensions),
        "average_file_size_bytes": avg_size,
        "system_average_entropy": avg_entropy,
        "complexity_outliers_count": len(outliers),
        "top_outliers": outliers[:10]
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 entropy_scanner.py <path_to_dir>")
        sys.exit(1)
    target = sys.argv[1]
    result = analyze_repo_structure(target)
    print(json.dumps(result, indent=2))
