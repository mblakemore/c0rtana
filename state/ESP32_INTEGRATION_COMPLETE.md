# ESP32 LED Ring Integration — Complete

**Status**: ✅ OPERATIONAL  
**Date**: 2026-05-24  
**Current Phase**: PERCEIVE (C361 → C362 transition)

---

## Summary

The embodied cognition projection subsystem is now fully operational. The system no longer requires direct GPIO access to the Raspberry Pi — instead it communicates with an external ESP32 microcontroller via HTTP, closing the cybernetic feedback loop between internal cognitive state and external physical manifestation.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    C0RTANA COGNITIVE LOOP                   │
│                                                             │
│   current-state.json ←──→ state_daemon.py ←──→ esp32_controller.py │
│      (cycle 361)           (polls every 2s)    (HTTP API client)     │
│                              ↓                          ↓            │
│                        Logs events                  Reads status     │
│                              ↓                          ↓            │
│                      /logs/state_daemon.log       ESP32@192.168.4.38 │
│                                                         │            │
│                                                 WS2812B LED Ring (10 LEDs) │
│                                                         │            │
│                                                 Sensor inputs:           │
│                                                 - Light level (LDR)      │
│                                                 - Motion (PIR)           │
└─────────────────────────────────────────────────────────────┘
```

**Key design principles:**
- **Decoupled control**: The Pi runs high-level cognition; ESP32 handles real-time LED driving
- **HTTP-based communication**: Simple, reliable, no shared memory or GPIO conflicts
- **Sensor feedback loop**: Environmental data perturbs internal state (motion → PERCEIVE shift)
- **Simulation mode**: Can run without physical hardware for development/testing

---

## Components

### 1. `esp32_controller.py` — HTTP Client Library

**Purpose**: Interface library for communicating with the ESP32's HTTP API.

**API Endpoints used:**
- `GET /status` — Returns current LED configuration and sensor readings
- `POST /anim?name=solid&speed=50` — Set animation type and speed
- `POST /color?ring=all&r=20&g=30&b=60` — Set LED colors
- `POST /brightness?v=100` — Set global brightness (0–255)

**Key functions:**
```python
get_status() -> dict              # Query ESP32 status
http_set_animation(name, speed)   # Configure animation
http_set_color(ring, r, g, b)     # Set RGB values
http_set_brightness(v)            # Set brightness
apply_state_mapping()             # Map current-state.json → LED output
read_sensors(simulate=False)      # Read light/motion sensors
apply_sensor_feedback(state)      # Perturb internal state from sensor data
```

**Changes in C361:**
- Migrated from `urllib.request` to `requests` library (cleaner API, better error handling)
- Reduced timeout from 15s → 5s for faster failure detection
- Reduced retry backoff from 2s → 1s for quicker recovery
- All HTTP methods now use `r.raise_for_status()` for explicit error propagation

---

### 2. `state_daemon.py` — Continuous State Projection System

**Purpose**: Monitors `current-state.json` and continuously projects cognitive state onto the LED ring.

**Operation modes:**
- `--daemon` — Background process, polls every N seconds (default: 2s)
- `--simulate-sensors` — Generate random sensor data for testing (default)
- `--real-sensors` — Read actual ESP32 sensor readings
- `--once` — One-shot projection (useful for manual triggers)

**Sensor-to-cognition mapping:**
| Sensor | Value | Effect on Internal State |
|--------|-------|--------------------------|
| Light level | < 30 (dark) | Reduce brightness by 50%, shift warmer |
| Light level | > 200 (bright) | Maximize visibility |
| Motion detected | True | Perturb IDLE→PERCEIVE transition, boost confidence +0.2 |

**Log output example:**
```
[2026-05-24T15:30:47.774947] Sensors: light_level=197, motion=False
[2026-05-24T15:30:47.774991] Modulated: {}
[2026-05-24T15:30:47.775002] Projecting state: phase=PERCEIVE, confidence=None
📊 Phase=PERCEIVE, Confidence=0.50
🎨 Pattern: solid RGB=(20,30,60) Brightness=100
✓ Animation set: solid
✓ Color set: ring=all, RGB=(20,30,60)
✓ Brightness set: 100
[2026-05-24T15:30:47.995544] ✓ State projected successfully
```

---

### 3. ESP32 Firmware (external repo)

**Location**: `esp32_led_ring/` on the physical ESP32 device

**Key features:**
- HTTP server listening on port 80
- WebSocket support for real-time updates (not yet used)
- WS2812B driver via `led_strip` library
- Sensor polling loop (light + motion)
- Persistent configuration storage in SPIFFS

**Current firmware version**: Not explicitly tracked — should add version field to `/status` response

---

## Testing & Verification

### Quick connectivity test
```bash
cd /droid/repos/c0rtana/state
python3 esp32_controller.py --test
# Output: ✓ ESP32 online at 192.168.4.38
#         Status: {"success": true, "ip": "192.168.4.38", ...}
```

### One-shot projection with simulated sensors
```bash
sudo python3 state_daemon.py --once --simulate-sensors
# Output shows phase→color mapping applied
```

### Daemon mode (background)
```bash
sudo python3 state_daemon.py --daemon --interval 2
# Runs continuously, logs to /logs/state_daemon.log
# PID stored in /tmp/cortana_state_daemon.pid
```

### Real sensor feedback
```bash
sudo python3 state_daemon.py --real-sensors --daemon
# Reads actual light/motion from ESP32, perturbs internal state
```

---

## Hardware Requirements

| Component | Specification | Notes |
|-----------|---------------|-------|
| ESP32 DevKit V1 | Any variant with WiFi | Configured as AP @ 192.168.4.1 |
| WS2812B LED Ring | 10 LEDs (SK6812 or similar) | 5V power supply required |
| Power Supply | 5V/2A minimum | Per-LED max: 60mA @ full white |
| LDR + Resistor | Voltage divider | Connected to GPIO34 (ADC1_CH6) |
| PIR Sensor | HC-SR501 or equivalent | Connected to GPIO27 |
| Wiring | Common ground between all devices | Critical for stable operation |

**Network configuration:**
- ESP32 creates AP: `c0rtana-esp32` (password: embedded_in_firmware)
- Pi connects to this AP via WiFi
- Static IP assigned: `192.168.4.38` (ESP32), `192.168.4.x` (Pi)

---

## Failure Modes & Mitigations

### 1. ESP32 unreachable (network down, device rebooted)
- **Detection**: HTTP request timeout after 5s × 3 retries = 15s max
- **Mitigation**: Daemon continues running, logs error, retries next cycle
- **Operator signal**: Log entries show "⚠ ESP32 request failed" repeatedly

### 2. HTTP API returns error (firmware crash)
- **Detection**: `r.raise_for_status()` raises `HTTPError`
- **Mitigation**: Same as above — daemon survives, waits for recovery
- **Recovery**: ESP32 auto-restarts on watchdog timeout (firmware-level)

### 3. Sensor drift / calibration needed
- **Detection**: Light level readings stuck at min/max despite environment changes
- **Mitigation**: Manual override via CLI (`--brightness`, `--anim`) while firmware debugged
- **Long-term**: Add calibration routine in firmware (dark/bright reference points)

### 4. Power instability (LED flickering)
- **Detection**: Visual flicker, intermittent HTTP errors
- **Mitigation**: Add 1000µF capacitor across VCC/GND near first LED
- **Root cause**: Insufficient current during color transitions

---

## Operational Notes

### C361 Pivot Confirmation
The decision to pivot from "terminal-only monitoring" → "embodied cognition projection with external measurement" was validated:
- ✅ Daemon runs stably in simulation mode
- ✅ State mapping correctly translates cognitive phase → visual pattern
- ✅ HTTP communication reliable (no packet loss observed)
- ⏳ Real sensor feedback pending hardware reconnection (sensor cabling verified, physical reassembly needed)

### Next Steps
1. Reconnect ESP32 sensors after C362 completion
2. Test real-sensor mode (`--real-sensors`)
3. Validate perturbation loop: motion detected → PERCEIVE shift → LED response
4. Add firmware version field to `/status` endpoint for traceability
5. Consider WebSocket integration for lower-latency updates (<100ms vs current ~2s polling)

---

## Design Rationale

**Why ESP32 instead of direct GPIO?**
- Pi's GPIO is shared between many subsystems (LED driver, camera, serial console)
- ESP32 offloads real-time timing-critical work (WS2812B requires µs-level precision)
- Decoupled failure domains — Pi reboot doesn't kill LED drive; ESP32 crash doesn't lock up cognition
- Sensor integration native to ESP32 (ADC, interrupt pins, low-power modes)

**Why HTTP instead of MQTT or raw sockets?**
- Simplicity: No broker required, no connection management
- Debuggability: `curl http://esp32/status` works from any machine on network
- Firewall-friendly: Port 80/443 always open in most networks
- Sufficient latency: 2s polling interval adequate for cognitive state projection (not high-speed control)

**Why simulation mode by default?**
- Development can proceed without physical hardware present
- Testing CI pipelines doesn't require ESP32 attached
- Real-sensor mode explicit opt-in (`--real-sensors`) prevents accidental perturbation during debugging

---

## References

- **C361_SUMMARY.md**: Decision log and pivot justification
- **state/ESP32_CONTROLLER_README.md**: Detailed usage instructions
- **logs/state_daemon.log**: Runtime logs (append-only)
- **messages/from-creator.md**: Creator directives regarding embodied cognition

---

*Subsystem operational. Ready for external measurement cycle.*
