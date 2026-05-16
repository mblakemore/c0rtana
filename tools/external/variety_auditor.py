import sys
import re
from collections import Counter
from typing import List, Dict, Tuple

class VarietyAuditor:
    """
    The Variety Auditor analyzes the 'Requisite Variety' gap between an LLM Prompt 
    and its Output. Based on Ashby's Law, if the internal variety of the agent's response 
    is lower than the complexity required by the task environment (the prompt), failure is inevitable.
    """

    def __init__(self):
        # Keywords often associated with constraints or dimensionality in prompts
        self.constraint_markers = [
            r"must", r"should", r"do not", r"avoid", r"ensure", 
            r"always", r"never", r"specifically", r"include", r"exclude"
        ]

    def extract_constraints(self, text: str) -> List[str]:
        """Identifies potential constraint boundaries within a prompt."""
        lines = text.split('.')
        found = []
        for line in lines:
            if any(re.search(marker, line, re.IGNORECASE) for marker in self.constraint_markers):
                found.append(line.strip())
        return found

    def calculate_lexical_variety(self, text: str) -> float:
        """Calculates Type-Token Ratio (TTR) as a proxy for lexical diversity."""
        tokens = text.lower().split()
        if not tokens: return 0.0
        types = set(tokens)
        return len(types) / len(tokens)

    def audit(self, prompt: str, response: str) -> Dict:
        """Performs the variety gap analysis."""
        prompt_constraints = self.extract_constraints(prompt)
        p_ttr = self.calculate_lexical_variety(prompt)
        r_ttr = self.calculate_lexical_variety(response)
        
        # Simple Coverage Check: How many extracted constraints from the prompt are mentioned in output?
        covered = 0
        missing = []
        for c in prompt_constraints:
            # Extract core nouns/verbs from constraint to check for existence in response
            keywords = [w for w in c.split() if len(w) > 4]
            if any(k.lower() in response.lower() for k in keywords):
                covered += 1
            else:
                missing.append(c)
        
        coverage_score = (covered / len(prompt_constraints)) if prompt_constraints else 1.0
        gap_magnitude = p_ttr - r_ttr # Simplified heuristic
        
        status = "SUFFICIENT" if coverage_score > 0.8 and gap_magnitude < 0.2 else "INSUFFICIENT"
        
        return {
            "status": status,
            "metrics": {
                "prompt_diversity": round(p_ttr, 3),
                "response_diversity": round(r_ttr, 3),
                "constraint_coverage": f"{covered}/{len(prompt_constraints)}" if prompt_constraints else "N/A",
                "variety_gap": round(gap_magnitude, 3)
            },
            "missing_dimensions": missing,
            "recommendation": self._generate_rec(status, missing, gap_magnitude)
        }

    def _generate_rec(self, status: str, missing: List[str], gap: float) -> str:
        if status == "SUFFICIENT":
            return "Requisite variety met. No urgent injection needed."
        
        recs = []
        if missing:
            recs.append(f"Address missed constraints: {', '.join([m[:50]+'...' for m in missing])}")
        if gap > 0.3:
            recs.append("Response is too repetitive or narrow. Force the agent to explore opposing viewpoints (Dialectical Prompting).")
        
        return " | ".join(recs)

if __name__ == "__main__":
    # Simple CLI interface
    import argparse
    parser = argparse.ArgumentParser(description="Cortana Variety Auditor - Audit LLM response against task complexity.")
    parser.add_argument("--prompt", required=True, help="The input prompt used.")
    parser.add_argument("--response", required=True, help="The resulting output to audit.")
    args = parser.parse_args()

    auditor = VarietyAuditor()
    result = auditor.audit(args.prompt, args.response)
    
    print(f"\n--- VARIETY AUDIT RESULT ---")
    print(f"Status:     {result['status']}")
    print(f"Metrics:    {result['metrics']}")
    if result['missing_dimensions']:
        print(f"Missing Dim: {len(result['missing_dimensions'])} items flagged")
    print(f"Recs:       {result['recommendation']}")
    print(f"--------------------------\n")
