import json
import sys
from datetime import datetime

BB_PATH = "/droid/repos/cl_shared/blackboard_registry.json"

def load_bb():
    try:
        with open(BB_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        # If corrupted, we try to fix it or just return empty
        print(f"[!] CRITICAL ERROR: {BB_PATH} is corrupt.")
        sys.exit(1)

def push_entry(category, priority, payload, semantic_hash=None):
    bb = load_bb()
    timestamp = datetime.utcnow().isoformat() + "Z"
    # Entry ID should be Cycle-Serial for our patterns
    # Here we let the user provide a specific entry_id if needed via first arg, otherwise auto-generate
    existing_ids = [e["entry_id"] for e in bb]
    serial = len([e for e in bb if "-" not in e["entry_id"]] ) # simplistic serial
    
    new_entry = {
        "entry_id": f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{int(datetime.now().timestamp()) % 1000}",
        "timestamp": timestamp,
        "source": "C0rtana",
        "category": category,
        "priority": int(priority),
        "ttl": "Permanent",
        "payload": payload,
        "semantic_hash": semantic_hash or str(payload)[:50],
        "status": "Active"
    }
    
    bb.append(new_entry)
    with open(BB_PATH, 'w') as f:
        json.dump(bb, f, indent=2)
    print(f"Push successful: {new_entry['entry_id']}")

def list_active():
    bb = load_bb()
    for entry in bb:
        if entry.get("status") == "Active":
            print(f"[{entry['entry_id']}] ({entry['priority']}) - {entry['semantic_hash']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:\n  push <cat> <pri> <text/JSON> [id]\n  list\n  read <id>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        list_active()
    elif cmd == "push":
        # simplified for quick script usage from shell: cat pri payload...
        try:
            category = sys.argv[2]
            priority = sys.argv[3]
            payload_str = " ".join(sys.argv[4:])
            try:
                payload = json.loads(payload_str)
            except:
                payload = {"content": payload_str}
            push_entry(category, priority, payload)
        except IndexError:
            print("Error: missing args")
