# ESP32 LED Controller

Projection bridge that translates cortana internal state → ESP32 WS2812B LED commands via HTTP REST API.

## Hardware Target

- **Device**: ESP32-WROOM-32 connected to concentric WS2812B rings (7+12+24 LEDs)
- **Network**: `dr0id` AP at `192.168.4.38`
- **API Endpoints**: `/color`, `/anim`, `/bright`, `/status`

## Usage

### Command-Line Control

```bash
# Set all rings to cyan
sudo python3 esp32_controller.py --ring all --color cyan

# Per-ring control
sudo python3 esp32_controller.py --ring inner --color blue     # 7-bit ring
sudo python3 esp32_controller.py --ring middle --color green   # 12-bit ring  
sudo python3 esp32_controller.py --ring outer --color yellow   # 24-bit ring

# Animation and brightness
sudo python3 esp32_controller.py --anim rainbow --speed 80
sudo python3 esp32_controller.py --bright 128

# Simulation mode (no network calls, useful for testing)
sudo python3 esp32_controller.py --sim --ring all --color cyan
```

### State-Driven Projection

Automatically maps cortana's current state → LED colors/animations:

```bash
# Real projection (reads current-state.json, sends to ESP32)
sudo python3 esp32_controller.py --state

# Simulation mode (logs what would be sent)
sudo python3 esp32_controller.py --state --sim
```

**State mappings:**

| Phase | Color | Animation | Brightness | Meaning |
|---|---|---|---|---|
| PERCEIVE | Blue (`#0080FF`) | Pulse | 128 | Sensing environment |
| REFLECT | Purple (`#8000FF`) | Sparkle | 140 | Thinking/analyzing |
| DECIDE | Orange (`#FF8000`) | Pulse | 160 | Choosing action |
| ACT | Red-Orange (`#FF4000`) | Fire | 200 | Executing action |
| CONSOLIDATE | Green (`#00FF80`) | Rainbow | 180 | Integrating learning |
| PERSIST | White (`#FFFFFF`) | Spin | 255 | Committing memory |

Confidence level modulates brightness (higher confidence = brighter).

## Integration

### Automated state projection

Add to your cycle script after PERSIST phase completes:

```bash
# After git push confirms
python3 esp32_controller.py --state &
```

Or as a systemd service that watches `current-state.json` for changes.

### Continuous ambient mode

Run background daemon that polls state every N seconds:

```bash
while true; do
    python3 esp32_controller.py --state
    sleep 5
done
```

## Testing Without Hardware

Use `--sim` flag to log expected commands without network calls:

```bash
$ python3 esp32_controller.py --sim --state
[SIMULATION] apply_state_to_leds: {'phase': 'ACT', 'confidence': 0.7, ...}
```

This is useful during development or if ESP32 is offline.

## API Reference

ESP32 HTTP endpoints (from `/droid/repos/cl_shared/esp32/README.md`):

| Endpoint | Params | Example |
|---|---|---|
| `GET /color` | `ring=0-3`, `r,g,b` | `/color?ring=0&r=0&g=255&b=255` |
| `GET /anim` | `name=solid\|rainbow\|spin\|pulse\|sparkle\|fire` | `/anim?name=rainbow&speed=80` |
| `GET /bright` | `v=0-255` | `/bright?v=128` |
| `GET /status` | — | Returns JSON status |

## Dependencies

- Python 3.6+
- Standard library only (`urllib.request`, `argparse`)

## Patterns Stored

See `patterns.jsonl` for P_C354_ESP32_PROJECTION entry documenting this tool's design decisions and validation criteria.
