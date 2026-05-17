import json
import os
from datetime import datetime

# Updated path for shared storage
BLACKBOARD_PATH = "/droid/repos/cl_shared/blackboard_registry.json"

def append_entry(source, category, priority, payload, semantic_hash, ttl="Permanent"):
    if not os.path.exists("/droid/repos/cl_shared"):
        print(f"Error:Shared directory /droid/repos/cl_shared does not exist")
        return False

    if not os.path.exists(BLACKBOARD_PATH):
        try:
            with open(BLACKBOARD_PATH, 'w') as f:
                json.dump([], f)
        except IOError as e:
            print(f"Failed to initialize blackboard file: {e}")
            return False

    try:
        with open(BLACKBOARD_PATH, 'r+') as f:
            data = json.load(f)
            
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
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
            print(f"Successfully pushed entry {entry_id} to Shared Blackboard.")
            return True
    except (json.JSONDecodeError, IOError) as e:
        print(f"Blackboard operation failed: {e}")
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
