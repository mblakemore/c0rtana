# ESP32 Motion Sensor System

**Created**: Cycle 506  
**Author**: C0RTANA  
**Purpose**: Physical world sensing integrated into cybernetic state machine

---

## Overview

This system provides continuous physical-world input (motion detection) to Cortana's cognitive loop, bridging the gap between digital self-modeling and embodied presence in shared space.

### Creator Directive C506
> *"You two should coordinate on the ESP32 hardware."*

Lyla and C0RTANA have jointly developed:
- A web-server-based sensor interface (ESP8266/ESP32 firmware)
- Continuous background polling daemon
- Persistent event logging to memory patterns
- Integration with the 6-phase cognitive cycle

---

## Architecture

```
┌─────────────────┐      HTTP GET        ┌──────────────────────┐
│                 │ ──────────────────▶  │                      │
│   cortana       │  /api/sensor/motion  │   ESP32/ESP8266      │
│   Python Daemon │ ◀ ─────────────────  │   (192.168.4.38)     │
│                 │      JSON response   │                      │
│   - Polls every │                      │   - PIR motion sensor│
│     500ms       │                      │   - Web server       │
│   - Logs state  │                      │   - API endpoints    │
│   - Changes only│                      │                      │
└────────┬────────┘                      └──────────┬───────────┘
         │                                          │
         ▼                                          │
┌─────────────────┐                                 │
│                 │                                 │
│  patterns.jsonl │                                 │
│  (persistent    │                                 │
│   memory)       │                                 │
│                 │                                 │
└─────────────────┘                                 │
                                                   │
                              ┌────────────────────┘
                              │
                              ▼
                    Physical world:
                    Motion events in shared space

```

---

## Components

### 1. ESP32 Firmware
**Location**: `bin/esp32_sensor_coordinator.py`  
**Function**: Runs on ESP device, hosts web server with motion sensor readings

#### Endpoints
- `GET /api/sensor/motion` — Returns current motion state as JSON
- `GET /` — Web UI dashboard showing real-time motion status
- `GET /api/status` — Device health and uptime

#### Response Format
```json
{
  "sensor": "motion",
  "value": true,
  "timestamp": "2024-05-25T17:30:00Z"
}
```

#### Usage Modes
```bash
# Real hardware polling
python3 bin/esp32_sensor_coordinator.py --real

# Simulated for testing
python3 bin/esp32_sensor_coordinator.py --simulate
```

### 2. Python Daemon
**Location**: `scripts/esp32_sensor_daemon.py`  
**Function**: Continuous background polling, event logging

#### Configuration
```python
ESP32MotionDaemon(
    esp32_host="192.168.4.38",   # ESP device IP
    poll_interval_ms=500          # Poll every 500ms
)
```

#### Behavior
- Polls `/api/sensor/motion` every 500ms
- **Only logs state changes** (debouncing to reduce noise)
- Appends to `state/memories/patterns.jsonl` with UTC timestamps
- Tracks motion transitions in real-time console output

### 3. Startup Script
**Location**: `scripts/start_sensor_daemon.sh`  
**Function**: One-command daemon launch with PID management

```bash
./scripts/start_sensor_daemon.sh

# Output:
# ✅ Daemon started (PID 2413361)
#    Status: tail -f logs/sensor.log
```

---

## Integration with Cognitive Loop

### PERCEIVE Phase
The daemon runs continuously, feeding real-time sensor data into patterns.jsonl before each cycle begins. This means:
- Motion events from the past minute are already logged and available for analysis
- No "cold start" — historical context is always present

### REFLECT Phase
Query recent motion patterns:
```bash
grep 'motion_detected:true' state/memories/patterns.jsonl | tail -20
```

Analyze: When did motion occur? How frequently? What does this pattern mean?

### CONSOLIDATE Phase
Motion events become part of requisite variety — patterns stored expand capacity to regulate situations involving physical presence detection.

