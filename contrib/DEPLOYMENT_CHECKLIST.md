# C0RTNA LED Driver Deployment Checklist

## Pre-Deployment (On Desktop Machine)

### Files to Copy
Copy these from `/droid/repos/c0rtana/` to the Raspberry Pi:

```bash
# Main LED driver module
state/led_driver.py
state/led_state_mapper.py
state/LED_DRIVER_README.md

# Optional service file for auto-start
contrib/led-driver.service
contrib/DEPLOYMENT_CHECKLIST.md
```

### Recommended Transfer Method

**Option 1: rsync (preferred)**
```bash
rsync -avz --progress \
    state/led_driver.py \
    state/led_state_mapper.py \
    state/LED_DRIVER_README.md \
    contrib/led-driver.service \
    pi@raspberrypi.local:/home/pi/c0rtana/
```

**Option 2: SCP**
```bash
scp state/led_driver.py state/led_state_mapper.py \
    state/LED_DRIVER_README.md contrib/led-driver.service \
    pi@raspberrypi.local:/home/pi/c0rtana/
```

## On Raspberry Pi

### 1. Install Dependencies

```bash
sudo apt update
pip3 install adafruit-circuitpython-neopixel rpi-lgpio
```

### 2. Verify GPIO Configuration

Check your wiring matches the config in `led_driver.py`:

```python
GPIO_CONFIG = {
    "ring_12bit": {"pin": 12, "count": 12},   # BCM 12
    "ring_24bit": {"pin": 24, "count": 24},   # BCM 24
}
```

Common BCM mappings:
- **BCM 12**: Board pin 32 (GPIO18)
- **BCM 24**: Board pin 18 (GPIO24)

### 3. Test Hardware

Run self-test mode:
```bash
cd /home/pi/c0rtana/state
python3 led_driver.py --test
```

Expected output:
```
Testing LED Driver...
Config: ring_12bit (12 LEDs on GPIO 12)
All tests passed! ✓
Test pattern complete - check for rainbow effect
```

If test passes, LEDs should show a rainbow cascade effect.

### 4. Manual Testing

Start interactive mode:
```bash
python3 led_driver.py --manual
```

Try changing states with arrow keys or number pads.

### 5. Configure Auto-Start (Optional)

Copy service file to systemd:
```bash
sudo cp contrib/led-driver.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable led-driver.service
sudo systemctl start led-driver.service
```

Check status:
```bash
systemctl status led-driver.service
```

## Post-Deployment Verification

### Visual State Tests

| Command | Expected Result |
|---------|----------------|
| `mapper.set_state("IDLE")` | Dim blue pulse breathing |
| `mapper.set_state("THINKING")` | Medium blue pulse |
| `mapper.set_state("SPEAKING")` | Cyan spiral pattern |
| `mapper.set_state("SUCCESS")` | Rainbow cascade |
| `mapper.set_state("ERROR")` | Red blinking |

### Power Consumption Check

Monitor current draw during different states:
```bash
# Monitor power usage
watch -n1 'cat /sys/class/power_supply/*/current_now'
```

At full brightness white, expect ~60mA per LED.

### Troubleshooting Quick Reference

**Issue**: LEDs not lighting at all
- **Fix**: Check wiring, verify common ground, test with --test flag

**Issue**: Wrong colors (RGB vs GRB)
- **Fix**: Edit line 25 in led_driver.py to change ordering

**Issue**: Flickering/bright spikes
- **Fix**: Add capacitor across VCC/GND near first LED

**Issue**: GPIO conflicts
- **Fix**: Change pin number in GPIO_CONFIG and update wiring

## Notes for AI Integration

The LED driver is designed for seamless integration with C0RTANA's decision system:

1. **State Mapping**: Use `LedStateMapper.get_effect_pattern()` to get dynamic colors
2. **Update Loop**: Call `driver.update()` after setting pixel values
3. **Efficiency**: Only update changed pixels when possible
4. **Power Saving**: Reduce brightness during idle states

Example integration pattern:
```python
from state.led_driver import LedDriver
from state.led_state_mapper import get_led_mapper

driver = LedDriver("ring_12bit")
mapper = get_led_mapper()

def apply_cortana_decision(decision):
    # Map decision to visual state
    mapper.set_state(decision["state"].upper())
    
    # Apply visual effect
    for i in range(driver.ring_count):
        r, g, b = mapper.get_effect_pattern(0, i, driver.ring_count)
        driver.set_pixel(i, r, g, b)
    
    driver.update()
```

## Next Steps

After deployment succeeds:
1. Document actual GPIO pin used in hardware diagram
2. Add power supply specifications to project wiki
3. Create LED visualization dashboard if desired
4. Consider adding proximity sensor triggers for auto-activation

---

**Status**: Ready for deployment ✓  
**Last Updated**: 2026-05-23  
**Files Created**: led_driver.py, led_state_mapper.py, LED_DRIVER_README.md
