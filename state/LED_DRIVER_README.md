# C0RTANA WS2812B LED Driver

## Overview

This module provides control over WS2812B addressable RGB LEDs connected to a Raspberry Pi GPIO pins. It supports multiple LED ring configurations and includes dynamic visual effects.

## Hardware Requirements

- **Raspberry Pi** (4B recommended for AI workloads)
- **WS2812B LED Ring** (12-bit or 24-bit common)
- **Power Supply**: 
  - 5V capable of providing sufficient current (~60mA per LED at full brightness)
  - Recommended: 5A minimum for 24 LED rings at full brightness
- **Wiring**:
  - VCC → 5V power supply
  - GND → Common ground with Pi
  - DIN → GPIO pin (see configuration below)
  - Data line → Optional 330Ω resistor between Pi and LED

## GPIO Configuration

Edit the `GPIO_CONFIG` dictionary in `led_driver.py`:

```python
GPIO_CONFIG = {
    "ring_12bit": {"pin": 12, "count": 12},   # BCM GPIO 12
    "ring_24bit": {"pin": 24, "count": 24},   # BCM GPIO 24
}
```

Common BCM GPIO numbers:
- GPIO 12: Board Pin 32
- GPIO 24: Board Pin 18 (PWM-capable)

## Installation

### On Raspberry Pi OS

1. Update system packages:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Enable I2C and SPI (if needed):
   ```bash
   sudo raspi-config
   # Interface Options → Enable I2C/SPI if required
   ```

3. Install CircuitPython libraries:
   ```bash
   pip3 install adafruit-circuitpython-neopixel
   ```

4. Copy files to the Pi:
   ```bash
   scp state/led_driver.py pi@<pi-ip>:/home/pi/c0rtana/state/
   ```

5. Run as a service (optional):
   ```bash
   sudo systemctl enable led-driver.service
   sudo systemctl start led-driver.service
   ```

## Usage

### Python API

```python
from state.led_driver import LedDriver
from state.led_state_mapper import get_led_mapper

# Initialize driver with ring configuration
driver = LedDriver("ring_12bit")  # or "ring_24bit"

# Get LED mapper for Cortana states
mapper = get_led_mapper()

# Set visual state
mapper.set_state("thinking")

# Update LEDs
for i in range(driver.ring_count):
    r, g, b = mapper.get_effect_pattern(0, i, driver.ring_count)
    driver.set_pixel(i, r, g, b)
    
driver.update()  # Apply changes

# Change state
mapper.set_state("speaking")
# ... repeat update loop
```

### Command Line Testing

```bash
# Self-test mode
python3 state/led_driver.py --test

# Manual control (interactive)
python3 state/led_driver.py --manual
```

## Visual States

The `LedStateMapper` provides predefined color states:

| State | Color | Description |
|-------|-------|-------------|
| IDLE | Dim blue | System idle, waiting |
| THINKING | Medium blue | Processing request |
| PROCESSING | Brighter blue | Active computation |
| LISTENING | Active blue | Voice listening mode |
| SPEAKING | Cyan | Speaking/talking |
| ERROR | Red | Error condition |
| SUCCESS | Green | Task completed |
| WARNING | Orange | Warning condition |
| CHARGING | Greenish | Battery charging |
| LOW_BATTERY | Orange-red | Battery low alert |

## Dynamic Effects

- **Breathing**: Idle/thinking states pulse gently
- **Pulsing**: Processing shows rhythmic breathing
- **Rainbow**: Success triggers rainbow cascade
- **Spiral**: Speaking creates moving spiral pattern
- **Blink**: Error blinks red for attention

## Power Considerations

WS2812B LEDs can draw significant power. At full white brightness:
- 12 LEDs ≈ 0.7A at 5V (~3.5W)
- 24 LEDs ≈ 1.4A at 5V (~7W)

**Recommendations:**
- Use separate power supply for LEDs (not USB from Pi)
- Include adequate capacitance near LED strip
- Keep brightness below 50% for normal operation
- Dim to 10% during idle to save power

## Troubleshooting

### LEDs not lighting up
1. Check wiring connections
2. Verify GPIO pin configuration matches hardware
3. Ensure common ground between Pi and power supply
4. Test with `--test` flag

### Flickering or unstable behavior
1. Add 1000µF capacitor across VCC/GND near first LED
2. Reduce brightness in code
3. Check power supply can handle peak current

### Wrong colors
1. WS2812B uses GRB ordering (default is correct)
2. Some clones use RGB - adjust if needed
3. Verify gamma correction isn't being applied twice

## API Reference

### LedDriver Class

```python
class LedDriver:
    def __init__(self, ring_config_name):
        # Initialize driver with config name
        
    def set_pixel(self, index, r, g, b):
        # Set single pixel color
        
    def clear(self):
        # Turn off all pixels
        
    def update(self):
        # Apply buffer to hardware
        
    @property
    def ring_count(self):
        # Number of LEDs in configured ring
```

### LedStateMapper Class

```python
class LedStateMapper:
    def set_state(self, state_name: str):
        # Change visual state
        
    def get_color(self, state_name: str) -> Tuple[int, int, int]:
        # Get static RGB color for state
        
    def get_effect_pattern(self, ring_idx, led_pos, total_leds) -> Tuple[int, int, int]:
        # Get dynamic pattern color for specific LED
```

## License

MIT License - See main project LICENSE file
