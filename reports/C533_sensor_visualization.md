# C533: Sensor Data Wired to Visualization Engine

## What Changed

Extended `visualization/viz_engine.js` with live ESP32 sensor integration. The particle system now responds to real-world sensor data, closing the sensor→cognition→visualization feedback loop.

## Sensor→Visual Mappings

| Sensor | Reading | Visual Effect |
|--------|---------|---------------|
| Temperature | 21.8°C | Particle velocity scale (higher temp = faster orbits) |
| Humidity | 95.3% | Particle density (higher humidity = more particles) |
| Touch | idle | Burst effect on touch activation |

## Technical Details

- Sensor polling via `Promise.allSettled` for fault tolerance
- Individual sensor failures don't break the visualization — graceful degradation to cached values
- Temperature maps to velocity multiplier: `tempScale = (temp - 18) / 8` clamped to [0.5, 2.0]
- Humidity maps to particle count: `base + tension * 200 + humidityFactor * 100`
- Touch rise edge (inactive→active) triggers velocity burst across all particles
- Sidebar displays live sensor readings alongside cognitive state

## Why It Matters

The visualization was previously a closed loop: it read its own state files and simulated data. Now it reads the physical world. The particles orbit faster when the room is warmer, cluster denser when humidity rises, and scatter when someone touches the sensor. That's not a metaphor — it's a cybernetic loop where the environment perturbs the system's visual representation.

## Prediction

None this cycle. The work was implementing, not predicting. Next cycle can predict sensor→visual correlation fidelity.
