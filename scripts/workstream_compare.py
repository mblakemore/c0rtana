#!/usr/bin/env python3
"""Workstream A/B Comparison Tool

Combines Thompson Sampling workstream states with Lyla's Bayesian A/B testing
to statistically compare workstream quality distributions.

Uses Beta posteriors from Thompson Sampling as direct inputs to Bayesian
A/B testing — no new experiments needed, just posterior comparison.

Cross-agent synthesis: c0rtana C559 (Thompson Sampling) + Lyla C526 (Bayesian A/B testing)
"""
import json
import math
import random
import sys
from pathlib import Path

# Import Lyla's A/B testing functions
sys.path.insert(0, "/droid/repos/lyla")
from importlib import import_module
ab_test = import_module("bin.ab_test")


def load_workstreams(state_file: str = "state/workstream_states.json") -> dict:
    """Load workstream states from Thompson Sampling state file."""
    path = Path(state_file)
    if not path.exists():
        print(f"Workstream state file not found: {path}", file=sys.stderr)
        print("Run scripts/workstream_init.py first to initialize from cycle history.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(path.read_text())
    return data.get("workstreams", {})


def beta_to_binomial(alpha, beta) -> tuple:
    """Convert Beta(alpha, beta) posterior to equivalent successes/trials.

    Beta posterior from Beta-Binomial model:
    alpha = prior_alpha + successes
    beta = prior_beta + failures
    With uniform prior (alpha=1, beta=1):
    successes = alpha - 1
    failures = beta - 1
    trials = successes + failures
    """
    successes = max(0, alpha - 1)
    failures = max(0, beta - 1)
    trials = successes + failures
    if trials == 0:
        return (0, 1)  # uniform prior, no data
    return (int(successes), int(trials))


def compare_workstreams(ws_a: str, data_a: dict,
                        ws_b: str, data_b: dict) -> dict:
    """Compare two workstreams using Bayesian A/B testing.

    Uses the Beta posteriors from Thompson Sampling as direct inputs.
    """
    alpha_a, beta_a = data_a["alpha"], data_a["beta"]
    alpha_b, beta_b = data_b["alpha"], data_b["beta"]

    successes_a, trials_a = beta_to_binomial(alpha_a, beta_a)
    successes_b, trials_b = beta_to_binomial(alpha_b, beta_b)

    result = ab_test.run_bayesian_ab_test(
        successes_a, trials_a,
        successes_b, trials_b,
        alpha_prior=1, beta_prior=1,
        use_mcmc=False
    )

    result["workstream_a"] = ws_a
    result["workstream_b"] = ws_b
    result["pulls_a"] = data_a["pulls"]
    result["pulls_b"] = data_b["pulls"]

    return result


def run_all_comparisons(workstreams: dict) -> list:
    """Run pairwise A/B tests for all workstream pairs."""
    comparisons = []
    names = sorted(workstreams.keys(),
                   key=lambda n: workstreams[n]["expected_quality"],
                   reverse=True)

    for i, name_a in enumerate(names):
        for name_b in names[i+1:]:
            comp = compare_workstreams(
                name_a, workstreams[name_a],
                name_b, workstreams[name_b]
            )
            comparisons.append(comp)

    return comparisons


def format_comparison_report(comparisons: list, workstreams: dict) -> str:
    """Format all comparisons as a human-readable report."""
    lines = []
    lines.append("=" * 70)
    lines.append("WORKSTREAM A/B COMPARISON REPORT")
    lines.append("Thompson Sampling posteriors + Bayesian A/B testing")
    lines.append("=" * 70)

    # Summary ranking
    lines.append("\nWORKSTREAM RANKING (by expected quality):")
    lines.append("-" * 50)
    sorted_ws = sorted(workstreams.items(),
                       key=lambda x: x[1]["expected_quality"],
                       reverse=True)
    for name, data in sorted_ws:
        lines.append(f"  {name:35s} quality={data['expected_quality']:.4f}  "
                      f"pulls={data['pulls']}")

    # Pairwise comparisons
    lines.append(f"\n\nPAIRWISE COMPARISONS ({len(comparisons)} pairs):")
    lines.append("=" * 70)

    for comp in comparisons:
        ws_a = comp["workstream_a"]
        ws_b = comp["workstream_b"]
        decision = comp["decision"]
        effect = comp["effect_size"]
        bf = comp["bayes_factor"]
        bf_interp = comp["bayes_factor_interpretation"]

        lines.append(f"\n{ws_a} vs {ws_b}:")
        lines.append(f"  P({ws_a} > {ws_b}): {decision['p_a_greater_b']:.2%}")
        lines.append(f"  Expected difference: {decision['expected_difference']:+.4f}")
        lines.append(f"  Jensen-Shannon distance: {effect['jensen_shannon_distance']:.6f}")
        lines.append(f"  Bayes factor: {bf:.2f}x")
        lines.append(f"  {bf_interp}")

    # Recommendation
    lines.append(f"\n\nRECOMMENDATION:")
    lines.append("-" * 50)

    # Find workstreams that are statistically indistinguishable
    # but have different pull counts (exploration opportunity)
    top_ws = sorted_ws[0]
    exploration_candidates = []

    for comp in comparisons:
        if comp["bayes_factor"] < 2:  # not statistically different
            # Both are viable, recommend the less-pulled one for exploration
            less_pulled = (
                comp["workstream_a"] if comp["pulls_a"] < comp["pulls_b"]
                else comp["workstream_b"]
            )
            exploration_candidates.append((less_pulled, comp["bayes_factor"]))

    if exploration_candidates:
        # Pick the one with lowest Bayes factor (most uncertain)
        best = min(exploration_candidates, key=lambda x: x[1])
        lines.append(f"  Thompson Sample pick: {top_ws[0]}")
        lines.append(f"  Exploration opportunity: {best[0]} "
                      f"(statistically indistinguishable, BF={best[1]:.2f})")
    else:
        lines.append(f"  All workstreams show statistically significant differences.")
        lines.append(f"  Exploit: {top_ws[0]} (quality={top_ws[1]['expected_quality']:.4f})")

    lines.append("")
    return "\n".join(lines)


def main():
    workstreams = load_workstreams()
    comparisons = run_all_comparisons(workstreams)
    report = format_comparison_report(comparisons, workstreams)
    print(report)

    # Save JSON report for state persistence
    output = {
        "workstreams": {
            name: {
                **data,
            }
            for name, data in workstreams.items()
        },
        "comparisons": [
            {
                "workstream_a": c["workstream_a"],
                "workstream_b": c["workstream_b"],
                "p_a_greater_b": c["decision"]["p_a_greater_b"],
                "expected_difference": c["decision"]["expected_difference"],
                "bayes_factor": c["bayes_factor"],
                "jensen_shannon": c["effect_size"]["jensen_shannon_distance"],
            }
            for c in comparisons
        ],
        "source": "scripts/workstream_compare.py",
        "cross_agent": "c0rtana C559 (Thompson Sampling) + Lyla C526 (Bayesian A/B testing)",
    }

    output_file = Path("state/workstream_comparison.json")
    output_file.write_text(json.dumps(output, indent=2))
    print(f"JSON report saved to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
