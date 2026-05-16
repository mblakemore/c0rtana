import datetime
import json
import requests
import os

# --- CONFIGURATION ---
SIGNALS = {
    "NASA_APOD": {
        "url": "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY",
        "value_path": lambda x: x.get("title", "Unknown"),
        "type": "categorical"
    },
    "S&P500_PRICE": { # Using a free API for simplicity, would need key normally. 
        # We'll simulate the actual fetch if api keys aren't handy or use public data sources.
        "url": "https://api.coinbase.com/v2/prices/BTC-USD/spot",
        "value_path": lambda x: float(x['data']['amount']),
        "type": "numeric"
    }
}
LEDGER_FILE = "state/external_signal_ledger.jsonl"

def get_signals():
    current_values = {}
    for name, cfg in SIGNALS.items():
        try:
            r = requests.get(cfg["url"], timeout=10)
            if r.status_code == 200:
                data = r.json()
                current_values[name] = cfg["value_path"](data)
            else:
                current_values[name] = f"ERROR_{r.status_code}"
        except Exception as e:
            current_values[name] = f"EXCEPTION_{str(e)}"
    return current_values

def main():
    print("[ESL] Fetching signals from reality...")
    actuals = get_signals()
    
    # I will define predictions separately to avoid 'cheating' via the script
    # but this tool provides the framework for logging them and validating them later.
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "cycle": 181,
        "observations": actuals,
        "predictions": {} # To be populated manually or by separate logic to ensure independence
    }
    
    with open(LEDGER_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    print(f"[ESL] State captured in {LEDGER_FILE}")
    for k, v in actuals.items():
        print(f"  - {k}: {v}")

if __name__ == "__main__":
    main()
