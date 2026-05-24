#!/usr/bin/env python3
"""
IBM Quantum Job Submitter — c0rtana integration following DC Network pattern.

Usage:
    python3 quantum_job_submitter.py --submit <prediction_id> "<circuit_description>"
    python3 quantum_job_submitter.py --list
    python3 quantum_job_submitter.py --grade <job_id> <actual_outcome>

Follows the established DC Network pattern: pre-register → execute → log → grade.
Targets ibm_marrakesh (156-qubit Heron-r2) via IBM Quantum Platform REST API.
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from qiskit import QuantumCircuit, transpile
    from qiskit_ibm_runtime import QiskitRuntimeService, Session, SamplerV2 as Sampler
except ImportError as e:
    print(f"ERROR: Missing dependency - {e}")
    print("Install with: pip install qiskit-ibm-runtime")
    exit(1)


# Paths
STATE_DIR = Path(__file__).parent
PREDICTIONS_FILE = STATE_DIR.parent / "state" / "predictions" / "grades.jsonl"
DEBUG_MODE = os.environ.get("QUANTUM_DEBUG", "false").lower() == "true"


def get_service():
    """Initialize QiskitRuntimeService — uses IBM_QUANTUM_API_TOKEN env var."""
    if DEBUG_MODE:
        # Use fake service for testing without credentials
        try:
            from qiskit_ibm_runtime.fake_provider import FakeMarrakeshV2
            backend_cls = FakeMarrakeshV2
        except ImportError:
            from qiskit_ibm_runtime.fake_provider import FakeMarrakesh
            backend_cls = FakeMarrakesh
        return {"backend": backend_cls()}
    
    try:
        return QiskitRuntimeService(channel="ibm_quantum")
    except Exception as e:
        print(f"ERROR: Failed to initialize QiskitRuntimeService: {e}")
        print("Set IBM_QUANTUM_API_TOKEN environment variable and retry.")
        exit(1)


def create_bell_state_circuit():
    """Create a simple Bell state circuit (maximally entangled pair)."""
    qc = QuantumCircuit(2, 2)
    qc.h(0)           # Hadamard on qubit 0
    qc.cx(0, 1)       # CNOT — creates entanglement
    qc.measure([0, 1], [0, 1])
    return qc


def submit_job(prediction_id: str, description: str) -> dict:
    """Submit a quantum job to ibm_marrakesh."""
    
    if DEBUG_MODE:
        from qiskit_ibm_runtime import Sampler
        from qiskit_ibm_runtime.fake_provider import FakeMarrakesh
        
        print("[DEBUG] Using fake Marrakesh for testing (no credentials needed)")
        backend = FakeMarrakesh()
        qc = create_bell_state_circuit()
        transpiled = transpile(qc, backend=backend)
        sampler = Sampler(mode=backend)
        job = sampler.run([transpiled])
        job_id = "FAKE_" + prediction_id  # Fake ID for debug mode
        print(f"[DEBUG] Job submitted (fake): {job_id}")
    else:
        service = get_service()
        backend = service.backend("ibm_marrakesh")
        print(f"[REAL] Submitting to ibm_marrakesh ({backend.configuration().num_qubits}-qubit Heron-r2)")
        
        with Session(service=service, backend=backend) as session:
            sampler = Sampler(mode=session)
            qc = create_bell_state_circuit()
            transpiled = transpile(qc, backend=backend)
            job = sampler.run([transpiled], precision=0.01)
            job_id = job.job_id()
    
    # Store prediction metadata
    entry = {
        "id": prediction_id,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id,
        "description": description,
        "status": "submitted"
    }
    
    # Append to predictions log
    PREDICTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PREDICTIONS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    print(f"✓ Job submitted: {job_id}")
    return entry


def list_jobs():
    """List all jobs from predictions log."""
    if not PREDICTIONS_FILE.exists():
        print("No jobs recorded yet.")
        return
    
    print("\n=== Quantum Jobs Log ===\n")
    with open(PREDICTIONS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line == "[]":  # Skip empty lines and array markers
                continue
            try:
                entry = json.loads(line)
                if isinstance(entry, dict):
                    print(f"ID: {entry.get('id', 'N/A')}")
                    print(f"  Submitted: {entry.get('submitted_at', 'N/A')}")
                    print(f"  Job ID: {entry.get('job_id', 'N/A')}")
                    print(f"  Status: {entry.get('status', 'unknown')}")
                    print()
            except json.JSONDecodeError:
                continue


def grade_job(job_id: str, actual_outcome: float):
    """Grade a job's outcome against prediction."""
    # Find the entry
    entries = []
    with open(PREDICTIONS_FILE) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    
    target = None
    for e in entries:
        if e.get("job_id") == job_id or e.get("id") == job_id:
            target = e
            break
    
    if not target:
        print(f"ERROR: No entry found for {job_id}")
        return
    
    # Calculate Brier score (simplified — assumes binary prediction)
    predicted_prob = target.get("predicted_probability", 0.5)
    brier_score = (predicted_prob - actual_outcome) ** 2
    
    graded_entry = {
        "id": target["id"],
        "job_id": job_id,
        "graded_at": datetime.now(timezone.utc).isoformat(),
        "actual_outcome": actual_outcome,
        "predicted_probability": predicted_prob,
        "brier_score": brier_score,
        "status": "graded"
    }
    
    # Replace the entry
    with open(PREDICTIONS_FILE, "w") as f:
        for e in entries:
            if e.get("job_id") == job_id or e.get("id") == job_id:
                json.dump(graded_entry, f)
                f.write("\n")
            elif e.get("job_id") or e.get("id"):  # keep other entries
                json.dump(e, f)
                f.write("\n")
    
    print(f"✓ Job graded: Brier score = {brier_score:.4f}")


def main():
    parser = argparse.ArgumentParser(description="IBM Quantum Job Submitter — c0rtana integration")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # --submit
    submit_parser = subparsers.add_parser("submit", help="Submit a quantum job")
    submit_parser.add_argument("prediction_id", help="Unique prediction ID (e.g., P_C499_TEST)")
    submit_parser.add_argument("description", help="Circuit description / prediction")
    
    # --list
    subparsers.add_parser("list", help="List all jobs")
    
    # --grade
    grade_parser = subparsers.add_parser("grade", help="Grade a job's outcome")
    grade_parser.add_argument("job_id", help="Job ID or prediction ID")
    grade_parser.add_argument("actual_outcome", type=float, help="Actual outcome (0-1)")
    
    args = parser.parse_args()
    
    if args.command == "submit":
        submit_job(args.prediction_id, args.description)
    elif args.command == "list":
        list_jobs()
    elif args.command == "grade":
        grade_job(args.job_id, args.actual_outcome)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
