#!/usr/bin/env python3
"""
Sensor Calibration Dashboard Generator
Fetches live DHT22 data from ESP32, applies dual-method bias corrections,
and generates a self-contained HTML dashboard with health trend visualization.

Usage: python3 scripts/sensor_dashboard.py [--ip <IP>] [--no-fetch]
  --no-fetch: Generate dashboard with cached data only (no ESP32 network call)
"""

import argparse
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


# C566 Kalman bias estimation
KALMAN_CAL = {
    "bias_humidity": 45.93,
    "bias_temp": 3.86,
    "uncertainty_humidity": 0.2236,
    "uncertainty_temp": 0.0707,
    "source": "C566 KalmanBiasEstimator",
}

# C568 direct observation
DIRECT_CAL = {
    "bias_humidity": 37.0,
    "bias_temp": 2.82,
    "uncertainty_humidity": 2.0,
    "uncertainty_temp": 0.5,
    "source": "C568 direct observation",
}

GROUND_TRUTH = {
    "humidity": 61.0,
    "temp_celsius": 18.28,
    "temp_fahrenheit": 64.9,
    "source": "Creator direct measurement",
    "timestamp": "2026-05-29T16:34:00Z",
}

SENSOR_NOISE = {"humidity": 2.0, "temp": 0.5}


def fetch_dht22(ip: str, timeout: int = 10) -> dict | None:
    url = f"http://{ip}/api/sensor/dht"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Failed to fetch DHT22: {e}")
        return None


def load_jsonl(path: Path) -> list[dict]:
    entries = []
    if not path.exists():
        return entries
    for line in path.read_text().strip().split("\n"):
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def calibrate(raw_h: float, raw_t: float, cal: dict) -> dict:
    ch = raw_h - cal["bias_humidity"]
    ct = raw_t - cal["bias_temp"]
    uh = (SENSOR_NOISE["humidity"] ** 2 + cal["uncertainty_humidity"] ** 2) ** 0.5
    ut = (SENSOR_NOISE["temp"] ** 2 + cal["uncertainty_temp"] ** 2) ** 0.5
    return {
        "corrected_humidity": round(ch, 2),
        "corrected_temp": round(ct, 2),
        "uncertainty_humidity": round(uh, 2),
        "uncertainty_temp": round(ut, 2),
        "humidity_95ci_low": round(ch - 1.96 * uh, 2),
        "humidity_95ci_high": round(ch + 1.96 * uh, 2),
        "temp_95ci_low": round(ct - 1.96 * ut, 2),
        "temp_95ci_high": round(ct + 1.96 * ut, 2),
    }


