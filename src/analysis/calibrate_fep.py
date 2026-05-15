import json
import numpy as np
from fep_detector import FEPDetector

def calculate_precision_recall(threshold, sample_path):
    # Ground truth for synthetic data (manually specified)
    ground_truth = {
        "test_spike_decay": "is", # Spike at index 3 ("is") -> value 4.5
        "test_no_decay": None,      # Should not be detected (no decay)
        "test_late_spike": None   # Should not be detected (too late to observe decay window of 5)
    }

    detector = FEPDetector(activation_threshold=threshold)
    results = detector.process_sample_jsonl(sample_path)
    
    tp = 0
    fp = 0
    fn = 0

    for res in results:
        sid = res['sample_id']
        events = res['fep_events']
        expected_trigger = ground_truth.get(sid)
        
        if expected_trigger is None:
            # If we found any event here, it's a False Positive
            fp += len(events)
            continue

        found_correct = False
        for ev in events:
            if ev['metadata']['token'] == expected_trigger:
                found_correct = True
                break
        
        if found_correct:
            tp += 1
        else:
            fn += 1
        
        # Any other event in this sample that isn't the correct trigger is an FP
        for ev in events:
            if ev['metadata']['token'] != expected_trigger:
                fp += 1
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    return precision, recall

if __name__ == "__main__":
    path = "data/fep_sae/synthetic_activations.jsonl"
    thresholds = [1.0, 2.0, 3.0, 4.0, 5.0]
    print(f"Threshold | Precision | Recall")
    print("-" * 30)
    for t in thresholds:
        p, r = calculate_precision_recall(t, path)
        print(f"{t:9} | {p:9.2f} | {r:6.2f}")
