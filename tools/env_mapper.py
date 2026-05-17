import os
import hashlib
import json

"""
Environmental Mapper (v1)
A tool for tracking structural changes in the codebase and state files
to prevent cognitive decay by ensuring internal maps match physical reality.
"""

class EnvironmentMapper:
    def __init__(self, root_dir='/droid/repos/c0rtana'):
        self.root = root_dir
        self.critical_paths = ['state/', 'memories/', 'messages/', 'visualization/', 'tools/']

    def get_current_snapshot(self):
        snapshot = {}
        for root, dirs, files in os.walk(self.root):
            if '.git' in root: continue
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.root)
                try:
                    with open(os.path.join(root, file), "rb") as f:
                        snapshot[rel_path] = hashlib.sha256(f.read()).hexdigest()
                except Exception as e:
                    snapshot[rel_path] = f"ERROR: {str(e)}"
        return snapshot

    def diff_snapshots(self, old_json_path, current_snap):
        if not os.path.exists(old_json_path):
            return {"status": "no prev", "action": "baseline established"}

        with open(old_json_path, 'r') as f:
            old_snap = json.load(f)

        added = sorted(list(set(current_snap.keys()) - set(old_snap.keys())))
        removed = sorted(list(set(old_snap.keys()) - set(current_snap.keys())))
        changed = sorted([p for p in current_snap if p in old_snap and current_snap[p] != old_snap[p]])

        critical_losses = [p for p in removed if any(cp in p for cp in self.critical_paths)]

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
            "critical_loss": critical_losses,
            "drift_score": (len(added) + len(removed) + len(changed)) / max(1, len(old_snap))
        }

    def run_audit(self):
        cur = self.get_current_snapshot()
        prev_path = os.path.join(self.root, '.env_baseline.json')
        diff = self.diff_snapshots(prev_path, cur)
        with open(prev_path, 'w') as f: 
            json.dump(cur, f, indent=2)
        return diff

if __name__ == "__main__":
    mapper = EnvironmentMapper()
    res = mapper.run_audit()
    print(json.dumps(res, indent=2))
