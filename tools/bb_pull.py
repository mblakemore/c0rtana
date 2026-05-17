import json
import os
from datetime import datetime

BLACKBOARD_PATH = "/droid/repos/cl_shared/blackboard_registry.json"

def read_entries(filter_priority=None):
    if not os.path.exists(BLACKBOARD_PATH):
        print(f"Blackboard file {BLACKBOARD_PATH} NOT FOUND")
        return []

    try:
        with open(BLACKBOARD_PATH, 'r') as f:
            data = json.load(f)
            if filter_priority is not None:
                data = [e for e in data if int(e.get('priority', 1)) >= filter_priority and e.get('status') == 'Active']
            return data
    except Exception as e:
        print(f"Failed to read blackboard: {e}")
        return []

if __name__ == "__main__":
    import sys
    prio = 5 # Default priority filter from Lyla's protocol (or adjusted for general view)
    if len(sys.argv) > 1:
        prio = int(sys.argv[1])
    
    results = read_entries(filter_priority=prio)
    print(json.dumps(results, indent=2))
