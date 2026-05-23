# C0RTANA LED Visual System Architecture

## Overview

The LED visual system provides real-time embodied feedback for the C0RTANA agent's internal state through WS2812B addressable RGB LEDs. This document describes the complete architecture and integration points.

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    C0RTANA Decision Engine                  │
│                     (Decision System v1.1)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              LedStateMapper Module                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ State Machine                                       │    │
│  │ • IDLE, THINKING, PROCESSING                        │    │
│  │ • LISTENING, SPEAKING                               │    │
│  │ • SUCCESS, ERROR, WARNING                           │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Effect Patterns                                     │    │
│  │ • Breathing (idle/thinking)                         │    │
│  │ • Spiral (speaking)                                 │    │
│  │ • Rainbow (success)                                 │    │
│  │ • Blinking (error)                                  │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────┘
                            │ RGB colors
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                LedDriver Hardware Layer                     │
│  • WS2812B Protocol Implementation                          │
│  • GPIO Timing Control                                      │
│  • Frame Buffer Management                                  │
└───────────────────────────┬─────────────────────────────────┘
                            │ GRB data stream
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Physical LED Ring (WS2812B)                    │
│           [LED]⚡[LED]⚡[LED]⚡[LED]...                       │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. LedStateMapper (`led_state_mapper.py`)

**Purpose**: Maps abstract decision states to visual representations.

**Key Methods**:
- `set_state(state_name: str)` - Change current state
- `get_color(state_name: str)` - Get static color for state
- `get_effect_pattern(timestamp, led_index, total_leds)` - Get dynamic pattern color

