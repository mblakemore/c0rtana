# C0RTANA Concentric LED Visual System

## Overview

This document describes the concentric triple-ring WS2812B LED system designed for C0RTANA's physical projection. The three-ring configuration enables layered visual feedback where each ring serves a distinct role in communicating internal state.

**Hardware Layout:**
- **Ring 7bit**: Innermost layer (center + 6 surrounding LEDs = 7 total)
- **Ring 12bit**: Middle layer (12 LEDs in circle)
- **Ring 24bit**: Outer canvas (24 LEDs - full animation surface)

Each ring is independently addressable via separate GPIO pins, allowing complex multi-layer visuals.

---

## Design Philosophy

### Priority Mapping

The concentric layout maps to decision priority:
- **Inner ring**: High-priority signals (speaking color, errors, critical states)
- **Middle ring**: Medium-priority context (thinking, processing, listening)
- **Outer ring**: Ambient background (idle breathing, charging status, low battery)

### Layered Communication

Visual complexity scales outward:
- Inner ring: Simple, high-contrast patterns (breathing pulse, solid color)
- Middle ring: Moderate animations (gentle spiral, rhythmic pulsing)
- Outer ring: Complex effects (rainbow cascades, gradient flows)

This creates a "visual hierarchy" that observers can intuitively parse.

---

## Hardware Configuration

### Pin Assignments (BCM GPIO)

| Ring | BCM Pin | Physical Pin | LED Count | Layer |
|------|---------|--------------|-----------|-------|
| 7bit | 18      | Board 36     | 7         | Inner |
| 12bit| 23      | Board 16     | 12        | Middle |
| 24bit| 24      | Board 18     | 24        | Outer |

**Note:** Adjust pin numbers in `led_driver.py` if your wiring differs.

### Wiring Diagram

```
WS2812B Ring Stack (concentric):
┌─────────────────────────┐
│    24-bit outer ring    │ ← GPIO 24 (Board 18)
│  ┌───────────────────┐  │
│  │   12-bit middle   │  │ ← GPIO 23 (Board 16)
│  │  ┌─────────────┐  │  │
│  │  │  7-bit inner│  │  │ ← GPIO 18 (Board 36)
│  │  │  center+6   │  │  │
│  │  └─────────────┘  │  │
│  └───────────────────┘  │
└─────────────────────────┘

Power & Data:
- All rings share common 5V power and GND
- Each ring has dedicated data input from respective GPIO
- Include 330Ω resistor on each data line
- Add 1000µF capacitor across VCC/GND near first LED
```

---

## API Reference

### Basic Usage

```python
from state.led_driver import WS2812Driver

# Initialize all three rings
driver = WS2812Driver()

# Set different colors per layer
colors = {
    "inner": (0, 150, 255),   # Cyan
    "middle": (0, 100, 200),  # Blue  
    "outer": (0, 50, 100),    # Dim blue
}
driver.set_concentric_state(colors, brightness=0.6)
```

### Priority-Based Visuals

```python
# Map decision priorities to layers
driver.set_layer_priority_visuals(
    high_priority_color=(255, 0, 0),     # Inner = error state
    medium_priority_color=(0, 200, 0),   # Middle = success context  
    low_priority_color=(0, 0, 255)       # Outer = ambient background
)
```

### Dynamic Effects

```python
import time

# Breathing effect with layered timing
for cycle in range(3):
    inner_bright = 0.5 + 0.3 * abs((time.time() % 2) - 1)
    middle_bright = 0.4 + 0.25 * abs((time.time() % 2.5) - 1.25)
    outer_bright = 0.3 + 0.2 * abs((time.time() % 3) - 1.5)
    
    colors = {
        "inner": (0, int(100 * inner_bright), 200),
        "middle": (0, int(80 * middle_bright), 180),
        "outer": (0, int(60 * outer_bright), 150),
    }
    
    driver.set_concentric_state(colors, brightness=1.0)
    time.sleep(0.1)
```

---

## State-to-Visual Mapping Examples

### IDLE State
```python
{
    "inner": (0, 0, 40),      # Dim blue pulse (breathing)
    "middle": (0, 0, 20),     # Even dimmer ambient  
    "outer": (0, 0, 10)       # Almost off background
}
```

### THINKING State
```python
{
    "inner": (0, 60, 120),    # Medium blue center
    "middle": (0, 40, 100),   # Slightly dimmer middle
    "outer": (0, 20, 80)      # Ambient glow
}
```

### SPEAKING State
```python
{
    "inner": (0, 255, 255),   # Bright cyan - speaking color
    "middle": (0, 180, 180),  # Cyan halo
    "outer": (0, 100, 100)    # Soft outer ring
}
```

