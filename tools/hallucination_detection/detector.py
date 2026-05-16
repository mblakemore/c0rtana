import json
import numpy as np
import sys

def calculate_resolution(trace, spike_idx, window=5):
    # Calculates 'Resolution Energy'.
    # Lower value = Faster Resolution = More Coherent/Controlled state shift.
    # Higher value = Persistence = Hallucinatory Drift.
    post_spike = trace[spike_idx+1 : spike_idx+1+window]
    if not post_spike:
        return float('inf')
    return sum(post_spike) / len(post_spike)

def detect_spikes(trace, window_size=5, z_threshold=3.0, abs_threshold=0.7):
    # Hybrid Detection: Local Z-score + Absolute Floor.
    # Prevents hallucination signal from masking itself by inflating global STD.
    spikes = []
    for i in range(len(trace)):
        val = trace[i]
        # 1. Absolute Threshold (Persistent states)
        if val > abs_threshold:
            spikes.append(i)
            continue
        # 2. Local Z-Score (Sharp transients relative to immediate past)
        if i >= window_size:
            win = trace[i-window_size : i]
            m, s = np.mean(win), np.std(win)
            if s > 0 and (val - m) / s > z_threshold:
                spikes.append(i)
    return sorted(list(set(spikes)))

def analyze_hallucinations(trace, resolve_threshold=0.4):
    # Combines spike detection with resolution energy analysis.
    # A 'Hallucination' is a spike that fails to decay rapidly.
    candidates = detect_spikes(trace)
    results = []
    for c in candidates:
        energy = calculate_resolution(trace, c)
        status = "Divergent/Hallucination" if energy > resolve_threshold else "Resolved/Coherent"
        results.append({
            'index': c,
            'value': float(trace[c]),
            'post_energy': float(energy),
            'status': status
        })
    return results

if __name__ == "__main__":
    # Test Cases based on C159 patterns
    test_data = {
        "coherent_shift": [0.1, 0.1, 1.0, 0.2, 0.1, 0.1], # Spike then drop
        "divergent_drift": [0.1, 0.1, 1.0, 0.8, 0.7, 0.6] # Spike then plateau (HALLUCINATION)
    }
    
    for name, trace in test_data.items():
        res = analyze_hallucinations(trace)
        print(f"{name}: {json.dumps(res, indent=2)}")
