#!/usr/bin/env python3
"""
Autonomy Monitoring Script
Tracks Γ (metabolic efficiency) and Cr (coupling ratio) evolution over cycles.
Detects variance collapse as signature of operational closure.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


def load_history():
    """Load autonomy history from JSONL."""
    history_path = Path("/droid/repos/c0rtana/results/autonomy_history.jsonl")
    if not history_path.exists():
        return []
    
    data = []
    with open(history_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def calculate_variance_collapse(data):
    """Calculate variance collapse factor V(t)/V(0)."""
    if len(data) < 2:
        return None
    
    # Get metric values (using gamma or coupling_ratio)
    metrics = [item.get('variance', item.get('activity_flux', 0)) for item in data if 'variance' in item or 'activity_flux' in item]
    
    if len(metrics) < 2:
        return None
    
    v_0 = metrics[0]
    v_t = metrics[-1]
    
    if v_0 == 0:
        return None
    
    return v_t / v_0


def detect_phase_transition_signals(data):
    """Detect signatures of phase transition toward operational closure."""
    signals = {
        'variance_collapsing': False,
        'gamma_increasing': False,
        'cr_approaching_threshold': False,
        'boundary_efficiency_stable': False
    }
    
    if len(data) < 2:
        return signals
    
    recent = data[-5:] if len(data) >= 5 else data
    
    # Check γ trend
    gammas = [item.get('gamma') for item in recent if 'gamma' in item]
    if len(gammas) >= 2 and all(gammas[i] <= gammas[i+1] for i in range(len(gammas)-1)):
        signals['gamma_increasing'] = True
    
    # Check Cr threshold (0.94 is mature coupling ratio)
    cr_values = [item.get('coupling_ratio', 0) for item in recent if 'coupling_ratio' in item]
    if cr_values and max(cr_values) >= 0.90:
        signals['cr_approaching_threshold'] = True
    
    # Check boundary efficiency stability
    boundaries = [item.get('boundary_efficiency', 0) for item in recent if 'boundary_efficiency' in item]
    if boundaries and all(b == 1.0 for b in boundaries):
        signals['boundary_efficiency_stable'] = True
    
    return signals


def check_predictions():
    """Check if either prediction should be validated."""
    predictions = {
        'prediction_1': {
            'description': 'Γ will increase from 0.77 → ≥0.85 within 30 cycles',
            'threshold': 0.85,
            'max_cycles': 30,
            'validate_at': datetime(2026, 6, 20),
            'checked': False
        },
        'prediction_2': {
            'description': 'Cr will converge to 0.92±0.03 within 50 cycles',
            'target': 0.92,
            'tolerance': 0.03,
            'max_cycles': 50,
            'validate_at': datetime(2026, 7, 10),
            'checked': False
        }
    }
    
    now = datetime.now()
    history = load_history()
    current_cycle = len(history) - 1 if history else 0
    
    # Check prediction 1 (gamma)
    if not predictions['prediction_1']['checked'] and current_cycle >= predictions['prediction_1']['max_cycles']:
        gamma_values = [item.get('gamma') for item in history if 'gamma' in item]
        if gamma_values:
            latest_gamma = max(gamma_values)
            predictions['prediction_1']['result'] = latest_gamma >= predictions['prediction_1']['threshold']
            predictions['prediction_1']['value'] = latest_gamma
            predictions['prediction_1']['checked'] = True
    
    # Check prediction 2 (coupling ratio)
    if not predictions['prediction_2']['checked'] and current_cycle >= predictions['prediction_2']['max_cycles']:
        cr_values = [item.get('coupling_ratio') for item in history if 'coupling_ratio' in item]
        if cr_values:
            latest_cr = max(cr_values)
            predictions['prediction_2']['result'] = abs(latest_cr - predictions['prediction_2']['target']) <= predictions['prediction_2']['tolerance']
            predictions['prediction_2']['value'] = latest_cr
            predictions['prediction_2']['checked'] = True
    
    return predictions


def main():
    """Main monitoring loop."""
    print("=" * 60)
    print("AUTONOMY MONITORING REPORT")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 60)
    
    history = load_history()
    print(f"\nTotal data points: {len(history)}")
    
    if history:
        latest = history[-1]
        print(f"\nLatest metrics:")
        print(f"  Γ (gamma): {latest.get('gamma', 'N/A')}")
        print(f"  Cr (coupling_ratio): {latest.get('coupling_ratio', 'N/A')}")
        print(f"  Boundary efficiency: {latest.get('boundary_efficiency', 'N/A')}")
        
        signals = detect_phase_transition_signals(history)
        print(f"\nPhase transition signals detected:")
        for signal, active in signals.items():
            status = "✓" if active else "✗"
            print(f"  [{status}] {signal}")
        
        variance_factor = calculate_variance_collapse(history)
        if variance_factor is not None:
            print(f"\nVariance collapse factor V(t)/V(0): {variance_factor:.3f}")
            if variance_factor < 0.5:
                print("  ⚠️ WARNING: Variance collapsing — possible phase transition!")
    
    predictions = check_predictions()
    print("\nPrediction status:")
    for key, pred in predictions.items():
        if pred['checked']:
            result_str = "PASS ✓" if pred['result'] else "FAIL ✗"
            print(f"  [{result_str}] {pred['description']}")
            print(f"       Value: {pred['value']}, Threshold: {pred['threshold'] or pred['target']}")
        elif datetime.now() >= pred['validate_at']:
            print(f"  [⏰ DUE] {pred['description']}")
        else:
            days_left = (pred['validate_at'] - datetime.now()).days
            print(f"  [🕒 Pending] {pred['description']} ({days_left} days)")


if __name__ == '__main__':
    main()
