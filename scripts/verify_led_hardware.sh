#!/bin/bash
# LED Hardware Verification Script
# Checks GPIO configuration and tests LED driver functionality

set -e

echo "=== C0RTANA LED Driver Hardware Check ==="
echo ""

# Check if Python with required libraries is available
echo "Checking dependencies..."
python3 -c "import neopixel; import lgpio" 2>/dev/null && echo "✓ Required Python libraries installed" || {
    echo "✗ Missing libraries - install with:"
    echo "  pip3 install adafruit-circuitpython-neopixel rpi-lgpio"
    exit 1
}

# Check if running on Raspberry Pi
if [ ! -f "/proc/device-tree/model" ]; then
    echo "⚠ Not running on Raspberry Pi (simulation mode)"
    SIMULATION_MODE=true
else
    PI_MODEL=$(cat /proc/device-tree/model)
    echo "✓ Running on: $PI_MODEL"
    SIMULATION_MODE=false
fi

echo ""

# Test LED driver module import
echo "Testing LED driver imports..."
cd /home/pi/c0rtana/state
python3 -c "from led_driver import LedDriver; from led_state_mapper import get_led_mapper, LedStateMapper" && \
    echo "✓ LED driver modules import successfully" || {
    echo "✗ Module import failed"
    exit 1
}

echo ""

# Show available GPIO configurations
echo "Available GPIO configurations in led_driver.py:"
grep -A5 'GPIO_CONFIG = {' state/led_driver.py | head -8

echo ""

# Run self-test if not in simulation mode
if [ "$SIMULATION_MODE" = false ]; then
    echo "Running hardware self-test..."
    python3 led_driver.py --test
    echo ""
    echo "✓ Hardware verification complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Verify LEDs show rainbow cascade during test"
    echo "  2. Check wiring connections match GPIO config"
    echo "  3. Ensure adequate power supply (5V, ~60mA per LED)"
else
    echo "Hardware test skipped (simulation mode)"
    echo "Run on actual Raspberry Pi for full verification"
fi
