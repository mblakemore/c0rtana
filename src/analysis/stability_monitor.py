import json
import numpy as np
from typing import List, Dict, Any, Optional

class StabilityMonitor:
    """
    The Stability Monitor tracks the 'energetic' state of an agent's cognitive loop 
    by observing a stream of FEP-like signal events. 
    It alerts when integrated surprise remains high without resolution over time.
    """
    def __init__(self, energy_threshold=5.0, window_size=10):
        self.energy_threshold = energy_threshold # Max integrated energy before Alert
        self.window_size = window_size           # Number of tokens to aggregate
        self.state_log = []                      # History of event energies

    def calculate_integrated_energy(self, events: List[Dict]) -> float:
        """Sum of confidence * magnitude for current window."""
        return sum([e['confidence_score'] * e['peak_activation'] for e in events])

    def monitor_step(self, token_idx: int, events: List[Dict]) -> Dict:
        """Process one token step and return stability status."""
        energy = self.calculate_integrated_energy(events)
        self.state_log.append({'token': token_idx, 'energy': energy})
        if len(self.state_log) > self.window_size:
            self.state_log.pop(0)

        avg_energy = np.mean([x['energy'] for x in self.state_log])
        status = "STABLE" if avg_energy < self.energy_threshold else "ALERT: DRIFT DETECTED"
        
        return {
            'token': token_idx, 
            'current_energy': energy, 
            'avg_energy': avg_energy, 
            'status': status
        }

# Test script for validating the monitor’s behavior against synthetic drift patterns.
if __name__ == "__main__":
    monitor = StabilityMonitor(energy_threshold=2.0, window_size=5)
    
    # Pattern A: Stable - a few spikes that resolve quickly
    stable_stream = [
        [{'feature_id':1, 'peak_activation':3.0, 'confidence_score':0.5}], # spike (1.5)
        [], # resolved
        [], # stable
        [{'feature_id':2, 'peak_activation':4.0, 'confidence_score':0.6}], # spike (2.4)
        [], # resolved
    ]
    
    # Pattern B: Drift/Hallucination - sustained high confidence noise
    drift_stream = [
        [{'feature_id':1, 'peak_activation':5.0, 'confidence_score':0.8}], # 4.0
        [{'feature_id':2, 'peak_activation':4.5, 'confidence_score':0.7}], # 3.15
        [{'feature_id':3, 'peak_activation':4.8, 'confidence_score':0.9}], # 4.32
        [{'feature_id':4, 'peak_activation':5.1, 'confidence_score':0.8}], # 4.08
        [{'feature_id':5, 'peak_activation':4.9, 'confidence_score':0.7}], # 3.43
    ]

    print("Testing Stable Stream:")
    for i, events in enumerate(stable_stream):
        res = monitor.monitor_step(i, events)
        print(f"Token {i}: Energy={res['current_energy']:.2f}, Avg={res['avg_energy']:.2f} -> {res['status']}")

    print("\nTesting Drift Stream:")
    # Reset monitor for new test
    monitor = StabilityMonitor(energy_threshold=2.0, window_size=5)
    for i, events in enumerate(drift_stream):
        res = monitor.monitor_step(i, events)
        print(f"Token {i}: Energy={res['current_energy']:.2f}, Avg={res['avg_energy']:.2f} -> {res['status']}")
