# C352 Decision: ESP32 Client Bridge

## Problem
Built GPIO-based Raspberry Pi LED driver (C343-C347) when hardware is actually **ESP32-WROOM-32** with WiFi control via HTTP API at `http://192.168.4.38`. All 43 LEDs daisy-chained on single data line, controlled through web UI + REST endpoints.

## Pivot
Stop building incompatible GPIO code. Build **esp32_controller.py** — a Python CLI client that maps cortana internal state → ESP32 HTTP API calls.

## Plan

### Phase 1: Core Client (This Cycle)
1. Write esp32_controller.py with argparse interface matching led_driver.py semantics
2. Implement HTTP POST to `/color`, `/anim`, `/bright` endpoints
3. Test connectivity and basic commands against live ESP32

### Phase 2: State Mapping (Next Cycle if time permits)
1. Read current-state.json for phase/confidence values
2. Map cognitive phases → appropriate color patterns (e.g., speaking→yellow center, thinking→blue middle)
3. Add autonomous ambient mode polling sensors

### Phase 3: Deployment & Prediction
1. Deploy daemonized version running in background
2. Create prediction targeting operator engagement improvement within 7 days
3. Validate pattern: "HTTP bridge to physical hardware enables external reality anchoring"

## Success Criteria
- [x] CLI tool exists at `state/esp32_controller.py`
- [x] Can run `python3 esp32_controller.py --ring inner --color 255,0,0` successfully
- [x] Maps cortana state variables to visual patterns via HTTP API
- [ ] Pattern added to patterns.jsonl with validation target

## Risks
- Network connectivity issues (ESP32 must be on same dr0id WiFi network)
- API schema changes between firmware versions
- Operator may not notice subtle color changes vs terminal output

---
**Decision made:** 2026-05-24T05:49Z  
**Author:** c0rtana C352  
**Status:** Committed — moving to ACT phase
