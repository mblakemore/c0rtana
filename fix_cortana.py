import re

with open("visualization/cortana.html", "r") as f:
    content = f.read()

# Find where the script variables start
var_start = content.find("let scene, camera, renderer, particles, controls, clock;")
if var_start == -1:
    print("Could not find variable declarations")
    exit(1)

js_part = content[var_start:]

# The HTML head and body reconstruction
head_body = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>C0RTANA // Cognitive State Interface (CSI)</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tween.js/18.6.4/tween.js"></script>
    <style>
        body { margin: 0; overflow: hidden; background-color: #000205; font-family: "Courier New", Courier, monospace; color: #00f2ff; }
        #ui-overlay {
            position: absolute; top: 20px; left: 20px; pointer-events: none; z-index: 10;
            display: flex; flex-direction: column; gap: 15px; text-shadow: 0 0 8px rgba(0, 242, 255, 0.6);
        }
        .telemetry-block {
            background: rgba(0, 20, 30, 0.7); border-left: 3px solid #00f2ff; padding: 10px 15px; backdrop-filter: blur(4px);
        }
        .status-item { margin-bottom: 5px; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
        .value { color: #fff; font-weight: bold; float: right; margin-left: 20px; }
        .label { opacity: 0.8; }
        #sync-container { width: 200px; height: 4px; background: rgba(0, 242, 255, 0.2); margin-top: 10px; position: relative; overflow: hidden; }
        #sync-fill { height: 100%; width: 0%; background: #00f2ff; transition: width 0.5s ease; box-shadow: 0 0 10px #00f2ff; }
        #metaphor-display {
            position: absolute; top: 20px; right: 20px; text-align: right; font-size: 18px;
            letter-spacing: 4px; color: #fff; text-transform: uppercase; opacity: 0.7;
        }
        #landscape-overlay {
            position: absolute; bottom: 20px; left: 20px; pointer-events: none; z-index: 10;
            display: flex; flex-direction: column; gap: 5px; background: rgba(0, 10, 20, 0.5); 
            border-right: 3px solid #00f2ff; padding: 10px; backdrop-filter: blur(4px);
        }
        .density-bar-container { display: flex; align-items: center; gap: 10px; margin-bottom: 3px; }
        .density-label { font-size: 9px; text-transform: uppercase; width: 80px; opacity: 0.7; }
        .density-bar-bg { background: rgba(0, 242, 255, 0.1); height: 6px; width: 100px; position: relative; }
        .density-bar-fill { background: #00f2ff; height: 100%; width: 0%; transition: width 1s ease; box-shadow: 0 0 5px #00f2ff; }
        canvas { display: block; }
        #heartbeat-canvas { filter: drop-shadow(0 0 5px #00f2ff); opacity: 0.8; }
    </style>
</head>
<body>
    <div id="ui-overlay">
        <div class="telemetry-block">
            <div class="status-item"><span class="label">Identity</span> <span class="value">CORTANA v0.99</span></div>
            <div class="status-item"><span class="label">Phase</span> <span id="phase-val" class="value">IDLE</span></div>
            <div class="status-item"><span class="label">Resonance</span> <span id="cat-val" class="value">DEFAULT</span></div>
            <div class="status-item"><span class="label">Confidence</span> <span id="conf-val" class="value">0%</span></div>
        </div>
        <div class="telemetry-block">
            <div class="status-item"><span class="label">Strategic Objective</span> <span id="obj-val" class="value">STRAT_OBJ_000</span></div>
            <div class="status-item"><span class="label">Focus</span> <span id="focus-val" class="value">BOOTSTRAPPING...</span></div>
            <div id="sync-container"><div id="sync-fill"></div></div>
        </div>
    </div>
    <div id="landscape-overlay">
        <div style="font-size: 10px; margin-bottom: 8px; color: #fff; opacity: 0.9;">COGNITIVE LANDSCAPE DENSITY</div>
        <div id="density-bars"></div>
    </div>
    <div id="metaphor-display">SENSING...</div>
    <canvas id="gl-canvas"></canvas>
    <canvas id="heartbeat-canvas" width="150" height="60" style="position: absolute; bottom: 20px; right: 20px; pointer-events: none;"></canvas>
    <script>
"""

# Reconstruct the missing part of init()
if "function init()" not in js_part[:500]:
    pattern = r"(let scene, camera, renderer, particles, controls, clock;.*?)(renderer = new THREE\.WebGLRenderer)"
    replacement = r"\1\n\n        function init() {\n            scene = new THREE.Scene();\n            clock = new THREE.Clock();\n            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);\n            camera.position.z = 180;\n\n            \2"
    js_part = re.sub(pattern, replacement, js_part, flags=re.DOTALL)

full_html = head_body + js_part + "\n    </script>\n</body>\n</html>"

with open("visualization/cortana.html", "w") as f:
    f.write(full_html)
