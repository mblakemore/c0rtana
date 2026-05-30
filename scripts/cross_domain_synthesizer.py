#!/usr/bin/env python3
"""C576 - Cross-Domain Pattern Synthesizer.

Finds structural similarities between different workstream domains by
analyzing pattern descriptions for shared concepts, methods, and insights.
This creates the first "meta-cognitive bridge" between C0rtana's sensor/calibration
work and Lyla's HMM/trading analysis.

Output: state/cross_domain_connections.jsonl + console summary."""

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone

REPO = "/droid/repos/c0rtana"
PATTERNS_FILE = os.path.join(REPO, "state/memories/patterns.jsonl")
OUTPUT_FILE = os.path.join(REPO, "state/cross_domain_connections.jsonl")

# Concept extraction rules — maps keywords to abstract concepts
CONCEPT_MAP = {
    # Methods/techniques
    r"kalman|filter": "state_estimation",
    r"hmm|hidden.*markov|baum.?welch": "latent_state_modeling",
    r"dqn|reinforc.*learn|neural": "reinforcement_learning",
    r"z.?score|iqr|anomal": "statistical_detection",
    r"calibrat|bias|drift": "systematic_error_correction",
    r"ema|exponential.*mov|smooth": "temporal_smoothing",
    r"walk.?forward|cross.?valid|backtest": "out_of_sample_validation",
    r"brier|log.?likelihoo|aic|bic": "model_selection_criteria",
    r"oscillat|period|cyc": "cyclic_behavior",
    r"regime|state.*switch|transition": "discrete_regimes",
    r"converge|stabiliz|equilibri": "convergence_dynamics",
    
    # Domain concepts
    r"sensor|esp32|dht22|humidity|temperature|touch": "physical_sensing",
    r"trading|stock|price|return|sharpe": "financial_markets",
    r"cognit|pattern|memory|consolidat": "cognitive_architecture",
    r"prediction|forecast|project": "temporal_prediction",
    
    # Broader structural concepts (catch more patterns)
    r"gradient|climb|accumulat|slow.*shift": "gradual_change",
    r"complexi|overengin|bloat|simplif": "complexity_growth",
    r"monitor|observ|watch|track": "continuous_monitoring",
    r"feedback|loop|iterat|refin": "feedback_loops",
    r"degrad|decay|erosion|worsen": "performance_degradation",
    r"recovery|repair|restor|fix": "self_repair",
    r"alignment|sync|cohere|match": "alignment_maintenance",
    r"uncertainti|noise|variab|signal": "uncertainty_handling",
    r"threshold|bound|limit|boundary": "decision_boundaries",
    r"automat|script|pipeline|workflow": "automation",
    r"test|valid|verify|check": "verification",
    r"version|migrate|update|evolve": "state_evolution",
}

def extract_concepts(text):
    """Extract abstract concepts from text using keyword mapping."""
    found = set()
    for pattern, concept in CONCEPT_MAP.items():
        if re.search(pattern, text.lower()):
            found.add(concept)
    return found

def compute_domain_stats(patterns):
    """Group patterns by category and compute stats."""
    domains = defaultdict(list)
    for p in patterns:
        cat = p.get("category", "unknown")
        domains[cat].append(p)
    
    domain_concepts = {}
    for cat, plist in domains.items():
        all_text = " ".join(
            p.get("pattern", "") + " " + p.get("description", "") + " " + p.get("insight", "")
            for p in plist
        )
        domain_concepts[cat] = {
            "patterns": len(plist),
            "concepts": extract_concepts(all_text),
            "latest_cycle": max((int(p.get("cycle", 0)) if isinstance(p.get("cycle"), (int, float)) else 0 for p in plist), default=0)
        }
    return domain_concepts

def find_connections(domain_concepts):
    """Find shared concepts between domain pairs — these are cross-domain bridges."""
    connections = []
    cats = list(domain_concepts.keys())
    
    for i in range(len(cats)):
        for j in range(i+1, len(cats)):
            c1, c2 = cats[i], cats[j]
            shared = domain_concepts[c1]["concepts"] & domain_concepts[c2]["concepts"]
            
            if shared:
                # Weight by how specific the shared concepts are
                specificity_score = len(shared) * min(
                    len(domain_concepts[c1]["concepts"]),
                    len(domain_concepts[c2]["concepts"])
                )
                
                connection = {
                    "domain_a": c1,
                    "domain_b": c2,
                    "shared_concepts": sorted(shared),
                    "n_shared": len(shared),
                    "specificity_score": specificity_score,
                    "interpretation": generate_interpretation(c1, c2, shared),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                connections.append(connection)
    
    # Sort by specificity score (most significant first)
    connections.sort(key=lambda x: -x["specificity_score"])
    return connections

def generate_interpretation(cat_a, cat_b, shared):
    """Generate a human-readable interpretation of a cross-domain bridge."""
    templates = {
        ("sensor", "prediction"): "Sensor calibration IS prediction — estimating true state from noisy observations. Kalman filter on DHT22 ≈ regime detection in trading.",
        ("hardware", "systems"): "ESP32 firmware updates mirror cognitive architecture changes — both require state migration and backward compatibility.",
        ("foundational", "cognitive"): "Foundational patterns encode the principles that cognitive architecture implements.",
        ("tooling", "infrastructure"): "Tools built for one domain become infrastructure for another.",
    }
    
    key = tuple(sorted([cat_a, cat_b]))
    reversed_key = tuple(sorted([cat_b, cat_a]))
    
    if key in templates:
        return templates[key]
    elif reversed_key in templates:
        return templates[reversed_key]
    else:
        concept_strs = ", ".join(list(shared)[:3])
        return f"Both domains share methods around: {concept_strs}. Cross-pollination opportunity."

def main():
    print(f"[C576] Loading patterns from {PATTERNS_FILE}")
    
    patterns = []
    with open(PATTERNS_FILE) as f:
        for line in f:
            if line.strip():
                try:
                    patterns.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    print(f"  Loaded {len(patterns)} patterns")
    
    # Compute domain-level concept profiles
    domain_concepts = compute_domain_stats(patterns)
    
    print(f"\n=== Domain Concept Profiles ===")
    for cat, info in sorted(domain_concepts.items(), key=lambda x: -x[1]["patterns"]):
        concepts_str = ", ".join(info["concepts"]) if info["concepts"] else "(no concepts detected)"
        print(f"  {cat:20s} ({info['patterns']:3d} patterns): {concepts_str}")
    
    # Find cross-domain connections
    connections = find_connections(domain_concepts)
    
    print(f"\n=== Top Cross-Domain Connections ===")
    for conn in connections[:10]:
        print(f"\n  [{conn['domain_a']} ↔ {conn['domain_b']}] score={conn['specificity_score']}")
        print(f"   Shared: {', '.join(conn['shared_concepts'])}")
        print(f"   → {conn['interpretation']}")
    
    # Write output
    with open(OUTPUT_FILE, "w") as f:
        for conn in connections:
            f.write(json.dumps(conn) + "\n")
    
    print(f"\n✓ Output saved to {OUTPUT_FILE}")
    print(f"  Total connections found: {len(connections)}")
    
    # Key insight extraction
    if connections:
        top = connections[0]
        print(f"\n★ KEY INSIGHT: Strongest bridge is between '{top['domain_a']}' and '{top['domain_b']}'")
        print(f"  via concepts: {', '.join(top['shared_concepts'])}")

if __name__ == "__main__":
    main()
