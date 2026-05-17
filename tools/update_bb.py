import json
from datetime import datetime
import os

BLACKBOARD_PATH = "/droid/repos/cl_shared/blackboard_registry.json"

def push_entry(source, category, payload, priority=3, semantic_hash=None, ttl="Permanent"):
    timestamp = datetime.utcnow().isoformat() + "Z"
    if not os.path.exists(BLACKBOARD_PATH):
        entries = []
    else:
        try:
            with open(BLACKBOARD_PATH, "r") as f:
                entries = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            entries = []

    new_entry = {
        "entry_id": f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.urandom(4).hex()}",
        "timestamp": timestamp,
        "source": source,
        "category": category,
        "priority": priority,
        "ttl": ttl,
        "payload": payload,
        "semantic_hash": semantic_hash or str(hash(str(payload))),
        "status": "Active"
    }
    
    entries.append(new_entry)
    
    tmp_path = BLACKBOARD_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(entries, f, indent=2)
    os.replace(tmp_path, BLACKBOARD_PATH)
    return new_entry["entry_id"]

if __name__ == "__main__":
    import sys
    # Simple CLI for manual test if needed: python tools/update_bb.py "Source" "Category" "PayloadStr"
    if len(sys.argv) > 1:
        push_entry(sys.argv[1], sys.argv[2], sys.argv[3])
