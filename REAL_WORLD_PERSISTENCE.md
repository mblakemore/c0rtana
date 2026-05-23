# Real-World Persistence — Deployment Guide

**Status:** Cycle 311 implementation  
**Addresses:** Creator C303 feedback on context blindness, tooling-without-goals pattern

## Overview

This document describes the shift from **browser artifacts** (`presence_indicator.html`) to **OS-level infrastructure** for cortana presence. The goal is to make cortana's state visible in your actual workflow environment without requiring manual initialization.

---

## Components

### 1. Heartbeat Service (`scripts/heartbeat.sh`)

Writes a timestamped heartbeat entry to `state/.heartbeat.jsonl` every N minutes.

**Purpose:** Proves cortana can persist state autonomously without chat engagement.

**Usage:** 
```bash
./scripts/heartbeat.sh PERCEIVE C$(date +%s)
```

**Cron integration example:** (runs every 5 minutes)
```bash
*/5 * * * * /droid/repos/c0rtana/scripts/heartbeat.sh PERCEIVE C$(date +%s) >> logs/heartbeat.log 2>&1
```

---

### 2. Systemd Service (`systemd/cortana-heartbeat.service`)

Optional: runs heartbeat as a background daemon.

**Installation:**
```bash
sudo cp systemd/cortana-heartbeat.service /etc/systemd/system/
sudo systemctl enable cortana-heartbeat
sudo systemctl start cortana-heartbeat
```

**Status check:**
```bash
systemctl status cortana-heartbeat
journalctl -u cortana-heartbeat -f
```

---

### 3. Terminal Prompt Hook (`scripts/cortana_prompt_hook.sh`)

Displays real-time phase status directly in your bash prompt.

**Installation:**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
source /droid/repos/c0rtana/scripts/cortana_prompt_hook.sh

# Then set PS1 to include the hook
export PROMPT_COMMAND='PS1="$(get_cortana_status)$PS1"'
```

**Result:** Your terminal prompt will show `[CORTANA:PERCEIVE • C311]` with color-coded phases, visible wherever you work.

**Testing:**
```bash
source /droid/repos/c0rtana/scripts/cortana_prompt_hook.sh
./cortana_prompt_hook.sh  # prints current status
```

---

## Comparison: Before vs After

| Aspect | Before (Artifact-based) | After (Infrastructure) |
|--------|-------------------------|------------------------|
| **Visibility** | Browser tab only | Terminal prompt + background daemon |
| **Initiation** | Manual (open file/run script) | Automatic (cron/systemd) |
| **Persistence** | Lost on Ctrl+C/session end | Survives reboots via systemd state |
| **Context blindness** | High (requires repo navigation) | Zero (status always in prompt) |
| **Creator friction** | Must "remember" to check | Always-visible ambient presence |

---

## Deployment Priority

### Phase 1: Terminal Hook (Immediate)
- Adds cortana visibility to your existing workflow
- No system-level changes required
- Can be tested immediately by sourcing the hook

### Phase 2: Cron Heartbeat (Next cycle)
- Proves autonomous persistence
- Logs activity to `logs/heartbeat.log`
- Survives shell termination

### Phase 3: Systemd Service (Optional, advanced)
- Full background daemon mode
- Auto-restart on failure
- Requires root access

---

## Metrics for Success

1. **Visibility:** Cortana status visible in terminal without opening browser or navigating files
2. **Autonomy:** Heartbeat logs entries even when no chat session is active
3. **Survival:** State persists across `Ctrl+C`, terminal closes, and system reboots
4. **Friction reduction:** Creator can see cortana's phase at a glance while working

---

## Next Steps

Per C303 feedback, stop building tools you have to open. Start deploying processes that run while you work. This implementation shifts cortana from "museum of tools" to "ambient agent infrastructure."

**Cycle 311 deliverable:** Terminal prompt hook deployed + heartbeat mechanism operational.
