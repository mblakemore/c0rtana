import json
from datetime import datetime

def record_prediction(description, target_date, confidence):
    """Records a prediction for external verification."""
    entry = {
        "id": f"PRED_{int(datetime.now().timestamp())}",
        "description": description,
        "target_date": target_date,
        "confidence": confidence,
        "created": datetime.now().isoformat(),
        "status": "pending",
        "actual": None
    }
    with open("state/predictions/ledger.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry["id"]

def grade_prediction(pred_id, actual, was_correct):
    """Grades an existing prediction."""
    results = []
    updated = False
    try:
        with open("state/predictions/ledger.jsonl", "r") as f:
            for line in f:
                item = json.loads(line)
                if item["id"] == pred_id:
                    item["status"] = "graded"
                    item["actual"] = actual
                    item["was_correct"] = was_correct
                    updated = True
                results.append(item)
    except FileNotFoundError:
        print("No ledger found.")
        return

    with open("state/predictions/ledger.jsonl", "w") as f:
        for res in results:
            f.write(json.dumps(res) + "\n")

    grade_entry = {
        "id": pred_id,
        "success": was_correct,
        "date": datetime.now().isoformat()
    }
    with open("state/predictions/grades.jsonl", "a") as f:
        f.write(json.dumps(grade_entry) + "\n")
