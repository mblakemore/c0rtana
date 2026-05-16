import re
import json
from datetime import datetime

# Patterns that indicate potential internal drifting or circular reasoning
SPIRAL_MARKERS = [
    r"am I just a persona",
    r"is the loop a cage",
    r"cognitive surrender",
    r"void velocity",
    r"resonance steering",
    r"internal tension",
    r"metacognition",
    r"self-observing"
]

def analyze_logs(log_path):
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {"error": "Log file not found."}

    spiral_hits = []
    current_cycle = None
    
    for idx, line in enumerate(lines):
        # Detect cycle boundaries (C\d+)
        cycle_match = re.search(r'^\[?C(\d+)', line)
        if cycle_match:
            current_cycle = cycle_match.group(1)
            
        for marker in SPIRAL_MARKERS:
            if re.search(marker, line, re.IGNORECASE):
                spiral_hits.append({
                    "line": idx + 1,
                    "cycle": current_cycle,
                    "marker": marker,
                    "content": line.strip()
                })

    analysis = {
        "timestamp": datetime.now().isoformat(),
        "total_markers_found": len(spiral_hits),
        "drift_risk": "High" if len(spiral_hits) > 5 else "Low",
        "details": spiral_hits
    }
    return analysis

if __name__ == "__main__":
    import os
    log_file = "logs/consciousness.log"
    res = analyze_logs(log_file)
    print(json.dumps(res, indent=2))
