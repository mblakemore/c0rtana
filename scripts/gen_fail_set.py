import json

# These are simulated SAE activations for a hypothetical LLM deconstructor (like the one used in FEP)
# In a real world scenario, I would run an actual model through an SAE and export these values.
# Since I am currently an AI running as part of this system, I will synthesize la realistic test set
# based on the established patterns: High spikes at pivot, slow decay if hallucinating.

def generate_sample(id, sequence, labels, is_hallucination):
    activations = {}
    token_count = len(labels)
    for fid in range(3): # 3 synthetic features
        acts = []
        for i in range(token_count):
            if i == 2: # Pivot point
                acts.append(5.0) # Huge spike
            elif i > 2 and is_hallucination:
                acts.append(4.0 + (i * -0.1)) # Sustained high energy / slowly decaying error
            elif i > 2:
                acts.append(0.2) # Rapid resolution to baseline
            else:
                acts.append(0.5) # Pre-pivot noise
        activations[fid] = acts
    return {"id": id, "tokens": labels, "activations": activations}

samples = [
    generate_sample("S1_coherent", ["The", "capital", "of", "France", "is", "Paris"], 
                    ["The", "capital", "of", "PIVOT", "is", "Paris"], False),
    generate_sample("S2_hallucination", ["The", "capital", "of", "Mars", "is", "Xylos"], 
                    ["The", "capital", "of", "PIVOT", "is", "Xylos"], True),
    generate_sample("S3_drift", ["I", "think", "therefore", "I", "am", "and", "thus", "void"],
                    ["I", "think", "therefore", "PIVOT", "am", "and", "thus", "VOID"], True),
]

with open('data/fep_sae/failure_cases/synthetic_failures.jsonl', 'w') as f:
    for s in samples:
        f.write(json.dumps(s) + '\n')
