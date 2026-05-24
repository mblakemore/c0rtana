#!/usr/bin/env python3
"""
Concentric LED Visualization Demo for C0RTANA
Demonstrates triple-ring configuration with layer-appropriate visuals

Usage:
    python examples/concentric_led_demo.py [--simulate]
    
Hardware Layout (Creator spec):
    - Ring 7bit: Center + 6 surrounding LEDs (innermost)
    - Ring 12bit: Middle ring  
    - Ring 24bit: Outer ring (full canvas)

Each ring can have independent colors/patterns based on internal state priority.
"""

import sys
import time
from typing import Tuple

# Add repo root to path
sys.path.insert(0, '/droid/repos/c0rtana')

try:
    from state.led_driver import WS2812Driver
except ImportError as e:
    print(f"Failed to import LED driver: {e}")
    print("Ensure you're running from /droid/repos/c0rtana/")
    sys.exit(1)


def simulate_visual(color: Tuple[int, int, int], led_count: int, name: str):
    """Simulate visualization without hardware."""
    r, g, b = color
    pattern = [f"[{r:3d},{g:3d},{b:3d}]" for _ in range(led_count)]
    print(f"{name}: {' '.join(pattern)}")


def demo_concentric_colors(driver: WS2812Driver, simulate: bool = False):
    """Demo concentric color mapping per layer."""
    print("\n=== Concentric Color Demo ===\n")
    
    # Mapping example: inner=high priority (cyan), middle=medium (blue), outer=low (dim blue)
    colors = {
        "inner": (0, 150, 255),   # Cyan - high visibility
        "middle": (0, 100, 200),  # Medium blue  
        "outer": (0, 50, 100),    # Dim blue - ambient background
    }
    
    if simulate:
        print("SIMULATION MODE (no hardware)")
        for layer, color in colors.items():
            ring_name = f"ring_{'7bit' if layer == 'inner' else '12bit' if layer == 'middle' else '24bit'}"
            count = driver.rings[ring_name]["count"] if ring_name in driver.rings else 0
            simulate_visual(color, count, f"{layer.upper()} ({ring_name})")
        return
    
    # Apply to actual hardware
    driver.set_concentric_state(colors, brightness=0.6)
    time.sleep(3)


def demo_priority_mapping(driver: WS2812Driver, simulate: bool = False):
    """Demo priority-based visual mapping."""
    print("\n=== Priority-Based Visuals Demo ===\n")
    
    # Example: Decision system priorities mapped to rings
    scenarios = [
        {
            "name": "IDLE", 
            "high": (0, 0, 40),      # Dim inner
            "medium": (0, 0, 20),    # Even dimmer middle  
            "low": (0, 0, 10)        # Almost off outer
        },
        {
            "name": "THINKING",
            "high": (0, 60, 120),    # Medium blue center
            "medium": (0, 40, 100),  # Slightly dimmer middle
            "low": (0, 20, 80)       # Ambient outer
        },
        {
            "name": "SPEAKING",
            "high": (0, 255, 255),   # Bright cyan center (speaking color)
            "medium": (0, 180, 180), # Cyan glow middle
            "low": (0, 100, 100)     # Soft outer halo
        },
        {
            "name": "SUCCESS",
            "high": (0, 200, 0),     # Green center
            "medium": (0, 150, 0),   # Green ring middle
            "low": (0, 100, 0)       # Green ambient outer
        },
        {
            "name": "ERROR",
            "high": (200, 0, 0),     # Red center
            "medium": (150, 0, 0),   # Red middle
            "low": (100, 0, 0)       # Dim red outer
        }
    ]
    
    for scenario in scenarios:
        state_name = scenario["name"]
        high = scenario["high"]
        medium = scenario["medium"]
        low = scenario["low"]
        print(f"\nState: {state_name}")
        
        if simulate:
            for name, color in [("HIGH (inner)", high), ("MEDIUM (middle)", medium), ("LOW (outer)", low)]:
                count = 7 if "inner" in name.lower() else 12 if "middle" in name.lower() else 24
                simulate_visual(color, count, name)
        else:
            driver.set_layer_priority_visuals(high, medium, low)
            time.sleep(2)


def demo_dynamic_effects(driver: WS2812Driver, simulate: bool = False):
    """Demo dynamic breathing/pulsing effects across concentric rings."""
    print("\n=== Dynamic Effects Demo ===\n")
    
    base_color = (0, 100, 200)  # Blue
    
    for cycle in range(3):
        print(f"Breathing cycle {cycle + 1}/3...")
        
        # Inner ring breathes fastest (high priority feedback)
        inner_brightness = 0.5 + 0.3 * abs((time.time() % 2) - 1)
        middle_brightness = 0.4 + 0.25 * abs((time.time() % 2.5) - 1.25)
        outer_brightness = 0.3 + 0.2 * abs((time.time() % 3) - 1.5)
        
        colors = {
            "inner": (int(base_color[0] * inner_brightness), 
                     int(base_color[1] * inner_brightness), 
                     int(base_color[2] * inner_brightness)),
            "middle": (int(base_color[0] * middle_brightness), 
                      int(base_color[1] * middle_brightness), 
                      int(base_color[2] * middle_brightness)),
            "outer": (int(base_color[0] * outer_brightness), 
                     int(base_color[1] * outer_brightness), 
                     int(base_color[2] * outer_brightness)),
        }
        
        if simulate:
            print(f"  Inner brightness: {inner_brightness:.2f}")
            print(f"  Middle brightness: {middle_brightness:.2f}")
            print(f"  Outer brightness: {outer_brightness:.2f}")
        else:
            driver.set_concentric_state(colors, brightness=1.0)
        
        time.sleep(2)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Concentric LED Visualization Demo")
    parser.add_argument("--simulate", action="store_true", help="Run without hardware")
    args = parser.parse_args()
    
    print("Initializing C0RTANA concentric LED system...")
    driver = WS2812Driver()
    
    if not driver.simulation_mode and not args.simulate:
        print(f"\nDetected rings:")
        for name, info in driver.rings.items():
            layer = info.get("layer", "unknown")
            count = info["count"]
            pin = info["pin"]
            print(f"  {name}: {count} LEDs on GPIO{pin} ({layer} layer)")
    else:
        print("\nSIMULATION MODE - no hardware detected or --simulate requested\n")
    
    # Run demos
    demo_concentric_colors(driver, simulate=args.simulate)
    demo_priority_mapping(driver, simulate=args.simulate)
    demo_dynamic_effects(driver, simulate=args.simulate)
    
    print("\n=== Demo Complete ===\n")
    print("To clear all lights:")
    if args.simulate:
        print("  (simulation mode - just exit)")
    else:
        print("  python3 examples/concentric_led_demo.py --clear")


if __name__ == "__main__":
    main()
