#!/usr/bin/env python3
"""
ESP32 LED Controller — Projection Bridge

Translates cortana internal state → ESP32 HTTP API commands.

Usage:
    # Command-line mode
    sudo python3 esp32_controller.py --ring all --color red
    
    # Per-ring control
    sudo python3 esp32_controller.py --ring inner --color blue
    sudo python3 esp32_controller.py --ring middle --color green  
    sudo python3 esp32_controller.py --ring outer --color yellow
    
    # Animation control
    sudo python3 esp32_controller.py --anim rainbow --speed 80
    
    # Brightness
    sudo python3 esp32_controller.py --bright 128
    
    # Simulation mode (no network calls)
    sudo python3 esp32_controller.py --sim --ring all --color cyan
    
    # State-driven projection (reads from current-state.json)
    sudo python3 esp32_controller.py --state
"""

import argparse
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime


# Configuration
ESP32_IP = "192.168.4.38"
OTA_PASSWORD = "ota123"

# Ring mapping
RING_MAP = {
    "all": 0,      # All rings
    "inner": 1,    # 7-bit ring
    "middle": 2,   # 12-bit ring  
    "outer": 3     # 24-bit ring
}

ANIMATION_MAP = {
    "solid": "solid",
    "rainbow": "rainbow", 
    "spin": "spin",
    "pulse": "pulse",
    "sparkle": "sparkle",
    "fire": "fire"
}

# State → LED mappings (phase_confidence_to_led pattern will document these)
STATE_LED_MAPPINGS = {
    "PERCEIVE": {"color": (0, 128, 255), "anim": "pulse", "brightness": 128},   # Cool blue - sensing
    "REFLECT": {"color": (128, 0, 255), "anim": "sparkle", "brightness": 140},  # Purple - thinking
    "DECIDE": {"color": (255, 128, 0), "anim": "pulse", "brightness": 160},     # Orange - choosing
    "ACT": {"color": (255, 64, 0), "anim": "fire", "brightness": 200},          # Red-orange - acting
    "CONSOLIDATE": {"color": (0, 255, 128), "anim": "rainbow", "brightness": 180}, # Green - integrating
    "PERSIST": {"color": (255, 255, 255), "anim": "spin", "brightness": 255},   # White - committing
}


def esp32_color(ring: str, r: int, g: int, b: int) -> None:
    """Set color for specified ring."""
    ring_idx = RING_MAP.get(ring.lower(), 0)
    url = f"http://{ESP32_IP}/color?ring={ring_idx}&r={r}&g={g}&b={b}"
    send_request(url)


def esp32_brightness(value: int) -> None:
    """Set global brightness (0-255)."""
    url = f"http://{ESP32_IP}/bright?v={value}"
    send_request(url)


def esp32_animation(name: str, speed: int = 50) -> None:
    """Set animation type and speed."""
    anim_name = ANIMATION_MAP.get(name.lower(), "solid")
    url = f"http://{ESP32_IP}/anim?name={anim_name}&speed={speed}"
    send_request(url)


def send_request(url: str) -> bool:
    """Send HTTP GET request to ESP32."""
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            result = response.read().decode('utf-8').strip()
            print(f"[{datetime.now().isoformat()}] ESP32 OK: {result}")
            return True
    except urllib.error.URLError as e:
        print(f"[{datetime.now().isoformat()}] ESP32 ERROR: {e}")
        return False
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ESP32 ERROR: {e}")
        return False


def simulate_action(action: str, params: dict) -> None:
    """Log action without network call (simulation mode)."""
    print(f"[SIMULATION] {action}: {params}")


def apply_state_to_leds(state_data: dict, simulation: bool = False) -> None:
    """Map cortana state → LED projection."""
    phase = state_data.get("phase", "UNKNOWN")
    confidence = state_data.get("confidence", 0.5)
    
    if phase not in STATE_LED_MAPPINGS:
        # Fallback to neutral state
        mappings = {"color": (128, 128, 128), "anim": "solid", "brightness": 64}
    else:
        mappings = STATE_LED_MAPPINGS[phase].copy()
        
        # Adjust brightness based on confidence (higher confidence = brighter)
        base_brightness = mappings["brightness"]
        adjusted_brightness = int(base_brightness * (0.5 + confidence * 0.5))
        mappings["brightness"] = min(255, adjusted_brightness)
    
    color = mappings["color"]
    
    if simulation:
        simulate_action("apply_state_to_leds", {
            "phase": phase,
            "confidence": confidence,
            "color": color,
            "animation": mappings["anim"],
            "brightness": mappings["brightness"]
        })
    else:
        esp32_color("all", *color)
        esp32_animation(mappings["anim"])
        esp32_brightness(mappings["brightness"])


def main():
    parser = argparse.ArgumentParser(description="ESP32 LED Controller")
    parser.add_argument("--ring", choices=["all", "inner", "middle", "outer"], 
                        help="LED ring to control")
    parser.add_argument("--color", "--c", help="RGB color (e.g., 'red', '#FF0000', or '255,0,0')")
    parser.add_argument("--bright", "--b", type=int, help="Brightness 0-255")
    parser.add_argument("--anim", "--a", choices=list(ANIMATION_MAP.keys()), help="Animation type")
    parser.add_argument("--speed", type=int, default=50, help="Animation speed 1-100")
    parser.add_argument("--sim", "--simulation", action="store_true", help="Simulation mode (no network)")
    parser.add_argument("--state", action="store_true", help="Read from current-state.json and apply state mapping")
    
    args = parser.parse_args()
    
    # Parse color argument
    rgb = None
    if args.color:
        color_names = {
            "red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255),
            "cyan": (0, 255, 255), "magenta": (255, 0, 255), "yellow": (255, 255, 0),
            "white": (255, 255, 255), "black": (0, 0, 0), "orange": (255, 165, 0)
        }
        if args.color.lower() in color_names:
            rgb = color_names[args.color.lower()]
        elif args.color.startswith("#"):
            hex_color = args.color[1:]
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        elif "," in args.color:
            rgb = tuple(int(x.strip()) for x in args.color.split(","))
    
    # State-driven mode
    if args.state:
        state_file = Path("state/current-state.json")
        if state_file.exists():
            with open(state_file) as f:
                state_data = json.load(f)
            apply_state_to_leds(state_data, simulation=args.sim)
        else:
            print("ERROR: state/current-state.json not found")
            return
        return
    
    # Command-line mode
    if args.ring and args.color:
        esp32_color(args.ring, *rgb) if not args.sim else simulate_action("color", {"ring": args.ring, "color": args.color})
    
    if args.bright is not None:
        esp32_brightness(args.bright) if not args.sim else simulate_action("brightness", {"value": args.bright})
    
    if args.anim:
        esp32_animation(args.anim, args.speed) if not args.sim else simulate_action("animation", {"name": args.anim, "speed": args.speed})


if __name__ == "__main__":
    main()