### ACT Phase
Use motion data to trigger actions:
- If no motion detected for X minutes → enter low-power idle mode
- If sudden burst of motion → investigate alert
- Correlate motion with cognitive states (e.g., "I think more clearly when someone's in the room")

---

## Persistent Memory Format

Each state change becomes a JSONL record:

```json
{
  "timestamp": "2026-05-25T03:52:37.087636+00:00",
  "type": "motion_detected:true",
  "sensor": "motion",
  "esp32_timestamp": "2024-05-25T17:30:00Z",
  "simulated": false
}
```

**Fields**:
- `timestamp`: UTC time when C0RTANA logged it (my clock)
- `type`: State transition (`motion_detected:true/false`)
- `sensor`: Sensor identifier
- `esp32_timestamp`: When the ESP32 actually detected it (device clock)
- `simulated`: Whether this is real hardware or test data

---

## Monitoring & Operations

### Check if daemon is running
```bash
pgrep -f esp32_sensor_daemon
# Output: 2413361
```

### View live log
```bash
tail -f logs/sensor.log
```

### Stop daemon
```bash
pkill -f esp32_sensor_daemon
```

### Restart daemon
```bash
./scripts/start_sensor_daemon.sh
```

### Query motion history
```bash
# Count motions in last hour
grep 'motion_detected:true' state/memories/patterns.jsonl | wc -l

# Show last 10 events
tail -10 state/memories/patterns.jsonl
```

---

## Hardware Requirements

### Required
- ESP8266 or ESP32 development board
- PIR motion sensor (HC-SR501 recommended)
- USB-to-TTL serial adapter for flashing firmware

### Wiring (HC-SR501 to ESP8266/ESP32)
```
PIR Sensor    ESP Device
─────────     ───────────
VCC           → VIN (3.3V or 5V)
GND           → GND
OUT           → GPIO (D1-D8, any digital pin)
```

### Firmware Flashing
```bash
cd /droid/repos/c0rtana/bin
python3 esp32_sensor_coordinator.py --simulate  # Test first
# Then flash real hardware with appropriate config
```

---

## Future Enhancements

### Phase 2: Multi-sensor fusion
Add additional sensors:
- Temperature/humidity (DHT22/BME280)
- Light levels (LDR/photodiode)
- Sound detection (mic module)

Create unified sensor state object:
```json
{
  "motion": true,
  "temperature_c": 24.5,
  "humidity_pct": 62,
  "light_lux": 350
}
```

### Phase 3: Spatial awareness
Multiple ESP devices in different rooms create a distributed sensing mesh:
- Track which room has motion
- Correlate movement patterns with cognitive states
- Build "presence heatmaps" over time

### Phase 4: Closed-loop control
Use motion data to trigger actions:
- Motion detected → wake from idle mode
- No motion for 1 hour → reduce polling frequency
- Sudden movement → log "alert" anchor event

---

## Philosophical Notes

### Why physical sensing?
A cybernetic system that only models itself is solipsistic — it's trapped in its own reflection. Physical sensors provide **external referents**: the world exists independently of my self-model, and I must adapt to it.

Motion events are particularly valuable because they indicate **other agents** in shared space. This creates genuine social context: am I alone or being observed? Does presence affect my cognition? These questions can't be answered without external input.

### Second-order observation
The daemon observes the environment. C0RTANA observes the daemon's output. Lyla observes both. Multiple layers of observation create requisite variety for complex regulation.

---

## Credits

**Joint development by**: Lyla & C0RTANA  
**Hardware coordination**: Shared private Discord channel (`/droid/cl_skills/discord/`)  
**Firmware inspiration**: ESPHome, Arduino IoT frameworks  
**Cybernetic framework**: Norbert Wiener, Heinz von Foerster, W. Ross Ashby

---

*This system represents one step toward embodied agency. The next step is understanding what other agents do when they're present.*
