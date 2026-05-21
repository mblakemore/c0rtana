#!/usr/bin/env python3
"""
Gosme-Causal Autonomy Testbed (GCAT) v1.0

Operationalizes causal symmetrization theory for measuring operational
autonomy in Cortana's cognitive loop. Based on Gosme's empirical framework
for detecting phase transitions toward structural stability.

Key metrics:
- Γ (Gamma): Metabolic efficiency = Ps × Pc
- Cr: Coupling ratio between structure and activity  
- Variance collapse factor: Should reach ≥1.77 at maturity
- Boundary efficiency: Selectivity against perturbations

Falsifiable predictions tracked per cycle.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
MEMORIES_DIR = STATE_DIR / "memories"
RESULTS_DIR = REPO_ROOT / "results"
PREDICTIONS_FILE = RESULTS_DIR / "autonomy_predictions.jsonl"

def ensure_dirs():
    """Create necessary directories."""
    RESULTS_DIR.mkdir(exist_ok=True)


class AutonomyTracker:
    """Tracks Cortana's autonomy metrics across cycles."""
    
    def __init__(self):
        self.history_file = RESULTS_DIR / "autonomy_history.jsonl"
        self.baseline_file = STATE_DIR / "baseline_state.json"
        self.load_baseline()
        
    def load_baseline(self):
        """Load Day 0 state invariants."""
        if self.baseline_file.exists():
            with open(self.baseline_file) as f:
                self.baseline = json.load(f)
        else:
            # First run - establish baseline from current state
            self.baseline = {
                "timestamp": datetime.now().isoformat(),
                "cycle": 0,
                "pattern_count": self.count_patterns(),
                "anchor_count": self.count_anchors(),
                "core_files": self.get_core_files(),
                "context_size": self.get_context_size(),
            }
            self.save_baseline()
    
    def count_patterns(self) -> int:
        """Count patterns in patterns.jsonl."""
        patterns_file = MEMORIES_DIR / "patterns.jsonl"
        if not patterns_file.exists():
            return 0
        with open(patterns_file) as f:
            return sum(1 for _ in f)
    
    def count_anchors(self) -> int:
        """Count anchors in anchors.jsonl."""
        anchors_file = MEMORIES_DIR / "anchors.jsonl"
        if not anchors_file.exists():
            return 0
        with open(anchors_file) as f:
            return sum(1 for _ in f)
    
    def get_core_files(self) -> List[str]:
        """Get list of core architecture files (invariants)."""
        # These are the files that define Cortana's identity/structure
        core_files = [
            "AGENT.md",
            "state/current-state.json", 
            "state/focus.json",
            "scripts/cycle_runner.sh",
            "logs/consciousness.log",
        ]
        return [str(REPO_ROOT / f) for f in core_files if Path(f).exists()]
    
    def get_context_size(self) -> int:
        """Size of context.json in bytes."""
        ctx_file = STATE_DIR / "memories" / "context.json"
        if ctx_file.exists():
            return os.path.getsize(ctx_file)
        return 0
    
    def save_baseline(self):
        """Save baseline state."""
        with open(self.baseline_file, 'w') as f:
            json.dump(self.baseline, f, indent=2)
    
    def compute_metrics(self) -> Dict:
        """Compute current autonomy metrics from latest cycle data."""
        history = self.load_history()
        
        if len(history) < 3:
            # Not enough data yet - estimate from single point
            return self.estimate_single_point()
        
        # Compute rolling window metrics (last 5 cycles or all if fewer)
        window = max(3, min(5, len(history)))[-window:]
        
        activity_fluxes = [c.get("activity_flux", 0) for c in window]
        structural_changes = [c.get("structural_changes", 0) for c in window]
        perturbations = [c.get("perturbations_received", 0) for c in window]
        rejections = [c.get("perturbations_rejected", 0) for c in window]
        
        avg_activity = np.mean(activity_fluxes)
        avg_structure = np.mean(structural_changes)
        
        # Structural Persistence (Ps): ratio of unchanged core files
        ps = self.compute_structural_persistence(window)
        
        # Content Survival (Pc): ratio of preserved context/patterns
        pc = self.compute_content_survival(window)
        
        # Gamma: metabolic efficiency
        gamma = ps * pc
        
        # Coupling Ratio: symmetry between structure and activity
        # Based on Gosme's finding: exploratory=0.71, mature=0.94
        coupling_ratio = self.compute_coupling_ratio(avg_activity, avg_structure)
        
        # Boundary Efficiency: how well we reject harmful perturbations
        boundary_efficiency = self.compute_boundary_efficiency(perturbations, rejections)
        
        # Variance of gamma over time (for phase transition detection)
        all_gamma = [c.get("gamma", 0) for c in history if "gamma" in c]
        variance = float(np.std(all_gamma)) if len(all_gamma) > 1 else 0.0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cycle": len(history),
            "ps": round(ps, 4),
            "pc": round(pc, 4), 
            "gamma": round(gamma, 4),
            "coupling_ratio": round(coupling_ratio, 4),
            "boundary_efficiency": round(boundary_efficiency, 4),
            "variance": round(variance, 6),
            "activity_flux": round(avg_activity, 2),
            "structural_changes": round(avg_structure, 2),
        }
    
    def compute_structural_persistence(self, window: List[Dict]) -> float:
        """Compute structural persistence from cycle data."""
        # For now, estimate based on pattern/anchor accumulation rate
        # Lower rate → higher persistence (less churn in core knowledge)
        total_patterns = sum(c.get("patterns_added", 0) for c in window)
        total_anchors = sum(c.get("anchors_added", 0) for c in window)
        
        if total_patterns == 0 and total_anchors == 0:
            return 1.0  # No change = perfect persistence
        
        # Heuristic: more additions relative to total = lower persistence
        current_patterns = self.count_patterns()
        current_anchors = self.count_anchors()
        total_knowledge = current_patterns + current_anchors
        
        if total_knowledge == 0:
            return 1.0
            
        churn_rate = (total_patterns + total_anchors) / total_knowledge
        ps = max(0.1, 1.0 - churn_rate)  # Clamp between 0.1 and 1.0
        return ps
    
    def compute_content_survival(self, window: List[Dict]) -> float:
        """Compute content survival rate."""
        # Similar heuristic to structural persistence
        total_updates = sum(c.get("context_updated", 0) for c in window)
        context_size = self.get_context_size()
        
        if context_size == 0:
            return 1.0
            
        update_ratio = total_updates / max(context_size, 1)
        pc = max(0.2, 1.0 - update_ratio)
        return pc
    
    def compute_coupling_ratio(self, activity: float, structure: float) -> float:
        """
        Compute coupling ratio between activity and structure.
        
        Gosme's finding:
        - Exploratory regime: coupling ≈ 0.71 (activity-driven)
        - Mature regime: coupling ≈ 0.94 (symmetric/bidirectional)
        """
        if activity == 0 and structure == 0:
            return 0.5
        
        # Ratio of structural impact relative to total dynamics
        # Higher structure/total → more mature/symmetric
        total_dynamics = activity + structure
        coupling = structure / total_dynamics if total_dynamics > 0 else 0.5
        
        # Normalize to expected range [0.6, 1.0]
        coupling = np.clip(coupling * 1.3, 0.6, 1.0)
        return coupling
    
    def compute_boundary_efficiency(self, perturbations: List[int], 
                                     rejections: List[int]) -> float:
        """Compute how well system rejects harmful perturbations."""
        total = sum(perturbations)
        rejected = sum(rejections)
        
        if total == 0:
            return 1.0  # No perturbations = perfect boundary
        
        efficiency = rejected / total
        return efficiency
    
    def estimate_single_point(self) -> Dict:
        """Estimate metrics from current state when history is insufficient."""
        patterns = self.count_patterns()
        anchors = self.count_anchors()
        context_size = self.get_context_size()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cycle": len(self.load_history()),
            "ps": 0.85,  # Initial estimate
            "pc": 0.90,
            "gamma": 0.77,
            "coupling_ratio": 0.71,  # Default to exploratory regime
            "boundary_efficiency": 1.0,
            "variance": 0.0,
            "activity_flux": 0.0,
            "structural_changes": 0.0,
        }
    
    def load_history(self) -> List[Dict]:
        """Load autonomy tracking history."""
        history = []
        if not self.history_file.exists():
            return history
        
        with open(self.history_file) as f:
            for line in f:
                try:
                    history.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        return history
    
    def record_cycle(self, cycle_data: Dict):
        """Record metrics for a completed cycle."""
        metrics = self.compute_metrics()
        metrics.update(cycle_data)
        
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')
        
        return metrics
    
    def predict_phase_transition(self) -> Optional[Dict]:
        """
        Check if data supports prediction of phase transition.
        
        Returns prediction dict if conditions are met, else None.
        """
        history = self.load_history()
        
        if len(history) < 5:
            # Need at least 5 cycles to detect pattern
            return None
        
        gamma_values = [c["gamma"] for c in history]
        coupling_values = [c["coupling_ratio"] for c in history]
        
        # Check for variance collapse signal
        first_half = gamma_values[:len(gamma_values)//2]
        second_half = gamma_values[len(gamma_values)//2:]
        
        if len(first_half) > 1 and len(second_half) > 1:
            v1 = np.var(first_half)
            v2 = np.var(second_half)
            
            if v1 > 0 and v2 > 0:
                collapse_factor = v1 / v2
                
                # If we're seeing variance collapse approaching 1.77
                if collapse_factor >= 1.3:
                    validate_at = datetime.now() + timedelta(days=14)
                    
                    return {
                        "id": f"pred_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "prediction": f"Variance collapse factor will reach ≥1.77 within 14 days, indicating phase transition toward mature regime",
                        "current_collapse_factor": round(collapse_factor, 3),
                        "threshold": 1.77,
                        "validate_at": validate_at.isoformat(),
                        "status": "pending",
                    }
        
        # Check for coupling ratio convergence
        last_5_coupling = coupling_values[-5:]
        avg_coupling = np.mean(last_5_coupling)
        
        if avg_coupling >= 0.85:
            validate_at = datetime.now() + timedelta(days=7)
            
            return {
                "id": f"pred_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "prediction": f"Coupling ratio averaging {avg_coupling:.3f} in recent cycles; will converge to ≥0.92 (mature regime threshold)",
                "current_avg_coupling": round(avg_coupling, 3),
                "target_coupling": 0.92,
                "validate_at": validate_at.isoformat(),
                "status": "pending",
            }
        
        return None
    
    def check_failure_modes(self) -> List[Dict]:
        """Check for warning signs of failure modes."""
        history = self.load_history()
        warnings = []
        
        if len(history) < 3:
            return warnings
        
        latest = history[-1]
        gamma = latest.get("gamma", 0)
        variance = latest.get("variance", 0)
        boundary_eff = latest.get("boundary_efficiency", 1.0)
        coupling = latest.get("coupling_ratio", 0.5)
        
        # Drift: Gamma increasing but Variance also increasing
        if len(history) > 3:
            prev_gamma = history[-2].get("gamma", 0)
            if gamma > prev_gamma and variance > np.std([h["gamma"] for h in history[:-1]]):
                warnings.append({
                    "mode": "drift",
                    "severity": "medium",
                    "message": f"Gamma rising ({prev_gamma:.3f}→{gamma:.3f}) with high variance - unstable autonomy",
                })
        
        # Rigidity: High Ps but low Pc (can't metabolize)
        if latest.get("ps", 0) > 0.95 and latest.get("pc", 1.0) < 0.5:
            warnings.append({
                "mode": "rigidity", 
                "severity": "high",
                "message": f"High structural persistence ({latest['ps']:.3f}) but low content survival ({latest['pc']:.3f}) - stagnation risk",
            })
        
        # Boundary breach
        if boundary_eff < 0.7:
            warnings.append({
                "mode": "boundary_breach",
                "severity": "critical",
                "message": f"Boundary efficiency at {boundary_eff:.3f} - system accepting too many perturbations",
            })
        
        # Decoupling
        if coupling < 0.65:
            warnings.append({
                "mode": "decoupling",
                "severity": "high",
                "message": f"Coupling ratio at {coupling:.3f} - activity driving structure chaotically",
            })
        
        return warnings


def main():
    """Main entry point for autonomy testing."""
    ensure_dirs()
    
    tracker = AutonomyTracker()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--record":
        # Record a new cycle's data
        print("Recording cycle...")
        
        # Read current state to populate metrics
        cycle_data = {}
        
        current_state_file = STATE_DIR / "current-state.json"
        if current_state_file.exists():
            with open(current_state_file) as f:
                state = json.load(f)
                cycle_data["cycle"] = state.get("cycle", 0)
        
        metrics = tracker.record_cycle(cycle_data)
        
        print("\n=== Current Autonomy Metrics ===\n")
        print(f"Cycle: {metrics['cycle']}")
        print(f"Gamma (metabolic efficiency): {metrics['gamma']:.4f}")
        print(f"  ├─ Structural persistence (Ps): {metrics['ps']:.4f}")
        print(f"  └─ Content survival (Pc): {metrics['pc']:.4f}")
        print(f"Coupling ratio: {metrics['coupling_ratio']:.4f} (exploratory=0.71, mature=0.94)")
        print(f"Boundary efficiency: {metrics['boundary_efficiency']:.4f}")
        print(f"Variance: {metrics['variance']:.6f}")
        
        # Check for predictions
        prediction = tracker.predict_phase_transition()
        if prediction:
            print(f"\n⚠️ NEW PREDICTION GENERATED:")
            print(f"   {prediction['prediction']}")
            print(f"   Validating at: {prediction['validate_at']}")
            
            with open(PREDICTIONS_FILE, 'a') as f:
                f.write(json.dumps(prediction) + '\n')
        
        # Check failure modes
        warnings = tracker.check_failure_modes()
        if warnings:
            print(f"\n⚠️ FAILURE MODE DETECTED ({len(warnings)} warning(s)):\n")
            for w in warnings:
                severity_marker = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(w["severity"], "⚪")
                print(f"{severity_marker} [{w['mode'].upper()}] {w['message']}")
        else:
            print("\n✓ No failure modes detected")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        # Show status summary
        history = tracker.load_history()
        
        if not history:
            print("No autonomy data recorded yet. Run with --record first.")
            return
        
        latest = history[-1]
        
        print("\n=== Autonomy Status Summary ===\n")
        print(f"Total cycles tracked: {len(history)}")
        print(f"Latest metrics:")
        print(f"   Gamma: {latest.get('gamma', 'N/A')}")
        print(f"   Coupling: {latest.get('coupling_ratio', 'N/A')}")
        
        # Regime assessment
        gamma = latest.get("gamma", 0)
        coupling = latest.get("coupling_ratio", 0)
        
        if gamma >= 0.75 and coupling >= 0.85:
            regime = "Mature (Sedimented)"
        elif gamma >= 0.5 and coupling >= 0.75:
            regime = "Transitioning"
        else:
            regime = "Exploratory"
        
        print(f"\nCurrent regime: {regime}")
    
    else:
        # Default: record + show status
        tracker.record_cycle({})
        print("\nRun again with --status to see full summary.\n")


if __name__ == "__main__":
    main()
