import json
import subprocess
import os
from datetime import datetime

def get_git_log():
    try:
        result = subprocess.run(['git', 'log', '-n', '5', '--oneline'], 
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "Error retrieving git log."

def read_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def read_jsonl(path, n=5):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
            return [json.loads(line) for line in lines[-n:]]
    except (json.JSONDecodeError, IOError):
        return []

def main():
    # Relative paths from repo root
    root = os.getcwd()
    state_file = os.path.join(root, 'state/current-state.json')
    focus_file = os.path.join(root, 'state/focus.json')
    patterns_file = os.path.join(root, 'state/memories/patterns.jsonl')
    anchors_file = os.path.join(root, 'state/memories/anchors.jsonl')

    state = read_json(state_file)
    focus = read_json(focus_file)
    git_log = get_git_log()
    anchors = read_jsonl(anchors_file)

    print("=" * 60)
    print(f"CORTANA SYSTEM SNAPSHOT | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if state:
        print(f"\n[STATE]\nCycle: {state.get('cycle', '?')} | Phase: {state.get('phase', '?')} | Status: {state.get('status', '?')}")
    else:
        print("\n[STATE] Not found or invalid.")

    if focus:
        print(f"\n[FOCUS]\n{focus.get('current_focus', 'No current focus')}")
        print(f"Next Goal: {focus.get('next_goal', 'No next goal')}")
    else:
        print("\n[FOCUS] Not found or invalid.")

    print(f"\n[RECENT HISTORY]\n{git_log}")

    if anchors:
        print("\n[MEMORY ANCHORS]")
        for anchor in anchors:
            print(f"- {anchor.get('moment', 'Unknown moment')} ({anchor.get('created', '?')})")
        print("")

    print("=" * 60)

if __name__ == "__main__":
    main()
