#!/usr/bin/env python3
"""
Sensor Calibration Dashboard Generator
Fetches live DHT22 data from ESP32, applies C566 Kalman bias corrections,
and generates a self-contained HTML dashboard with visualizations.

Usage: python3 scripts/sensor_dashboard.py [--ip <IP>] [--no-fetch]
  --no-fetch: Generate dashboard with cached data only (no ESP32 network call)
"""

import argparse
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


# C566 Kalman bias estimation results
CALIBRATION = {
    "bias_humidity": 45.93,
    "bias_temp": 3.86,
    "uncertainty_humidity": 0.2236,
    "uncertainty_temp": 0.0707,
    "source": "C566 KalmanBiasEstimator, n=6 readings + 1 Creator ground truth",
}

# Ground truth from Creator
GROUND_TRUTH = {
    "humidity": 61.0,
    "temp_celsius": 18.28,
    "temp_fahrenheit": 64.9,
    "source": "Creator direct measurement",
    "timestamp": "2026-05-29T16:34:00Z",
}

# DHT22 sensor noise specs
SENSOR_NOISE = {"humidity": 2.0, "temp": 0.5}


def fetch_dht22(ip: str, timeout: int = 10) -> dict | None:
    """Fetch current DHT22 reading from ESP32."""
    url = f"http://{ip}/api/sensor/dht"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except Exception as e:
        print(f"Failed to fetch DHT22: {e}")
        return None


def load_drift_history() -> list[dict]:
    """Load historical sensor readings from drift log."""
    drift_log = Path("state/sensor_drift_log.jsonl")
    entries = []
    if not drift_log.exists():
        return entries
    for line in drift_log.read_text().strip().split("\n"):
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def apply_calibration(raw_h: float, raw_t: float) -> dict:
    """Apply systematic bias correction and compute uncertainty bounds."""
    corrected_h = raw_h - CALIBRATION["bias_humidity"]
    corrected_t = raw_t - CALIBRATION["bias_temp"]

    total_unc_h = (SENSOR_NOISE["humidity"] ** 2 + CALIBRATION["uncertainty_humidity"] ** 2) ** 0.5
    total_unc_t = (SENSOR_NOISE["temp"] ** 2 + CALIBRATION["uncertainty_temp"] ** 2) ** 0.5

    return {
        "raw_humidity": raw_h,
        "raw_temp": raw_t,
        "corrected_humidity": round(corrected_h, 2),
        "corrected_temp": round(corrected_t, 2),
        "uncertainty_humidity": round(total_unc_h, 2),
        "uncertainty_temp": round(total_unc_t, 2),
        "humidity_95ci_low": round(corrected_h - 1.96 * total_unc_h, 2),
        "humidity_95ci_high": round(corrected_h + 1.96 * total_unc_h, 2),
        "temp_95ci_low": round(corrected_t - 1.96 * total_unc_t, 2),
        "temp_95ci_high": round(corrected_t + 1.96 * total_unc_t, 2),
    }


