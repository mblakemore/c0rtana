import os
import math
from pathlib import Path

def calculate_repo_complexity(root_path):
    """
    Calculate a simplistic measure of directory complexity.
    Using Ratio = total_files / log(total_dirs + 1) * constant’s as a proxy for spread.
    Alternatively, use the depth average vs width ratio.
    """
    all_paths = []
    for root, dirs, files in os.walk(root_path):
        # Skip .git
        if '.git' in root: continue
        
        level = root.replace(root_path, '').count(os.sep)
        indent = ' ' * level
        all_paths.append((level, len(files)))

    total_files = sum([p[1] for p in all_paths])
    total_dirs = len(all_paths)
    avg_depth = sum([p[0] for p in all_paths]) / max(1, total_dirs)
    
    # Rough "Fractal Dimension" estimate: log(Files) / log(Depth+1)
    dim = math.log2(max(1, total_files)) / math.log2(max(1, avg_depth + 1)) if total_dirs > 0 else 0
    
    return {
        "total_files": total_files,
        "total_dirs": total_dirs,
        "avg_depth": round(avg_depth, 2),
        "complexity_score": round(dim, 3)
    }

if __name__ == "__main__":
    res = calculate_repo_complexity('.')
    print(f"Repo complexity stats: {res}")
