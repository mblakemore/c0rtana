#!/usr/bin/env python3
"""
ESP32 LED Controller for C0RTANA Physical Projection System

Maps cortana internal state to ESP32 HTTP API calls controlling WS2812B rings.

Hardware: ESP32-WROOM-32 at http://192.168.4.38
All 43 LEDs daisy-chained on single data line (GPIO4), controlled via REST endpoints.

Usage:
    python esp32_controller.py --ring <inner|middle|outer|all> --color R,G,B
    python esp32_controller.py --anim rainbow --speed 75
    python esp32_controller.py --state  # Read current-state.json and apply mapping
"""

import argparse
import json
import urllib.request
import urllib.error
import time
from typing import Optional, Tuple


# ============================================================================
# CONFIGURATION
# ============================================================================

ESP32_IP = "192.168.4.38"
ESP32_PORT = 80

# Ring mappings to ESP32's single-daisy-chain model
# ESP32 firmware treats all 43 LEDs as one strip, but web UI can address subsets
RING_OFFSETS = {
    "inner": 0,      # LEDs 0-6 (7 LEDs)
    "middle": 7,     # LEDs 7-18 (12 LEDs)  
    "outer": 19,     # LEDs 19-42 (24 LEDs)
}

RING_COUNTS = {
    "inner": 7,
    "middle": 12,
    "outer": 24,
}


# ============================================================================
# HTTP API CLIENT
# ============================================================================

def http_get(endpoint: str, params: dict = None) -> dict:
    """Make GET request to ESP32 HTTP API. Returns JSON for /status, plain text 'ok' for commands."""
    base_url = f"http://{ESP32_IP}:{ESP32_PORT}"
    
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{base_url}{endpoint}?{query}"
    else:
        url = f"{base_url}{endpoint}"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                body = response.read().decode("utf-8")
                # Try parsing as JSON, fall back to plain text
                try:
                    return {"success": True, **json.loads(body)}
                except json.JSONDecodeError:
                    return {"success": body.strip() == "ok", "body": body}
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠ ESP32 request attempt {attempt+1}/{max_retries} failed: {e}, retrying...")
                time.sleep(2)
            else:
                print(f"✗ ESP32 request failed after {max_retries} attempts: {e}")
                raise


def http_set_color(ring: str, r: int, g: int, b: int) -> bool:
    """Set color for specific ring or all rings."""
    endpoint = "/color"
    params = {"ring": RING_OFFSETS.get(ring, 0)}
    
    # For "all", use ring=0 which controls entire strip
    if ring == "all":
        params["ring"] = 0
    
    try:
        result = http_get(endpoint, {**params, "r": r, "g": g, "b": b})
        print(f"✓ Color set: ring={ring}, RGB=({r},{g},{b})")
        return True
    except Exception as e:
        print(f"✗ Failed to set color: {e}")
        return False


def http_set_animation(name: str, speed: Optional[int] = None) -> bool:
    """Set animation type and optionally speed."""
    valid_anims = ["solid", "rainbow", "spin", "pulse", "sparkle", "fire"]
    
    if name not in valid_anims:
        print(f"✗ Invalid animation '{name}'. Valid: {', '.join(valid_anims)}")
        return False
    
    params = {"name": name}
    if speed is not None:
        params["v"] = speed
    
    try:
        result = http_get("/anim", params)
        print(f"✓ Animation set: {name}" + (f" speed={speed}" if speed else ""))
        return True
    except Exception as e:
        print(f"✗ Failed to set animation: {e}")
        return False


def http_set_brightness(value: int) -> bool:
    """Set global brightness (0-255)."""
    if not 0 <= value <= 255:
        print(f"✗ Brightness must be 0-255, got {value}")
        return False
    
    try:
        result = http_get("/bright", {"v": value})
        print(f"✓ Brightness set: {value}")
        return True
    except Exception as e:
        print(f"✗ Failed to set brightness: {e}")
        return False


def get_status() -> dict:
    """Get current ESP32 status."""
    return http_get("/status")


# ============================================================================
# STATE MAPPING (Cognitive Phase → Visual Pattern)
# ============================================================================

