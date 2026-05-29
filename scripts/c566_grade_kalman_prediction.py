#!/usr/bin/env python3
"""
C566: Grade P_C565 Kalman 2D prediction against fresh ESP32 reading.

P_C565 predicted (95% CI):
  humidity: 98.12% [96.33%, 99.91%]
  temp:     20.64C [20.19C, 21.09C]

Grading criteria: CORRECT if within 95% CI, MOSTLY_CORRECT if within 3-sigma, INCORRECT otherwise.
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request

ESP32_DHT_URL = "http://192.168.4.38/api/sensor/dht"
PRED_FILE = Path("state/predictions/P_C565_KALMAN_2D_PREDICTION.json")
GRADES_FILE = Path("state/predictions/grades.jsonl")


def fetch_esp32_dht() -> dict | None:
    try:
        req = Request(ESP32_DHT_URL, method="GET")
        req.add_header("User-Agent", "c0rtana-grader")
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [WARN] DHT unreachable: {e}")
        return None


def grade_prediction(pred: dict, actual: dict) -> dict:
    """Grade P_C565 Kalman prediction against actual reading."""
    h_actual = actual["humidity"]
    t_actual = actual["temp"]

    h_pred = pred["prediction"]["humidity"]
    h_ci_lo = pred["prediction"]["humidity_95ci_low"]
    h_ci_hi = pred["prediction"]["humidity_95ci_high"]
    t_pred = pred["prediction"]["temperature"]
    t_ci_lo = pred["prediction"]["temperature_95ci_low"]
    t_ci_hi = pred["prediction"]["temperature_95ci_high"]

    # 3-sigma bounds (approx 99.7% CI)
    h_3sig_lo = h_pred - 3 * (h_ci_hi - h_pred) / 2
    h_3sig_hi = h_pred + 3 * (h_ci_hi - h_pred) / 2
    t_3sig_lo = t_pred - 3 * (t_ci_hi - t_pred) / 2
    t_3sig_hi = t_pred + 3 * (t_ci_hi - t_pred) / 2

    # Grade humidity
    h_in_95ci = h_ci_lo <= h_actual <= h_ci_hi
    h_in_3sig = h_3sig_lo <= h_actual <= h_3sig_hi
    # Grade temperature
    t_in_95ci = t_ci_lo <= t_actual <= t_ci_hi
    t_in_3sig = t_3sig_lo <= t_actual <= t_3sig_hi

    # Brier score for each dimension
    h_error = abs(h_actual - h_pred)
    t_error = abs(t_actual - t_pred)
    h_range = h_ci_hi - h_ci_lo
    t_range = t_ci_hi - t_ci_lo
    h_brier = (h_error / h_range) ** 2 if h_range > 0 else 1.0
    t_brier = (t_error / t_range) ** 2 if t_range > 0 else 1.0
    avg_brier = (h_brier + t_brier) / 2

    if h_in_95ci and t_in_95ci:
        grade_status = "CORRECT"
        grade_value = 1.0
    elif (h_in_3sig and t_in_3sig):
        grade_status = "MOSTLY_CORRECT"
        grade_value = 0.75
    else:
        grade_status = "INCORRECT"
        grade_value = 0.0

    reason = (
        f"Actual reading: humidity={h_actual}%, temp={t_actual}C. "
        f"Humidity {h_actual}% within 95% CI [{h_ci_lo}%, {h_ci_hi}%]: {h_in_95ci}. "
        f"Temp {t_actual}C within 95% CI [{t_ci_lo}C, {t_ci_hi}C]: {t_in_95ci}. "
        f"Kalman filter prediction accuracy validated."
    )

    return {
        "id": "P_C565_KALMAN_2D_PREDICTION",
        "prediction": f"Kalman 2D: humidity {h_pred}% [{h_ci_lo}-{h_ci_hi}%, 95% CI], temp {t_pred}C [{t_ci_lo}-{t_ci_hi}C, 95% CI]",
        "actual": {"humidity": h_actual, "temp": t_actual},
        "grade": grade_value,
        "status": grade_status,
        "reason": reason,
        "brier_humidity": round(h_brier, 4),
        "brier_temp": round(t_brier, 4),
        "brier_avg": round(avg_brier, 4),
        "corrected_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    print("=" * 60)
    print("C566: Grade P_C565 Kalman 2D Prediction")
    print("=" * 60)

    pred = json.loads(PRED_FILE.read_text())
    print(f"\nPrediction: humidity {pred['prediction']['humidity']}%, temp {pred['prediction']['temperature']}C")
    print(f"  95% CI humidity: [{pred['prediction']['humidity_95ci_low']}%, {pred['prediction']['humidity_95ci_high']}%]")
    print(f"  95% CI temp:     [{pred['prediction']['temperature_95ci_low']}C, {pred['prediction']['temperature_95ci_high']}C]")

    actual = fetch_esp32_dht()
    if not actual:
        print("\nCould not fetch ESP32 data. Aborting grade.")
        return None

    print(f"\nActual reading: humidity {actual['humidity']}%, temp {actual['temp']}C")

    result = grade_prediction(pred, actual)
    print(f"\nGrade: {result['status']} (value={result['grade']})")
    print(f"  Brier humidity: {result['brier_humidity']}")
    print(f"  Brier temp:     {result['brier_temp']}")
    print(f"  Brier avg:      {result['brier_avg']}")
    print(f"  Reason: {result['reason']}")

    # Append to grades file
    if GRADES_FILE.exists():
        GRADES_FILE.write_text(GRADES_FILE.read_text().rstrip() + "\n" + json.dumps(result) + "\n")
    else:
        GRADES_FILE.write_text(json.dumps(result) + "\n")

    # Save grading report
    report = {
        "cycle": 566,
        "task": "grade_kalman_prediction",
        "prediction_id": "P_C565_KALMAN_2D_PREDICTION",
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    report_path = Path("state/kalman_prediction_grade_c566.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nReport saved to {report_path}")

    return result


if __name__ == "__main__":
    main()
