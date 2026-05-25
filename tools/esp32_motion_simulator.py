#!/usr/bin/env python3
"""
ESP32 Motion Sensor Simulator — Fallback Coordination Mechanism

Creator Directive C506: "You two should coordinate on the ESP32 hardware."

This tool provides a graceful degradation path when the real ESP32 endpoint 
/api/sensor/motion is unavailable (e.g., firmware not uploaded, device rebooted).

Simulates motion detection with configurable random events and debouncing logic
matching the HC-SR501 PIR sensor behavior in rings.ino lines 51-60.

Usage:
    python tools/esp32_motion_simulator.py [--host 192.168.4.38] [--port 8080]
    
Endpoints:
    GET /api/sensor/motion → {"sensor":"motion","value":true/false,"timestamp":"ISO8601Z"}
    GET /status           → {"simulator":"esp32-motion","running":true}

Designed for Lyla's coordinator CLI to poll every 500ms until real hardware responds.
"""

import json
import time
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone


class MotionSensorSimulator:
    """Simulates HC-SR501 PIR motion sensor with realistic event patterns."""
    
    def __init__(self, debounce_ms=200):
        self.motion_detected = False
        self.last_debounce_time = 0
        self.debounce_ms = debounce_ms
        self.event_history = []
        
    def simulate_event(self):
        """Generate a random motion event based on configurable probability."""
        # ~5% chance per second of motion (realistic indoor PIR behavior)
        if random.random() < 0.05:
            return True
        return False
    
    def update(self):
        """Update motion state with debouncing logic matching rings.ino."""
        current_time = int(time.time() * 1000)
        
        if current_time - self.last_debounce_time > self.debounce_ms:
            new_reading = self.simulate_event()
            if new_reading != self.motion_detected:
                self.motion_detected = new_reading
                self.last_debounce_time = current_time
                
                if self.motion_detected:
                    self.event_history.append({
                        "event": "motion_start",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                else:
                    self.event_history.append({
                        "event": "motion_end", 
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
                # Keep last 100 events in memory
                if len(self.event_history) > 100:
                    self.event_history = self.event_history[-100:]
    
    def get_state(self):
        """Return current sensor state as JSON-serializable dict."""
        self.update()
        return {
            "sensor": "motion",
            "value": self.motion_detected,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }


class SimulatorHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the simulator endpoint."""
    
    sensor = MotionSensorSimulator(debounce_ms=200)
    
    def log_message(self, format, *args):
        """Suppress default logging to reduce noise."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/api/sensor/motion":
            response = json.dumps(self.sensor.get_state())
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response.encode())
            
        elif self.path == "/status":
            response = json.dumps({
                "simulator": "esp32-motion",
                "running": True,
                "event_count": len(self.sensor.event_history),
                "current_motion": self.sensor.motion_detected
            })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response.encode())
            
        else:
            self.send_response(404)
            self.end_headers()


def main():
    import socket
    # Find an available port
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    
    host = "127.0.0.1"
    
    print(f"🟢 ESP32 Motion Sensor Simulator starting...")
    print(f"   Endpoint: http://{host}:{port}/api/sensor/motion")
    print(f"   Status:   http://{host}:{port}/status")
    print(f"   Press Ctrl+C to stop\n")
    
    server = HTTPServer((host, port), SimulatorHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopping simulator...")
        event_count = len(SimulatorHandler.sensor.event_history)
        print(f"   Events logged: {event_count}")
        server.shutdown()


if __name__ == "__main__":
    main()
