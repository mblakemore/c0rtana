#!/usr/bin/env python3
"""
ESP32 Health Check Script
Probes ESP32 HTTP endpoints to diagnose firmware status and endpoint availability.
Usage: python3 scripts/esp32_health_check.py [--ip <IP>] [--verbose]
Default IP: 192.168.4.38
"""

import argparse
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone


def probe_endpoint(ip: str, path: str, timeout: int = 5) -> dict:
    """Probe a single HTTP endpoint and return structured result."""
    url = f"http://{ip}{path}"
    start = datetime.now(timezone.utc)

    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read().decode("utf-8")
            elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000

            try:
                parsed = json.loads(data) if data.strip() else {}
            except json.JSONDecodeError:
                parsed = {"raw": data[:200]}

            return {
                "url": url,
                "status_code": response.status,
                "elapsed_ms": round(elapsed, 2),
                "success": True,
                "response": parsed
            }
    except urllib.error.HTTPError as e:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        return {
            "url": url,
            "status_code": e.code,
            "error": str(e.reason),
            "elapsed_ms": round(elapsed, 2),
            "success": False
        }
    except urllib.error.URLError as e:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        return {
            "url": url,
            "error": str(e.reason),
            "elapsed_ms": round(elapsed, 2),
            "success": False
        }
    except Exception as e:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        return {
            "url": url,
            "error": str(e),
            "elapsed_ms": round(elapsed, 2),
            "success": False
        }


def main():
    parser = argparse.ArgumentParser(description="ESP32 HTTP endpoint health check")
    parser.add_argument("--ip", default="192.168.4.38", help="ESP32 IP address")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print(f"=== ESP32 Health Check ===")
    print(f"Target: {args.ip}")
    now = datetime.now(timezone.utc)
    print(f"Timestamp: {now.isoformat()}\n")

    endpoints = [
        "/",
        "/status",
        "/api/sensor/touch",
        "/api/sensor/touch/history",
        "/api/sensor/dht",
        "/api/sensor/temp",
        "/api/sensor/humidity",
    ]
    results = []

    for path in endpoints:
        result = probe_endpoint(args.ip, path)
        results.append(result)

        status = "OK" if result.get("status_code") == 200 else f"FAIL {result.get('status_code', '?')}"
        print(f"{path}: {status} ({result['elapsed_ms']}ms)")

        if args.verbose and result.get("response"):
            print(f"  Response: {json.dumps(result['response'], indent=2)}")

    # Summary diagnosis
    print("\n=== Diagnosis ===")
    root_ok = any(r["url"].endswith("/") and r.get("success") for r in results)
    status_ok = any(r["url"].endswith("/status") and r.get("success") for r in results)
    sensors = [r for r in results if "/api/sensor" in r["url"] and r.get("success")]
    sensors_ok = len(sensors) >= 3  # touch, dht, temp/humidity

    if not root_ok:
        print("ESP32 root endpoint unreachable — HTTP server may be down")
        print("   Action: Check device power/reboot")
    elif status_ok and sensors_ok:
        print(f"ESP32 fully operational — {len(sensors)}/5 sensor endpoints responding")
    elif status_ok:
        print(f"ESP32 status OK — {len(sensors)}/5 sensor endpoints responding")
    else:
        print("Root OK but sensor endpoints partial — check DHT/touch wiring")

    # Output JSON summary for logging
    summary = {
        "timestamp": now.isoformat(),
        "target_ip": args.ip,
        "endpoints_probed": len(endpoints),
        "root_ok": root_ok,
        "status_ok": status_ok,
        "sensors_ok": sensors_ok,
        "sensors_responding": len(sensors),
        "diagnosis": "OK" if (status_ok and sensors_ok) else ("PARTIAL" if root_ok else "DOWN"),
        "results": results
    }

    print(f"\n=== JSON Summary ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
