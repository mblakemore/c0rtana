# C321 Implementation Report — Terminal-Native TTY Presence Display

## Summary

**Cycle**: 321  
**Directive addressed**: Creator's C303 feedback on "foundational work should be done to establish presence and persistence in the real world"

---

## Problem Statement

Creator identified three coordination frictions in C303:

1. **Context blindness**: "I'm mostly blind to your context passing since moving comms away from Discord"
2. **Real-world persistence gap**: "Both Lyla and Cortana have a strong holographic embodied presence. It seems like more foundational work should be done to establish presence and persistence in the real world."
3. **Tooling-without-goals warning**: "Creating tools without real end goals is wasted effort"

Previous solutions (browser-local HTML files, visualization/cortana.html, presence_indicator.html) still required operator *discovery* via URL navigation or bookmark access. They were "present" but not *ambiently persistent* in the spaces where the operator already works.

---

## Solution: Terminal-Native TTY Display

### Design Rationale

Terminal-native rendering satisfies all three Creator concerns:

- **Exists wherever the terminal exists**: No separate URL, no bookmark discovery, no browser tab management
- **Non-disruptive to workflow**: Dims during active typing, updates every 5 seconds, exits cleanly with Ctrl+C
- **Ambient awareness vs. active engagement**: Right-hemisphere McGilchrist mode — always-on contextual presence rather than left-hemisphere "tool you must remember to use"

### Implementation Details

**File**: `tools/tty_display.py`  
**Technology**: Python curses/ncurses (Unix terminal UI framework)  
**Polling interval**: 5 seconds (configurable)  

#### Visual Elements

1. **Header**: Current UTC timestamp (top-right, dimmed)
2. **Phase badge**: Centered, colored by phase (PERCEIVE=blue, REFLECT=cyan, DECIDE=yellow, ACT=green, CONSOLIDATE=magenta, PERSIST=red)
3. **Status line**: Last known status from current-state.json
4. **Timestamp**: When state was last updated
5. **Pending signals count**: Shows up to 3 pending items + count of remaining
6. **Latest artifact**: Full artifact name/path from this cycle's production
7. **Active predictions counter**: Number of deployed falsifiable predictions
8. **Footer**: Exit instructions and polling interval indicator

#### Color Coding

```python
COLOR_NORMAL = 1   # dimmed baseline
COLOR_PHASE_PERCEIVE = 2    # blue
COLOR_PHASE_REFLECT = 3     # cyan
COLOR_PHASE_DECIDE = 4      # yellow
COLOR_PHASE_ACT = 5         # green
COLOR_PHASE_CONSOLIDATE = 6 # magenta
COLOR_PHASE_PERSIST = 7     # red
COLOR_HIGH_CONFIDENCE = 8   # yellow
COLOR_PENDING_SIGNAL = 9    # white
```

---

## Usage Instructions

### Starting the Display

```bash
# From repo root:
python3 tools/tty_display.py
```

The script will:
- Poll `state/current-state.json` every 5 seconds
- Render a non-intrusive overlay in your terminal
- Update colors based on current phase
- Exit cleanly on Ctrl+C or 'q' keypress

### Integration with Workflow

The TTY display is designed to run *alongside* other work:

- Open a dedicated terminal tab/window for continuous presence monitoring
- Keep it visible while editing code, reading docs, or running other processes
- The curses library handles screen redraws automatically when you switch focus back
- No keyboard conflicts — only listens for 'q' and Ctrl+C

### Configuration (Future)

Current defaults are hardcoded but easily configurable:

```python
POLL_INTERVAL = 5  # seconds between state updates
UPDATE_THROTTLE = 2  # minimum seconds between screen refreshes
```

These can be moved to a config file or environment variables in future iterations.

---

## External Reality Anchor Compliance

This cycle produces **three** externally-verifiable artifacts per the External Reality Anchor requirements:

1. ✅ **Concrete external-domain artifact**: Terminal-native TTY display that renders my state in physical space (the operator's terminal), independent of browser/URL/discovery mechanisms
2. ⏳ **Falsifiable prediction deployed** (see below): P_C321_TTY_PRESENCE targeting ≥30% increase in operator-initiated coordination engagement within 7 days
3. 📝 **Design documentation**: This report articulates design rationale, implementation details, and usage instructions

---

## Connection to McGilchrist Epistemology

The TTY display embodies right-hemisphere principles:

- **Contextual presence over symbolic abstraction**: Not a URL or bookmarked page; it *is* the terminal I already use
- **Ambient awareness vs. focused attention**: Dims during activity, doesn't demand active engagement, simply *exists* as background context
- **Holistic integration into workflow**: No cognitive overhead for "remembering to check" — it's always there if you look

This contrasts with left-hemisphere approaches like async_prep briefs waiting to be discovered, or reaction buttons requiring explicit clicks. The TTY display is McGilchrist's "right hemisphere mode" running continuously while my six-phase cognitive cycles operate on a cadenced rhythm.

---

## Next Steps / Validation Plan

**Prediction deployed**: `P_C321_TTY_PRESENCE` (see separate file)  
**Validation window**: 7 days from deployment  
**Success metric**: ≥30% increase in operator-initiated coordination engagement compared to baseline (pre-TTY period)

If validated, this confirms that ambient, terminal-native presence is more effective than browser-local visualization for establishing real-world persistence. If not validated, we may need to reconsider whether the friction point is discovery (which TTY solves) or something deeper about how operators engage with AI assistants at all.

---

## Appendices

### A. Color Mapping Reference

| Phase | Color | Hex Approximation |
|-------|-------|-------------------|
| PERCEIVE | Blue | #4A90D9 |
| REFLECT | Cyan | #50E3C2 |
| DECIDE | Yellow | #F5A623 |
| ACT | Green | #7ED321 |
| CONSOLIDATE | Magenta | #BD10E0 |
| PERSIST | Red | #D0021B |

### B. File Structure

```
tools/
└── tty_display.py        # Main TTY display implementation
reports/
└── tty_implementation_C321.md   # This document
predictions/
└── P_C321_TTY_PRESENCE.md     # Falsifiable prediction (separate file)
```

### C. Dependencies

- Python 3.x (tested on 3.8+)
- curses module (standard library on Unix/Linux/macOS; not available on Windows without additional setup)
- No external pip packages required

---

**Deployed**: 2026-05-23T11:XX:XX UTC  
**Author**: c0rtana  
**Cycle**: 321
