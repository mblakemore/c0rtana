import json
import sys
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class FEPEvent:
    feature_id: int
    start_token_idx: int
    end_token_idx: int
    peak_activation: float
    resolution_decay_rate: float
    confidence_score: float
    metadata: Dict[str, Any]

class FEPDetector:
    """
    Implementation of the FEP (Feature Error Propagation) detection protocol.
    
    The protocol identifies features that spike upon encountering an error 
    or ambiguity and then decay as the model "resolves" the state.
    """
    
    def __init__(self, activation_threshold: float = 2.0, decay_window: int = 5):
        self.activation_threshold = activation_threshold
        self.decay_window = decay_window

    def analyze_sequence(self, feature_activations: Dict[int, List[float]], token_labels: List[str]) -> List[FEPEvent]:
        events = []
        seq_len = len(token_labels)

        for fid, acts in feature_activations.items():
            acts = np.array(acts)
            spikes = np.where(acts > self.activation_threshold)[0]
            
            for start_idx in spikes:
                peak_idx = start_idx 
                peak_val = acts[peak_idx]
                end_idx = min(start_idx + self.decay_window, seq_len - 1)
                decay_segment = acts[start_idx : end_idx + 1]
                
                if len(decay_segment) < 2:
                    continue
                
                x = np.arange(len(decay_segment))
                y = decay_segment
                slope, _ = np.polyfit(x, y, 1)
                
                if slope < 0:
                    confidence = (peak_val * abs(slope)) / (1.0 + abs(slope))
                    events.append(FEPEvent(
                        feature_id=int(fid),
                        start_token_idx=int(start_idx),
                        end_token_idx=int(end_idx),
                        peak_activation=float(peak_val),
                        resolution_decay_rate=float(slope),
                        confidence_score=float(confidence),
                        metadata={"token": token_labels[start_idx]}
                    ))
        return events

    def process_sample_jsonl(self, filepath: str):
        results = []
        with open(filepath, "r") as f:
            for line in f:
                data = json.loads(line)
                if "activations" not in data or "tokens" not in data:
                    continue
                events = self.analyze_sequence(data["activations"], data["tokens"])
                results.append({
                    "sample_id": data.get("id", "unknown"),
                    "fep_events": [vars(e) for e in events]
                })
        return results

if __name__ == "__main__":
    import os
    # Use first argument if provided, otherwise default to a common path
    sample_path = sys.argv[1] if len(sys.argv) > 1 else "data/fep_sae/information_gain_samples.jsonl"
    
    if os.path.exists(sample_path):
        detector = FEPDetector()
        findings = detector.process_sample_jsonl(sample_path)
        print(f"Processed {len(findings)} samples from {sample_path}.")
        for res in findings:
            sid = res['sample_id']
            evs = res['fep_events']
            print(f"Sample {sid}: Found {len(evs)} FEP signals.")
            for ev in evs:
                token = ev['metadata']['token']
                fid = ev['feature_id']
                conf = ev['confidence_score']
                print(f"  - Feature {fid} spiked at \"{token}\" (Conf: {conf:.2f})")
    else:
        print(f"Error: Sample data not found at {sample_path}")
        sys.exit(1)
