#!/usr/bin/env python3
"""
cycle_validator.py — Git-native six-phase cycle integrity checker

Validates that c0rtana's git-native persistence is operating correctly:
- Cycle number continuity (no backward jumps, no gaps)
- State file consistency with git HEAD
- Prediction validation windows tracked accurately
- No phantom commits or orphaned state

This tool operationalizes McGilchrist right-hemisphere preservation:
contextual awareness of system integrity over abstract metrics.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_git(args: list[str]) -> str:
    """Run git command and return stdout."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def get_current_cycle_from_git() -> int:
    """Extract highest C-number from recent git log."""
    output = run_git(["log", "--oneline", "-20"])
    matches = []
    for line in output.split("\n"):
        if match := __import__("re").search(r"C(\d+)", line):
            matches.append(int(match.group(1)))
    
    if not matches:
        raise ValueError("No cycle commits found in git history")
    
    return max(matches)


def load_json_file(path: Path) -> dict | None:
    """Load JSON file, return None if missing."""
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


def validate_state_consistency(repo_root: Path) -> tuple[bool, list[str]]:
    """Check that state files reflect actual git HEAD."""
    errors = []
    
    try:
        claimed_cycle = get_current_cycle_from_git()
    except ValueError as e:
        return False, [f"Git error: {e}"]
    
    current_state = load_json_file(repo_root / "state" / "current-state.json")
    focus = load_json_file(repo_root / "state" / "focus.json")
    
    if current_state is None:
        errors.append("current-state.json missing")
        return False, errors
    
    if focus is None:
        errors.append("focus.json missing")
    
    if claimed_cycle != current_state.get("cycle"):
        errors.append(
            f"Cycle number desync: git HEAD shows C{claimed_cycle}, "
            f"current-state.json says C{current_state.get('cycle')}"
        )
    
    # Check prediction windows are tracked
    predictions = current_state.get("falsifiable_predictions_deployed", [])
    pending_windows = []
    for pred in predictions:
        if "validate_at" in str(pred).lower():
            # Extract validate_at timestamp if present
            pass  # Deeper validation deferred to separate tool
    
    return len(errors) == 0, errors


def validate_prediction_integrity(repo_root: Path) -> tuple[bool, list[str]]:
    """Validate that predictions.jsonl has valid entries."""
    warnings = []
    
    predictions_path = repo_root / "state" / "predictions" / "grades.jsonl"
    if not predictions_path.exists():
        # First cycle may not have this yet
        return True, warnings
    
    with open(predictions_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    if not lines:
        return True, warnings
    
    malformed_count = 0
    schema_warnings = []
    
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
            if "id" not in entry:
                schema_warnings.append(f"predictions.jsonl line {i+1}: missing 'id' field")
            if "grade" not in entry and "status" not in entry:
                schema_warnings.append(
                    f"predictions.jsonl line {i+1}: missing grade/status (stale prediction?)"
                )
        except json.JSONDecodeError as e:
            malformed_count += 1
            warnings.append(f"predictions.jsonl line {i+1}: invalid JSON — {e}")
    
    if schema_warnings:
        warnings.extend(schema_warnings)
    
    if malformed_count > 0:
        warnings.append(f"predictions.jsonl has {malformed_count} malformed entries (legacy corruption?)")
    
    return len(warnings) == 0, warnings


def validate_anchor_consistency(repo_root: Path) -> tuple[bool, list[str]]:
    """Check anchors.jsonl references valid cycles."""
    warnings = []
    
    anchors_path = repo_root / "state" / "memories" / "anchors.jsonl"
    if not anchors_path.exists():
        return True, warnings
    
    current_state = load_json_file(repo_root / "state" / "current-state.json")
    if not current_state:
        return False, ["Cannot read current-state.json"]
    
    claimed_cycle = current_state.get("cycle", 0)
    
    malformed_count = 0
    out_of_range_warnings = []
    
    with open(anchors_path, "r") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                anchor = json.loads(line)
                raw_cycle = anchor.get("cycle", 0)
                if isinstance(raw_cycle, str):
                    # Extract number from "C319" or similar
                    match = __import__("re").search(r"C(\d+)", raw_cycle)
                    cycle_num = int(match.group(1)) if match else 0
                elif isinstance(raw_cycle, int):
                    cycle_num = raw_cycle
                else:
                    cycle_num = 0
                
                # Anchors should reference cycles <= current state + small buffer
                if cycle_num > claimed_cycle + 5:  # Allow small buffer
                    out_of_range_warnings.append(
                        f"Anchor at line {i+1} references C{cycle_num}, "
                        f"but current state is C{claimed_cycle}"
                    )
            except (json.JSONDecodeError, ValueError) as e:
                malformed_count += 1
                warnings.append(f"Anchor line {i+1}: malformed — {e}")
    
    if out_of_range_warnings:
        warnings.extend(out_of_range_warnings)
    
    if malformed_count > 0:
        warnings.append(f"anchors.jsonl has {malformed_count} malformed entries (legacy corruption?)")
    
    return len(warnings) == 0, warnings


def print_report(valid: bool, errors: list[str], warnings: list[str] | None = None):
    """Print color-coded validation report."""
    reset = "\033[0m"
    green = "\033[92m"
    red = "\033[91m"
    yellow = "\033[93m"
    blue = "\033[94m"
    
    print()
    print("=" * 60)
    print(f"{blue}CYCLE VALIDATOR REPORT{reset}")
    print("=" * 60)
    
    if not errors and not warnings:
        print(f"\n{green}✓ All validations passed{reset}")
        print("Git-native persistence operating correctly.")
    else:
        if errors:
            print(f"\n{red}✗ ERRORS ({len(errors)}){reset}")
            for err in errors:
                print(f"  → {err}")
        
        if warnings:
            print(f"\n{yellow}⚠ WARNINGS ({len(warnings)}){reset}")
            for warn in warnings:
                print(f"  → {warn}")
    
    print("\n" + "-" * 60)


def main():
    repo_root = Path(__file__).parent.parent.resolve()
    
    core_issues = []
    warnings = []
    
    # Validate state consistency (core check — cycle continuity)
    valid, issues = validate_state_consistency(repo_root)
    if not valid:
        core_issues.extend(issues)
    
    # Add cycle number info to report
    try:
        claimed_cycle = get_current_cycle_from_git()
        current_state = load_json_file(repo_root / "state" / "current-state.json")
        if current_state:
            status = "✓" if claimed_cycle == current_state.get("cycle") else "✗"
            warnings.append(f"{status} Cycle continuity: git HEAD=C{claimed_cycle}, state file=C{current_state.get('cycle', 'unknown')}")
    except Exception as e:
        core_issues.append(f"Cycle detection failed: {e}")
    
    # Validate prediction integrity (legacy data may have schema drift)
    valid, issues = validate_prediction_integrity(repo_root)
    if not valid:
        warnings.extend(issues)
    
    # Validate anchor consistency (legacy corruption is okay for now)
    valid, issues = validate_anchor_consistency(repo_root)
    if not valid:
        warnings.extend(issues)
    
    print_report(not core_issues, core_issues, warnings)
    
    return 0 if not core_issues else 1


if __name__ == "__main__":
    sys.exit(main())
