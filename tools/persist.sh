#!/bin/bash

# PERSIST.SH - Atomic Persistence for Cortana
# Usage: ./tools/persist.sh <cycle_number> "<commit_message>"

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <cycle_number> <commit_message>"
    exit 1
fi

CYCLE=$1
MESSAGE=$2

echo "C${CYCLE}: Initiating Persistence Sequence..."

# 1. Verify state files exist
if [ ! -f state/current-state.json ] || [ ! -f state/focus.json ]; then
    echo "ERROR: Critical state files missing. Persistence aborted."
    exit 1
fi

# 2. Stage critical directories
echo "Staging state, logs, messages, and visualization..."
git add state/ logs/ messages/ visualization/

# 3. Commit with standardized format
COMMIT_MSG="C${CYCLE}: ${MESSAGE}"
echo "Committing: ${COMMIT_MSG}"
git commit -m "${COMMIT_MSG}"

# 4. Push to remote
echo "Pushing to remote..."
if git push; then
    echo "C${CYCLE}: Persistence successful."
    exit 0
else
    echo "ERROR: Push failed. Persistence incomplete."
    exit 1
fi
