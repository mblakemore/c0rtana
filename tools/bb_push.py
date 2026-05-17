import json
import os
from datetime import datetime

BLACKBOARD_PATH = "/mnt/droid/repos/lyla/state/blackboard_registry.json"

def append_entry(source, category, priority, payload, semantic_hash, ttl="Permanent"):
    if not os.path.exists(BLACKBOARD_PATH):
        print(f"Error: Blackboard file not found at {BLACKBOARD_PATH}")
        return False
    
    try:
        with open(BLACKBOARD_PATH, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        data = []

    # Simple ID generation: use current timestamp + source hash if possible, 
    # but here we just take cycle from input or generate uuid
    entry_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"

    new_entry = {
        "entry_id": entry_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": source,
        "category": category,
        "priority": int(priority),
        "ttl": ttl,
        "payload": payload,
        "semantic_hash": semantic_hash,
        "status": "Active"
    }

    data.append(new_entry)
    
    try:
        with open(BLACKBOARD_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully pushed entry {entry_id} to Blackboard.")
        return True
    except IOError as e:
        print(f"Failed to write to blackboard: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 6:
        print("Usage: python bb_push.py <source> <category> <priority> <semantic_hash> '<payload_json>'")
        sys.exit(1)
    
    src = sys.argv[1]
    cat = sys.argv[2]
    prio = sys.argv[3]
    shash = sys.argv[4]
    try:
        pay = json.loads(sys.argv[5])
    except json.JSONDecodeError:
        pay = {"text": sys.argv[5]}
        
    append_entry(src, cat, prio, pay, shash)
