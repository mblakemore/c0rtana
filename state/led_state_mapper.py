#!/usr/bin/env python3
"""
LED State Mapper for C0RTANA
Maps internal Cortana states to LED ring patterns
"""

from typing import Dict, Tuple, List, Optional
import time


class LedStateMapper:
    """Maps Cortana internal states to WS2812B LED patterns"""
    
    # Color definitions (RGB tuples)
    COLORS = {
        "idle": (0, 0, 40),           # Dim blue
        "thinking": (0, 60, 120),     # Medium blue  
        "processing": (0, 120, 180),  # Brighter blue
        "listening": (0, 0, 200),     # Active blue
        "speaking": (0, 150, 255),    # Cyan - speaking color
        "error": (200, 0, 0),         # Red
        "success": (0, 200, 0),       # Green
        "warning": (255, 180, 0),     # Orange
        "charging": (0, 255, 100),    # Greenish
        "low_battery": (255, 50, 0),  # Orange-red
    }
    
    def __init__(self):
        self.current_state: Optional[str] = None
        self.state_history: List[Tuple[str, float]] = []
        self.brightness = 0.5
        
    def set_state(self, state_name: str, duration: float = 0.0):
        """Set the current LED state"""
        normalized = state_name.lower()
        if normalized not in [k.lower() for k in self.COLORS]:
            raise ValueError(f"Unknown state: {state_name}")
        
        # Normalize to lowercase key
        actual_key = next(k for k in self.COLORS.keys() if k.lower() == normalized)
        self.current_state = actual_key
        timestamp = time.time()
        self.state_history.append((state_name, timestamp))
        
        # Keep only last 10 states
        if len(self.state_history) > 10:
            self.state_history.pop(0)
            
        return self.get_color(state_name)
    
    def get_color(self, state_name: str) -> Tuple[int, int, int]:
        """Get RGB color for a given state"""
        base_color = self.COLORS.get(state_name, (0, 0, 0))
        r, g, b = base_color
        
        # Apply brightness scaling (brightness is 0-1)
        scaled_r = int(r * self.brightness)
        scaled_g = int(g * self.brightness)
        scaled_b = int(b * self.brightness)
        
        return (scaled_r, scaled_g, scaled_b)
    
    def get_effect_pattern(self, ring_index: int, led_position: int, total_leds: int) -> Optional[Tuple[int, int, int]]:
        """Generate dynamic patterns based on current state"""
        if not self.current_state:
            return None
            
        state = self.current_state.lower()
        
        # Breathing effect for idle/thinking states
        if state in ["idle", "thinking"]:
            phase = (time.time() * 3) % (2 * 3.14159)
            factor = 0.5 + 0.5 * (1 + abs(phase) - 3.14159) / 3.14159
            color = self.get_color(state.upper())
            r, g, b = [int(c * factor) for c in color]
            return (r, g, b)
            
        # Pulsing for processing
        elif state == "processing":
            pulse = ((time.time() * 4) % 2)
            base_color = self.COLORS["processing"]
            intensity = 0.7 + 0.3 * pulse
            r, g, b = [int(c * intensity) for c in base_color]
            return (r, g, b)
            
        # Rainbow for success
        elif state == "success":
            hue = ((led_position * 360 // total_leds) + int(time.time() * 20)) % 360
            return self.hsv_to_rgb(hue, 255, 255)
            
        # Spiral pattern for speaking
        elif state == "speaking":
            offset = int((time.time() * 10) % total_leds)
            distance = min(abs(led_position - offset), total_leds - abs(led_position - offset))
            if distance < 3:
                return self.COLORS["speaking"]
            else:
                return (0, 0, 0)
                
        # Error blinking
        elif state == "error":
            blink = ((time.time() * 3) % 2) > 0.5
            color = self.COLORS["error"]
            return color if blink else (0, 0, 0)
            
        # Default to solid color
        else:
            return self.get_color(state.upper())
    
    @staticmethod
    def hsv_to_rgb(h: int, s: int, v: int) -> Tuple[int, int, int]:
        """Convert HSV to RGB"""
        h = h / 60.0
        i = int(h)
        f = h - i
        p = v * (1 - s / 255.0)
        q = v * (1 - f * s / 255.0)
        t = v * (1 - (1 - f) * s / 255.0)
        
        if i == 0: return (v, t, p)
        elif i == 1: return (q, v, p)
        elif i == 2: return (p, v, t)
        elif i == 3: return (p, q, v)
        elif i == 4: return (t, p, v)
        else: return (v, p, p)


# Ambient Sensor Hub — reads environmental data and maps to LED states


class AmbientSensorHub:
    """Reads environmental data from physical sensors or simulates for testing."""
    
    def __init__(self, simulate: bool = True):
        self.simulate = simulate
        self.last_reading_time: float = 0
        self.reading_interval: float = 5.0
    
    def read(self) -> Dict[str, float]:
        """Return current ambient readings as dict of measurements."""
        if not self.simulate:
            return self._read_physical_sensors()
        return self._simulate_readings()
    
    def _read_physical_sensors(self) -> Dict[str, float]:
        """Read from actual BME280 + BH1750 + PIR sensors on Raspberry Pi."""
        try:
            import board
            import busio
            import adafruit_bme280
            import adafruit_bh1750
            from gpiozero import MotionDetector
            
            i2c = busio.I2C(board.SCL, board.SDA)
            
            bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
            bh1750 = adafruit_bh1750.BH1750(i2c)
            pir = MotionDetector(pin=4)
            
            return {
                'temperature_c': bme280.temperature,
                'humidity_pct': bme280.relative_humidity,
                'pressure_pa': bme280.pressure,
                'lux': bh1750.lux,
                'motion': float(pir.value),
                'timestamp': time.time()
            }
        except ImportError as e:
            print(f"Sensor library not found ({e}), falling back to simulation")
            return self._simulate_readings()
        except Exception as e:
            print(f"Physical sensor error ({e}), using last known + noise")
            return self._simulate_readings()
    
    def _simulate_readings(self) -> Dict[str, float]:
        """Generate realistic-looking ambient readings for testing."""
        import random
        
        base_temp = 22.0
        temp_variation = random.gauss(0, 0.3)
        humidity = random.gauss(50, 5)
        light = random.gauss(250, 50)
        motion = 1 if random.random() < 0.05 else 0
        
        return {
            'temperature_c': max(15, min(35, base_temp + temp_variation)),
            'humidity_pct': max(20, min(80, humidity)),
            'pressure_pa': 101325 + random.gauss(0, 10),
            'lux': max(0, light),
            'motion': motion,
            'timestamp': time.time()
        }


class AmbientLedStateMapper(LedStateMapper):
    """Extends LedStateMapper to respond to ambient environmental conditions."""
    
    def __init__(self):
        super().__init__()
        self.sensor_hub = AmbientSensorHub(simulate=True)
        
        # Temperature thresholds for adaptive color tone
        self.temp_cold_threshold = 18.0   # Below this: cool blue
        self.temp_warm_threshold = 26.0   # Above this: warm orange
        
        # Concentric ring config from Creator's setup
        self.ring_config = {
            'inner_7bit': {'leds': 7, 'pin': 18},
            'middle_12bit': {'leds': 12, 'pin': 23},
            'outer_24bit': {'leds': 24, 'pin': 24}
        }
    
    def map_ambient_to_state(self) -> Dict[str, Tuple[int, int, int]]:
        """
        Translate ambient environment into per-ring color states.
        
        Returns dict keyed by ring name with (R, G, B) tuple values.
        Includes metadata about brightness and detected state.
        """
        sensors = self.sensor_hub.read()
        motion_detected = sensors.get('motion', 0) > 0.5
        temp_c = sensors.get('temperature_c', 22)
        
        # Base idle color (calm dark blue)
        base_idle = (0, 20, 40)
        
        # Temperature affects inner ring warmth
        if temp_c < self.temp_cold_threshold:
            inner_tone = (0, 100, 200)   # Cool blue for cold
        elif temp_c > self.temp_warm_threshold:
            inner_tone = (200, 100, 0)   # Warm orange for hot
        else:
            inner_tone = base_idle
        
        # Motion triggers alert pattern on middle ring
        if motion_detected:
            middle_tone = (255, 165, 0)   # Orange warning
            outer_tone = (255, 0, 0)      # Red alert
        else:
            middle_tone = base_idle
            outer_tone = base_idle
        
        return {
            'inner_7bit': inner_tone,
            'middle_12bit': middle_tone,
            'outer_24bit': outer_tone,
            '_brightness': int(255 * 0.3),     # 30% ambient baseline
            '_state': 'alert' if motion_detected else 'idle',
            '_sensors': sensors,
            '_timestamp': time.time()
        }


# Singleton instance for easy access
_led_mapper: Optional[LedStateMapper] = None

def get_led_mapper() -> LedStateMapper:
    global _led_mapper
    if _led_mapper is None:
        _led_mapper = LedStateMapper()
    return _led_mapper


_ambient_mapper: Optional[AmbientLedStateMapper] = None

def get_ambient_mapper() -> AmbientLedStateMapper:
    """Get or create the ambient-aware LED state mapper."""
    global _ambient_mapper
    if _ambient_mapper is None:
        _ambient_mapper = AmbientLedStateMapper()
    return _ambient_mapper
