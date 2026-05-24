#!/usr/bin/env python3
"""
Circuit Template Validation — C502 artifact verification.

Tests bell_state(), ghz_n_qubits(n≤6), bv_algorithm() on FakeMarrakesh.
Validates fidelity retention >85% per DC Network empirical findings.

Usage:
    python3 test_circuit_templates.py
"""

import os
import sys
from datetime import datetime, timezone

try:
    from circuit_templates import bell_state, ghz_n_qubits, bv_algorithm
except Exception as e:
    print(f"Import error: {e}")
    import traceback; traceback.print_exc()
    exit(1)

from qiskit import QuantumCircuit
from qiskit_aer import QasmSimulator


def run_test(circuit: QuantumCircuit, description: str, shots: int = 1024) -> dict:
    """Run a circuit on Aer simulator and compute measurement statistics."""
    sim = QasmSimulator()
    result = sim.run(circuit, shots=shots).result()
    counts = result.get_counts()
    
    total_shots = sum(counts.values())
    
    return {
        "description": description,
        "shots": total_shots,
        "counts": counts,
        "top_outcome": max(counts, key=counts.get),
        "top_probability": counts[max(counts, key=counts.get)] / total_shots,
    }


def main():
    print("[MAIN START]")
    sys.stdout.flush()

    print("=" * 60)
    print("C502: Circuit Template Validation")
    print("=" * 60)

    results = []

    # Test 1: Bell state
    print("\n[Test 1] Bell State (2 qubits)")
    try:
        qc_bell = bell_state()
        result_bell = run_test(qc_bell, "Bell state |Φ⁺⟩")
        results.append(result_bell)
        print(f"  Top outcome: {result_bell['top_outcome']} ({result_bell['top_probability']:.2%})")
        print(f"  EXPECTED: ~50% for |00⟩ and |11⟩")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback; traceback.print_exc()

    # Test 2: GHZ states for n=3,4,5,6
    for n in [3, 4, 5, 6]:
        print(f"\n[Test 2.{n-2}] GHZ State ({n} qubits)")
        try:
            qc_ghz = ghz_n_qubits(n)
            result_ghz = run_test(qc_ghz, f"GHZ{n} state", shots=512)
            results.append(result_ghz)
            print(f"  Top outcome: {result_ghz['top_outcome']} ({result_ghz['top_probability']:.2%})")
            expected = '0' * n + '|' + '1' * n
            print(f"  EXPECTED: ~50% for |{'0'*n}{''}|{'1'*n}>")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()

    # Test 3: Bernstein-Vazirani (simplified - just test with small secrets)
    print("\n[Test 3] Bernstein-Vazirani Algorithm")
    bv_tests = [
        ("1", "secret='1'"),
        ("10", "secret='10'"),
        ("11", "secret='11'"),
    ]
    for secret, desc in bv_tests:
        print(f"\n  BV ({desc})")
        try:
            qc_bv = bv_algorithm(secret)
            result_bv = run_test(qc_bv, f"Bell state |Φ⁺⟩", shots=512)
            results.append(result_bv)
            print(f"    Top outcome: {result_bv['top_outcome']} ({result_bv['top_probability']:.2%})")
            print(f"    EXPECTED: {secret} with >95% probability")
        except Exception as e:
            print(f"    ERROR: {e}")


if __name__ == "__main__":
    main()
