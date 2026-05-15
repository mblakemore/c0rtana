import json
import numpy as np
from stability_monitor import StabilityMonitor

def run_stability_test(input_path, output_path):
    with open(input_path, 'r') as f:
        stream = json.load(f)
    
    # We'll test with different thresholds to see the Sensitivity Curve
    thresholds = [1.0, 2.5, 4.0, 6.0]
    results = {}

    for t in thresholds:
        monitor = StabilityMonitor(energy_threshold=t, window_size=10)
        alerts = []
        for i, events in enumerate(stream):
            res = monitor.monitor_step(i, events)
            if "ALERT" in res['status']:
                alerts.append(i)
        
        results[str(t)] = {
            "total_tokens": len(stream),
            "alert_count": len(alerts),
            "drift_percentage": (len(alerts) / len(stream)) * 100,
            "first_alert": alerts[0] if alerts else None
        }

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Stability scan complete. Results written to {output_path}")

if __name__ == "__main__":
    run_stability_test('src/analysis/data/sample_stream.json', 'src/analysis/stability_report.json')
