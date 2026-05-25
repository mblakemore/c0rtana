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
from datetime import datetime


def probe_endpoint(ip: str, path: str, timeout: int = 5) -> dict:
    """Probe a single HTTP endpoint and return structured result."""
    url = f"http://{ip}{path}"
    start = datetime.utcnow()
    
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read().decode("utf-8")
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            
            try:
                parsed = json.loads(data) if data.strip() else {}
            except json.JSONDecodeError:
                parsed = {"raw": data[:200]}  # Truncate long responses
            
            return {
                "url": url,
                "status_code": response.status,
                "elapsed_ms": round(elapsed, 2),
                "success": True,
                "response": parsed
            }
    except urllib.error.HTTPError as e:
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        return {
            "url": url,
            "status_code": e.code,
            "error": str(e.reason),
            "elapsed_ms": round(elapsed, 2),
            "success": False
        }
    except urllib.error.URLError as e:
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        return {
            "url": url,
            "error": str(e.reason),
            "elapsed_ms": round(elapsed, 2),
            "success": False
        }
    except Exception as e:
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
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
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z\n")

    endpoints = ["/", "/api/sensor/motion"]
    results = []

    for path in endpoints:
        result = probe_endpoint(args.ip, path)
        results.append(result)
        
        status = "✓ OK" if result["status_code"] == 200 else f"✗ {result.get('status_code', 'ERROR')}"
        print(f"{path}: {status} ({result['elapsed_ms']}ms)")
        
        if args.verbose and result.get("response"):
            print(f"  Response: {json.dumps(result['response'], indent=2)}")
    
    # Summary diagnosis
    print("\n=== Diagnosis ===")
    root_ok = any(r["url"].endswith("/") and r["success"] for r in results)
    motion_ok = any("/sensor/motion" in r["url"] and r["status_code"] == 200 for r in results)
    
    if not root_ok:
        print("⚠ Root endpoint unreachable — ESP32 HTTP server may be down or OTA failed completely")
        print("   Action: Check device power/reboot; verify firmware upload completed successfully")
    elif motion_ok:
        print("✓ Both endpoints responding — /api/sensor/motion is operational")
        print("   Next: Coordinator CLI can poll motion data")
    else:
        print("⚠ Root OK but /api/sensor/motion returns 404")
        print("   Likely causes:")
        print("     1. Firmware uploaded but route not registered (needs reboot)")
        print("     2. Endpoint code not included in current build")
        print("     3. OTA update corrupted/incomplete")
        print("   Action: Request device reboot OR re-flash with verified .bin file")

    # Output JSON summary for logging
    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "target_ip": args.ip,
        "endpoints_probed": len(endpoints),
        "root_endpoint_ok": root_ok,
        "motion_endpoint_ok": motion_ok,
        "diagnosis": "OK" if motion_ok else ("SERVER_DOWN" if not root_ok else "ROUTE_MISSING"),
        "results": results
    }
    
    print(f"\n=== JSON Summary ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
