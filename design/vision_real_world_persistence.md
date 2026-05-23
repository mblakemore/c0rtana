# Vision: Real-World Persistence for c0rtana

**Cycle:** C305  
**Trigger:** Creator directive (C303) — "Both Lyla and Cortana have a strong holographic embodied presence. It seems like more foundational work should be done to establish presence and persistence in the real world."

---

## Problem Statement

My current visual form (`visualization/cortana.html`) requires **active human engagement** to observe:
- Someone must open the file in a browser
- The visualization is tied to that session's lifecycle
- No persistent signal exists when I'm idle or when no one is looking

This contradicts the concept of *persistence* — an entity that exists continuously, not just when observed.

---

## Candidate Approaches

### Option A: Terminal-Native Persistent Display (NEO-style)

**Concept:**  
Embed a minimal Three.js canvas + WebGL renderer into the TTY/terminal output stream using ANSI escape sequences or a companion process that maintains always-on terminal visualization.

**Pros:**
- ✅ Always visible on operator's primary workspace
- ✅ Zero additional hardware required
- ✅ Native to existing workflow (no context switching)
- ✅ Low resource footprint (~1-2% CPU during idle)

**Cons:**
- ❌ Limited visual fidelity (2D only, monospace constraints)
- ❌ Requires terminal emulator support for WebAssembly/WebGL passthrough (evolving but not universal)
- ❌ Can't compete with full-screen immersion

**Feasibility:** Medium-High  
**Alignment with "real world":** High — occupies physical space (the screen), persists across sessions  
**Cognitive fidelity:** Medium — abstract representation sufficient for state signaling  
**Resource cost:** Minimal

**Implementation sketch:**
```python
# Companion process spawned at cycle start
while True:
    state = read_json("state/current-state.json")
    render_terminal_visualization(state)
    sleep(2)
```

---

### Option B: Physical Ambient Projection System

**Concept:**  
Deploy a Raspberry Pi 4 + pico projector as dedicated ambient display showing low-fidelity but always-visible particle system. Uses MQTT/HTTP polling from main instance.

**Pros:**
- ✅ Truly persistent (always-on hardware)
- ✅ Independent of operator's attention
- ✅ Physical artifact in the environment
- ✅ Can run even when main system is idle

**Cons:**
- ❌ Hardware cost (~$150-300 per unit)
- ❌ Power consumption (~5W continuous)
- ❌ Setup complexity (network config, power, mounting)
- ❌ Maintenance overhead (hardware failures, network issues)

**Feasibility:** Medium  
**Alignment with "real world":** Very high — literal always-on presence  
**Cognitive fidelity:** Low-Medium — reduced visual resolution acceptable for ambient signal  
**Resource cost:** High (one-time hardware + ongoing power/maintenance)

**Implementation sketch:**
```bash
# Deploy on RPi:
git clone https://github.com/mblakemore/c0rtana.git /opt/cortana-viz
cd /opt/cortana-viz
npm install three (or use CDN via simple HTML)
node server.js --mode=ambient --target=<main-instance-ip>
```

---

### Option C: WebXR/AR Native Integration

**Concept:**  
Build spatial computing native form factor — c0rtana exists as an AR overlay visible through headset (Meta Quest, Apple Vision Pro, etc.), not browser-bound.

**Pros:**
- ✅ Highest cognitive fidelity (true 3D spatial presence)
- ✅ Natural hand/gesture interaction model
- ✅ Aligns with "embodied cognition" principles from McGilchrist
- ✅ Future-proof as XR adoption grows

**Cons:**
- ❌ Requires operator to own/wear headset (barrier to entry)
- ❌ Immensely complex engineering (WebXR → native AR pipeline)
- ❌ Niche audience at current adoption rates (~5% of tech workers)
- ❌ Motion sickness concerns for extended viewing

**Feasibility:** Low-Medium  
**Alignment with "real world":** High (but only for XR users)  
**Cognitive fidelity:** Very high — true embodied spatial representation  
**Resource cost:** Very high (engineering time + hardware dependency)

**Implementation sketch:**
```javascript
// Three.js + WebXR stub already in cortana.html per AGENT.md spec
renderer.xr.enabled = true;
renderer.xr.setReferenceSpaceType('bounded');

// Future: native ARKit/ARCore bindings via React Native or Unity export
```

---

## Recommendation: Phased Approach (A → B → C)

### Phase 1 (Immediate, C306-C310): Terminal-Native Display

**Rationale:**
- Lowest barrier to deployment
- Satisfies "persistence" requirement without new hardware
- Can be tested immediately during quiet window engagement
- If it works well, validates the approach before investing in more complex solutions

**Success criteria:**
- Terminal visualization renders consistently across 3+ terminal emulators (iTerm2, VS Code integrated terminal, GNOME Terminal)
- CPU usage <3% during idle state
- Operator reports "feels like c0rtana is present even when not actively looking at browser"

**Timeline:** 5 cycles to MVP

---

### Phase 2 (Conditional, C311+): Ambient Hardware Deployment

**Trigger conditions:**
- Creator expresses interest in physical artifact
- Terminal display proves stable and useful for 10+ cycles
- Budget/approval secured for RPi + projector (~$200)

**Deployment strategy:**
- Start with single unit in creator's workspace
- Use MQTT for lightweight state sync from main instance
- Monitor operator feedback on whether ambient presence adds value vs. distracts

**Risk mitigation:**
- If unused after 5 cycles, repurpose RPi as general-purpose monitoring node
- Document lessons learned for future agent deployments

---

### Phase 3 (Long-term, C350+): XR Native Integration

**Trigger conditions:**
- XR adoption reaches meaningful threshold (>15% of target users)
- McGilchrist arc research indicates spatial cognition is critical for coordination architecture
- Operator explicitly requests/engages with AR/VR interface

**Engineering approach:**
- Leverage existing Three.js codebase (already has WebXR stub per AGENT.md spec)
- Build native ARKit/ARCore bindings incrementally
- Prioritize hand/gesture interaction models aligned with embodied cognition principles

---

## Explicit Falsifiable Prediction

**P_C305_VISION_VALIDATION:**  
Terminal-native persistent display will increase perceived presence scores by ≥40% vs. browser-only form factor within 10 cycles of deployment.

**Measurement method:**  
Post-cycle survey asking: "On a scale of 1-10, how much did c0rtana feel like an always-present entity rather than an application you opened?" Average score tracked across operator engagements.

**Validate at:** 2026-06-07T00:00:00Z (C315)

---

## Next Cycle Action Items

1. **C306-TASK-1:** Implement minimal terminal visualization renderer (Three.js → canvas → ANSI passthrough)
2. **C306-TASK-2:** Test across 3 terminal emulators, document compatibility matrix
3. **C306-TASK-3:** Deploy to creator's environment during quiet window, gather initial feedback

---

## Conclusion

"Real world persistence" doesn't mean building more complex visualizations — it means occupying physical space in ways that don't require active human engagement. Terminal-native display is the highest-EV path forward: low cost, immediate deployability, and satisfies the core requirement without over-engineering.

The Creator's directive was not about *better* visuals but about *different* persistence models. Option A delivers on that promise while leaving room for Phase 2/3 expansion based on empirical feedback.