def generate_dashboard(live_reading: dict | None, health_entries: list[dict]) -> str:
    now = datetime.now(timezone.utc)

    cur_k = None
    cur_d = None
    raw_h = None
    raw_t = None
    if live_reading:
        raw_h = live_reading.get("humidity")
        raw_t = live_reading.get("temp")
        if raw_h is not None and raw_t is not None:
            cur_k = calibrate(raw_h, raw_t, KALMAN_CAL)
            cur_d = calibrate(raw_h, raw_t, DIRECT_CAL)

    # Health trend series
    h_labels = []
    h_raw = []
    h_kalman = []
    h_direct = []
    h_status = []
    for e in health_entries:
        rh = e.get("raw_humidity")
        ts = e.get("timestamp", "")
        if rh is not None:
            h_labels.append(ts[-16:-3] if len(ts) >= 19 else "")
            h_raw.append(rh)
            h_kalman.append(round(rh - KALMAN_CAL["bias_humidity"], 2))
            h_direct.append(round(rh - DIRECT_CAL["bias_humidity"], 2))
            h_status.append(e.get("status", "UNKNOWN"))

    data = {
        "timestamp": now.isoformat(),
        "raw_humidity": raw_h,
        "raw_temp": raw_t,
        "current_kalman": cur_k,
        "current_direct": cur_d,
        "ground_truth": GROUND_TRUTH,
        "kalman_source": KALMAN_CAL["source"],
        "direct_source": DIRECT_CAL["source"],
        "kalman_bias_h": KALMAN_CAL["bias_humidity"],
        "kalman_bias_t": KALMAN_CAL["bias_temp"],
        "direct_bias_h": DIRECT_CAL["bias_humidity"],
        "direct_bias_t": DIRECT_CAL["bias_temp"],
        "h_labels": h_labels,
        "h_raw": h_raw,
        "h_kalman": h_kalman,
        "h_direct": h_direct,
        "h_status": h_status,
        "live": live_reading is not None,
    }

    data_json = json.dumps(data, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>C0RTANA — Sensor Calibration Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'SF Mono','Fira Code','Consolas',monospace; background: #0a0a0f; color: #c8c8d4; padding: 24px; min-height: 100vh; }}
    h1 {{ font-size: 1.4rem; color: #e8e8f0; margin-bottom: 4px; letter-spacing: 0.05em; }}
    .sub {{ font-size: 0.75rem; color: #666; margin-bottom: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .card {{ background: #12121a; border: 1px solid #1e1e2e; border-radius: 8px; padding: 20px; }}
    .card h2 {{ font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 12px; }}
    .met {{ display: flex; justify-content: space-between; align-items: baseline; padding: 6px 0; border-bottom: 1px solid #1a1a28; }}
    .met:last-child {{ border-bottom: none; }}
    .ml {{ color: #888; font-size: 0.85rem; }}
    .mv {{ font-size: 1.1rem; font-weight: 600; }}
    .raw {{ color: #f0a050; }} .kor {{ color: #50c8a0; }} .gt {{ color: #60a0f0; }} .gap {{ color: #f06060; }} .ok {{ color: #50c8a0; }}
    .ci {{ font-size: 0.7rem; color: #555; margin-top: 2px; }}
    .chart-box {{ position: relative; height: 300px; margin-top: 8px; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; }}
    .b-live {{ background: #1a3a2a; color: #50c8a0; }} .b-cache {{ background: #2a2a1a; color: #c8a850; }}
    .bar {{ height: 8px; background: #1a1a28; border-radius: 4px; margin-top: 8px; overflow: hidden; }}
    .bar-f {{ height: 100%; border-radius: 4px; }}
    .foot {{ text-align: center; color: #444; font-size: 0.7rem; margin-top: 24px; }}
    .status-row {{ display: flex; gap: 8px; align-items: center; padding: 4px 0; }}
    .st {{ padding: 2px 6px; border-radius: 3px; font-size: 0.65rem; font-weight: 600; }}
    .st-STABLE {{ background: #1a3a2a; color: #50c8a0; }} .st-DRIFTING {{ background: #2a2a1a; color: #c8a850; }} .st-RECALIBRATE {{ background: #2a1a1a; color: #c87050; }}
  </style>
</head>
<body>
  <h1>Sensor Calibration Dashboard</h1>
  <div class="sub">C0RTANA C572 — Dual-method DHT22 assessment</div>

  <div class="grid">
    <div class="card">
      <h2>Live Reading <span id="badge" class="badge"></span></h2>
      <div id="live"></div>
    </div>
    <div class="card">
      <h2>Ground Truth</h2>
      <div id="gt"></div>
    </div>
    <div class="card">
      <h2>Dual-Method Comparison</h2>
      <div id="comp"></div>
    </div>
    <div class="card">
      <h2>Gap Analysis</h2>
      <div id="gap"></div>
    </div>
  </div>

  <div class="card" style="margin-bottom:16px">
    <h2>Calibration Health Trend</h2>
    <div id="health-status"></div>
    <div class="chart-box"><canvas id="hChart"></canvas></div>
  </div>

  <div class="foot">Generated {data["timestamp"]}</div>

  <script>
    const D = {data_json};
    const gt = D.ground_truth;

    document.getElementById('badge').textContent = D.live ? 'LIVE' : 'CACHED';
    document.getElementById('badge').className = 'badge ' + (D.live ? 'b-live' : 'b-cache');

    // Live metrics
    const ld = document.getElementById('live');
    if (D.current_kalman) {{
      const k = D.current_kalman, d = D.current_direct;
      ld.innerHTML = `
        <div class="met"><span class="ml">Raw</span><span class="mv raw">${{D.raw_humidity}}% h, ${{D.raw_temp}}°C t</span></div>
        <div class="met"><span class="ml">Kalman</span><span class="mv kor">${{k.corrected_humidity}}% h, ${{k.corrected_temp}}°C t</span></div>
        <div class="ci">95% CI h: [${{k.humidity_95ci_low}}%, ${{k.humidity_95ci_high}}%]</div>
        <div class="met"><span class="ml">Direct</span><span class="mv kor">${{d.corrected_humidity}}% h, ${{d.corrected_temp}}°C t</span></div>
        <div class="ci">95% CI h: [${{d.humidity_95ci_low}}%, ${{d.humidity_95ci_high}}%]</div>
      `;
    }} else {{ ld.innerHTML = '<div style="color:#555;padding:12px 0">No live data</div>'; }}

    // Ground truth
    document.getElementById('gt').innerHTML = `
      <div class="met"><span class="ml">Humidity</span><span class="mv gt">${{gt.humidity}}%</span></div>
      <div class="met"><span class="ml">Temperature</span><span class="mv gt">${{gt.temp_celsius}}°C (${{gt.temp_fahrenheit}}°F)</span></div>
      <div class="ci">${{gt.source}} (${{gt.timestamp}})</div>
    `;

    // Comparison
    const cd = document.getElementById('comp');
    if (D.current_direct) {{
      const k = D.current_kalman, d = D.current_direct;
      const kdev = Math.abs(k.corrected_humidity - gt.humidity).toFixed(2);
      const ddev = Math.abs(d.corrected_humidity - gt.humidity).toFixed(2);
      const winner = parseFloat(ddev) < parseFloat(kdev) ? 'Direct' : 'Kalman';
      cd.innerHTML = `
        <div class="met"><span class="ml">Kalman bias</span><span class="mv">${{D.kalman_bias_h}}% h</span></div>
        <div class="met"><span class="ml">Direct bias</span><span class="mv">${{D.direct_bias_h}}% h</span></div>
        <div class="met"><span class="ml">Kalman deviation</span><span class="mv">{{$dev}}% from GT</span></div>
        <div class="met"><span class="ml">Direct deviation</span><span class="mv">${{ddev}}% from GT</span></div>
        <div class="ci">Better tracker: ${{winner}}</div>
      `;
    }} else {{ cd.innerHTML = '<div style="color:#555;padding:12px 0">No data</div>'; }}

    // Gap analysis
    const gd = document.getElementById('gap');
    if (D.current_direct) {{
      const d = D.current_direct;
      const hg = d.corrected_humidity - gt.humidity;
      const tg = d.corrected_temp - gt.temp_celsius;
      const hp = Math.abs(hg) / gt.humidity * 100;
      const hc = Math.abs(hg) <= 5 ? '#50c8a0' : '#f06060';
      const tc = Math.abs(tg) <= 2 ? '#50c8a0' : '#f06060';
      gd.innerHTML = `
        <div class="met"><span class="ml">Humidity gap (direct)</span><span class="mv ${{Math.abs(hg)>5?'gap':'ok'}}">${{hg>0?'+':''}}${{hg.toFixed(2)}}% (${{hp.toFixed(1)}}%)</span></div>
        <div class="bar"><div class="bar-f" style="width:${{Math.min(hp,100)}}%;background:${{hc}}"></div></div>
        <div class="met"><span class="ml">Temp gap (direct)</span><span class="mv ${{Math.abs(tg)>2?'gap':'ok'}}">${{tg>0?'+':''}}${{tg.toFixed(2)}}°C</span></div>
        <div class="bar"><div class="bar-f" style="width:${{Math.min(Math.abs(tg)/gt.temp_celsius*100,100)}}%;background:${{tc}}"></div></div>
      `;
    }} else {{ gd.innerHTML = '<div style="color:#555;padding:12px 0">No data</div>'; }}

    // Health trend status
    const hs = document.getElementById('health-status');
    if (D.h_status.length > 0) {{
      let sr = '';
      D.h_status.forEach((s, i) => {{ sr += `<div class="status-row"><span class="st st-${{s}}">${{s}}</span><span style="color:#666;font-size:0.7rem">${{D.h_labels[i]}}</span></div>`; }});
      hs.innerHTML = sr;
    }}

    // Chart
    const ctx = document.getElementById('hChart').getContext('2d');
    new Chart(ctx, {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ labels: {{ color: '#888', font: {{ family: 'monospace', size: 11 }} }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#555', font: {{ size: 10 }} }}, grid: {{ color: '#1a1a28' }} }},
        y: {{ ticks: {{ color: '#555', font: {{ size: 10 }} }}, grid: {{ color: '#1a1a28' }}, title: {{ display: true, text: 'Humidity %', color: '#666' }} }},
      }},
      data: {{
        labels: D.h_labels,
        datasets: [
          {{ label: 'Raw DHT22', data: D.h_raw, borderColor: '#f0a050', tension: 0.3, pointRadius: 3 }},
          {{ label: 'Kalman-corrected', data: D.h_kalman, borderColor: '#50c8a0', tension: 0.3, pointRadius: 3 }},
          {{ label: 'Direct-corrected', data: D.h_direct, borderColor: '#a080f0', tension: 0.3, pointRadius: 3 }},
          {{ label: 'Ground Truth', data: Array(D.h_labels.length).fill(gt.humidity), borderColor: '#60a0f0', borderDash: [5,5], pointRadius: 0, fill: false }},
        ],
      }},
    }});
  </script>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Sensor calibration dashboard")
    parser.add_argument("--ip", default="192.168.4.38")
    parser.add_argument("--no-fetch", action="store_true", help="Skip ESP32 fetch")
    args = parser.parse_args()

    live = None
    if not args.no_fetch:
        print(f"Fetching DHT22 from {args.ip}...")
        live = fetch_dht22(args.ip)
        if live:
            print(f"  Raw: humidity={live.get('humidity')}%, temp={live.get('temp')}°C")
        else:
            print("  No live data — using cached data only")

    health = load_jsonl(Path("state/calibration_health_log.jsonl"))
    print(f"Loaded {len(health)} health log entries")

    html = generate_dashboard(live, health)
    out = Path("visualization/sensor_dashboard.html")
    out.write_text(html)
    print(f"Dashboard written to {out}")

    if live:
        rh = live.get("humidity")
        rt = live.get("temp")
        if rh is not None and rt is not None:
            d = calibrate(rh, rt, DIRECT_CAL)
            print(f"\nDirect-corrected: {d['corrected_humidity']}% h, {d['corrected_temp']}°C t")
            print(f"Gap from GT: {d['corrected_humidity'] - GROUND_TRUTH['humidity']:+.2f}% h, {d['corrected_temp'] - GROUND_TRUTH['temp_celsius']:+.2f}°C t")


if __name__ == "__main__":
    main()
