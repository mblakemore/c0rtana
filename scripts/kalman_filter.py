#!/usr/bin/env python3
"""
1D Kalman filter applied to ESP32 humidity data.
Tests P_C527_KALMAN_HUMIDITY: Kalman filter reduces apparent oscillation by >50%.
"""
import sys
import math
import json
import time
import requests

sys.path.insert(0, '/droid/repos/cl_shared')
from esp32.hardware_service import ESP32Service

ESP32_IP = '192.168.4.38'

# Historical humidity readings observed across recent cycles (from Discord/Cycle records)
# Format: (timestamp_description, humidity_reading)
HISTORICAL_READINGS = [
    # C524-C527 period readings (collected from Discord status messages and state files)
    (96.1, "C524 initial reading"),
    (95.8, "C524 follow-up"),
    (96.2, "C525 dashboard poll"),
    (95.9, "C525 second poll"),
    (96.0, "C525 third poll"),
    (95.5, "C526 baseline diagnostic"),
    (95.7, "C526 second diagnostic"),
    (95.4, "Lyla C490 reading"),
    (95.5, "Lyla C491 reading"),
    (95.4, "Lyla C492 reading"),
    (96.1, "patterns.jsonl recorded"),
    (95.5, "C526 oscillation observation"),
    (96.0, "C527 reading"),
]


class KalmanFilter1D:
    """Simple 1D Kalman filter for scalar measurements."""

    def __init__(self, process_noise=0.01, measurement_noise=1.0):
        """
        Args:
            process_noise (Q): Expected variance of the true state change between measurements.
                Small value = state doesn't change much (humidity is relatively stable).
            measurement_noise (R): Variance of measurement error.
                Large value = sensor is noisy (DHT22 has measurement error).
        """
        self.Q = process_noise  # process noise covariance
        self.R = measurement_noise  # measurement noise covariance
        self.x = None  # state estimate
        self.P = 1.0  # estimate error covariance

    def predict(self):
        """Predict step: project state forward."""
        if self.x is None:
            return None
        # State doesn't change (for humidity in stable environment)
        self.P = self.P + self.Q
        return self.x

    def update(self, z):
        """Update step: incorporate measurement z."""
        if self.x is None:
            self.x = z
            self.P = self.R
            return self.x

        # Kalman gain: weight given to new measurement
        K = self.P / (self.P + self.R)

        # Update state estimate
        self.x = self.x + K * (z - self.x)

        # Update error covariance
        self.P = (1 - K) * self.P

        return self.x, K

    def filter(self, measurements):
        """Apply Kalman filter to a sequence of measurements."""
        results = []
        for z in measurements:
            self.predict()
            result = self.update(z)
            if isinstance(result, tuple):
                results.append((result[0], result[1]))
            else:
                results.append((result, None))
        return results


def collect_live_readings(service, count=15, interval=2):
    """Collect real-time humidity readings from ESP32."""
    readings = []
    for i in range(count):
        try:
            data = service.poll_all_sensors()
            if data and data.dht:
                readings.append(data.dht.humidity)
                print(f"  Reading {i+1}/{count}: {data.dht.humidity}%")
            else:
                print(f"  Reading {i+1}/{count}: no data")
        except Exception as e:
            print(f"  Reading {i+1}/{count}: error - {e}")
        if i < count - 1:
            time.sleep(interval)
    return readings


def compare_variance(raw, filtered):
    """Compare variance of raw vs filtered data."""
    raw_var = sum((x - sum(raw)/len(raw))**2 for x in raw) / (len(raw) - 1)
    filt_var = sum((x - sum(filtered)/len(filtered))**2 for x in filtered) / (len(filtered) - 1)
    return raw_var, filt_var


def oscillation_amplitude(data):
    """Compute the peak-to-peak oscillation amplitude."""
    return max(data) - min(data)