### SUCCESS State
```python
{
    "inner": (0, 200, 0),     # Green center
    "middle": (0, 150, 0),    # Green ring
    "outer": (0, 100, 0)      # Green ambient
}
```

### ERROR State
```python
{
    "inner": (200, 0, 0),     # Red pulse (high priority warning)
    "middle": (150, 0, 0),    # Red context
    "outer": (100, 0, 0)      # Dim red background
}
```

---

## Integration with Decision System

### Example: Decision Cycle Callback

```python
from state.led_driver import WS2812Driver
from state.led_state_mapper import get_led_mapper

driver = WS2812Driver()
mapper = get_led_mapper()

def on_decision_made(decision):
    """Called whenever a decision is made."""
    
    # Map decision to visual state
    mapper.set_state(decision["state"].upper())
    
    # Get current colors from mapper
    inner_color = mapper.get_color("THINKING") if decision["type"] == "internal" else mapper.get_color(decision["state"])
    middle_color = mapper.get_color("PROCESSING")
    outer_color = mapper.get_color("IDLE")
    
    # Apply concentric visualization
    driver.set_layer_priority_visuals(inner_color, middle_color, outer_color)
```

### Real-Time Update Loop

```python
import time

while True:
    # Get current decision state from shared memory/queue
    decision_state = get_current_decision()
    
    if decision_state != last_state:
        # Update LED system only when state changes
        update_concentric_viz(decision_state)
        last_state = decision_state
    
    time.sleep(0.1)  # ~10Hz check rate
```

---

## Testing & Verification

### Self-Test Sequence

```bash
# Run simulation mode (no hardware required)
cd /droid/repos/c0rtana
python3 examples/concentric_led_demo.py --simulate

# Expected output:
# SIMULATION MODE - no hardware detected or --simulate requested
# 
# === Concentric Color Demo ===
# INNER (ring_7bit): [  0, 150, 255] [  0, 150, 255] ... (7 times)
# MIDDLE (ring_12bit): [  0, 100, 200] ... (12 times)
# OUTER (ring_24bit): [  0, 50, 100] ... (24 times)
```

### Hardware Test Mode

```bash
# Run on Raspberry Pi with actual LEDs
python3 examples/concentric_led_demo.py

# Expected: Each ring lights up with its assigned color
# - Inner (7 LEDs): Cyan breathing pulse
# - Middle (12 LEDs): Blue medium brightness  
# - Outer (24 LEDs): Dim blue ambient glow
```

---

## Power Considerations

### Current Draw Estimates

| Configuration | Full White Brightness | Typical Usage |
|---------------|----------------------|---------------|
| All 3 rings @ 50% | ~2.1A @ 5V (~10.5W) | ~600-900mA |

**Recommendations:**
- Use dedicated 5V power supply (minimum 2A capacity)
- Do NOT power from Raspberry Pi USB port alone
- Include adequate capacitance near each ring's first LED
- Keep brightness at 50% for normal operation to reduce heat

---

## Troubleshooting

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| Only some rings light | Wrong GPIO pin mapping | Check `led_driver.py` PIN_* constants match wiring |
| Colors look wrong (RGB vs GRB) | Pixel order mismatch | Edit line 78: change `NeoPixel.GRB` to `NeoPixel.RGB` if needed |
| Flickering/bright spikes | Insufficient power/capacitance | Add 1000µF capacitor, verify power supply rating |
| Outer ring dimmer than inner | Different wire resistance | Use thicker gauge for outer ring power feed |
| Rings interfering with each other | Data line crosstalk | Add 330Ω resistor on each data input |

---

## Future Enhancements

### Short-Term (Next 5 cycles)
- [ ] Ambient light sensor integration for auto-brightness scaling
- [ ] Proximity detection to activate/deactivate based on user presence
- [ ] Custom effect pattern editor via web interface

### Medium-Term (Next 20 cycles)  
- [ ] Machine learning optimization of visual patterns based on engagement feedback
- [ ] Cross-device coordination with additional C0RTANA units
- [ ] Multi-sensory synchronization (haptic + visual feedback)

### Long-Term Vision
- [ ] Holographic projection systems (WebXR, ARKit/ARCore)
- [ ] Physical robot body integration with position-responsive visuals
- [ ] Full color spectrum control with dynamic gradient mapping

---

## References

- **WS2812B Datasheet**: Addressable RGB LED specifications and timing requirements
- **Adafruit NeoPixel Library**: CircuitPython implementation reference
- **RPi.GPIO Documentation**: Raspberry Pi GPIO pin mappings
- **Embodied Cognition Literature**: Visual feedback principles for AI presence

---

**Status**: ✅ Ready for deployment  
**Last Updated**: 2026-05-23  
**Implemented by**: C0RTANA (Cycle 343)  
**Hardware**: Triple concentric WS2812B rings (7+12+24 LEDs)
