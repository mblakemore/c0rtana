import json
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

class AgentTrace:
    """
    A lightweight telemetry wrapper for Agentic Workflows.
    Provides a way to track 'Cognitive Spans' (phases of thought) 
    and log them to a JSONL file for external analysis.
    Designed as a general purpose utility independent of specific agent frameworks.
    """
    def __init__(self, session_id: str = None, log_file: str = "agent_telemetry.jsonl"):
        self.session_id = session_id or str(uuid.uuid4())
        self.log_file = log_file
        self.active_spans: List[Dict[str, Any]] = []

    def start_span(self, phase_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Marks the beginning of a cognitive phase (e.g., 'Reflection', 'Tool Use')."""
        span = {
            "span_id": str(uuid.uuid4()),
            "session_id": self.session_id,
            "phase": phase_name,
            "start_time": time.time(),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        self.active_spans.append(span)
        return span["span_id"]

    def end_span(self, span_id: str, outcome: str = "success", confidence: float = 1.0, thoughts: str = ""):
        """Closes a phase and commits the record to the telemetry log."""
        for span in self.active_spans:
            if span["span_id"] == span_id:
                span["end_time"] = time.time()
                span["duration"] = span["end_time"] - span["start_time"]
                span["outcome"] = outcome
                span["confidence"] = confidence
                span["thoughts"] = thoughts
                
                self._flush(span)
                self.active_spans.remove(span)
                return True
        return False

    def _flush(self, record: Dict[str, Any]):
        """Persists the record to JSONL."""
        with open(self.log_file, "a") as f:
            f.write(json.dumps(record) + "\n")

# --- Test Implementation / Demonstration ---
if __name__ == "__main__":
    # Simulate an agent using the telemetry tool
    trace = AgentTrace(session_id="C177_Validation_Run")
    
    print(f"Starting trace session: {trace.session_id}")
    
    # Phase 1: Perception
    s1 = trace.start_span("Perception", {"input_length": 500})
    time.sleep(0.1) # Simulate work
    trace.end_span(s1, thoughts="Analyzing user prompt for constraints.")
    
    # Phase 2: Planning (Nested logic)
    s2 = trace.start_span("Planning", {"strategy": "chain-of-thought"})
    time.sleep(0.2)
    trace.end_span(s2, confidence=0.9, thoughts="Determined that the agent_trace.py implementation is sufficient.")
    
    # Phase 3: Execution
    s3 = trace.start_span("Execution", {"tool": "python_interpreter"})
    time.sleep(0.1)
    trace.end_span(s3, outcome="success", thoughts="Code written and verified.")
    
    print(f"Telemetry written to {trace.log_file}. Check the file for structured cognitive logs.")
