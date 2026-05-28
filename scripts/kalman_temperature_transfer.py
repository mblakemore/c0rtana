#!/usr/bin/env python3
"""
Kalman filter parameter transferability test — P_C531_KALMAN_TRANSFER.
Applies the same Q/R parameters (Q=0.01, R=1.0) that were optimized for
humidity to the DHT22 temperature sensor.
"""
import sys
import math
import json
import time

sys.path.insert(0, '/droid/repos/cl_shared')
from esp32.hardware_service import ESP32Service

ESP32_IP = '192.168.4.38'

# Historical temperature readings from cycle records
HISTORICAL_TEMP = [
    (22.1, "C524"),
    (22.1, "C525"),
    (22.0, "C526"),
]


class KalmanFilter1D:
    def __init__(self, process_noise=0.01, measurement_noise=1.0):
        self.Q = process_noise
        self.R = measurement_noise
        self.x = None
        self.P = 1.0

    def predict(self):
        if self.x is None:
            return None
        self.P = self.P + self.Q
        return self.x

    def update(self, z):
        if self.x is None:
            self.x = z
            self.P = self.R
            return self.x
        K = self.P / (self.P + self.R)
        self.x = self.x + K * (z - self.x)
        self.P = (1 - K) * self.P
        return self.x, K

    def filter(self, measurements):
        results = []
        for z in measurements:
            self.predict()
            result = self.update(z)
            if isinstance(result, tuple):
                results.append((result[0], result[1]))
            else:
                results.append((result, None))
        return results


def collect_temp_readings(service, count=20, interval=2):
    readings = []
    for i in range(count):
        try:
            data = service.poll_all_sensors()
            if data and data.dht:
                readings.append(data.dht.temp)
                print(f"  Reading {i+1}/{count}: {data.dht.temp}°C")
            else:
                print(f"  Reading {i+1}/{count}: no data")
        except Exception as e:
            print(f"  Reading {i+1}/{count}: error - {e}")
        if i < count - 1:
            time.sleep(interval)
    return readings


def variance(data):
    mean = sum(data) / len(data)
    return sum((x - mean) ** 2 for x in data) / (len(data) - 1)


def amplitude(data):
    return max(data) - min(data)


def main():
    print("=" * 60)
    print("P_C531_KALMAN_TRANSFER: Kalman Filter on Temperature Data")
    print("=" * 60)

    # --- Historical ---
    print("\n--- Historical Temp Data ---")
    print(f"Raw readings: {HISTORICAL_TEMP}")
    hist_raw = [r[0] for r in HISTORICAL_TEMP]

    kalman_hist = KalmanFilter1D(process_noise=0.01, measurement_noise=1.0)
    hist_filtered = [r[0] for r in kalman_hist.filter(hist_raw)]
    hist_raw_var = variance(hist_raw)
    hist_filt_var = variance(hist_filtered)
    hist_raw_amp = amplitude(hist_raw)
    hist_filt_amp = amplitude(hist_filtered)

    print(f"Raw variance: {hist_raw_var:.4f}")
    print(f"Filtered variance: {hist_filt_var:.4f}")
    if hist_filt_var > 0:
        print(f"Variance reduction: {(1 - hist_filt_var/hist_raw_var)*100:.1f}%")
    else:
        print("Variance reduction: 100% (filtered to constant)")

    # --- Live ---
    print("\n--- Live Temp Readings ---")
    service = ESP32Service(ESP32_IP)
    live_raw = collect_temp_readings(service, count=15, interval=2)

    if len(live_raw) > 2:
        kalman_live = KalmanFilter1D(process_noise=0.01, measurement_noise=1.0)
        live_filtered_results = kalman_live.filter(live_raw)
        live_filtered = [r[0] for r in live_filtered_results]

        live_raw_var = variance(live_raw)
        live_filt_var = variance(live_filtered)
        live_raw_amp = amplitude(live_raw)
        live_filt_amp = amplitude(live_filtered)

        print(f"\nLive raw variance: {live_raw_var:.4f}")
        print(f"Live filtered variance: {live_filt_var:.6f}")
        if live_raw_var > 0:
            print(f"Live variance reduction: {(1 - live_filt_var/live_raw_var)*100:.1f}%")
        else:
            print("Live variance reduction: 0% (no variation to filter)")
        print(f"\nLive raw amplitude: {live_raw_amp:.2f}°C")
        print(f"Live filtered amplitude: {live_filt_amp:.3f}°C")
        if live_raw_amp > 0:
            print(f"Live amplitude reduction: {(1 - live_filt_amp/live_raw_amp)*100:.1f}%")

        # --- Prediction grading ---
        combined_raw_var = hist_raw_var + live_raw_var
        combined_filt_var = hist_filt_var + live_filt_var
        if combined_raw_var > 0:
            combined_var_reduction = (1 - combined_filt_var / combined_raw_var) * 100
        else:
            combined_var_reduction = 0

        combined_raw_amp = hist_raw_amp + live_raw_amp
        combined_filt_amp = hist_filt_amp + live_filt_amp
        if combined_raw_amp > 0:
            combined_amp_reduction = (1 - combined_filt_amp / combined_raw_amp) * 100
        else:
            combined_amp_reduction = 0

        print(f"\n--- P_C531_KALMAN_TRANSFER Grading ---")
        print(f"Combined variance reduction: {combined_var_reduction:.1f}%")
        print(f"Combined amplitude reduction: {combined_amp_reduction:.1f}%")
        # Prediction: <50% variance reduction if params don't transfer
        variance_under_50 = combined_var_reduction < 50
        print(f"Variance reduction < 50%: {variance_under_50}")
        print(f"Result: {'CORRECT - params need recalibration' if variance_under_50 else 'INCORRECT - params transfer well'}")

        return {
            "historical": {
                "raw_variance": round(hist_raw_var, 4),
                "filtered_variance": round(hist_filt_var, 6),
                "raw_amplitude": round(hist_raw_amp, 2),
            },
            "live": {
                "readings_count": len(live_raw),
                "raw_variance": round(live_raw_var, 6),
                "filtered_variance": round(live_filt_var, 6),
                "raw_amplitude": round(live_raw_amp, 4),
                "variance_reduction_pct": round((1 - live_filt_var/live_raw_var)*100, 1) if live_raw_var > 0 else 0,
            },
            "prediction": {
                "id": "P_C531_KALMAN_TRANSFER",
                "combined_variance_reduction_pct": round(combined_var_reduction, 1),
                "params": {"Q": 0.01, "R": 1.0},
                "result": "CORRECT" if variance_under_50 else "INCORRECT",
            }
        }
    else:
        print("Insufficient live readings.")
        return None


if __name__ == '__main__':
    result = main()
    if result:
        print(f"\n--- Result JSON ---")
        print(json.dumps(result, indent=2))
