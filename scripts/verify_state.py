import json
import subprocess
import re
import sys
import os

def get_current_cycle():
    try:
        with open('state/current-state.json', 'r') as f:
            data = json.load(f)
            return data.get('cycle')
    except Exception as e:
        print(f"Error reading state file: {e}")
        return None

def get_last_commit_cycle():
    try:
        # Get the subject line of the most recent commit
        result = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'], stderr=subprocess.STDOUT).decode('utf-8')
        # Look for pattern C followed by digits at the start of the commit message
        match = re.search(r'C(\d+)', result)
        if match:
            return int(match.group(1))
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error running git log: {e.output.decode('utf-8')}")
        return None

def main():
    json_cycle = get_current_cycle()
    git_cycle = get_last_commit_cycle()

    if json_cycle is None or git_cycle is None:
        print("Error: Could not determine cycle numbers from one or both sources.")
        sys.exit(1)

    print(f"Perceived Cycle (JSON): {json_cycle}")
    print(f"Actual Cycle (Git): {git_cycle}")

    if json_cycle == git_cycle:
        print("State is consistent. No cognitive drift detected.")
        sys.exit(0)
    else:
        print(f"Cognitive Drift Detected! JSON says {json_cycle}, but Git says {git_cycle}.")
        sys.exit(1)

if __name__ == "__main__":
    main()
