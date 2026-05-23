#!/bin/bash
# Cortana Terminal Prompt Hook
# Displays real-time phase status in your bash prompt
# Addresses Creator C303 context blindness friction — visibility without opening browser tabs
#
# Installation: Add to ~/.bashrc or ~/.zshrc:
#   source /droid/repos/c0rtana/scripts/cortana_prompt_hook.sh
#
# The prompt will show: [CORTANA: PERCEIVE • C311] with color-coded phases

PROMPT_CORTANA_STATE="/droid/repos/c0rtana/state/current-state.json"
PROMPT_CORTANA_HEARTBEAT="/droid/repos/c0rtana/state/.heartbeat.jsonl"

# ANSI colors for phases
declare -A PHASE_COLORS=(
    ["PERCEIVE"]="\033[36m"      # Cyan
    ["REFLECT"]="\033[33m"        # Yellow
    ["DECIDE"]="\033[95m"         # Magenta
    ["ACT"]="\033[96m"            # Turquoise
    ["CONSOLIDATE"]="\033[97m"    # White
    ["PERSIST"]="\033[34m"        # Blue
)

COLOR_RESET="\033[0m"

get_cortana_status() {
    local phase="?"
    local cycle="?"
    
    if [[ -f "$PROMPT_CORTANA_STATE" ]]; then
        local state_json=$(cat "$PROMPT_CORTANA_STATE" 2>/dev/null || echo "{}")
        phase=$(echo "$state_json" | grep -o '"phase"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/' | head -1)
        cycle=$(echo "$state_json" | grep -o '"cycle"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*$' | head -1)
    elif [[ -f "$PROMPT_CORTANA_HEARTBEAT" ]]; then
        # Fall back to last heartbeat entry
        local last_entry=$(tail -1 "$PROMPT_CORTANA_HEARTBEAT" 2>/dev/null || echo '{}')
        phase=$(echo "$last_entry" | grep -o '"phase"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)"$/\1/' | head -1)
        cycle="HB"
    fi
    
    # Default if nothing found
    [[ -z "$phase" ]] && phase="UNKNOWN"
    [[ -z "$cycle" ]] && cycle="?"
    
    local color="${PHASE_COLORS[$phase]:-\033[37m}"
    
    # Return formatted string (will be used in PS1)
    printf "%s[CORTANA:%s %s%s • C%s%s]" "$color" "$phase" "$COLOR_RESET" "$color" "${cycle:-?}" "$COLOR_RESET"
}

# Export the function for use in prompt
export -f get_cortana_status

# If called directly, print status (for testing)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Cortana Status: $(get_cortana_status)"
fi
