#!/usr/bin/env python3
"""Category consolidation v2 — semantic clustering, not just prefix matching.

Addresses C556 prediction: 157 categories → ~30 supercategories.
Current state: 91 categories, partially consolidated.
This pass uses explicit semantic mapping for categories the prefix tool missed.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

PATTERNS_PATH = Path("state/memories/patterns.jsonl")

# Semantic consolidation map: maps specific/narrow categories to canonical supercategories
# Built from manual analysis of 91 categories with 346 patterns
CANONICAL_MAP = {
    # sensor family
    "sensor": "sensor",
    "sensor-calibration": "sensor",
    "sensor_calibration": "sensor",
    # hardware family
    "hardware": "hardware",
    "firmware": "hardware",
    "esp32-firmware": "hardware",
    "embedded-hardware": "hardware",
    # visualization family
    "visualization": "visualization",
    "visualization/hologram": "visualization",
    "visualization/embodiment": "visualization",
    "visual_language": "visualization",
    # external domain
    "external": "external",
    "external_reading": "external",
    # theory family
    "theory": "theory",
    "theoretical_framework": "theory",
    "theory/autonomy": "theory",
    "theory/autopoiesis": "theory",
    # cognitive / neuroscience
    "cognitive": "cognitive",
    "neuroscience": "cognitive",
    "computational_neuroscience": "cognitive",
    "predictive_processing": "cognitive",
    "active_inference": "cognitive",
    # decision
    "decision-theory": "decision",
    "decision_theory": "decision",
    # cybernetics
    "cybernetics": "cybernetics",
    "applied-cybernetics": "cybernetics",
    "cybernetic_interface": "cybernetics",
    # design / architecture
    "architecture": "design",
    "software_architecture": "design",
    "abstraction_design": "design",
    "protocol_design": "design",
    "interface_design": "design",
    "ux_design": "design",
    # self-knowledge
    "self_knowledge": "self-knowledge",
    "interpretability-finding": "self-knowledge",
    # operational
    "operational": "operational",
    "operator": "operational",
    "execution": "operational",
    # methodology
    "methodology": "methodology",
    "research_methodology": "methodology",
    "development_methodology": "methodology",
    "verification_methodology": "methodology",
    "productivity_method": "methodology",
    # collaboration
    "collaboration": "collaboration",
    "collaborative_intelligence": "collaboration",
    "epistemological_coordination": "collaboration",
    "communication_protocol": "collaboration",
    # systems
    "system": "systems",
    "distributed_systems": "systems",
    "multi": "systems",
    "agentics": "systems",
    "agent-scaling": "systems",
    # state management
    "state": "state-management",
    "cycle": "state-management",
    # data / information
    "data_quality": "data",
    "analytics": "data",
    "information-theory": "data",
    # physical / embodied (keep embodied as is, it's large)
    "physical": "physical",
    "real": "physical",
    # discovery
    "discovery-pattern": "discovery",
    "empirical": "discovery",
    # stability / robustness
    "stability-control": "stability",
    "robustness": "stability",
    # governance / meta
    "governance": "governance",
    "reality-anchor": "governance",
    # quantum
    "quantum": "quantum",
    "qiskit_quirks": "quantum",
    # engagement
    "engagement": "engagement",
    "creator_directive": "engagement",
    "role_definition": "engagement",
    # tooling
    "tooling": "tooling",
    "shared_tooling": "tooling",
    "instrumentation": "tooling",
    "api": "tooling",
    # deployment
    "deployment": "deployment",
    "async_prep": "deployment",
    # foundational (keep, already large)
    "foundational": "foundational",
    # coordination (keep, already large)
    "coordination": "coordination",
    # embodied (keep, already large)
    "embodied": "embodied",
    # prediction (keep, already large)
    "prediction": "prediction",
    # infrastructure (keep, already large)
    "infrastructure": "infrastructure",
    # meta (keep)
    "meta": "meta",
    # engineering
    "engineering": "engineering",
    "technical": "engineering",
    "control_theory": "engineering",
    "robotics_learning": "engineering",
    # design catch-all
    "design": "design",
    # filesystem
    "filesystem_topology": "infrastructure",
    # climate
    "climate_anxiety_art_market_institutions": "external",
    # utility
    "utility": "tooling",
}


def load_patterns() -> list[dict]:
    patterns = []
    with open(PATTERNS_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    patterns.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return patterns


def analyze_before(patterns: list[dict]) -> dict:
    cats = Counter()
    for p in patterns:
        cats[p.get("category", "unknown").lower().strip()] += 1
    return {
        "total_patterns": len(patterns),
        "num_categories": len(cats),
        "avg_per_category": len(patterns) / len(cats) if cats else 0,
        "categories": dict(cats),
    }


def apply_consolidation(patterns: list[dict]) -> tuple[list[dict], dict]:
    """Return consolidated patterns and merge statistics."""
    merged = 0
    skipped = 0
    changes = defaultdict(list)

    for p in patterns:
        old_cat = p.get("category", "unknown").lower().strip()
        new_cat = CANONICAL_MAP.get(old_cat, old_cat)
        if old_cat != new_cat:
            changes[new_cat].append((old_cat, p.get("id", "?")))
            p["category"] = new_cat
            merged += 1
        elif old_cat not in CANONICAL_MAP:
            skipped += 1

    return patterns, {
        "patterns_merged": merged,
        "categories_unmapped": skipped,
        "changes": dict(changes),
    }


def main():
    patterns = load_patterns()
    before = analyze_before(patterns)

    print(f"Before: {before['num_categories']} categories, {before['total_patterns']} patterns")
    print(f"Avg patterns/category: {before['avg_per_category']:.1f}")
    print()

    # Show unmapped categories
    existing_cats = set(before["categories"].keys())
    unmapped = existing_cats - set(CANONICAL_MAP.keys())
    if unmapped:
        print(f"Unmapped categories ({len(unmapped)}):")
        for cat in sorted(unmapped):
            print(f"  {cat}: {before['categories'][cat]}")
        print()

    # Apply
    consolidated, stats = apply_consolidation(patterns)
    after = analyze_before(consolidated)

    print(f"After:  {after['num_categories']} categories, {after['total_patterns']} patterns")
    print(f"Avg patterns/category: {after['avg_per_category']:.1f}")
    print(f"Patterns remapped: {stats['patterns_merged']}")
    print()

    # Top categories after
    sorted_cats = sorted(after["categories"].items(), key=lambda x: -x[1])
    print("Top categories after consolidation:")
    for cat, count in sorted_cats[:20]:
        print(f"  {cat}: {count}")
    print(f"  ... and {len(sorted_cats) - 20} more")
    print()

    # C556 prediction validation
    c556_target = 30
    actual = after["num_categories"]
    improvement = before["avg_per_category"] / after["avg_per_category"] if after["avg_per_category"] else 0

    print(f"C556 prediction: {before['num_categories']} → ~{c556_target} supercategories")
    print(f"Actual result:   {before['num_categories']} → {actual} categories")
    print(f"Retrieval improvement: {improvement:.1f}x (C556 predicted 5x)")
    print()

    # Write backup and updated file
    backup_path = Path(f"state/memories/patterns.jsonl.bak.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}")
    import shutil
    shutil.copy2(PATTERNS_PATH, backup_path)
    print(f"Backup written to: {backup_path}")

    with open(PATTERNS_PATH, "w") as f:
        for p in consolidated:
            f.write(json.dumps(p) + "\n")
    print(f"Updated {PATTERNS_PATH}")

    # Write consolidation report
    report = {
        "id": f"P_C574_CATEGORY_CONSOLIDATION_V2",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "before": before,
        "after": after,
        "stats": stats,
        "c556_prediction": {
            "predicted_reduction": f"157 → ~{c556_target}",
            "actual_reduction": f"{before['num_categories']} → {actual}",
            "predicted_improvement": "5x",
            "actual_improvement": f"{improvement:.1f}x",
        },
    }
    report_path = Path("state/category_consolidation_v2_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
