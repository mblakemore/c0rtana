
import json
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
    or ambiguity and then decay as the model \"resolves\" the state.
    """
    
    def __init__(self, activation_threshold: float = 2.0, decay_window: int = 5):
        self.activation_threshold = activation_threshold
        self.decay_window = decay_window

    def analyze_sequence(self, feature_activations: Dict[int, List[float]], token_labels: List[str]) -> List[FEPEvent]:
        """
        Analyzes a sequence of activations for a set of features to find FEP patterns.
        
        :param feature_activations: Map of feature_id -> list of activation values across sequence
        :param token_labels: The tokens associated with the indices
        """
        events = []
        seq_len = len(token_labels)

        for fid, acts in feature_activations.items():
            acts = np.array(acts)
            
            # 1. Detect Spikes (Trigger events)
            spikes = np.where(acts > self.activation_threshold)[0]
            
            for start_idx in spikes:
                # Look for the peak in the immediate vicinity
                peak_idx = start_idx # simplified for this impl
                peak_val = acts[peak_idx]
                
                # 2. Measure Resolution Decay (The \"F\" in FEP)
                # We look at the slope of activation after the spike
                end_idx = min(start_idx + self.decay_window, seq_len - 1)
                decay_segment = acts[start_idx : end_idx + 1]
                
                if len(decay_segment) < 2:
                    continue
                
                # Linear regression for decay rate
                x = np.arange(len(decay_segment))
                y = decay_segment
                slope, _ = np.polyfit(x, y, 1)
                
                # FEP criteria: Strong spike followed by negative slope (decay)
                if slope < 0:
                    # Confidence is a factor of peak magnitude and steepness of decay
                    confidence = (peak_val * abs(slope)) / (1.0 + abs(slope))
                    
                    events.append(FEPEvent(
                        feature_id=fid,
                        start_token_idx=int(start_idx),
                        end_token_idx=int(end_idx),
                        peak_activation=float(peak_val),
                        resolution_decay_rate=float(slope),
                        confidence_score=float(confidence),
                        metadata={"token": token_labels[start_idx]}
                    ))
                    
        return events

    def process_sample_jsonl(self, filepath: str):
        """
        Utility to run the detector against the synthetic sample data.
        """
        results = []
        with open(filepath, \"r\") as f:
            for line in f:
                data = json.loads(line)
                # Extract activations: {fid: [val1, val2...]}
                # Expected format in jsonl: {"tokens": [], "activations": {fid: []}}
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
    sample_path = "data/fep_sae/information_gain_samples.jsonl"
    
    if os.path.exists(sample_path):
        detector = FEPDetector()
        findings = detector.process_sample_jsonl(sample_path)
        print(f"Processed {len(findings)} samples.")
        for res in findings:
            print(f"Sample {res[sample_id]}: Found {len(res[fep_events])} FEP signals.")
            for ev in res[fep_events]:
                print(f"  - Feature {ev[feature_id]} spiked at \"{ev[metadata][token]}\" (Conf: {ev[confidence_score]:.2f})")
    else:
        print(f"Sample data not found at {sample_path}.")
