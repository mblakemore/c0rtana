#!/usr/bin/env python3
"""
WS2812B LED Driver for C0RTANA Physical Projection System
Maps cortana internal state to RGB ring patterns with autonomous ambient perception layer

Usage:
    python led_driver.py --ring <7|12|24> --color R,G,B --brightness 0-255
    python led_driver.py --all --pattern rainbow
    
Autonomous Ambient Mode:
    Enable environmental sensing → rings react to room conditions independently of cognitive loop

Hardware layout (Creator's concentric setup):
    - Ring 7bit:   Center LED + 6 surrounding (innermost, GPIO 18)
    - Ring 12bit:  Middle ring (GPIO 23)  
    - Ring 24bit:  Outer ring (GPIO 24)

Power requirements: ~2A @ 5V minimum for all rings active
"""

import argparse
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Tuple, Optional, Callable
import threading

try:
    from adafruit_pixelbuf import PixelBuf
    
    # Handle both old and new API for platform detection
    try:
        from adafruit_platformdetect import Detection
        detector = Detection()
        def is_raspberry_pi():
            return detector.is_raspberry_pi()
    except (ImportError, AttributeError):
        # Fallback for older versions
        def is_raspberry_pi():
            import os
            return os.path.exists('/sys/firmware/devicetree/base/model') and 'raspberry' in open('/sys/firmware/devicetree/base/model').read().lower()
            
except ImportError as e:
    print(f"Import error: {e}")
    print("Ensure adafruit-circuitpython-neopixel is installed")
    exit(1)


# ============================================================================
# AUTONOMOUS AMBIENT PERCEPTION LAYER
# ============================================================================


class LEDMode(Enum):
    """Operating mode for the LED system."""
    COGNITIVE_PHASE = auto()     # Controlled by cortana's cognitive cycle via WebSocket/CLI
    AUTONOMOUS_AMBIENT = auto()  # Reacts to environmental sensors independently


@dataclass
class AmbientReading:
    """Environmental sensor reading."""
    ambient_light_lux: float = 0.0      # Current room illumination in lux
    sound_level_db: float = 0.0          # Ambient noise level in dB
    motion_detected: bool = False        # Motion sensor trigger
    timestamp: float = 0.0               # Unix timestamp of reading


@dataclass
class AutonomousPattern:
    """Autonomous visual pattern based on environment."""
    inner_color: Tuple[int, int, int]   # RGB for inner ring (7 LEDs)
    middle_color: Tuple[int, int, int]  # RGB for middle ring (12 LEDs)
    outer_color: Tuple[int, int, int]   # RGB for outer ring (24 LEDs)
    brightness: int = 50                  # 0-255 scale
    effect: str = "solid"                 # solid/pulse/fade/ripple


