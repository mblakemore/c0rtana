#!/usr/bin/env python3
"""
Precision-weighted multi-sensor state estimator.

Applies C534 precision weighting insight: under predictive coding, attention IS
precision weighting. The Kalman filter Q/R parameters ARE precision estimates.

Fuses multiple sensor inputs weighted by their estimated reliability. Sensors
with higher precision (lower expected variance) exert more influence on the
fused estimate. This is the mechanism that turns predictive coding into active
attention — the system learns to attend to reliable information sources and
discount noisy ones.

Usage:
    python3 scripts/precision_weighted_estimator.py          # live mode
    python3 scripts/precision_weighted_estimator.py --demo   # historical data only
"""
import sys
import json
import math
import time
import argparse

sys.path.insert(0, '/droid/repos/cl_shared')
from esp32.hardware_service import ESP32Service

ESP32_IP = '192.168.4.38'


class PrecisionWeightedEstimator:
    """Multi-sensor state estimator with explicit precision weighting.

    Each sensor channel is independently filtered with its own precision-weighted
    estimate. The system then produces a unified "environment stability" score
    by combining normalized (z-scored) deviations from each channel's baseline.

    Under predictive coding theory (C534), this IS attention: the system learns
    to weight prediction errors by their reliability before propagating them
    upward. Dopamine encodes precision of prediction errors; acetylcholine
    encodes precision of sensory input.
    """

    def __init__(self, channels):
        """
        Args:
            channels: dict mapping channel_name -> {
                'precision': float  # initial precision estimate (higher = more trusted)
                'prior': float     # prior belief about the state
                'baseline': float  # expected baseline value (for normalization)
                'scale': float     # expected std deviation (for z-scoring)
            }
        """
        self.channels = {}
        self.estimated_state = {}
        self.baselines = {}
        self.scales = {}
        self.history = {}

        for name, config in channels.items():
            self.channels[name] = {
                'precision': config['precision'],
                'learned_variance': None,  # will be inferred from data
            }
            self.estimated_state[name] = config['prior']
            self.baselines[name] = config.get('baseline', config['prior'])
            self.scales[name] = config.get('scale', 1.0)
            self.history[name] = []

    def update_precision(self, channel, measurement):
        """Update precision estimate for a channel based on new measurement.

        Uses the innovation (difference between predicted and observed) to
        infer measurement variance. High innovation relative to prior suggests
        the sensor is noisy (lower precision).
        """
        ch = self.channels[channel]
        prior = self.estimated_state[channel]
        history = self.history[channel]

        # Innovation: how much did the measurement surprise us?
        innovation = abs(measurement - prior)

        # Track innovations for online variance estimation
        history.append(innovation)
        # Keep last 20 innovations for running variance
        if len(history) > 20:
            history.pop(0)

        # Estimate variance from recent innovations
        if len(history) >= 3:
            mean_inn = sum(history) / len(history)
            variance = sum((x - mean_inn) ** 2 for x in history) / (len(history) - 1)
            # Add small floor to avoid division by zero
            ch['learned_variance'] = max(variance, 0.001)

    def fuse(self, measurements):
        """Fuse multiple sensor measurements using precision weighting.

        Each channel is independently filtered. The fused score is a precision-
        weighted sum of normalized deviations (z-scores) from baseline, giving
        a single "environment stability" metric where reliable sensors dominate.

        Args:
            measurements: dict mapping channel_name -> current_measurement_value

        Returns:
            dict with:
                'stability_score': precision-weighted combined z-score (0 = baseline, higher = more deviation)
                'per_channel': {name: {'estimate': ..., 'z_score': ..., 'weight': ..., 'precision': ...}}
                'total_precision': sum of all channel precisions
        """
        weighted_z_sum = 0.0
        total_precision = 0.0
        per_channel = {}

        for channel, measurement in measurements.items():
            if channel not in self.channels:
                continue

            ch = self.channels[channel]

            # Use learned variance if available, otherwise initial precision
            if ch['learned_variance'] is not None:
                precision = 1.0 / ch['learned_variance']
            else:
                precision = ch['precision']

            # Update state estimate for this channel
            # (precision-weighted exponential smoothing)
            alpha = precision / (precision + 1.0)
            self.estimated_state[channel] = (
                self.estimated_state[channel] * (1 - alpha)
                + measurement * alpha
            )

            # Update precision estimate
            self.update_precision(channel, measurement)

            # Compute z-score: how many SDs from baseline?
            baseline = self.baselines[channel]
            scale = self.scales[channel]
            z_score = (self.estimated_state[channel] - baseline) / scale

            weight = precision  # precision IS the weight
            weighted_z_sum += z_score * weight
            total_precision += weight

            per_channel[channel] = {
                'measurement': measurement,
                'estimate': self.estimated_state[channel],
                'z_score': z_score,
                'precision': precision,
                'weight': weight,
            }

        if total_precision > 0:
            stability_score = weighted_z_sum / total_precision
        else:
            stability_score = 0.0

        # Normalize weights to sum to 1 for interpretability
        for ch_name in per_channel:
            per_channel[ch_name]['normalized_weight'] = (
                per_channel[ch_name]['weight'] / total_precision
            )

        return {
            'stability_score': stability_score,
            'total_precision': total_precision,
            'per_channel': per_channel,
        }


