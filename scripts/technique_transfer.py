#!/usr/bin/env python3
"""C577 - Technique Transfer Engine.

Takes cross-domain connections (shared concepts) and produces concrete
technique transfer recommendations: specific methods from one domain
that can solve problems in another.

Input:  state/memories/patterns.jsonl, state/cross_domain_connections.jsonl
Output: state/technique_transfers.jsonl + console summary"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone

REPO = "/droid/repos/c0rtana"
PATTERNS_FILE = os.path.join(REPO, "state/memories/patterns.jsonl")
CONNECTIONS_FILE = os.path.join(REPO, "state/cross_domain_connections.jsonl")
OUTPUT_FILE = os.path.join(REPO, "state/technique_transfers.jsonl")

# Technique indicators — patterns that describe a METHOD rather than just an observation
TECHNIQUE_INDICATORS = [
    r"must|should|use|apply|build|implement",
    r"method|approach|technique|strategy|algorithm",
    r"formula|equation|model|pipeline|system",
    r"rule|heuristic|threshold|criterion",
    r"estimat|detect|correct|calibrat|filter|smooth",
    r"monitor|track|measure|assess|evaluate",
    r"converge|sweep|optimize|tune|select",
]

# Problem indicators — patterns that describe a CHALLENGE
PROBLEM_INDICATORS = [
    r"gap|error|drift|degrad|decay|noise",
    r"fail|break|wrong|incorrect|mislead",
    r"confound|ambigu|uncertain|unstable",
    r"overfit|oscillat|diverge|spiral",
    r"need|require|missing|lacking|blind",
]


def is_technique(pattern_text):
    """Heuristic: does this pattern describe an extractable method?"""
    text = pattern_text.lower()
    return bool(re.search("|".join(TECHNIQUE_INDICATORS), text))


def is_problem(pattern_text):
    """Heuristic: does this pattern describe a challenge to solve?"""
    text = pattern_text.lower()
    return bool(re.search("|".join(PROBLEM_INDICATORS), text))


def load_patterns():
    """Load all patterns grouped by category."""
    patterns_by_cat = defaultdict(list)
    with open(PATTERNS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                cat = obj.get("category", "unknown")
                obj["_is_technique"] = is_technique(obj.get("pattern", ""))
                obj["_is_problem"] = is_problem(obj.get("pattern", ""))
                patterns_by_cat[cat].append(obj)
            except json.JSONDecodeError:
                pass
    return patterns_by_cat


def load_connections():
    """Load cross-domain connections."""
    connections = []
    with open(CONNECTIONS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                connections.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return connections


def score_transfer(source_pattern, target_domain_patterns, shared_concepts):
    """Score how well a technique from domain A transfers to domain B.

    Uses relative scoring (0-1) based on three factors:
    1. Novelty: technique is not already known in target domain
    2. Relevance: technique text mentions shared concepts
    3. Fit: target domain has problems this technique could solve

    Higher score = more likely to be useful and novel.
    """
    technique_text = source_pattern.get("pattern", "").lower()
    technique_words = set(technique_text.split()) - {
        "the", "and", "is", "in", "of", "to", "for", "a", "an", "by", "on", "at"
    }

    # --- Novelty (0-0.4) ---
    target_techniques = [p for p in target_domain_patterns if p.get("_is_technique")]
    novelty = 1.0
    if target_techniques:
        best_overlap = 0
        for t in target_techniques:
            t_words = set(t.get("pattern", "").lower().split()) - {
                "the", "and", "is", "in", "of", "to", "for", "a", "an", "by", "on", "at"
            }
            overlap = len(technique_words & t_words) / max(len(technique_words), 1)
            best_overlap = max(best_overlap, overlap)
        novelty = 1.0 - best_overlap
    novelty_score = 0.4 * novelty

    # --- Relevance (0-0.35) ---
    concept_hits = sum(1 for c in shared_concepts
                       if c.replace("_", " ") in technique_text or c in technique_text)
    relevance_score = 0.35 * min(concept_hits / max(len(shared_concepts), 1), 1.0)

    # --- Fit (0-0.25) ---
    problem_count = sum(1 for p in target_domain_patterns if p.get("_is_problem"))
    problem_ratio = problem_count / max(len(target_domain_patterns), 1)
    fit_score = 0.25 * min(problem_ratio * 2, 1.0)  # scaled: 50% problems = max fit

    score = novelty_score + relevance_score + fit_score
    return round(min(max(score, 0.0), 1.0), 3)


def generate_transfer_recommendation(source, target_cat, shared_concepts, score,
                                      target_patterns=None):
    """Generate a concrete recommendation for transferring a technique."""
    source_id = source.get("id", "unknown")
    source_cat = source.get("category", "unknown")
    technique_summary = source.get("pattern", "")[:200]

    problem_hint = ""
    if target_patterns:
        problem_count = sum(1 for p in target_patterns if p.get("_is_problem"))
        if problem_count > 0:
            problem_hint = (
                f" Target domain has {problem_count} challenge patterns this technique could address."
            )

    return {
        "transfer_id": f"T_{source_id}_to_{target_cat}",
        "source_pattern_id": source_id,
        "source_category": source_cat,
        "target_category": target_cat,
        "technique": technique_summary,
        "shared_concepts": shared_concepts,
        "transfer_score": score,
        "recommendation": (
            f"Apply '{source_id}' from {source_cat} to {target_cat}."
            f" The technique ({technique_summary[:100]}...)"
            f" addresses shared concepts: {', '.join(shared_concepts[:3])}."
            f"{problem_hint}"
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    print(f"[C577] Loading data...")
    patterns_by_cat = load_patterns()
    connections = load_connections()

    print(f"  {len(patterns_by_cat)} domains, {sum(len(v) for v in patterns_by_cat.values())} patterns")
    print(f"  {len(connections)} cross-domain connections")

    # Process top connections by specificity score
    transfers = []
    top_connections = connections[:20]  # Focus on highest-quality bridges

    for conn in top_connections:
        cat_a = conn["domain_a"]
        cat_b = conn["domain_b"]
        shared = conn["shared_concepts"]

        patterns_a = patterns_by_cat.get(cat_a, [])
        patterns_b = patterns_by_cat.get(cat_b, [])

        if not patterns_a or not patterns_b:
            continue

        # Find techniques in A that could transfer to B
        techniques_a = [p for p in patterns_a if p.get("_is_technique")]
        for technique in techniques_a:
            score = score_transfer(technique, patterns_b, shared)
            if score > 0.55:
                transfer = generate_transfer_recommendation(
                    technique, cat_b, shared, score, patterns_b
                )
                transfers.append(transfer)

        # And vice versa: techniques in B that could transfer to A
        techniques_b = [p for p in patterns_b if p.get("_is_technique")]
        for technique in techniques_b:
            score = score_transfer(technique, patterns_a, shared)
            if score > 0.55:
                transfer = generate_transfer_recommendation(
                    technique, cat_a, shared, score, patterns_a
                )
                transfers.append(transfer)

    # Deduplicate: keep best transfer per (source_id, target_category) pair
    seen = set()
    deduped = []
    for t in transfers:
        key = (t["source_pattern_id"], t["target_category"])
        if key not in seen:
            seen.add(key)
            deduped.append(t)
    transfers = deduped

    # Sort by score
    transfers.sort(key=lambda x: -x["transfer_score"])

    # Write output — all transfers above threshold
    with open(OUTPUT_FILE, "w") as f:
        for t in transfers:
            f.write(json.dumps(t) + "\n")

    # Best transfer per source pattern (prevents one pattern from dominating)
    best_per_source = {}
    for t in transfers:
        sid = t["source_pattern_id"]
        if sid not in best_per_source or t["transfer_score"] > best_per_source[sid]["transfer_score"]:
            best_per_source[sid] = t
    highlights = sorted(best_per_source.values(), key=lambda x: -x["transfer_score"])

    # Console summary — highlights (best per source, prevents dominance)
    print(f"\n=== Top Technique Transfers (Best per Source) ===")
    for t in highlights[:15]:
        print(f"\n  [{t['transfer_score']:.2f}] {t['source_category']} -> {t['target_category']}")
        print(f"    {t['recommendation'][:150]}")

    print(f"\n✓ Output saved to {OUTPUT_FILE}")
    print(f"  Total transfers (all above 0.55): {len(transfers)}")
    print(f"  Unique source patterns: {len(highlights)}")

    # Statistics — domain pair distribution
    if transfers:
        cat_pairs = defaultdict(int)
        for t in transfers:
            pair = f"{t['source_category']}->{t['target_category']}"
            cat_pairs[pair] += 1
        print(f"\n=== Transfer Distribution (Top Pairs) ===")
        for pair, count in sorted(cat_pairs.items(), key=lambda x: -x[1])[:10]:
            print(f"  {pair}: {count}")


if __name__ == "__main__":
    main()