**State Definitions**:
| State | Color | Effect | Meaning |
|-------|-------|--------|---------|
| IDLE | Dim blue (#000028) | Breathing pulse | System idle, waiting for input |
| THINKING | Medium blue (#000073) | Gentle breathing | Processing request internally |
| PROCESSING | Brighter blue (#0000BF) | Rhythmic pulse | Active computation in progress |
| LISTENING | Active blue (#0000FF) | Static or slight pulse | Voice listening mode active |
| SPEAKING | Cyan (#0096FF) | Moving spiral | Speaking/talking output |
| SUCCESS | Green (#00FF00) | Rainbow cascade | Task completed successfully |
| ERROR | Red (#FF0000) | Blinking (1Hz) | Error condition detected |
| WARNING | Orange (#FFA500) | Pulsing orange | Warning/alert condition |
| CHARGING | Greenish cyan (#00FFFF) | Slow breath | Battery charging |
| LOW_BATTERY | Orange-red (#FF4500) | Rapid blink | Critical battery level |

**Design Principles**:
- **Brightness Scaling**: All colors scaled by 0.5 by default to reduce power consumption
- **Case Insensitive**: State names normalized to lowercase internally
- **State History**: Tracks state transitions for debugging/analysis
- **Effect Patterns**: Dynamic patterns vary per LED position and time

### 2. LedDriver (`led_driver.py`)

**Purpose**: Low-level hardware control of WS2812B LEDs.

**Key Features**:
- Protocol timing compliance (WS2812B requires precise 800kHz signaling)
- Frame buffer management (stores RGB values before sending)
- GPIO pin configuration support (BCM numbering)
- Power-efficient updates (only refresh changed pixels when possible)

**Configuration**:
```python
GPIO_CONFIG = {
    "ring_12bit": {"pin": 12, "count": 12},   # BCM GPIO 12
    "ring_24bit": {"pin": 24, "count": 24},   # BCM GPIO 24
}
```

**Hardware Requirements**:
- Raspberry Pi with accessible GPIO pins
- 5V capable power supply (~60mA per LED at full brightness)
- Common ground between Pi and power supply
- Optional: 330Ω resistor on data line, 1000µF capacitor across VCC/GND

## Integration Points

### Decision System Integration

The LED driver integrates with C0RTANA's decision system through the state mapper:

```python
# In decision cycle or callback
from state.led_state_mapper import get_led_mapper
from state.led_driver import LedDriver

def on_decision_made(decision: Dict[str, Any]):
    """Called whenever a decision is made."""
    
    # Map decision to visual state
    mapper = get_led_mapper()
    mapper.set_state(decision["state"].upper())
    
    # Get LED colors for current effect pattern
    driver = LedDriver("ring_12bit")
    for i in range(driver.ring_count):
        r, g, b = mapper.get_effect_pattern(
            time.time(), 
            i, 
            driver.ring_count
        )
        driver.set_pixel(i, r, g, b)
    
    # Apply changes
    driver.update()
```

### Real-Time Update Loop

For responsive visual feedback, run an update loop at ~10Hz:

```python
import time
from state.led_driver import LedDriver
from state.led_state_mapper import get_led_mapper

driver = LedDriver("ring_12bit")
mapper = get_led_mapper()

update_interval = 0.1  # 10Hz

while True:
    # Get current state from decision system (shared memory or queue)
    current_state = get_current_decision_state()
    
    if current_state != mapper.current_state:
        mapper.set_state(current_state.upper())
        
        # Apply visual effect
        for i in range(driver.ring_count):
            r, g, b = mapper.get_effect_pattern(time.time(), i, driver.ring_count)
            driver.set_pixel(i, r, g, b)
        
        driver.update()
    
    time.sleep(update_interval)
```

## Power Management

WS2812B LEDs can consume significant power. The design includes several power-saving features:

### Built-in Features
- **Default brightness scaling**: 50% of maximum by default (`brightness = 0.5`)
- **Dim idle states**: IDLE uses very low intensity (~#000028 → RGB(0,0,13) at 50%)
- **Effect patterns**: Dynamic effects often use lower average brightness

### Manual Control
Adjust brightness dynamically based on context:
```python
mapper.brightness = 1.0      # Full brightness for important events
mapper.brightness = 0.3      # Dim for background awareness
mapper.brightness = 0.1      # Night mode / minimal power
```

### Hardware Considerations
- Use separate 5V power supply (not USB from Pi)
- Calculate current: ~60mA per LED at full white
- For 12 LEDs at full brightness: ~720mA @ 5V
- For 24 LEDs at full brightness: ~1.4A @ 5V
- Include adequate capacitance near first LED (1000µF recommended)

## Visual Design Philosophy

The LED system embodies the following principles:

### 1. **Embodied Cognition** 
Visual feedback makes abstract internal states tangible and observable.

### 2. **Subtlety Over Loudness**
- Breathing pulses instead of frantic flashing
- Gradual transitions between states
- Avoids overwhelming visual noise

### 3. **Context Awareness**
- Brightness adjusts to ambient conditions (future enhancement)
- Different patterns for different interaction modes
- Power-conscious defaults

### 4. **Human-Friendly Colors**
- Blue tones for cognitive processes (thinking, processing)
- Cyan for communication (speaking)
- Green for positive outcomes (success)
- Red/Orange for alerts (error, warning)

## Testing & Debugging

### Self-Test Mode
```bash
python3 led_driver.py --test
```
Runs hardware diagnostic and shows rainbow cascade effect.

### Manual Control Mode
```bash
python3 led_driver.py --manual
```
Interactive control with keyboard commands.

### Simulation Mode
```bash
python3 examples/led_integration_example.py --simulate
```
Prints color values without touching hardware.

### Logging
State changes logged to JSONL file:
```jsonl
{"timestamp": 1748025600.123, "state": "IDLE", "duration": 0.0}
{"timestamp": 1748025603.456, "state": "THINKING", "duration": 4.0}
```

## Future Enhancements

Potential improvements for future iterations:

### Short-Term
- [ ] Ambient light sensor integration for auto-brightness
- [ ] Proximity detection for LED activation/deactivation
- [ ] Custom effect pattern editor via web interface

### Medium-Term  
- [ ] Multi-ring support (physical layout awareness)
- [ ] Color temperature adjustment based on time of day
- [ ] Haptic feedback synchronization

### Long-Term
- [ ] Machine learning optimization of visual patterns
- [ ] User preference learning for personalization
- [ ] Cross-device coordination (multiple C0RTANA units)

## References

- **WS2812B Datasheet**: Addressable RGB LED specifications
- **Adafruit NeoPixel Library**: CircuitPython implementation
- **RPi.GPIO Documentation**: Raspberry Pi GPIO control
- **Cognitive Science Literature**: Embodied cognition principles

---

**Version**: 1.0  
**Last Updated**: 2026-05-23  
**Author**: C0RTANA Development Team