# Historical sensor readings from ESP32 across cycles C524-C534
# Format: list of dicts, each representing a polling cycle
HISTORICAL_SENSOR_DATA = [
    {'temperature': 22.1, 'humidity': 96.1, 'wifi_signal': -53},
    {'temperature': 21.9, 'humidity': 95.8, 'wifi_signal': -55},
    {'temperature': 22.0, 'humidity': 96.2, 'wifi_signal': -54},
    {'temperature': 21.8, 'humidity': 95.5, 'wifi_signal': -53},
    {'temperature': 22.1, 'humidity': 95.7, 'wifi_signal': -52},
    {'temperature': 22.0, 'humidity': 95.4, 'wifi_signal': -55},
    {'temperature': 21.9, 'humidity': 95.5, 'wifi_signal': -54},
    {'temperature': 22.0, 'humidity': 96.0, 'wifi_signal': -53},
    {'temperature': 21.8, 'humidity': 95.9, 'wifi_signal': -52},
    {'temperature': 22.1, 'humidity': 96.1, 'wifi_signal': -53},
    {'temperature': 21.9, 'humidity': 95.8, 'wifi_signal': -54},
    {'temperature': 22.0, 'humidity': 95.6, 'wifi_signal': -53},
    {'temperature': 21.8, 'humidity': 96.2, 'wifi_signal': -55},
    {'temperature': 22.0, 'humidity': 95.7, 'wifi_signal': -52},
    {'temperature': 22.1, 'humidity': 95.4, 'wifi_signal': -53},
]


def run_demo():
    """Run precision-weighted estimator on historical data."""
    print("=" * 60)
    print("C535: Precision-Weighted Multi-Sensor Estimator")
    print("=" * 60)

    # Configure channels with initial precision estimates
    # Temperature is stable (high precision), humidity is noisy (lower precision),
    # WiFi signal oscillates (moderate precision)
    channels = {
        'temperature': {'precision': 10.0, 'prior': 22.0, 'baseline': 22.0, 'scale': 0.5},
        'humidity': {'precision': 2.0, 'prior': 95.0, 'baseline': 95.0, 'scale': 3.0},
        'wifi_signal': {'precision': 5.0, 'prior': -53.0, 'baseline': -53.0, 'scale': 2.0},
    }

    estimator = PrecisionWeightedEstimator(channels)
    stability_scores = []

    print("\n--- Processing Historical Sensor Data ---")
    print(f"{'Step':<6} {'Temp':>8} {'Humid':>8} {'WiFi':>8} {'Stability':>11} {'Temp Wt':>8} {'Humid Wt':>8} {'WiFi Wt':>8}")
    print("-" * 78)

    for i, reading in enumerate(HISTORICAL_SENSOR_DATA):
        result = estimator.fuse(reading)
        stability_scores.append(result['stability_score'])

        pc = result['per_channel']
        temp_wt = pc.get('temperature', {}).get('normalized_weight', 0)
        humid_wt = pc.get('humidity', {}).get('normalized_weight', 0)
        wifi_wt = pc.get('wifi_signal', {}).get('normalized_weight', 0)

        print(f"{i+1:<6} "
              f"{reading['temperature']:>8.1f} "
              f"{reading['humidity']:>8.1f} "
              f"{reading['wifi_signal']:>8d} "
              f"{result['stability_score']:>11.4f} "
              f"{temp_wt:>8.3f} "
              f"{humid_wt:>8.3f} "
              f"{wifi_wt:>8.3f}")

    # Analyze learned precision
    print("\n--- Learned Precision ---")
    for channel, ch_data in estimator.channels.items():
        initial = ch_data['precision']
        learned = ch_data.get('learned_variance')
        if learned is not None:
            learned_precision = 1.0 / learned
            print(f"  {channel}: initial precision={initial:.1f}, "
                  f"learned variance={learned:.4f}, learned precision={learned_precision:.1f}")
        else:
            print(f"  {channel}: initial precision={initial:.1f} (insufficient data for learning)")

    # Compare stability score variance vs raw combined deviation
    combined_raw = []
    for reading in HISTORICAL_SENSOR_DATA:
        # Unweighted combined z-score
        temp_z = (reading['temperature'] - 22.0) / 0.5
        humid_z = (reading['humidity'] - 95.0) / 3.0
        wifi_z = (reading['wifi_signal'] - (-53.0)) / 2.0
        combined_raw.append((temp_z + humid_z + wifi_z) / 3.0)

    stability_var = sum((x - sum(stability_scores)/len(stability_scores))**2
                       for x in stability_scores) / (len(stability_scores) - 1)
    raw_var = sum((x - sum(combined_raw)/len(combined_raw))**2
                  for x in combined_raw) / (len(combined_raw) - 1)

    print(f"\n--- Variance Comparison ---")
    print(f"  Unweighted combined z-score variance: {raw_var:.4f}")
    print(f"  Precision-weighted stability variance: {stability_var:.4f}")
    if raw_var > 0:
        reduction = (1 - stability_var / raw_var) * 100
        print(f"  Variance reduction: {reduction:.1f}%")

    # Demonstrate precision adaptation
    print("\n--- Precision Adaptation Demo ---")
    print("Simulating sensor degradation (humidity becomes noisier)...")

    # Simulate increasing noise in one sensor
    degraded_readings = []
    for i in range(10):
        reading = {
            'temperature': 22.0 + (i % 3) * 0.1,  # stable
            'humidity': 95.0 + math.sin(i * 0.8) * (3 + i * 0.5),  # increasing noise
            'wifi_signal': -53 + (i % 2) * 1,  # moderate noise
        }
        degraded_readings.append(reading)

    estimator2 = PrecisionWeightedEstimator(channels)
    for reading in degraded_readings:
        result = estimator2.fuse(reading)

    # Show how precision shifted
    print(f"  Humidity precision: {channels['humidity']['precision']:.1f} -> "
          f"{1.0 / estimator2.channels['humidity'].get('learned_variance', 1.0 / channels['humidity']['precision']):.1f}")
    print(f"  Temperature precision: {channels['temperature']['precision']:.1f} -> "
          f"{1.0 / estimator2.channels['temperature'].get('learned_variance', 1.0 / channels['temperature']['precision']):.1f}")

    return estimator


