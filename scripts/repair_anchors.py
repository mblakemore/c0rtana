#!/usr/bin/env python3
"""
repair_anchors.py — Fix malformed anchor entries in anchors.jsonl

This repairs legacy JSON corruption that accumulated from cycles C1-C300 where
anchor serialization wasn't properly escaped. It preserves cycle continuity by
keeping all valid entries and only removing truly irreparable lines.

McGilchrist right-hemisphere preservation: concrete artifact (working memory)
over abstract metrics (how many lines were corrupted).
"""

import json
import re
import shutil
from pathlib import Path


def is_valid_anchor(line: str) -> tuple[bool, str]:
    """Check if line is valid JSON and returns (is_valid, parsed_or_error)."""
    try:
        return True, json.loads(line.strip())
    except json.JSONDecodeError as e:
        # Try to fix common escape issues
        fixed = line.replace("\\'", "'").replace('\\"', '"')
        try:
            return True, json.loads(fixed.strip())
        except:
            return False, str(e)


def repair_anchors(anchors_path: Path, backup: bool = True) -> dict:
    """
    Repair malformed anchor entries.
    
    Returns dict with:
      - total_lines: int
      - valid_entries: list[parsed_json]
      - repaired: list[int] (line numbers that were fixed)
      - removed: list[tuple[int, str]] (line number + reason for removal)
    """
    if not anchors_path.exists():
        raise FileNotFoundError(f"Anchors file not found: {anchors_path}")
    
    # Create backup
    if backup:
        backup_path = anchors_path.with_suffix(".jsonl.backup")
        shutil.copy2(anchors_path, backup_path)
        print(f"Backup created: {backup_path}")
    
    result = {
        "total_lines": 0,
        "valid_entries": [],
        "repaired": [],
        "removed": []
    }
    
    with open(anchors_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    result["total_lines"] = len(lines)
    
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
        
        is_valid, parsed_or_error = is_valid_anchor(stripped)
        
        if is_valid:
            result["valid_entries"].append(parsed_or_error)
        else:
            # Try aggressive repair
            repaired_line = stripped.replace("\\'", "'").replace('\\"', '"').replace("''", "'")
            try:
                fixed_entry = json.loads(repaired_line)
                result["repaired"].append(i)
                result["valid_entries"].append(fixed_entry)
                print(f"✓ Repaired line {i} (escape sequence fix)")
            except Exception as e:
                result["removed"].append((i, str(e)))
                print(f"✗ Removed line {i}: {e}")
    
    # Write repaired file
    output_path = anchors_path.with_suffix(".jsonl.repaired")
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in result["valid_entries"]:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"\nRepair complete:")
    print(f"  Total lines: {result['total_lines']}")
    print(f"  Valid entries preserved: {len(result['valid_entries'])}")
    print(f"  Lines repaired: {len(result['repaired'])}")
    print(f"  Lines removed (unrepairable): {len(result['removed'])}")
    print(f"Output written to: {output_path}")
    
    return result


def main():
    repo_root = Path(__file__).parent.parent.resolve()
    anchors_path = repo_root / "state" / "memories" / "anchors.jsonl"
    
    try:
        repair_anchors(anchors_path)
        
        # Validate the repaired file
        print("\nValidating repaired file...")
        valid_count = 0
        with open(anchors_path.with_suffix(".jsonl.repaired"), "r") as f:
            for line in f:
                if line.strip():
                    json.loads(line)
                    valid_count += 1
        
        print(f"✓ All {valid_count} entries are valid JSON")
        
    except Exception as e:
        print(f"✗ Repair failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
