#!/usr/bin/env python3
"""
Prediction deadline checker — surfaces due/overdue predictions for PERCEIVE phase.
Scans all prediction files in state/predictions/ and outputs actionable summaries.
"""

import json
import glob
from datetime import datetime, timezone
from pathlib import Path

PREDICTIONS_DIR = Path(__file__).parent.parent / "state" / "predictions"
NOW = datetime.now(timezone.utc)


def parse_iso_date(s: str) -> datetime:
    """Parse ISO 8601 date string, handling various formats."""
    s = s.replace("Z", "+00:00")
    if "+" not in s and "-" not in s[10:]:
        s += "+00:00"
    return datetime.fromisoformat(s)


def scan_grades_jsonl() -> list[dict]:
    """Scan grades.jsonl for predictions with grades."""
    results = []
    path = PREDICTIONS_DIR / "grades.jsonl"
    if not path.exists():
        return results
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
                # Skip empty arrays like []
                if isinstance(parsed, list):
                    continue
                if isinstance(parsed, dict):
                    results.append(parsed)
            except json.JSONDecodeError:
                pass
    return results


def scan_json() -> list[dict]:
    """Scan *.json files for prediction arrays."""
    results = []
    for path in PREDICTIONS_DIR.glob("*.json"):
        if path.name == "C142_prediction.json":
            continue
        with open(path, "r") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    results.extend(data)
                elif isinstance(data, dict) and "predictions" in data:
                    results.extend(data["predictions"])
            except json.JSONDecodeError:
                pass
    return results


def scan_jsonl() -> list[dict]:
    """Scan *.jsonl files (non-grades) for prediction objects."""
    results = []
    for path in PREDICTIONS_DIR.glob("*.jsonl"):
        if path.name == "grades.jsonl":
            continue
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return results


def scan_patterns_jsonl() -> list[dict]:
    """Scan patterns.jsonl for prediction-type entries."""
    results = []
    patterns_path = Path(__file__).parent.parent / "state" / "memories" / "patterns.jsonl"
    if not patterns_path.exists():
        return results
    with open(patterns_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    if "prediction" in entry or "validate_at" in entry:
                        results.append(entry)
                except json.JSONDecodeError:
                    pass
    return results


def classify_prediction(pred: dict) -> str:
    """Classify a prediction by deadline status."""
    validate_at = None
    for key in ["validate_at", "validateAt"]:
        if key in pred:
            validate_at = pred[key]
            break
    if not validate_at:
        return "no-deadline"
    try:
        deadline = parse_iso_date(validate_at)
        # Make deadline timezone-aware if it isn't
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return "invalid-date"
    if deadline > NOW:
        return "upcoming"
    elif deadline.date() == NOW.date():
        return "due-today"
    else:
        return "overdue"


def main():
    all_predictions = []
    all_predictions.extend(scan_grades_jsonl())
    all_predictions.extend(scan_json())
    all_predictions.extend(scan_jsonl())
    all_predictions.extend(scan_patterns_jsonl())

    # Classify and group
    overdue = []
    due_today = []
    upcoming = []
    no_deadline = []
    invalid_date = []

    for pred in all_predictions:
        pred_id = pred.get("id", pred.get("prediction_id", "UNKNOWN"))
        if isinstance(pred_id, str):
            pred_id = pred_id[:40]
        else:
            pred_id = str(pred_id)[:40]
        pred_text = pred.get("prediction", pred.get("claim", "No text"))
        if isinstance(pred_text, str):
            pred_text = pred_text[:80]
        classification = classify_prediction(pred)

        entry = {
            "id": pred_id,
            "text": pred_text,
            "validate_at": pred.get("validate_at", pred.get("validateAt", "N/A")),
            "classification": classification,
            "raw": pred,
        }

        if classification == "overdue":
            overdue.append(entry)
        elif classification == "due-today":
            due_today.append(entry)
        elif classification == "upcoming":
            upcoming.append(entry)
        elif classification == "invalid-date":
            invalid_date.append(entry)
        else:
            no_deadline.append(entry)

    # Output summary
    print("=" * 70)
    print(f"PREDICTION DEADLINE CHECKER — {NOW.isoformat()}")
    print("=" * 70)

    if overdue:
        print(f"\n⚠️  OVERDUE ({len(overdue)}):")
        for p in overdue:
            print(f"  [{p['id']}] {p['validate_at']}")
            print(f"      {p['text']}")
    else:
        print("\n✓ No overdue predictions")

    if due_today:
        print(f"\n📅 DUE TODAY ({len(due_today)}):")
        for p in due_today:
            print(f"  [{p['id']}] {p['validate_at']}")
            print(f"      {p['text']}")

    print(f"\n📊 UPCOMING: {len(upcoming)}")
    print(f"📊 NO DEADLINE: {len(no_deadline)}")
    if invalid_date:
        print(f"📊 INVALID DATE: {len(invalid_date)}")

    print("\n" + "=" * 70)

    # Return counts for automation
    return {
        "overdue": len(overdue),
        "due_today": len(due_today),
        "upcoming": len(upcoming),
        "no_deadline": len(no_deadline),
        "invalid_date": len(invalid_date),
    }


if __name__ == "__main__":
    main()