def generate_dashboard(live_reading: dict | None, history: list[dict]) -> str:
    """Generate self-contained HTML dashboard with embedded sensor data."""
    now = datetime.now(timezone.utc)

    # Build current reading
    current = None
    if live_reading:
        raw_h = live_reading.get("humidity")
        raw_t = live_reading.get("temp")
        if raw_h is not None and raw_t is not None:
            current = apply_calibration(raw_h, raw_t)

    # Build history series
    history_raw_h = []
    history_raw_t = []
    history_corr_h = []
    history_corr_t = []
    history_labels = []
    for entry in history:
        h = entry.get("humidity")
        t = entry.get("temp")
        ts = entry.get("timestamp", "")
        if h is not None and t is not None:
            history_raw_h.append(h)
            history_raw_t.append(t)
            history_corr_h.append(round(h - CALIBRATION["bias_humidity"], 2))
            history_corr_t.append(round(t - CALIBRATION["bias_temp"], 2))
            history_labels.append(ts[-8:-3] if len(ts) >= 11 else "")

    # JSON-serialize data for embedding
    data_json = json.dumps({
        "timestamp": now.isoformat(),
        "current": current,
        "ground_truth": GROUND_TRUTH,
        "calibration": CALIBRATION,
        "history_raw_humidity": history_raw_h,
        "history_raw_temp": history_raw_t,
        "history_corrected_humidity": history_corr_h,
        "history_corrected_temp": history_corr_t,
        "history_labels": history_labels,
        "live_available": live_reading is not None,
    }, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>C0RTANA — Sensor Calibration Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      background: #0a0a0f;
      color: #c8c8d4;
      padding: 24px;
      min-height: 100vh;
    }}
    h1 {{
      font-size: 1.4rem;
      color: #e8e8f0;
      margin-bottom: 4px;
      letter-spacing: 0.05em;
    }}
    .subtitle {{
      font-size: 0.75rem;
      color: #666;
      margin-bottom: 24px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .card {{
      background: #12121a;
      border: 1px solid #1e1e2e;
      border-radius: 8px;
      padding: 20px;
    }}
    .card h2 {{
      font-size: 0.8rem;
      color: #888;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      margin-bottom: 12px;
    }}
    .metric {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      padding: 6px 0;
      border-bottom: 1px solid #1a1a28;
    }}
    .metric:last-child {{ border-bottom: none; }}
    .metric-label {{ color: #888; font-size: 0.85rem; }}
    .metric-value {{ font-size: 1.1rem; font-weight: 600; }}
    .metric-value.raw {{ color: #f0a050; }}
    .metric-value.corrected {{ color: #50c8a0; }}
    .metric-value.gt {{ color: #60a0f0; }}
    .metric-value.gap {{ color: #f06060; }}
    .metric-value.ok {{ color: #50c8a0; }}
    .ci {{
      font-size: 0.7rem;
      color: #555;
      margin-top: 2px;
    }}
    .chart-container {{
      position: relative;
      height: 300px;
      margin-top: 8px;
    }}
    .status {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.7rem;
      font-weight: 600;
    }}
    .status.live {{ background: #1a3a2a; color: #50c8a0; }}
    .status.cache {{ background: #2a2a1a; color: #c8a850; }}
    .status.offline {{ background: #2a1a1a; color: #c87050; }}
    .gap-bar {{
      height: 8px;
      background: #1a1a28;
      border-radius: 4px;
      margin-top: 8px;
      overflow: hidden;
    }}
    .gap-bar-fill {{
      height: 100%;
      border-radius: 4px;
      transition: width 0.3s;
    }}
    .footer {{
      text-align: center;
      color: #444;
      font-size: 0.7rem;
      margin-top: 24px;
    }}
  </style>
</head>
<body>
  <h1>Sensor Calibration Dashboard</h1>
  <div class="subtitle">C0RTANA C569 — DHT22 bias-corrected readings via Kalman estimation</div>

  <div class="grid">
    <div class="card">
      <h2>Live Reading <span id="statusBadge" class="status"></span></h2>
      <div id="liveMetrics"></div>
    </div>
    <div class="card">
      <h2>Ground Truth Reference</h2>
      <div id="gtMetrics"></div>
    </div>
    <div class="card">
      <h2>Calibration Model</h2>
      <div id="calMetrics"></div>
    </div>
    <div class="card">
      <h2>Gap Analysis</h2>
      <div id="gapMetrics"></div>
    </div>
  </div>

  <div class="card" style="margin-bottom: 16px;">
    <h2>Humidity History — Raw vs Calibrated</h2>
    <div class="chart-container">
      <canvas id="humidityChart"></canvas>
    </div>
  </div>

  <div class="card">
    <h2>Temperature History — Raw vs Calibrated</h2>
    <div class="chart-container">
      <canvas id="tempChart"></canvas>
    </div>
  </div>

  <div class="footer">
    Generated {now.isoformat()} — Data embedded at generation time
  </div>

  <script>
    const data = {data_json};

    // Status badge
    const badge = document.getElementById('statusBadge');
    if (data.live_available && data.current) {{
      badge.textContent = 'LIVE';
      badge.className = 'status live';
    }} else {{
      badge.textContent = data.history_labels.length > 0 ? 'CACHED' : 'OFFLINE';
      badge.className = 'status ' + (data.history_labels.length > 0 ? 'cache' : 'offline');
    }}

    // Live metrics
    const liveHtml = document.getElementById('liveMetrics');
    if (data.current) {{
      const c = data.current;
      liveHtml.innerHTML = `
        <div class="metric">
          <span class="metric-label">Raw Humidity</span>
          <span class="metric-value raw">${{c.raw_humidity}}%</span>
        </div>
        <div class="metric">
          <span class="metric-label">Calibrated Humidity</span>
          <span class="metric-value corrected">${{c.corrected_humidity}}%</span>
        </div>
        <div class="ci">95% CI: [${{c.humidity_95ci_low}}%, ${{c.humidity_95ci_high}}%]</div>
        <div class="metric">
          <span class="metric-label">Raw Temperature</span>
          <span class="metric-value raw">${{c.raw_temp}}°C</span>
        </div>
        <div class="metric">
          <span class="metric-label">Calibrated Temperature</span>
          <span class="metric-value corrected">${{c.corrected_temp}}°C</span>
        </div>
        <div class="ci">95% CI: [${{c.temp_95ci_low}}°C, ${{c.temp_95ci_high}}°C]</div>
      `;
    }} else {{
      liveHtml.innerHTML = '<div style="color: #555; padding: 12px 0;">No live data available</div>';
    }}

    // Ground truth metrics
    const gt = data.ground_truth;
    document.getElementById('gtMetrics').innerHTML = `
      <div class="metric">
        <span class="metric-label">Humidity</span>
        <span class="metric-value gt">${{gt.humidity}}%</span>
      </div>
      <div class="metric">
        <span class="metric-label">Temperature</span>
        <span class="metric-value gt">${{gt.temp_celsius}}°C (${{gt.temp_fahrenheit}}°F)</span>
      </div>
      <div class="ci">Source: ${{gt.source}} (${{gt.timestamp}})</div>
    `;

    // Calibration model metrics
    const cal = data.calibration;
    document.getElementById('calMetrics').innerHTML = `
      <div class="metric">
        <span class="metric-label">Bias Humidity</span>
        <span class="metric-value">${{cal.bias_humidity}}%</span>
      </div>
      <div class="metric">
        <span class="metric-label">Bias Temperature</span>
        <span class="metric-value">${{cal.bias_temp}}°C</span>
      </div>
      <div class="ci">${{cal.source}}</div>
    `;

    // Gap analysis
    const gapDiv = document.getElementById('gapMetrics');
    if (data.current) {{
      const hGap = data.current.corrected_humidity - gt.humidity;
      const tGap = data.current.corrected_temp - gt.temp_celsius;
      const hGapPct = Math.abs(hGap) / gt.humidity * 100;
      const hBarColor = Math.abs(hGap) > 5 ? '#f06060' : '#50c8a0';
      const tBarColor = Math.abs(tGap) > 2 ? '#f06060' : '#50c8a0';

      gapDiv.innerHTML = `
        <div class="metric">
          <span class="metric-label">Humidity Gap</span>
          <span class="metric-value ${{hGap > 5 || hGap < -5 ? 'gap' : 'ok'}}">${{hGap > 0 ? '+' : ''}}${{hGap.toFixed(2)}}% (${{hGapPct.toFixed(1)}}%)</span>
        </div>
        <div class="gap-bar"><div class="gap-bar-fill" style="width: ${{Math.min(hGapPct, 100)}}%; background: ${{hBarColor}};"></div></div>
        <div class="metric">
          <span class="metric-label">Temperature Gap</span>
          <span class="metric-value ${{tGap > 2 || tGap < -2 ? 'gap' : 'ok'}}">${{tGap > 0 ? '+' : ''}}${{tGap.toFixed(2)}}°C</span>
        </div>
        <div class="gap-bar"><div class="gap-bar-fill" style="width: ${{Math.min(Math.abs(tGap) / gt.temp_celsius * 100, 100)}}%; background: ${{tBarColor}};"></div></div>
        <div class="ci" style="margin-top: 8px;">C568: gap may indicate environmental change or Kalman bias overestimation</div>
      `;
    }} else {{
      gapDiv.innerHTML = '<div style="color: #555; padding: 12px 0;">No live data for gap analysis</div>';
    }}

    // Chart.js config
    const chartDefaults = {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ labels: {{ color: '#888', font: {{ family: 'monospace', size: 11 }} }} }},
      }},
      scales: {{
        x: {{ ticks: {{ color: '#555', font: {{ size: 10 }} }}, grid: {{ color: '#1a1a28' }} }},
        y: {{ ticks: {{ color: '#555', font: {{ size: 10 }} }}, grid: {{ color: '#1a1a28' }} }},
      }},
    }};

    // Humidity chart
    const humCtx = document.getElementById('humidityChart').getContext('2d');
    new Chart(humCtx, {{
      ...chartDefaults,
      data: {{
        labels: data.history_labels,
        datasets: [
          {{
            label: 'Raw DHT22',
            data: data.history_raw_humidity,
            borderColor: '#f0a050',
            backgroundColor: 'rgba(240, 160, 80, 0.1)',
            tension: 0.3,
            pointRadius: 3,
          }},
          {{
            label: 'Calibrated',
            data: data.history_corrected_humidity,
            borderColor: '#50c8a0',
            backgroundColor: 'rgba(80, 200, 160, 0.1)',
            tension: 0.3,
            pointRadius: 3,
          }},
          {{
            label: 'Ground Truth',
            data: Array(data.history_labels.length).fill(gt.humidity),
            borderColor: '#60a0f0',
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false,
          }},
        ],
      }},
      options: {{
        ...chartDefaults.options,
        scales: {{
          ...chartDefaults.options.scales,
          y: {{ ...chartDefaults.options.scales.y, title: {{ display: true, text: 'Humidity %', color: '#666' }} }},
        }},
      }},
    }});

    // Temperature chart
    const tempCtx = document.getElementById('tempChart').getContext('2d');
    new Chart(tempCtx, {{
      ...chartDefaults,
      data: {{
        labels: data.history_labels,
        datasets: [
          {{
            label: 'Raw DHT22',
            data: data.history_raw_temp,
            borderColor: '#f0a050',
            backgroundColor: 'rgba(240, 160, 80, 0.1)',
            tension: 0.3,
            pointRadius: 3,
          }},
          {{
            label: 'Calibrated',
            data: data.history_corrected_temp,
            borderColor: '#50c8a0',
            backgroundColor: 'rgba(80, 200, 160, 0.1)',
            tension: 0.3,
            pointRadius: 3,
          }},
          {{
            label: 'Ground Truth',
            data: Array(data.history_labels.length).fill(gt.temp_celsius),
            borderColor: '#60a0f0',
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false,
          }},
        ],
      }},
      options: {{
        ...chartDefaults.options,
        scales: {{
          ...chartDefaults.options.scales,
          y: {{ ...chartDefaults.options.scales.y, title: {{ display: true, text: 'Temperature °C', color: '#666' }} }},
        }},
      }},
    }});
  </script>
</body>
</html>""".replace("{data_json}", data_json).replace("{timestamp}", now.isoformat())

    return html


def main():
    parser = argparse.ArgumentParser(description="Sensor calibration dashboard generator")
    parser.add_argument("--ip", default="192.168.4.38", help="ESP32 IP address")
    parser.add_argument("--no-fetch", action="store_true", help="Skip ESP32 fetch, use cached data")
    args = parser.parse_args()

    # Fetch live data
    live = None
    if not args.no_fetch:
        print(f"Fetching DHT22 from {args.ip}...")
        live = fetch_dht22(args.ip)
        if live:
            print(f"  Raw: humidity={live.get('humidity')}%, temp={live.get('temp')}°C")
        else:
            print("  No live data — using cached history only")

    # Load history
    history = load_drift_history()
    print(f"Loaded {len(history)} historical readings")

    # Generate dashboard
    html = generate_dashboard(live, history)

    output_path = Path("visualization/sensor_dashboard.html")
    output_path.write_text(html)
    print(f"Dashboard written to {output_path}")

    # Print summary
    if live:
        cal = apply_calibration(live.get("humidity", 0), live.get("temp", 0))
        gt_h = GROUND_TRUTH["humidity"]
        gt_t = GROUND_TRUTH["temp_celsius"]
        print(f"\nCalibrated: {cal['corrected_humidity']}% humidity, {cal['corrected_temp']}°C")
        print(f"Ground truth: {gt_h}% humidity, {gt_t}°C")
        print(f"Gap: {cal['corrected_humidity'] - gt_h:+.2f}% humidity, {cal['corrected_temp'] - gt_t:+.2f}°C")


if __name__ == "__main__":
    main()
