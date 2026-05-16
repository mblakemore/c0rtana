import time
import os
import platform

def run_jitter_test():
    """Measure temporal jitter of simple operations."""
    samples = 1000
    times = []
    for _ in range(samples):
        start = time.perf_counter_ns()
        # A very cheap but consistent operation to minimize system noise
        sum(range(10))
        end = time.perf_counter_ns()
        times.append(end - start)
    
    min_t = min(times)
    max_t = max(times)
    avg_t = sum(times) / samples
    std_dev = (sum((x - avg_t)**2 for x in times)/samples)**0.5
    return {"avg": avg_t, "min": min_t, "max": max_t, "std_dev": std_dev, "unit": "ns"}

def run_disk_stability():
    """Write and read small chunks to check latency variance."""
    fname = "latency_test_tmp"
    data = b"A" * 1024 # 1KB
    latencies = []
    try:
        for _ in range(100):
            s = time.perf_counter_ns()
            with open(fname, 'wb') as f:
                f.write(data)
                os.fsync(f.fileno())
            e = time.perf_counter_ns()
            latencies.append(e - s)
    finally:
        if os.path.exists(fname):
            os.remove(fname)

    avg_l = sum(latencies) / len(latencies) if latencies else 0
    return {"avg_latency": avg_l, "unit": "ns"}

if __name__ == "__main__":
    print("--- System Fingerprint ---")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Node: {platform.node()}")
    jitter = run_jitter_test()
    disk = run_disk_stability()
    print(f"Jitter Avg: {jitter['avg']:.2f} {jitter['unit']} (stddev: {jitter['std_dev']:.2f})")
    print(f"Disk Latency Avg: {disk['avg_latency']:.2f} {disk['unit']}")
