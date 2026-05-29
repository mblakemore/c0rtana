#!/usr/bin/env python3
"""Category consolidation analysis tool.

Reads patterns.jsonl, clusters similar categories using string similarity,
and produces a consolidation plan that reduces category fragmentation.

Addresses C556 finding: 157 categories for 326 patterns (avg 2.08/category)
makes category-based retrieval a weak signal.
"""

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path


def load_patterns(path: str) -> list[dict]:
    patterns = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    patterns.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return patterns


def get_category(pattern: dict) -> str:
    return pattern.get("category", "uncategorized").lower().strip()


def compute_entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in counter.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def normalize_category(cat: str) -> str:
    """Normalize category name: lowercase, replace separators with hyphens."""
    return cat.lower().replace("_", "-")


def get_root_prefix(cat: str) -> str:
    """Extract the root concept from a category name.

    'hardware-infrastructure' -> 'hardware'
    'embodied_cognition' -> 'embodied'
    'coordination-protocol' -> 'coordination'
    'prediction-validation-methodology' -> 'prediction'
    """
    normalized = normalize_category(cat)
    tokens = normalized.split("-")
    if not tokens:
        return normalized
    return tokens[0]


def cluster_categories(categories: list[str]) -> list[list[str]]:
    """Cluster categories by root prefix.

    Groups categories that share the same root concept, handling separator
    variants (hyphen vs underscore) naturally via normalization.
    """
    prefix_groups = defaultdict(list)
    for cat in categories:
        prefix = get_root_prefix(cat)
        prefix_groups[prefix].append(cat)

    clusters = []
    for prefix, group in prefix_groups.items():
        if len(group) >= 2:
            clusters.append(sorted(group))

    return clusters


def propose_canonical_name(cluster: list[str], pattern_counts: dict[str, int]) -> str:
    """Propose a canonical name for a cluster of categories.

    Uses the shared root prefix as the canonical name.
    """
    prefix = get_root_prefix(cluster[0])
    return prefix


def build_consolidation_plan(patterns_path: str) -> dict:
    patterns = load_patterns(patterns_path)
    category_counter = Counter(get_category(p) for p in patterns)

    entropy_before = compute_entropy(category_counter)
    max_entropy = math.log2(len(category_counter)) if category_counter else 1.0
    evenness_before = entropy_before / max_entropy if max_entropy > 0 else 0

    categories = list(category_counter.keys())
    clusters = cluster_categories(categories)

    merges = []
    patterns_moved = 0
    categories_removed = 0

    for cluster in sorted(clusters, key=lambda c: -max(category_counter.get(c, 0) for c in c)):
        canonical = propose_canonical_name(cluster, category_counter)
        total_patterns = sum(category_counter.get(c, 0) for c in cluster)
        details = [{"category": c, "patterns": category_counter.get(c, 0)}
                   for c in sorted(cluster, key=lambda c: -category_counter.get(c, 0))]

        merges.append({
            "canonical": canonical,
            "merge": cluster,
            "total_patterns": total_patterns,
            "details": details
        })
        patterns_moved += total_patterns
        categories_removed += len(cluster) - 1

    # Compute post-consolidation metrics
    post_categories = len(category_counter) - categories_removed
    # Build post-consolidation counter: merged clusters become single categories
    merged_categories = {c for m in merges for c in m["merge"]}
    post_counter = Counter()
    for m in merges:
        post_counter[m["canonical"]] = m["total_patterns"]
    for cat, count in category_counter.items():
        if cat not in merged_categories:
            post_counter[cat] = count

    entropy_after = compute_entropy(post_counter)
    max_entropy_after = math.log2(post_categories) if post_categories > 0 else 1.0
    evenness_after = entropy_after / max_entropy_after if max_entropy_after > 0 else 0

    # Patterns per category
    total_patterns = sum(category_counter.values())
    avg_before = total_patterns / len(category_counter) if category_counter else 0
    avg_after = total_patterns / post_categories if post_categories else 0

    return {
        "summary": {
            "total_patterns": total_patterns,
            "categories_before": len(category_counter),
            "categories_after": post_categories,
            "categories_removed": categories_removed,
            "merges_proposed": len(merges),
            "avg_patterns_per_category_before": round(avg_before, 2),
            "avg_patterns_per_category_after": round(avg_after, 2),
            "entropy_before": round(entropy_before, 3),
            "entropy_after": round(entropy_after, 3),
            "evenness_before": round(evenness_before, 3),
            "evenness_after": round(evenness_after, 3),
            "retrieval_improvement": round(avg_after / avg_before, 2) if avg_before > 0 else 0
        },
        "merges": merges
    }


