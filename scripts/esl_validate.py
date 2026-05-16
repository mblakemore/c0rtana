import json, datetime, requests

LEDGER_FILE = "state/external_signal_ledger.jsonl"
GRADES_FILE = "state/predictions/grades.jsonl"

def load_jsonl(path):
    data = []
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try: data.append(json.loads(line))
                except: pass
    except FileNotFoundError: pass
    return data

def main():
    print("--- ESL Validation Process Start ---")
    current_signals = {}
    try:
        r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5)
        if r.status_code == 200:
             val = float(r.json()['data']['amount'])
             current_signals["S&P500_PRICE"] = val
             print(f"Current Sensor (S&P500_PRICE alias BTC): {val}")
    except Exception as e:
        print(f"Sensor Fetch Failed: {e}")

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ledger = load_jsonl(LEDGER_FILE)
    graded_this_run = 0

    with open(GRADES_FILE, "a") as grades_out:
        for i, entry in enumerate(ledger):
            preds = entry.get("predictions", {})
            if not preds: continue
            
            for signal, p in preds.items():
                expiry = p.get("validate_at")
                if not expiry: continue
                
                # Log the check regardless of outcome for debugging’s sake during this C183 build phase
                print(f"Checking prediction {p.get('id')} - Expiry: {expiry} | Now: {now}", end=" -> ")

                if now >= expiry:
                    actual = current_signals.get(signal)
                    target = p.get("value")
                    tol = p.get("tolerance", 0)
                    success = False
                    
                    if actual is not None and target is not None:
                        if isinstance(target, (int, float)) and abs(target - actual) <= tol: success = True
                        elif str(target) == str(actual): success = True
                    
                    grade = {"timestamp": now, "prediction_id": p.get("id"), "expected": target, "actual": actual, "outcome": "PASS" if success else "FAIL"}
                    grades_out.write(json.dumps(grade) + "\n")
                    graded_this_run += 1
                    print("GRADED")
                else:
                    print("PENDING")

    print(f"--- Validated {graded_this_run} entries. ---")

if __name__ == "__main__": main()
