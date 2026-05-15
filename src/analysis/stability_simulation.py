import numpy as np
import json
from datetime import datetime
from stability_monitor import StabilityMonitor

def generate_simulated_stream(length=100, drift_point=None, drift_magnitude=2.0):
    """Generates synthetic activations simulating a transition from stable to drifted states."""
    stream = []
    for i in range(length):
        # Base noise (stable)
        num_events = np.random.randint(0, 3)
        events = [
            {'feature_id': j, 'peak_activation': np.random.uniform(1, 3), 'confidence_score': np.random.uniform(0.1, 0.4)}
            for j in range(num_events)
        ]
        
        # Inject Drift if we've hit the point
        if drift_point is not None and i >= drift_point:
            drift_events = [
                {'feature_id': k, 'peak_activation': np.random.uniform(4, 6), 'confidence_score': np.random.uniform(0.6, 0.9)}
                for k in range(np.random.randint(2, 5))
            ]
            events.extend(drift_events)
        
        stream.append(events)
    return stream

def run_experiment():
    # Setup experiments
    configs = [
        {"name": "Baseline Stable", "drift_point": None},
        {"name": "Rapid Shift", "drift_point": 20},
        {"name": "Late Decay", "drift_point": 70}
    ]
    
    results = {}
    
    for cfg in configs:
        # NEW MONITOR for EACH experiment to ensure zero state contamination
        monitor = StabilityMonitor(energy_threshold=5.0, window_size=10)
        stream = generate_simulated_stream(length=100, drift_point=cfg["drift_point"])
        log = []
        detected_at = None
        
        for i, events in enumerate(stream):
            res = monitor.monitor_step(i, events)
            log.append(res)
            if res['status'] == "ALERT: DRIFT DETECTED" and detected_at is None:
                detected_at = i
        
        results[cfg["name"]] = {
            "detected_at": detected_at,
            "actual_drift": cfg["drift_point"],
            "lag": (detected_at - cfg["drift_point"]) if (detected_at is not None and cfg["drift_point"] is not None) else None,
            "final_avg_energy": log[-1]['avg_energy']
        }
    
    return results

if __name__ == "__main__":
    print("Running Stability Transition Simulations...")
    data = run_experiment()
    print(json.dumps(data, indent=2))
    
    # Save for the agent to analyze later
    with open('src/analysis/simulation_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "metrics": data
        }, f, indent=2)