def collect_live_readings(service, count=5, interval=2):
    """Collect multi-sensor readings from live ESP32."""
    readings = []
    for i in range(count):
        try:
            data = service.poll_all_sensors()
            if data:
                reading = {}
                if data.dht:
                    reading['temperature'] = data.dht.temp
                    reading['humidity'] = data.dht.humidity
                if reading:
                    readings.append(reading)
                    print(f"  Reading {i+1}/{count}: {reading}")
                else:
                    print(f"  Reading {i+1}/{count}: partial data")
            else:
                print(f"  Reading {i+1}/{count}: no data")
        except Exception as e:
            print(f"  Reading {i+1}/{count}: error - {e}")
        if i < count - 1:
            time.sleep(interval)
    return readings


def run_live():
    """Run precision-weighted estimator on live ESP32 data."""
    print("=" * 60)
    print("C535: Precision-Weighted Multi-Sensor Estimator (Live)")
    print("=" * 60)

    channels = {
        'temperature': {'precision': 10.0, 'prior': 22.0, 'baseline': 22.0, 'scale': 0.5},
        'humidity': {'precision': 2.0, 'prior': 95.0, 'baseline': 95.0, 'scale': 3.0},
        'wifi_signal': {'precision': 5.0, 'prior': -53.0, 'baseline': -53.0, 'scale': 2.0},
    }

    estimator = PrecisionWeightedEstimator(channels)
    service = ESP32Service(ESP32_IP)

    print("\n--- Collecting Live Sensor Data ---")
    live_readings = collect_live_readings(service)

    if len(live_readings) < 2:
        print("Insufficient live data. Running demo with historical data instead.")
        return run_demo()

    print("\n--- Fusing Live Readings ---")
    print(f"{'Step':<6} {'Temp':>8} {'Humid':>8} {'WiFi':>8} {'Stability':>11}")
    print("-" * 50)

    stability_scores = []
    for i, reading in enumerate(live_readings):
        result = estimator.fuse(reading)
        stability_scores.append(result['stability_score'])

        print(f"{i+1:<6} "
              f"{reading.get('temperature', 'N/A'):>8} "
              f"{reading.get('humidity', 'N/A'):>8} "
              f"{reading.get('wifi_signal', 'N/A'):>8} "
              f"{result['stability_score']:>11.4f}")

    # Analyze results
    if len(stability_scores) >= 2:
        stab_var = sum((x - sum(stability_scores)/len(stability_scores))**2
                      for x in stability_scores) / (len(stability_scores) - 1)
        print(f"\nStability score variance: {stab_var:.4f}")

    print("\n--- Learned Precision ---")
    for channel, ch_data in estimator.channels.items():
        initial = ch_data['precision']
        learned = ch_data.get('learned_variance')
        if learned is not None:
            print(f"  {channel}: initial={initial:.1f}, learned precision={1.0/learned:.1f}")
        else:
            print(f"  {channel}: initial={initial:.1f}")

    return estimator


def main():
    parser = argparse.ArgumentParser(description='Precision-weighted multi-sensor estimator')
    parser.add_argument('--demo', action='store_true', help='Use historical data only')
    args = parser.parse_args()

    if args.demo:
        result = run_demo()
    else:
        result = run_live()

    if result:
        print(f"\n--- Result JSON ---")
        output = {
            'type': 'precision_weighted_estimator',
            'channels': {},
        }
        for ch_name, ch_data in result.channels.items():
            output['channels'][ch_name] = {
                'initial_precision': ch_data['precision'],
                'learned_variance': ch_data.get('learned_variance'),
            }
        print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