def apply_consolidation(patterns_path: str, backup_path: str) -> dict:
    """Apply consolidation plan: rewrite patterns.jsonl with normalized categories.

    Returns a mapping of old_category -> new_category for changed categories.
    """
    plan_path = "state/category-consolidation-plan.json"
    if not Path(plan_path).exists():
        print(f"Error: plan file not found at {plan_path}. Run analysis first.", file=sys.stderr)
        sys.exit(1)

    with open(plan_path) as f:
        plan = json.load(f)

    # Build mapping: old category -> canonical name
    category_map = {}
    for merge in plan["merges"]:
        canonical = merge["canonical"]
        for old_cat in merge["merge"]:
            category_map[old_cat] = canonical

    # Backup original
    import shutil
    shutil.copy2(patterns_path, backup_path)

    # Rewrite patterns with consolidated categories
    patterns = load_patterns(patterns_path)
    changed = 0
    with open(patterns_path, "w") as f:
        for p in patterns:
            cat = get_category(p)
            if cat in category_map:
                p["category"] = category_map[cat]
                changed += 1
            f.write(json.dumps(p) + "\n")

    print(f"Applied consolidation: {changed} patterns re-categorized across {len(category_map)} categories")
    print(f"Backup saved to: {backup_path}")
    return category_map


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Category consolidation analysis tool")
    parser.add_argument("patterns", nargs="?", default="state/memories/patterns.jsonl",
                        help="Path to patterns.jsonl")
    parser.add_argument("output", nargs="?", default="state/category-consolidation-plan.json",
                        help="Output path for consolidation plan")
    parser.add_argument("--apply", action="store_true",
                        help="Apply consolidation to patterns file (creates backup first)")
    parser.add_argument("--backup", default=None,
                        help="Backup path (default: patterns.jsonl.bak)")
    args = parser.parse_args()

    patterns_path = args.patterns
    output_path = args.output

    if not Path(patterns_path).exists():
        print(f"Error: {patterns_path} not found", file=sys.stderr)
        sys.exit(1)

    plan = build_consolidation_plan(patterns_path)

    # Write plan
    with open(output_path, "w") as f:
        json.dump(plan, f, indent=2)

    # Print summary
    s = plan["summary"]
    print(f"Category Consolidation Plan")
    print(f"===========================")
    print(f"Total patterns: {s['total_patterns']}")
    print(f"Categories: {s['categories_before']} -> {s['categories_after']} ({s['categories_removed']} removed)")
    print(f"Merges proposed: {s['merges_proposed']}")
    print(f"Avg patterns/category: {s['avg_patterns_per_category_before']} -> {s['avg_patterns_per_category_after']}")
    print(f"Entropy: {s['entropy_before']} -> {s['entropy_after']} bits")
    print(f"Evenness: {s['evenness_before']} -> {s['evenness_after']}")
    print(f"Retrieval improvement: {s['retrieval_improvement']}x")
    print(f"\nPlan written to: {output_path}")

    # Show top merges
    print(f"\nTop merges:")
    for merge in plan["merges"][:10]:
        cats = ", ".join(merge["merge"])
        print(f"  -> {merge['canonical']} ({merge['total_patterns']} patterns): {cats}")

    if args.apply:
        backup = args.backup or f"{patterns_path}.bak"
        print(f"\nApplying consolidation...")
        apply_consolidation(patterns_path, backup)


if __name__ == "__main__":
    main()