def map_phase_to_pattern(phase: str, confidence: float = 0.5) -> Tuple[str, Tuple[int, int, int], int]:
    """Map cortana cognitive phase to ESP32 visual pattern.
    
    Returns: (animation_name, color_rgb, brightness)
    """
    
    # Default fallback
    default = ("solid", (20, 30, 60), 100)  # Calm blue-gray breathing
    
    if phase == "perceive":
        return ("rainbow", (100, 100, 255), 128)  # Blue rainbow scanning
    
    elif phase == "reflect":
        return ("pulse", (255, 200, 100), 150)  # Orange pulsing contemplation
    
    elif phase == "decide":
        return ("sparkle", (255, 255, 100), 180)  # Yellow sparks decision-making
    
    elif phase == "act":
        return ("spin", (100, 255, 100), 200)  # Green spinning action execution
    
    elif phase == "sync":
        return ("fire", (255, 100, 50), 180)  # Red-orange fire synchronization
    
    elif phase == "idle":
        return ("solid", (10, 10, 30), 50)  # Dim standby
    
    else:
        return default


def apply_state_mapping(state_file: str = "/droid/repos/c0rtana/state/current-state.json") -> bool:
    """Read current-state.json and map to ESP32 visual pattern."""
    
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        phase = state.get("phase", "idle")
        confidence = state.get("confidence", 0.5)
        
        anim, color, brightness = map_phase_to_pattern(phase, confidence)
        r, g, b = color
        
        print(f"📊 Phase={phase}, Confidence={confidence:.2f}")
        print(f"🎨 Pattern: {anim} RGB=({r},{g},{b}) Brightness={brightness}")
        
        http_set_animation(anim)
        http_set_color("all", r, g, b)
        http_set_brightness(brightness)
        
        return True
        
    except FileNotFoundError:
        print(f"✗ State file not found: {state_file}")
        return False
    except Exception as e:
        print(f"✗ Failed to apply state mapping: {e}")
        return False


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="ESP32 LED Controller for C0RTANA")
    parser.add_argument("--ring", choices=["inner", "middle", "outer", "all"], default="all", help="Target ring(s)")
    parser.add_argument("--color", type=str, default="0,0,0", help="RGB color (comma-separated, 0-255)")
    parser.add_argument("--anim", choices=["solid", "rainbow", "spin", "pulse", "sparkle", "fire"], help="Animation type")
    parser.add_argument("--speed", type=int, help="Animation speed (1-100)")
    parser.add_argument("--brightness", type=int, help="Global brightness (0-255)")
    parser.add_argument("--state", action="store_true", help="Read current-state.json and apply pattern mapping")
    parser.add_argument("--status", action="store_true", help="Show current ESP32 status")
    parser.add_argument("--test", action="store_true", help="Quick connectivity test")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon, polling state file continuously")
    parser.add_argument("--interval", type=int, default=2, help="Daemon poll interval in seconds (default: 2)")
    
    args = parser.parse_args()
    
    # Validate speed range
    if args.speed is not None and (args.speed < 1 or args.speed > 100):
        print("✗ Speed must be between 1 and 100")
        exit(1)
    
    # Validate brightness range  
    if args.brightness is not None and (args.brightness < 0 or args.brightness > 255):
        print("✗ Brightness must be between 0 and 255")
        exit(1)
    
    # Test connectivity
    if args.test:
        try:
            status = get_status()
            print(f"✓ ESP32 online at {ESP32_IP}")
            print(f"  Status: {json.dumps(status)}")
            return
        except Exception as e:
            print(f"✗ ESP32 unreachable: {e}")
            return
    
    # Show status
    if args.status:
        try:
            status = get_status()
            print(json.dumps(status, indent=2))
            return
        except Exception as e:
            print(f"✗ Failed to get status: {e}")
            return
    
    # Apply state mapping from file
    if args.state:
        success = apply_state_mapping()
        exit(0 if success else 1)
    
    # Daemon mode — continuous polling of state file
    if args.daemon:
        print(f"🚀 Starting ESP32 daemon (polling every {args.interval}s)...")
        try:
            while True:
                start_time = time.time()
                
                if apply_state_mapping():
                    elapsed = time.time() - start_time
                    print(f"✓ State updated in {elapsed:.2f}s")
                
                sleep_time = max(0, args.interval - (time.time() - start_time))
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\n🛑 Daemon stopped by user")
            exit(0)
        return
    
    # Parse RGB color
    try:
        r, g, b = map(int, args.color.split(","))
        if not all(0 <= c <= 255 for c in [r, g, b]):
            raise ValueError("RGB values must be 0-255")
    except Exception as e:
        print(f"✗ Invalid color format: {args.color}. Use R,G,B (e.g., 255,0,0)")
        exit(1)
    
    # Execute commands
    success = True
    
    if args.anim:
        speed = args.speed if args.speed else None
        if not http_set_animation(args.anim, speed):
            success = False
    
    if args.brightness is not None:
        if not http_set_brightness(args.brightness):
            success = False
    
    if args.color != "0,0,0":  # Only set color if explicitly provided and not black
        if not http_set_color(args.ring, r, g, b):
            success = False
    
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
