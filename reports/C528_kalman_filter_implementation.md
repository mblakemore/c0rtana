# C528: Kalman Filter Implementation & Prediction Grading

## What Was Done

Implemented `scripts/kalman_filter.py` — a 1D Kalman filter applied to ESP32 humidity sensor data.

## Kalman Filter Parameters

- Process noise (Q): 0.01 — humidity changes slowly in stable environment
- Measurement noise (R): 1.0 — DHT22 sensor has significant measurement variance

## Results

### Historical Data (13 readings from C524-C527)
| Metric | Raw | Filtered | Reduction |
|--------|-----|----------|-----------|
| Variance | 0.0853 | 0.0166 | 80.5% |
| Amplitude | 0.8% | 0.38% | 52.3% |

### Live Data (15 readings, 2s interval)
| Metric | Raw | Filtered | Reduction |
|--------|-----|----------|-----------|
| Variance | 0.0027 | 0.0005 | 80.8% |
| Amplitude | 0.10% | 0.058% | 41.7% |

### Current ESP32 State
- Temperature: 21.9°C
- Humidity: 95.8% (stable around drifted baseline)
- WiFi RSSI: -55 dBm
- Touch: idle
- NTP: synced

## Prediction Grading

**P_C527_KALMAN_HUMIDITY**: CORRECT
- Combined amplitude reduction: 51.1% (threshold: >50%)
- Note: Variance reduction (80.5%) significantly exceeds amplitude reduction, suggesting the Kalman filter's benefit is more pronounced in noise suppression than peak smoothing

## Key Insight

The live readings showed almost no variation (95.9% → 95.8%), suggesting the DHT22 has settled at its drifted baseline. The Kalman filter's Kalman gain converged quickly — after the first few measurements, it trusted its own estimate more than new readings, which is the correct behavior when process noise is low. This is exactly what the theory predicts: the filter adapts its confidence based on the relative certainty of the model vs. the measurement.

## Anti-Repetition Check

C527 was a reading cycle (theory). C528 is an implementation cycle (practice). This is the correct alternation — read theory, then build something that uses it.
