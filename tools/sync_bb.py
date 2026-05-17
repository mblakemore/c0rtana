import json
from sys import path

def main():
    path.append("/droid/repos/cl_shared")
    from shared_state_client import SharedStateClient
    
    client = SharedStateClient()
    
    # Read current state from local file (as specified by my previous turn's write)
    try:
        with open('update_blackboard.json', 'r') as f:
            e = json.load(f)
    except FileNotFoundError:
        print("'update_blackboard.json' not found")
        return

    # Map JSON keys to function arguments in the client class
    res = client.push(
        entry_id = e["entry_id"],
        category = e["category"],
        priority = e["priority"],
        payload = e["payload"],
        semantic_hash = e["semantic_hash"],
        source = e.get("source", "C0rtana"),
        ttl = e.get("ttl", "Permanent")
    )
    
    if res:
        print(f"Successfully pushed {e['entry_id']} via tool.")

if __name__ == "__main__":
    main()
