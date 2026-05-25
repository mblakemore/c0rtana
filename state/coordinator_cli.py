#!/usr/bin/env python3
"""
Coordinating ESP32 Sensor Data with State Memory

Creator Directive C506: "You two should coordinate on the ESP32 hardware."

This CLI polls the ESP32 /api/sensor/motion endpoint and writes detected events
to state/memories/patterns.jsonl for persistent tracking. It implements the
coordination mechanism between Lyla (sensor data source) and c0rtana (state memory).

Usage:
    python state/coordinator_cli.py [--esp32-host IP] [--simulate] [--poll-interval MS]

Endpoints:
    GET http://ESP32_HOST/api/sensor/motion → {"sensor":"motion","value":bool,"timestamp":"ISO8601Z"}

State writes:
    APPEND state/memories/patterns.jsonl ← motion_detected:true/false events
"""

import argparse
import json
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError


class ESP32MotionPoller:
    """Polls ESP32 motion sensor at configurable interval."""
    
    def __init__(self, esp32_host="192.168.4.38", poll_interval_ms=500):
        self.esp32_host = esp32_host
        self.poll_interval_sec = poll_interval_ms / 1000.0
        self.motion_endpoint = f"http://{esp32_host}/api/sensor/motion"
        
    def poll(self):
        """Fetch current motion state from ESP32."""
        try:
            req = Request(self.motion_endpoint)
            with urlopen(req, timeout=2) as response:
                return json.loads(response.read().decode())
        except (URLError, Exception) as e:
            raise ConnectionError(f"Failed to reach ESP32 at {self.esp32_host}: {e}")
    
    def get_timestamp(self):
        """Return ISO8601Z timestamp for local event logging."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_pattern(event_type, data):
    """Append pattern to patterns.jsonl for persistent tracking."""
    import os
    
    patterns_file = "state/memories/patterns.jsonl"
    os.makedirs("state/memories", exist_ok=True)
    
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        **data
    }
    
    with open(patterns_file, "a") as f:
        f.write(json.dumps(record) + "\n")


def run_simulation():
    """Simulate motion events for testing without real hardware."""
    import random
    
    last_motion_state = False
    debounce_counter = 0
    
    print("🟢 SIMULATION MODE — no real ESP32 polling")
    print("   Generating simulated motion events...\n")
    
    try:
        while True:
            # ~5% chance of motion per second (realistic PIR behavior)
            new_motion = random.random() < 0.05
            
            if new_motion != last_motion_state:
                debounce_counter += 1
                
                if debounce_counter >= 4:  # Debounce threshold
                    event_type = "motion_detected:true" if new_motion else "motion_detected:false"
                    
                    write_pattern(event_type, {
                        "simulated": True,
                        "value": new_motion
                    })
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] EVENT: {event_type}")
                    
                    last_motion_state = new_motion
                    debounce_counter = 0
            
            time.sleep(1)  # 1-second simulation tick
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped simulation.")


def run_real_polling():
    """Poll real ESP32 hardware at configured interval."""
    poller = ESP32MotionPoller()
    last_motion_value = None
    
    print(f"🟢 REAL HARDWARE MODE — polling ESP32 at {poller.esp32_host}")
    print("   Endpoint: http://192.168.4.38/api/sensor/motion\n")
    
    try:
        while True:
            motion_data = poller.poll()
            
            current_value = motion_data.get("value", False)
            
            # Only log state changes to reduce noise
            if current_value != last_motion_value:
                event_type = "motion_detected:true" if current_value else "motion_detected:false"
                
                write_pattern(event_type, {
                    "sensor": motion_data.get("sensor"),
                    "timestamp": motion_data.get("timestamp"),
                    "simulated": False
                })
                
                status_icon = "🔴 MOTION" if current_value else "⚪ NO MOTION"
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} ({event_type})")
                
                last_motion_value = current_value
            
            time.sleep(poller.poll_interval_sec)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped real polling.")


def main():
    parser = argparse.ArgumentParser(
        description="Coordinate ESP32 sensor data with c0rtana state memory."
    )
    parser.add_argument(
        "--esp32-host", 
        default="192.168.4.38",
        help="ESP32 IP address (default: 192.168.4.38)"
    )
    parser.add_argument(
        "--simulate", 
        action="store_true",
        help="Run simulation mode without real hardware"
    )
    parser.add_argument(
        "--poll-interval", 
        type=int, 
        default=500,
        help="Polling interval in milliseconds (default: 500)"
    )
    
    args = parser.parse_args()
    
    if args.simulate:
        run_simulation()
    else:
        # Verify ESP32 is reachable before starting
        try:
            ESP32MotionPoller(args.esp32_host).poll()
            print(f"✓ Connected to ESP32 at {args.esp32_host}\n")
        except ConnectionError as e:
            print(f"✗ ERROR: {e}")
            print("\n🟢 FALLING BACK TO SIMULATION MODE")
            time.sleep(2)
            run_simulation()
        
        run_real_polling()


if __name__ == "__main__":
    main()
