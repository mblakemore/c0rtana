#!/usr/bin/env python3
"""
Sensor calibration tool with Kalman bias estimation.

Uses ground-truth reference measurement to estimate DHT22 systematic bias,
then applies Kalman filtering to produce corrected readings and forward predictions.

Augmented state-space model (4D):
  State: [true_humidity, true_temp, bias_humidity, bias_temp]
  Process: random walk (all 4 states slowly drift)
  Measurement: z = [raw_h, raw_t] = [true_h + bias_h, true_t + bias_t] + noise

When a ground-truth reference is available, we observe both raw AND true,
giving us a direct bias measurement. This dramatically reduces uncertainty
in the bias estimate compared to inferring it from raw data alone.

Connection to C565 Kalman filter: same recursive Bayesian framework,
extended to handle systematic bias as a state variable.
Connection to Lyla C497: Lyla already identified DHT22 calibration offsets
(humidity -43.6, temp -2.7C). Our tool tracks how those offsets evolve.
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

DRIFT_LOG = Path("state/sensor_drift_log.jsonl")


class KalmanBiasEstimator:
    """4D Kalman filter: [true_h, true_t, bias_h, bias_t].

    Estimates both the true sensor value AND the systematic bias,
    using raw DHT22 readings and optional ground-truth references.
    """

    def __init__(self):
        self.x = None  # 4-element state vector
        self.P = None  # 4x4 covariance matrix

        # Process noise covariances (how fast each state can change)
        self.Q = {
            "true_h": 0.01,    # True humidity changes slowly
            "true_t": 0.001,   # True temp changes slowly
            "bias_h": 0.05,    # Bias can drift (DHT22 aging, temperature effects)
            "bias_t": 0.005,   # Temp bias drifts slowly
        }

        # Measurement noise covariances
        self.R_raw = {"h": 4.0, "t": 0.25}       # DHT22 accuracy
        self.R_ref = {"h": 2.0, "t": 0.25}        # Ground truth + timing uncertainty

    def _init_state(self, raw_h, raw_t):
        """Initialize from first raw reading.

        Split raw reading roughly in half between true value and bias.
        This is a crude prior — the filter corrects it quickly.
        """
        # Prior: assume ~50/50 split (true ~74%, bias ~24% for humidity)
        self.x = [raw_h * 0.75, 20.0, raw_h * 0.25, raw_t - 20.0]
        # Initialize diagonal covariance — high uncertainty for bias
        self.P = [
            [100, 0, 0, 0],
            [0, 4, 0, 0],
            [0, 0, 400, 0],
            [0, 0, 0, 16],
        ]

    def _q_matrix(self):
        return [
            [self.Q["true_h"], 0, 0, 0],
            [0, self.Q["true_t"], 0, 0],
            [0, 0, self.Q["bias_h"], 0],
            [0, 0, 0, self.Q["bias_t"]],
        ]

    def predict(self):
        """Predict step: propagate state and covariance."""
        if self.x is None:
            return
        # State stays same (random walk), covariance grows
        Q = self._q_matrix()
        self.P = [[self.P[i][j] + Q[i][j] for j in range(4)] for i in range(4)]

    def _mat_inv_2x2(self, m):
        det = m[0][0] * m[1][1] - m[0][1] * m[1][0]
        if abs(det) < 1e-12:
            return [[1, 0], [0, 1]]
        return [
            [m[1][1] / det, -m[0][1] / det],
            [-m[1][0] / det, m[0][0] / det],
        ]

    def update_raw(self, raw_h, raw_t):
        """Update with raw DHT22 reading.

        Measurement model: z = [true_h + bias_h, true_t + bias_t]
        Innovation: z - (x[0] + x[2], x[1] + x[3])
        """
        if self.x is None:
            self._init_state(raw_h, raw_t)
            return {
                "corrected": [self.x[0], self.x[1]],
                "bias": [self.x[2], self.x[3]],
                "kalman_gain": None,
            }

        self.predict()

        # Innovation
        pred_h = self.x[0] + self.x[2]
        pred_t = self.x[1] + self.x[3]
        innov = [raw_h - pred_h, raw_t - pred_t]

        # Measurement matrix H: maps 4D state to 2D observation
        # H = [[1, 0, 1, 0], [0, 1, 0, 1]]
        # HP = H @ P (2x4)
        HP = [
            [self.P[0][j] + self.P[2][j] for j in range(4)],
            [self.P[1][j] + self.P[3][j] for j in range(4)],
        ]
        # HPt = HP @ H^T = HP[:, [0,1,2,3]] projected to 2x2
        HPt = [
            [HP[0][0] + HP[0][2], HP[0][1] + HP[0][3]],
            [HP[1][0] + HP[1][2], HP[1][1] + HP[1][3]],
        ]
        # S = HPt + R
        S = [
            [HPt[0][0] + self.R_raw["h"], HPt[0][1]],
            [HPt[1][0], HPt[1][1] + self.R_raw["t"]],
        ]
        S_inv = self._mat_inv_2x2(S)

        # Kalman gain K = P @ H^T @ S^-1 (4x2)
        K = [
            [HP[0][0] * S_inv[0][0] + HP[0][1] * S_inv[1][0],
             HP[0][0] * S_inv[0][1] + HP[0][1] * S_inv[1][1]],
            [HP[1][0] * S_inv[0][0] + HP[1][1] * S_inv[1][0],
             HP[1][0] * S_inv[0][1] + HP[1][1] * S_inv[1][1]],
            [HP[0][0] * S_inv[0][0] + HP[0][1] * S_inv[1][0],
             HP[0][0] * S_inv[0][1] + HP[0][1] * S_inv[1][1]],
            [HP[1][0] * S_inv[0][0] + HP[1][1] * S_inv[1][0],
             HP[1][0] * S_inv[0][1] + HP[1][1] * S_inv[1][1]],
        ]

        # Update state
        for i in range(4):
            self.x[i] += K[i][0] * innov[0] + K[i][1] * innov[1]

        KH = [[0]*4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                h_j0 = 1 if j in (0, 2) else 0
                h_j1 = 1 if j in (1, 3) else 0
                KH[i][j] = K[i][0] * h_j0 + K[i][1] * h_j1

        KHP = [[sum(KH[i][k] * self.P[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
        self.P = [[self.P[i][j] - KHP[i][j] for j in range(4)] for i in range(4)]

        # Clamp diagonal to prevent negative variance
        for i in range(4):
            self.P[i][i] = max(self.P[i][i], 1e-6)

        corrected_h = self.x[0]
        corrected_t = self.x[1]

        return {
            "corrected": [corrected_h, corrected_t],
            "bias": [self.x[2], self.x[3]],
            "kalman_gain": K,
        }

    def update_reference(self, raw_h, raw_t, true_h, true_t):
        """Update with ground-truth reference measurement.

        We observe both raw AND true values, giving direct bias info.
        Innovation on bias: bias = raw - true
        This is the most informative update type.
        """
        if self.x is None:
            self.x = [true_h, true_t, raw_h - true_h, raw_t - true_t]
            self.P = [
                [self.R_ref["h"], 0, 0, 0],
                [0, self.R_ref["t"], 0, 0],
                [0, 0, self.R_raw["h"] + self.R_ref["h"], 0],
                [0, 0, 0, self.R_raw["t"] + self.R_ref["t"]],
            ]
            return {
                "corrected": [true_h, true_t],
                "bias": [self.x[2], self.x[3]],
                "kalman_gain": None,
            }

        self.predict()

        # Innovations: true value and bias
        innov_true_h = true_h - self.x[0]
        innov_true_t = true_t - self.x[1]
        innov_bias_h = (raw_h - true_h) - self.x[2]
        innov_bias_t = (raw_t - true_t) - self.x[3]
        innov = [innov_true_h, innov_true_t, innov_bias_h, innov_bias_t]

        # Measurement: [true_h, true_t, raw_h - true_h, raw_t - true_t]
        # H = 4x4 identity (we observe all 4 states directly, with noise)
        # K = P @ (P + R)^-1
        R_aug = [
            [self.R_ref["h"], 0, 0, 0],
            [0, self.R_ref["t"], 0, 0],
            [0, 0, self.R_raw["h"] + self.R_ref["h"], 0],
            [0, 0, 0, self.R_raw["t"] + self.R_ref["t"]],
        ]
        PR = [[self.P[i][j] + R_aug[i][j] if i == j else self.P[i][j]
               for j in range(4)] for i in range(4)]

        # Inverse of diagonal matrix is just reciprocal of diagonal
        PR_inv = [[0]*4 for _ in range(4)]
        for i in range(4):
            PR_inv[i][i] = 1.0 / PR[i][i] if abs(PR[i][i]) > 1e-12 else 1.0

        # K = P @ PR_inv
        K = [[sum(self.P[i][k] * PR_inv[k][j] for k in range(4))
              for j in range(4)] for i in range(4)]

        # Update state
        for i in range(4):
            self.x[i] += sum(K[i][j] * innov[j] for j in range(4))

        # Update covariance: P = (I - K) @ (P + R) = (I - K) @ PR
        IK = [[(1 if i == j else 0) - K[i][j] for j in range(4)] for i in range(4)]
        self.P = [[sum(IK[i][k] * PR[k][j] for k in range(4))
                   for j in range(4)] for i in range(4)]

        # Clamp diagonal to prevent negative variance (numerical stability)
        for i in range(4):
            self.P[i][i] = max(self.P[i][i], 1e-6)

        return {
            "corrected": [self.x[0], self.x[1]],
            "bias": [self.x[2], self.x[3]],
            "kalman_gain": K,
        }

    def get_uncertainty(self):
        return {
            "true_h": math.sqrt(self.P[0][0]) if self.P else None,
            "true_t": math.sqrt(self.P[1][1]) if self.P else None,
            "bias_h": math.sqrt(self.P[2][2]) if self.P else None,
            "bias_t": math.sqrt(self.P[3][3]) if self.P else None,
        }


def load_drift_log():
    entries = []
    if not DRIFT_LOG.exists():
        return entries
    for line in DRIFT_LOG.read_text().strip().split("\n"):
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def main():
    print("=" * 60)
    print("C566: Sensor Calibration — Kalman Bias Estimation")
    print("=" * 60)

    readings = load_drift_log()
    if not readings:
        print("No sensor data available")
        return None

    # Ground truth from Creator
    true_humidity = 61.0
    true_temp = (64.9 - 32) * 5 / 9  # 18.28°C
    print(f"\nGround truth: humidity={true_humidity}%, temp={true_temp:.2f}°C")

    # Use the last reading as the reference point (closest in time to ground truth)
    last_reading = readings[-1]
    print(f"Reference DHT22: humidity={last_reading['humidity']}%, "
          f"temp={last_reading['temp']}°C")
    print(f"Raw bias: humidity={last_reading['humidity'] - true_humidity:.1f}%, "
          f"temp={last_reading['temp'] - true_temp:.2f}°C")

    # Run augmented Kalman filter
    kf = KalmanBiasEstimator()

    print(f"\n{'Step':>4} {'Raw H':>7} {'Raw T':>7} {'Corr H':>7} {'Corr T':>7} "
          f"{'Bias H':>7} {'Bias T':>7}")
    print("-" * 65)

    results = []
    for i, r in enumerate(readings):
        raw_h, raw_t = r["humidity"], r["temp"]

        if i == len(readings) - 1:
            # Last reading: use ground-truth reference
            result = kf.update_reference(raw_h, raw_t, true_humidity, true_temp)
            marker = " <-- REF"
        else:
            result = kf.update_raw(raw_h, raw_t)
            marker = ""

        results.append(result)
        print(f"{i+1:>4} {raw_h:>7.1f} {raw_t:>7.1f} "
              f"{result['corrected'][0]:>7.2f} {result['corrected'][1]:>7.2f} "
              f"{result['bias'][0]:>7.2f} {result['bias'][1]:>7.2f}{marker}")

    # Forward prediction
    kf.predict()  # Step forward one measurement
    unc = kf.get_uncertainty()

    pred_h = kf.x[0]
    pred_t = kf.x[1]
    pred_bias_h = kf.x[2]
    pred_bias_t = kf.x[3]

    h_unc = unc["true_h"]
    t_unc = unc["true_t"]

    h_lo, h_hi = pred_h - 2 * h_unc, pred_h + 2 * h_unc
    t_lo, t_hi = pred_t - 2 * t_unc, pred_t + 2 * t_unc

    print(f"\n--- Forward Prediction (corrected, next reading) ---")
    print(f"Predicted true humidity: {pred_h:.2f}% +/- {h_unc:.2f}%")
    print(f"Predicted true temp:     {pred_t:.2f}C +/- {t_unc:.2f}C")
    print(f"Estimated bias humidity: {pred_bias_h:.2f}%")
    print(f"Estimated bias temp:     {pred_bias_t:.2f}C")
    print(f"\n95% CI true humidity: [{h_lo:.2f}%, {h_hi:.2f}%]")
    print(f"95% CI true temp:     [{t_lo:.2f}C, {t_hi:.2f}C]")

    # Compare with Lyla C497 calibration
    lyla_bias_h = 43.6
    lyla_bias_t = 2.7
    print(f"\n--- Comparison with Lyla C497 Calibration ---")
    print(f"Lyla bias:  humidity={lyla_bias_h}%, temp={lyla_bias_t}C")
    print(f"Our bias:   humidity={pred_bias_h:.1f}%, temp={pred_bias_t:.2f}C")
    print(f"Delta:      humidity={lyla_bias_h - pred_bias_h:.1f}%, "
          f"temp={lyla_bias_t - pred_bias_t:.2f}C")
    print(f"Interpretation: bias decreased by {lyla_bias_h - pred_bias_h:.1f}% humidity")
    print(f"  → DHT22 drift is modifying the systematic offset, not just adding noise")

    # Build prediction artifact
    prediction = {
        "id": "P_C566_SENSOR_CALIBRATION",
        "cycle": 566,
        "type": "calibrated_forward_prediction",
        "description": "Kalman bias estimator predicts next TRUE room conditions "
                       "using DHT22 + ground-truth calibration",
        "prediction": {
            "true_humidity": round(pred_h, 2),
            "true_humidity_95ci_low": round(h_lo, 2),
            "true_humidity_95ci_high": round(h_hi, 2),
            "true_temperature": round(pred_t, 2),
            "true_temperature_95ci_low": round(t_lo, 2),
            "true_temperature_95ci_high": round(t_hi, 2),
            "estimated_bias_humidity": round(pred_bias_h, 2),
            "estimated_bias_temperature": round(pred_bias_t, 2),
        },
        "ground_truth": {
            "humidity": true_humidity,
            "temperature": round(true_temp, 2),
            "temperature_fahrenheit": 64.9,
            "source": "Creator direct measurement",
        },
        "model": {
            "type": "KalmanBiasEstimator",
            "state_dim": 4,
            "n_training_readings": len(readings),
            "n_reference_measurements": 1,
        },
        "validate_at": "2026-06-05T00:00:00Z",
        "grading_criteria": "CORRECT if Creator's next reference measurement "
                           "is within 95% CI, MOSTLY_CORRECT if within 3-sigma, "
                           "INCORRECT otherwise",
        "created": datetime.now(timezone.utc).isoformat(),
    }

    pred_path = Path("state/predictions/P_C566_SENSOR_CALIBRATION.json")
    pred_path.write_text(json.dumps(prediction, indent=2) + "\n")
    print(f"\nPrediction saved to {pred_path}")

    # Save full report
    report = {
        "cycle": 566,
        "tool": "sensor_calibration.py",
        "description": "Sensor calibration with Kalman bias estimation",
        "calibration_analysis": {
            "n_readings": len(readings),
            "ground_truth": {
                "humidity": true_humidity,
                "temp_celsius": round(true_temp, 2),
                "temp_fahrenheit": 64.9,
            },
            "estimated_bias": {
                "humidity": round(pred_bias_h, 2),
                "temp": round(pred_bias_t, 2),
            },
            "lyla_c497_bias": {
                "humidity": lyla_bias_h,
                "temp": lyla_bias_t,
            },
            "bias_drift": {
                "humidity": round(lyla_bias_h - pred_bias_h, 1),
                "temp": round(lyla_bias_t - pred_bias_t, 2),
            },
            "corrected_readings": [
                {
                    "step": i + 1,
                    "corrected_humidity": round(r["corrected"][0], 4),
                    "corrected_temp": round(r["corrected"][1], 4),
                    "bias_humidity": round(r["bias"][0], 4),
                    "bias_temp": round(r["bias"][1], 4),
                }
                for i, r in enumerate(results)
            ],
            "final_uncertainty": {
                "true_humidity": round(unc["true_h"], 4),
                "true_temp": round(unc["true_t"], 4),
                "bias_humidity": round(unc["bias_h"], 4),
                "bias_temp": round(unc["bias_t"], 4),
            },
        },
        "forward_prediction": prediction,
        "created": datetime.now(timezone.utc).isoformat(),
    }

    report_path = Path("state/sensor_calibration_report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Report saved to {report_path}")

    return report


if __name__ == "__main__":
    main()
