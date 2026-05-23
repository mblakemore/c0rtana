#!/usr/bin/env python3
"""
LED Driver Integration Example

This script demonstrates how to integrate the WS2812B LED driver 
with C0RTANA's decision-making system. It shows state transitions
and visual effect patterns.

Usage:
    python3 led_integration_example.py [--simulate]

Options:
    --simulate  Run without hardware (print instead of update LEDs)
"""

import time
from typing import Dict, Any


def simulate_led_update(ring_config: str = "ring_12bit", simulate: bool = False):
    """Simulate LED updates for testing without hardware."""
    
    # Import LED components
    from state.led_driver import LedDriver
    from state.led_state_mapper import get_led_mapper
    
    # Initialize
    driver = LedDriver(ring_config)
    mapper = get_led_mapper()
    
    print(f"\n{'='*60}")
    print(f"C0RTANA LED Visual System - {driver.ring_count} LEDs")
    print(f"{'='*60}\n")
    
    # Define test scenarios with durations
    scenarios = [
        ("IDLE", 3),           # Idle breathing
        ("THINKING", 4),       # Processing thought
        ("LISTENING", 5),      # Voice listening
        ("SPEAKING", 6),       # Speaking spiral
        ("SUCCESS", 3),        # Success rainbow
        ("ERROR", 2),          # Error blink
        ("WARNING", 3),        # Warning pulse
    ]
    
    try:
        for state_name, duration in scenarios:
            print(f"\n>>> State: {state_name.upper()} (for {duration}s)")
            
            # Set the visual state
            color = mapper.set_state(state_name)
            print(f"   Base color: RGB{color}")
            
            # Apply visual effect to all LEDs
            for led_idx in range(driver.ring_count):
                r, g, b = mapper.get_effect_pattern(0, led_idx, driver.ring_count)
                driver.set_pixel(led_idx, r, g, b)
            
            if not simulate:
                driver.update()
            
            # Simulate duration
            time.sleep(duration / 10.0)  # Faster than real-time
            
            # Show LED pattern after some time
            print(f"   Visual effect active - checking LED patterns:")
            for i in [0, driver.ring_count//4, driver.ring_count//2, 
                     (driver.ring_count*3)//4, driver.ring_count-1]:
                r, g, b = mapper.get_effect_pattern(0, i, driver.ring_count)
                status = "active" if any([r>50, g>50, b>50]) else "off"
                print(f"     LED {i:2d}: RGB({r:3d}, {g:3d}, {b:3d}) [{status}]")
        
        print("\n✓ All scenarios completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user - cleaning up...")
        driver.clear()
        if not simulate:
            driver.update()
        print("LEDs cleared.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="C0RTANA LED Driver Integration Demo")
    parser.add_argument("--simulate", action="store_true", help="Run without hardware")
    parser.add_argument("--ring", choices=["ring_12bit", "ring_24bit"], default="ring_12bit",
                       help="LED ring configuration")
    
    args = parser.parse_args()
    
    print("\n🔌 C0RTANA LED Visual System Integration Test")
    print("This demo shows how LEDs respond to system states.\n")
    
    simulate_led_update(args.ring, args.simulate)


if __name__ == "__main__":
    main()
