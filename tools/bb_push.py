import json
import os
from datetime import datetime

BLACKBOARD_PATH = "/droid/repos/cl_shared/blackboard_registry.json"

def push_entry(source, category, payload, priority=3, semantic_hash=None, ttl="Permanent"):
    timestamp = datetime.utcnow().isoformat() + "Z"
    try:
        with open("state/current-state.json", "r") as f:
            curr_cycle = json.load(f).get("cycle", "UNK")
    except Exception:
        curr_cycle = "UNK"
    
    entry_id = f"{curr_cycle}-{int(datetime.now().timestamp())}"
    
    new_entry = {
        "entry_id": entry_id,
        "timestamp": timestamp,
        "source": source,
        "category": category,
        "priority": int(priority),
        "ttl": ttl,
        "payload": payload,
        "semantic_hash": semantic_hash or str(payload)[:100],
        "status": "Active"
    }

    data = []
    if os.path.exists(BLACKBOARD_PATH):
        try:
            with open(BLACKBOARD_PATH, "r") as f:
                data = json.load(f)
                if not isinstance(data, list): data = [data]
        except Exception:
            data = []

    data.append(new_entry)
    try:
        with open(BLACKBOARD_PATH, "w") as f: json.dump(data, f, indent=2)
        print(f"Pushed {entry_id}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3: exit(1)
    push_entry("C0rtana", sys.argv[1], {"content": sys.argv[2]}, int(sys.argv[3]) if len(sys.argv)>3 else 3)
