import sys
import json
import statistics
from collections import Counter

def analyze_numeric(data):
    """Perform basic statistical analysis on numeric lists."""
    if not data: return {}
    try:
        return {
            "count": len(data),
            "min": min(data),
            "max": max(data),
            "mean": round(statistics.mean(data), 4),
            "median": statistics.median(data),
            "stdev": round(statistics.stdev(data), 4) if len(data) > 1 else 0,
        }
    except (TypeError, statistics.StatisticsError):
        return {"error": "Non-numeric data provided"}

def analyze_categorical(data):
    """Analyze distribution of categorical strings."""
    if not data: return {}
    counts = Counter(data)
    total = len(data)
    return {
        "top_values": {val: count for val, count in counts.most_common(5)},
        "unique_count": len(counts),
        "distribution_pct": {val: round((cnt/total)*100, 2) for val, cnt in counts.items()}
    }

def process_jsonl(filepath):
    """Read a JSONL file and synthesize a summary report by field."""
    results = {}
    fields_data = {}
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                obj = json.loads(line)
                for k, v in obj.items():
                    if k not in fields_data: fields_data[k] = []
                    fields_data[k].append(v)
        
        for field, values in fields_data.items():
            # Sample the first value to determine type (heuristic)
            sample = values[0] if values else None
            if isinstance(sample, (int, float)):
                results[field] = analyze_numeric([x for x in values if isinstance(x, (int, float))])
            elif isinstance(sample, str):
                results[field] = analyze_categorical([str(x) for x in values])
            else:
                results[field] = {"type": str(type(sample)), "note": "skipped analysis"}
                
        return results
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 data_synthesizer.py <jsonl_file>")
        sys.exit(1)
    
    path = sys.argv[1]
    summary = process_jsonl(path)
    print(json.dumps(summary, indent=2))
