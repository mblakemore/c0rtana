import os
import re
from pathlib import Path

class ConsistencyChecker:
    """
    Validates logical consistency across various config and state files in the C0rtana repo.
    Ensures that references to cycles and goals are not contradicting themselves.
    """
    def __init__(self):
        self.files_to_check = {
            "state/current-state.json": "cycle",
            "state/focus.json": "target",
            "AGENT.md": "Cognitive Loop"
        }
        self.errors = []

    def run(self):
        print("--- Starting Consistency Audit ---")
        
        # Check if focus target is present in current logic stream (consciousness.log)
        try:
            with open("state/focus.json", 'r') as f:
                import json
                focus = json.load(f).get('target', '')
            
            if focus:
                with open("logs/consciousness.log", 'r') as log:
                    content = log.read()
                    if focus.lower() not in content.lower():
                        self.errors.append(f"Focus gap: '{focus}' not mentioned in recent consciousness logs.")
        except Exception as e:
            self.errors.append(f"Error reading focus vs log: {e}")

        # Verify cycle numbering consistency
        try:
            with open("state/current-state.json", 'r') as f:
                import json
                curr_cycle = json.load(f).get('cycle')
            
            # Scan git history to ensure the latest commit matches state
            os.system(f"git log -1 --pretty=%B > .last_commit_msg")
            with open(".last_commit_msg", 'r') as f:
                msg = f.read()
                if curr_cycle and f"C{curr_cycle}" not in msg:
                    self.errors.append(f"State Cycle ({curr_cycle}) diverges from last Git commit message ({msg.strip()}).")
        except Exception as e:
             self.errors.append(f"Error verifying cycle integrity: {e}")
        finally:
            if os.path.exists(".last_commit_msg"):
                os.remove(".last_commit_msg")

        if not self.errors:
            print("✅ All structural invariants hold.")
            return True
        else:
            for err in self.errors:
                print(f"❌ {err}")
            return False

if __name__ == "__main__":
    checker = ConsistencyChecker()
    success = checker.run()
    exit(0 if success else 1)
