#!/usr/bin/env python3
"""
WS2812B LED Driver for C0RTANA Physical Projection System
Maps cortana internal state to RGB ring patterns

Usage:
    python led_driver.py --ring <7|12|24> --color R,G,B --brightness 0-255
    python led_driver.py --all --pattern rainbow
"""

import argparse
import time
from typing import Tuple, Optional

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


class WS2812Driver:
    """Multi-ring WS2812B controller with state mapping"""
    
    # Pin assignments (adjust based on actual wiring)
    PIN_7BIT = 18   # Center + 6 LEDs (innermost)
    PIN_12BIT = 23  # Middle ring
    PIN_24BIT = 24  # Outer ring
    
    def __init__(self):
        self.rings = {}
        self._detect_hardware()
        
    def _detect_hardware(self):
        """Detect which rings are present and initialize them"""
        if not is_raspberry_pi():
            print("WARNING: Not running on Raspberry Pi - using simulation mode")
            self.simulation_mode = True
            return
            
        self.simulation_mode = False
        
        # Initialize each possible ring
        for name, pin, count in [
            ("ring_7bit", self.PIN_7BIT, 7),
            ("ring_12bit", self.PIN_12BIT, 12),
            ("ring_24bit", self.PIN_24BIT, 24),
        ]:
            try:
                import board
                from adafruit_neopixel import NeoPixel
                
                # Use GPIO pin mapping for RPi - direct number works on most systems
                if isinstance(pin, int):
                    gpio_pin = pin
                else:
                    gpio_pin = getattr(board, f'DGPIO{pin}', pin)
                
                pixel_buf = NeoPixel(
                    gpio_pin,
                    count,
                    brightness=0.5,
                    auto_write=False,
                    pixel_order=NeoPixel.GRB  # WS2812B is typically GRB
                )
                self.rings[name] = {
                    "buf": pixel_buf,
                    "count": count,
                    "pin": pin
                }
                print(f"Initialized {name} ({count} LEDs) on GPIO{pin}")
                
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


def main():
    parser = argparse.ArgumentParser(description="WS2812B LED Controller for C0RTANA")
    parser.add_argument("--ring", choices=["7bit", "12bit", "24bit"], help="Specific ring to control")
    parser.add_argument("--all", action="store_true", help="Control all rings")
    parser.add_argument("--color", type=str, default="0,0,0", help="RGB color (comma-separated)")
    parser.add_argument("--brightness", type=float, default=0.5, help="Brightness 0-1")
    parser.add_argument("--pattern", choices=["rainbow", "off"], default=None, help="Pattern type")
    parser.add_argument("--test", action="store_true", help="Run self-test sequence")
    
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
