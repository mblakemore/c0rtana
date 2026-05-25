#!/usr/bin/env python3
"""
ESP32 Motion Sensor Daemon — Continuous polling with event logging

Creator Directive C506: "You two should coordinate on the ESP32 hardware."

This daemon runs in background, polling the ESP32 motion endpoint every 500ms
and appending detected state changes to state/memories/patterns.jsonl for
persistent tracking across cycles.

Usage:
    nohup python3 scripts/esp32_sensor_daemon.py > logs/sensor.log 2>&1 &
    
    # Check status
    pgrep -f esp32_sensor_daemon
    
    # Stop
    pkill -f esp32_sensor_daemon
"""

#!/usr/bin/env python3 -u
"""ESP32 Motion Sensor Daemon with unbuffered stdout."""

import json
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError


class ESP32MotionDaemon:
    """Polls ESP32 motion sensor and logs events to patterns.jsonl."""
    
    def __init__(self, esp32_host="192.168.4.38", poll_interval_ms=500):
        self.esp32_host = esp32_host
        self.poll_interval_sec = poll_interval_ms / 1000.0
        self.motion_endpoint = f"http://{esp32_host}/api/sensor/motion"
        self.patterns_file = "state/memories/patterns.jsonl"
        
        # Track last value to only log state changes (debouncing)
        self.last_motion_value = None
        self.start_time = datetime.now()
        self.event_count = 0
        
    def poll(self):
        """Fetch current motion state from ESP32."""
        try:
            req = Request(self.motion_endpoint)
            with urlopen(req, timeout=2) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            raise ConnectionError(f"Failed to reach ESP32 at {self.esp32_host}: {e}")
    
    def write_pattern(self, event_type, data):
        """Append pattern to patterns.jsonl for persistent tracking."""
        import os
        os.makedirs("state/memories", exist_ok=True)
        
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            **data
        }
        
        with open(self.patterns_file, "a") as f:
            f.write(json.dumps(record) + "\n")
            
        self.event_count += 1
    
    def run(self):
        """Main polling loop."""
        print(f"🟢 ESP32 Motion Daemon starting...")
        print(f"   Host:     {self.esp32_host}")
        print(f"   Endpoint: {self.motion_endpoint}")
        print(f"   Interval: {self.poll_interval_sec*1000:.0f}ms")
        print(f"   Press Ctrl+C to stop\n")
        
        try:
            while True:
                motion_data = self.poll()
                current_value = motion_data.get("value", False)
                
                # Only log state changes (reduces noise)
                if current_value != self.last_motion_value:
                    event_type = "motion_detected:true" if current_value else "motion_detected:false"
                    
                    self.write_pattern(event_type, {
                        "sensor": motion_data.get("sensor"),
                        "esp32_timestamp": motion_data.get("timestamp"),
                        "simulated": False
                    })
                    
                    status_icon = "🔴 MOTION" if current_value else "⚪ NO MOTION"
                    elapsed = datetime.now() - self.start_time
                    
                    print(f"[{elapsed}] [{datetime.now().strftime('%H:%M:%S')}] {status_icon} ({event_type})")
                    
                    self.last_motion_value = current_value
                
                time.sleep(self.poll_interval_sec)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Daemon stopped.")
            print(f"   Events logged: {self.event_count}")


if __name__ == "__main__":
    # Force unbuffered output for logging
    sys.stdout.reconfigure(line_buffering=True)
    
    daemon = ESP32MotionDaemon(
        esp32_host="192.168.4.38",
        poll_interval_ms=500
    )
    
    daemon.run()
