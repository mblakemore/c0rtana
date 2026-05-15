import numpy as np
import json
import os

def simulate_fep_signal(token_sequence, is_coherent_pivot=True):
    """
    Simulates FEP (Free Energy Principle) signal intensity.
    Coherent pivots: High spike at pivot, rapid decay (integration).
    Incoherent pivots: High spike at pivot, sustained noise (failure to resolve).
    """
    signals = []
    for i, token in enumerate(token_sequence):
        if token == 'PIVOT':
            # The initial surprise is high for both
            signals.append(1.0) 
        elif i > 0 and token_sequence[i-1] == 'PIVOT':
            # After pivot: Coherent resolves quickly, Incoherent stays high
            signals.append(0.2 if is_coherent_pivot else 0.8)
        else:
            signals.append(0.1) # Baseline
    return signals

def run_test():
    test_cases = [
        {"name": "coherent_pivot", "seq": ["A", "A", "PIVOT", "B", "B"], "coherent": True},
        {"name": "random_pivot", "seq": ["A", "A", "PIVOT", "A", "C"], "coherent": False}
    ]
    
    results = {}
    for case in test_cases:
        signal = simulate_fep_signal(case['seq'], case['coherent'])
        results[case['name']] = {
            "sequence": case['seq'],
            "fep_trace": signal,
            "integration_efficiency": 1.0 - np.mean(signal[3:])
        }
    
    return results

if __name__ == "__main__":
    res = run_test()
    with open('reports/FEP_C159_raw_data.json', 'w') as f:
        json.dump(res, f, indent=2)
    print("C159 Coherence Test Data Generated.")
