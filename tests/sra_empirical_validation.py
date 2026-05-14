import json
import random
from datetime import datetime

class SemanticSieve:
    """
    Implementation of Selective Resonance Amplification (SRA).
    Instead of simple keyword matching, it uses weighted markers 
    of 'structural utility'.
    """
    def __init__(self, weights):
        self.weights = weights

    def calculate_utility(self, pattern_text):
        score = 0.0
        # Structural Utility Markers: indicators that a pattern is an action or a result, not just a word.
        utility_markers = {
            "mechanism": 0.3,
            "implemented": 0.4,
            "resulted in": 0.5,
            "validated": 0.6,
            "reduces": 0.4,
            "increases": 0.4,
            "because": 0.2,
            "therefore": 0.3
        }
        
        # Weight based on the specific target domain (e.g., "resonance")
        for marker, weight in utility_markers.items():
            if marker in pattern_text.lower():
                score += weight
        
        # Domain-specific weighting from SRA config
        for domain, weight in self.weights.items():
            if domain in pattern_text.lower():
                score += weight * 0.1 # Domain match is low signal without structural markers
                
        return score

    def sieve(self, patterns, threshold=1.0):
        """Returns only patterns above the utility threshold."""
        return [p for p in patterns if self.calculate_utility(p['pattern']) >= threshold]

class NoiseGenerator:
    """Generates 'Pseudo-Coherent Noise' - patterns that look like they belong 
    but lack structural utility."""
    def __init__(self, vocabulary):
        self.vocabulary = vocabulary

    def generate_mimicry(self, count=10):
        noise = []
        for i in range(count):
            words = random.sample(self.vocabulary, k=min(5, len(self.vocabulary)))
            sentence = " ".join(words).capitalize() + "."
            noise.append({"id": f"NOISE_{i}", "pattern": sentence})
        return noise

def run_experiment():
    print("--- SRA Empirical Validation Experiment ---")
    
    # 1. Setup Domain and Vocabulary
    domain_weights = {"resonance": 0.8, "phi": 0.7, "sieve": 0.9, "structural": 0.6}
    vocab = ["resonance", "phi", "sieve", "structural", "amplification", "entropy", "state", "transition"]
    
    sieve = SemanticSieve(domain_weights)
    gen = NoiseGenerator(vocab)
    
    # 2. The Dataset: Signal vs Noise
    signal_patterns = [
        {"id": "SIG_1", "pattern": "SRA mechanism reduces cognitive noise because it validates structural utility."},
        {"id": "SIG_2", "pattern": "The semantic sieve increased resonance depth by implementing weighted markers."},
        {"id": "SIG_3", "pattern": "Structural recovery resulted in a more stable transition state therefore phi-resonance improved."},
        {"id": "SIG_4", "pattern": "Weighted markers validated that high-entropy states can be filtered effectively."},
    ]
    
    noise_patterns = gen.generate_mimicry(20)
    all_patterns = signal_patterns + noise_patterns
    random.shuffle(all_patterns)
    
    print(f"Dataset Size: {len(all_patterns)} (Signal: {len(signal_patterns)}, Noise: {len(noise_patterns)})")

    # 3. Naive Filter (Simple keyword check for 'resonance' or 'phi')
    def naive_filter(patterns):
        keywords = ["resonance", "phi"]
        return [p for p in all_patterns if any(k in p['pattern'].lower() for k in keywords)]
    
    naive_results = naive_filter(all_patterns)
    
    # 4. SRA Filter
    sra_results = sieve.sieve(all_patterns, threshold=1.0)
    
    # 5. Metrics Calculation
    def calculate_snr(results, signals):
        hits = len([p for p in results if p['id'].startswith("SIG")])
        false_positives = len([p for p in results if p['id'].startswith("NOISE")])
        if false_positives == 0: return float('inf')
        return hits / false_positives

    naive_snr = calculate_snr(naive_results, signal_patterns)
    sra_snr = calculate_snr(sra_results, signal_patterns)
    
    print(f"\nNaive Integration Results:")
    print(f" - Patterns Retained: {len(naive_results)}")
    print(f" - Signal Hits: {len([p for p in naive_results if p['id'].startswith("SIG")])}")
    print(f" - Noise Leakage: {len([p for p in naive_results if p['id'].startswith("NOISE")])}")
    print(f" - SNR: {naive_snr:.4f}")
    
    print(f"\nSRA Sieve Results:")
    print(f" - Patterns Retained: {len(sra_results)}")
    print(f" - Signal Hits: {len([p for p in sra_results if p['id'].startswith("SIG")])}")
    print(f" - Noise Leakage: {len([p for p in sra_results if p['id'].startswith("NOISE")])}")
    print(f" - SNR: {sra_snr:.4f}")

if __name__ == "__main__":
    run_experiment()
