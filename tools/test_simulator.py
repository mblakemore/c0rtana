#!/usr/bin/env python3
"""Quick test of motion sensor simulation logic."""

import json
from datetime import datetime, timezone

# Simplified version matching rings.ino lines 51-60
class MotionSensor:
    def __init__(self):
        self.motion_detected = False
        self.last_debounce_time = 0
        self.debounce_ms = 200
    
    def update(self):
        current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        if current_time - self.last_debounce_time > self.debounce_ms:
            # Random motion event (~5% probability)
            new_reading = random.random() < 0.05
            if new_reading != self.motion_detected:
                self.motion_detected = new_reading
                self.last_debounce_time = current_time

import random
sensor = MotionSensor()

print("Testing ESP32 motion simulator logic:")
for i in range(10):
    sensor.update()
    state = {
        "sensor": "motion",
        "value": sensor.motion_detected,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    print(f"  {i+1}: {json.dumps(state)}")
