import time
import math

def compute_pi(n):
    # Simple Leibniz series (slow) or something slightly better
    # For our purposes, we just want a CPU-intensive load that is predictable
    pi = 0
    for i in range(n):
        pi += ((-1)**i) / (2*i + 1)
    return pi * 4

if __name__ == "__main__":
    ITERATIONS = 5_000_000
    start = time.perf_counter_ns()
    result = compute_pi(ITERATIONS)
    end = time.perf_counter_ns()
    duration_ms = (end - start) / 1e6
    print(f"Result: {result}")
    print(f"Duration: {duration_ms:.4f} ms")
    print(f"Timestamp: {time.time()}")