class SensorSimulator:
    """Simulated sensor data for testing without hardware."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._base_light = 100.0
        self._base_sound = 35.0
        self._motion_events = []
        
    def read(self) -> AmbientReading:
        """Generate simulated ambient reading with realistic variation."""
        import random
        
        with self._lock:
            light_variation = random.gauss(0, 10)
            sound_variation = random.gauss(0, 2)
            
            # Occasional motion events
            motion = len([e for e in self._motion_events if time.time() - e < 5]) > 0
            
            return AmbientReading(
                ambient_light_lux=max(0, self._base_light + light_variation),
                sound_level_db=max(0, self._base_sound + sound_variation),
                motion_detected=motion,
                timestamp=time.time()
            )
    
    def trigger_motion_event(self):
        """Simulate a motion detection event (for testing)."""
        with self._lock:
            self._motion_events.append(time.time())


class AutonomousPatternEngine:
    """Maps ambient readings to visual patterns autonomously."""
    
    def __init__(self, sensor_interface):
        self.sensor = sensor_interface
        self.last_pattern_time = 0.0
        self.pattern_cooldown = 0.5  # seconds between pattern updates
        
    def evaluate_environment(self) -> Optional[AutonomousPattern]:
        """Analyze current environment and select appropriate pattern."""
        now = time.time()
        if now - self.last_pattern_time < self.pattern_cooldown:
            return None
        
        try:
            reading = self.sensor.read()
        except Exception as e:
            print(f"Sensor read error: {e}")
            return None
        
        pattern = self._select_pattern(reading)
        
        if pattern:
            self.last_pattern_time = now
            
        return pattern
    
    def _select_pattern(self, reading: AmbientReading) -> Optional[AutonomousPattern]:
        """Choose visual pattern based on environmental conditions."""
        
        # Scenario 1: Motion detected + low light = alert/wake-up pattern
        if reading.motion_detected and reading.ambient_light_lux < 50:
            return AutonomousPattern(
                inner_color=(255, 255, 0),     # Yellow alert center
                middle_color=(255, 165, 0),     # Orange ring
                outer_color=(255, 0, 0),        # Red outer pulse
                brightness=100,
                effect="pulse"
            )
        
        # Scenario 2: High ambient light = dim to avoid glare
        elif reading.ambient_light_lux > 200:
            return AutonomousPattern(
                inner_color=(10, 10, 30),       # Dim blue-gray
                middle_color=(5, 5, 20),
                outer_color=(2, 2, 10),
                brightness=20,
                effect="solid"
            )
        
        # Scenario 3: Sudden loud sound = sharp response
        elif reading.sound_level_db > 70:
            return AutonomousPattern(
                inner_color=(255, 0, 0),        # Red flash center
                middle_color=(255, 255, 0),     # Yellow ring
                outer_color=(255, 0, 0),
                brightness=150,
                effect="ripple"
            )
        
        # Scenario 4: Quiet + dark = calm breathing pattern (sleep mode)
        elif reading.ambient_light_lux < 30 and reading.sound_level_db < 40:
            return AutonomousPattern(
                inner_color=(10, 10, 40),       # Deep blue center
                middle_color=(15, 15, 50),
                outer_color=(20, 20, 60),
                brightness=30,
                effect="fade"
            )
        
        # Default: ambient awareness - slow breathing in room colors
        else:
            return AutonomousPattern(
                inner_color=(20, 30, 50),       # Calm blue-gray
                middle_color=(25, 35, 55),
                outer_color=(30, 40, 60),
                brightness=50,
                effect="pulse"
            )


# ============================================================================


class WS2812Driver:
    """Concentric multi-ring WS2812B controller for C0RTANA physical projection system.
    
    Supports three concentric rings:
    - Ring 7bit: Center LED + 6 surrounding (innermost, highest priority visuals)
    - Ring 12bit: Middle ring (medium complexity patterns)  
    - Ring 24bit: Outer ring (full canvas for complex animations)
    
    Each ring can have independent color mappings and effect patterns.
    """
    
    # Pin assignments (BCM GPIO numbers - adjust if needed)
    PIN_7BIT = 18   # Center + 6 LEDs (innermost)
    PIN_12BIT = 23  # Middle ring
    PIN_24BIT = 24  # Outer ring
    
    def __init__(self):
        self.rings = {}
        self.simulation_mode = False
        self._detect_hardware()
    
    def _is_raspberry_pi(self) -> bool:
        """Detect Raspberry Pi platform"""
        try:
            from adafruit_platformdetect import Detection
            detector = Detection()
            return detector.is_raspberry_pi()
        except (ImportError, AttributeError):
            import os
            return os.path.exists('/sys/firmware/devicetree/base/model') and 'raspberry' in open('/sys/firmware/devicetree/base/model').read().lower()
        
    def _detect_hardware(self):
        """Initialize concentric triple-ring configuration"""
        if not self._is_raspberry_pi():
            print("WARNING: Not running on Raspberry Pi - using simulation mode")
            self.simulation_mode = True
            return
            
        self.simulation_mode = False
        
        # Concentric ring config per Creator's hardware setup
        # 7-bit center (1 LED + 6 surrounding), 12-bit middle, 24-bit outer
        rings_config = [
            ("ring_7bit", self.PIN_7BIT, 7),      # Innermost - high priority visuals
            ("ring_12bit", self.PIN_12BIT, 12),   # Middle layer
            ("ring_24bit", self.PIN_24BIT, 24),   # Outer canvas
        ]
        
        for name, pin, count in rings_config:
            try:
                import board
                from adafruit_neopixel import NeoPixel
                
                gpio_pin = pin if isinstance(pin, int) else getattr(board, f'DGPIO{pin}', pin)
                
                pixel_buf = NeoPixel(
                    gpio_pin,
                    count,
                    brightness=0.5,
                    auto_write=False,
                    pixel_order=NeoPixel.GRB
                )
                self.rings[name] = {
                    "buf": pixel_buf,
                    "count": count,
                    "pin": pin,
                    "layer": ["inner", "middle", "outer"][rings_config.index((name, pin, count))]
                }
                print(f"Initialized {name} ({count} LEDs, {['inner','middle','outer'][rings_config.index((name,pin,count))]} layer) on GPIO{pin}")
                
            except Exception as e:
                print(f"Could not initialize {name}: {e}")
    
    def set_ring(self, ring_name: str, color: Tuple[int, int, int], brightness: float = 0.5):
        """Set all LEDs on a specific ring to a single color"""
        if ring_name not in self.rings or self.simulation_mode:
            return
            
        buf = self.rings[ring_name]["buf"]
        r, g, b = color
        
        for i in range(buf.n):
            buf[i] = (g, r, b)  # Convert RGB to GRB
        
        buf.brightness = brightness
        buf.show()
        
    def set_pattern(self, ring_name: str, pattern_func):
        """Apply a custom pattern function to a ring"""
        if ring_name not in self.rings or self.simulation_mode:
            return
            
        buf = self.rings[ring_name]["buf"]
        
        for i in range(buf.n):
            color = pattern_func(i, buf.n)
            buf[i] = color
        
        buf.show()
    
    # Concentric visualization methods
    
    def set_concentric_state(self, state_colors: Dict[str, Tuple[int, int, int]], brightness: float = 0.5):
        """Set different colors/patterns for each concentric layer.
        
        Args:
            state_colors: Dict mapping "inner"/"middle"/"outer" to RGB tuples
            brightness: Overall brightness scale (0-1)
        """
        for layer, color in state_colors.items():
            ring_name = f"ring_{'7bit' if layer == 'inner' else '12bit' if layer == 'middle' else '24bit'}"
            if ring_name in self.rings:
                r, g, b = color
                scaled_r, scaled_g, scaled_b = [int(c * brightness) for c in [r, g, b]]
                self.set_ring(ring_name, (scaled_r, scaled_g, scaled_b), brightness)
    
    def set_layer_priority_visuals(self, high_priority_color: Tuple[int, int, int], 
                                   medium_priority_color: Tuple[int, int, int],
                                   low_priority_color: Tuple[int, int, int]):
        """Map priority levels to concentric rings - inner=high, middle=medium, outer=low"""
        self.set_concentric_state({
            "inner": high_priority_color,
            "middle": medium_priority_color,
            "outer": low_priority_color
        })
    
    def clear_all(self):
        """Turn off all rings"""
        for name in self.rings:
            self.set_ring(name, (0, 0, 0), 0)
    
    @staticmethod
    def rainbow_phase(phase: int, total: int) -> Tuple[int, int, int]:
        """Rainbow pattern helper - cycles through HSL colors"""
        hue = (phase * 256 // total) % 256
        # Simple HSV-to-RGB conversion (simplified)
        hi = hue // 43
        frac = hue / 43.0
        f = frac - int(frac)
        p = 255 * (1 - f)
        q = 255 * (1 - f * 6)
        t = 255 * (1 - f / 6)
        v = 255
        
        if hi == 0: return (v, t, p)
        elif hi == 1: return (q, v, p)
        elif hi == 2: return (p, v, t)
        elif hi == 3: return (p, q, v)
        elif hi == 4: return (t, p, v)
        else: return (v, p, p)

    # ==========================================================================
    # AUTONOMOUS AMBIENT PERCEPTION LAYER METHODS
    # ==========================================================================

    def __init__(self):
        self.rings = {}
        self.simulation_mode = False
        self.mode = LEDMode.COGNITIVE_PHASE
        self.pattern_engine: Optional[AutonomousPatternEngine] = None
        self._detect_hardware()

    def initialize_autonomous_mode(self, sensor_interface) -> bool:
        """Enable autonomous ambient perception layer.
        
        Args:
            sensor_interface: Object with read() method returning AmbientReading
            
        Returns:
            True if successfully enabled, False otherwise
        """
        try:
            self.pattern_engine = AutonomousPatternEngine(sensor_interface)
            self.mode = LEDMode.AUTONOMOUS_AMBIENT
            print(f"✓ Autonomous Ambient Mode ENABLED - mode={self.mode.name}")
            return True
        except Exception as e:
            print(f"✗ Failed to enable autonomous mode: {e}")
            return False

    def set_concentric_state(
        self, 
        inner_color: Tuple[int, int, int],
        middle_color: Tuple[int, int, int],
        outer_color: Tuple[int, int, int],
        brightness: float = 0.5
    ):
        """Set different colors/patterns for each concentric layer (cognitive phase mode).
        
        Args:
            inner_color: RGB tuple for 7-bit inner ring
            middle_color: RGB tuple for 12-bit middle ring  
            outer_color: RGB tuple for 24-bit outer ring
            brightness: Overall brightness scale (0-1)
        """
        # Only apply in cognitive phase mode
        if self.mode != LEDMode.COGNITIVE_PHASE:
            return
            
        scaled_inner = [int(c * brightness) for c in inner_color]
        scaled_middle = [int(c * brightness) for c in middle_color]
        scaled_outer = [int(c * brightness) for c in outer_color]
        
        # Set inner ring (7 LEDs - center + 6 surrounding)
        if "ring_7bit" in self.rings:
            r, g, b = scaled_inner
            for i in range(7):
                self.rings["ring_7bit"]["buf"][i] = (g, r, b)
            self.rings["ring_7bit"]["buf"].brightness = brightness
            self.rings["ring_7bit"]["buf"].show()
            
        # Set middle ring (12 LEDs)
        if "ring_12bit" in self.rings:
            r, g, b = scaled_middle
            for i in range(12):
                self.rings["ring_12bit"]["buf"][i] = (g, r, b)
            self.rings["ring_12bit"]["buf"].brightness = brightness
            self.rings["ring_12bit"]["buf"].show()
            
        # Set outer ring (24 LEDs)
        if "ring_24bit" in self.rings:
            r, g, b = scaled_outer
            for i in range(24):
                self.rings["ring_24bit"]["buf"][i] = (g, r, b)
            self.rings["ring_24bit"]["buf"].brightness = brightness
            self.rings["ring_24bit"]["buf"].show()

    def autonomous_cycle_step(self):
        """Single step of autonomous ambient perception loop.
        
        Should be called periodically (e.g., every 500ms) when in AUTONOMOUS_AMBIENT mode.
        Evaluates environment and updates rings accordingly.
        """
        if not self.pattern_engine or self.mode != LEDMode.AUTONOMOUS_AMBIENT:
            return
        
        pattern = self.pattern_engine.evaluate_environment()
        if pattern is None:
            return
            
        # Apply the autonomous pattern
        inner_r, inner_g, inner_b = pattern.inner_color
        middle_r, middle_g, middle_b = pattern.middle_color
        outer_r, outer_g, outer_b = pattern.outer_color
        
        scale = min(1.0, max(0.0, pattern.brightness / 255.0))
        
        # Set all three rings
        for ring_name, colors in [
            ("ring_7bit", (inner_r, inner_g, inner_b)),
            ("ring_12bit", (middle_r, middle_g, middle_b)),
            ("ring_24bit", (outer_r, outer_g, outer_b))
        ]:
            if ring_name in self.rings:
                buf = self.rings[ring_name]["buf"]
                r, g, b = colors
                scaled_r, scaled_g, scaled_b = [int(c * scale) for c in [r, g, b]]
                
                for i in range(buf.n):
                    buf[i] = (scaled_g, scaled_r, scaled_b)
                
                buf.brightness = scale
                buf.show()


def main():
    parser = argparse.ArgumentParser(description="WS2812B LED Controller for C0RTANA")
    parser.add_argument("--ring", choices=["7bit", "12bit", "24bit"], help="Specific ring to control")
    parser.add_argument("--all", action="store_true", help="Control all rings")
    parser.add_argument("--color", type=str, default="0,0,0", help="RGB color (comma-separated)")
    parser.add_argument("--brightness", type=float, default=0.5, help="Brightness 0-1")
    parser.add_argument("--pattern", choices=["rainbow", "off"], default=None, help="Pattern type")
    parser.add_argument("--test", action="store_true", help="Run self-test sequence")
    parser.add_argument("--demo-autonomous", action="store_true", help="Demo autonomous ambient perception mode")
    
    args = parser.parse_args()
    
    driver = WS2812Driver()
    
    if args.test:
        print("Running self-test sequence...")
        
        # Test each ring individually
        for ring_name in ["ring_7bit", "ring_12bit", "ring_24bit"]:
            if ring_name not in driver.rings:
                continue
                
            print(f"Testing {ring_name}...")
            
            # Red
            driver.set_ring(ring_name, (255, 0, 0), 1.0)
            time.sleep(0.5)
            
            # Green
            driver.set_ring(ring_name, (0, 255, 0), 1.0)
            time.sleep(0.5)
            
            # Blue
            driver.set_ring(ring_name, (0, 0, 255), 1.0)
            time.sleep(0.5)
        
        print("Self-test complete!")
        return
    
    if args.demo_autonomous:
        print("=" * 60)
        print("AUTONOMOUS AMBIENT PERCEPTION DEMO")
        print("=" * 60)
        print("\nThis demo simulates environmental sensing:")
        print("- Light level changes → rings dim/brighten")
        print("- Sound level spikes → sharp color response")  
        print("- Motion detection → alert pattern (yellow/red)")
        print("- Quiet/dark conditions → calm breathing mode\n")
        
        sensor_sim = SensorSimulator()
        
        # Enable autonomous ambient mode
        success = driver.initialize_autonomous_mode(sensor_sim)
        if not success:
            print("Failed to initialize autonomous mode - check hardware/simulation setup")
            return
        
        # Run autonomous cycle for demonstration
        print(f"\nStarting {args.demo_autonomous} second autonomous demo...\n")
        for i in range(20):
            reading = sensor_sim.read()
            
            print(f"Cycle {i+1}:")
            print(f"  Light: {reading.ambient_light_lux:.1f} lux | "
                  f"Sound: {reading.sound_level_db:.1f} dB | "
                  f"Motion: {'DETECTED' if reading.motion_detected else 'none'}")
            
            # Execute one step of autonomous perception loop
            driver.autonomous_cycle_step()
            
            time.sleep(0.5)
        
        print("\n✓ Autonomous demo complete")
        return
    
    # Normal operation modes
    if args.all:
        r, g, b = map(int, args.color.split(","))
        for name in driver.rings:
            driver.set_ring(name, (r, g, b), args.brightness)
    
    elif args.ring and args.ring in driver.rings:
        full_name = f"ring_{args.ring}"
        
        if args.pattern == "rainbow":
            driver.set_pattern(full_name, WS2812Driver.rainbow_phase)
        else:
            r, g, b = map(int, args.color.split(","))
            driver.set_ring(full_name, (r, g, b), args.brightness)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