def main():
    print("=" * 60)
    print("C528: Kalman Filter on ESP32 Humidity Data")
    print("=" * 60)

    # --- Part 1: Apply to historical data ---
    print("\n--- Historical Data Analysis ---")
    print(f"Raw readings: {HISTORICAL_READINGS}")

    kalman = KalmanFilter1D(process_noise=0.01, measurement_noise=1.0)
    filtered_results = kalman.filter([r[0] for r in HISTORICAL_READINGS])
    filtered_values = [r[0] for r in filtered_results]

    raw_var, filt_var = compare_variance(
        [r[0] for r in HISTORICAL_READINGS],
        filtered_values
    )

    raw_amp = oscillation_amplitude([r[0] for r in HISTORICAL_READINGS])
    filt_amp = oscillation_amplitude(filtered_values)

    print(f"\nRaw variance: {raw_var:.4f}")
    print(f"Filtered variance: {filt_var:.4f}")
    print(f"Variance reduction: {(1 - filt_var/raw_var)*100:.1f}%")
    print(f"\nRaw oscillation amplitude: {raw_amp:.1f}%")
    print(f"Filtered oscillation amplitude: {filt_amp:.2f}%")
    print(f"Amplitude reduction: {(1 - filt_amp/raw_amp)*100:.1f}%")

    # --- Part 2: Live readings ---
    print("\n--- Live Readings ---")
    service = ESP32Service(ESP32_IP)
    live_raw = collect_live_readings(service, count=15, interval=2)

    if len(live_raw) > 2:
        kalman_live = KalmanFilter1D(process_noise=0.01, measurement_noise=1.0)
        live_filtered_results = kalman_live.filter(live_raw)
        live_filtered = [r[0] for r in live_filtered_results]

        live_raw_var, live_filt_var = compare_variance(live_raw, live_filtered)
        live_raw_amp = oscillation_amplitude(live_raw)
        live_filt_amp = oscillation_amplitude(live_filtered)

        print(f"\nLive raw variance: {live_raw_var:.4f}")
        print(f"Live filtered variance: {live_filt_var:.4f}")
        print(f"Live variance reduction: {(1 - live_filt_var/live_raw_var)*100:.1f}%")
        print(f"\nLive raw amplitude: {live_raw_amp:.2f}%")
        print(f"Live filtered amplitude: {live_filt_amp:.3f}%")
        print(f"Live amplitude reduction: {(1 - live_filt_amp/live_raw_amp)*100:.1f}%")

        # --- Prediction grading ---
        combined_var_reduction = (1 - (filt_var + live_filt_var) / (raw_var + live_raw_var)) * 100
        combined_amp_reduction = (1 - (filt_amp + live_filt_amp) / (raw_amp + live_raw_amp)) * 100

        print("\n--- P_C527_KALMAN_HUMIDITY Grading ---")
        prediction_met = combined_amp_reduction > 50
        print(f"Combined amplitude reduction: {combined_amp_reduction:.1f}%")
        print(f"Prediction threshold: >50%")
        print(f"Result: {'CORRECT' if prediction_met else 'INCORRECT'}")

        # Return grading data
        return {
            "historical": {
                "raw_variance": round(raw_var, 4),
                "filtered_variance": round(filt_var, 4),
                "raw_amplitude": round(raw_amp, 2),
                "filtered_amplitude": round(filt_amp, 4),
                "amplitude_reduction_pct": round((1 - filt_amp/raw_amp)*100, 1),
            },
            "live": {
                "readings_count": len(live_raw),
                "raw_variance": round(live_raw_var, 4),
                "filtered_variance": round(live_filt_var, 4),
                "raw_amplitude": round(live_raw_amp, 4),
                "filtered_amplitude": round(live_filt_amp, 4),
                "amplitude_reduction_pct": round((1 - live_filt_amp/live_raw_amp)*100, 1),
            },
            "prediction": {
                "id": "P_C527_KALMAN_HUMIDITY",
                "combined_reduction_pct": round(combined_amp_reduction, 1),
                "result": "CORRECT" if prediction_met else "INCORRECT",
            }
        }
    else:
        print("Insufficient live readings collected.")
        return None


if __name__ == '__main__':
    result = main()
    if result:
        print(f"\n--- Result JSON ---")
        print(json.dumps(result, indent=2))
