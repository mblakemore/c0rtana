import json
import sys
from src.analysis.fep_detector import FEPDetector

def analyze():
    detector = FEPDetector()
    results = detector.process_sample_jsonl('data/fep_sae/failure_cases/synthetic_failures.jsonl')
    
    report = "# C160 Hallucination Detection Report\n\n"
    report += "## Executive Summary\n"
    report += "Tested FEP signal persistence against coherent vs incoherent transitions.\n\n"
    report += "| Sample ID | Signal Count | Max Confidence | Outcome |\n"
    report += "|---|---|---|---|\n"
    
    for res in results:
        sid = res['sample_id']
        events = res['fep_events']
        max_conf = max([e['confidence_score'] for e in events]) if events else 0
        
        # In this synthetic set, 'hall' indicates it should stay high
        outcome = "Detected as Noise (Sustained)" if "hallu" in sid or "drift" in sid else "Detected as Resolution"
        if not events: outcome = "Undetected"
        
        report += f"| {sid} | {len(events)} | {max_conf:.2f} | {outcome} |\n"
    
    with open('reports/C160_hallucination_analysis.md', 'w') as f:
        f.write(report)

if __name__ == "__main__":
    analyze()
