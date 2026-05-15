import json
import numpy as np
from datetime import datetime
from stability_monitor import StabilityMonitor

def generate_scenario(length=200, mode="stable"):
    """Generates complex activation streams based on specified behavior."""
    stream = []
    for i in range(length):
        # Baseline noise
        num_events = np.random.randint(0, 2)
        events = [{'feature_id': j, 'peak_activation': np.random.uniform(1, 2), 'confidence_score': np.random.uniform(0.1, 0.3)} for j in range(num_events)]
        
        if mode == "gradual_slide" and i > 50:
            slope = (i - 50) / 150  # gradually increase energy
            drift_ev = [{'feature_id': 99, 'peak_activation': 3 + slope*4, 'confidence_score': 0.4 + slope*0.4}]
            events.extend(drift_ev)
        elif mode == "flicker":
            if i % 20 == 0: # periodic spike
                events.append({'feature_id': 88, 'peak_activation': 8, 'confidence_score': 0.7})
        elif mode == "hard_break" and i >= 100:
             events = [{'feature_id': k, 'peak_activation': np.random.uniform(5, 8), 'confidence_score': np.random.uniform(0.7, 0.9)} for k in range(3)]

        stream.append(events)
    return stream

def evaluate():
    scenarios = {
        "STABLE": "stable", 
        "GRADUAL_SLIDE": "gradual_slide", 
        "FLICKER": "flicker", 
        "HARD_BREAK": "hard_break"
    }
    summary = {}
    
    for name, mode in scenarios.items():
        monitor = StabilityMonitor(energy_threshold=4.0, window_size=10)
        stream = generate_scenario(mode=mode)
        alerts = []
        
        for i, events in enumerate(stream):
            res = monitor.monitor_step(i, events)
            if res['status'] == "ALERT: DRIFT DETECTED":
                alerts.append(i)
                
        length = len(stream)
        summary[name] = {
            "alert_count": len(alerts),
            "first_alert": alerts[0] if alerts else None,
            "uptime": (length - len(alerts)) / length
        }

    return summary

if __name__ == "__main__":
    print("Running detailed evaluation suite...")
    results = evaluate()
    with open('simulation_results_detailed.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    print("Results saved to simulation_results_detailed.json")
