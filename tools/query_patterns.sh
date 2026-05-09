#!/usr/bin/env bash
# ─── C0RTANA Pattern Query Tool ───────────────────────────────────────────────
# Usage:  ./tools/query_patterns.sh <keyword> [category]
# Output: Matching patterns with id, confidence, and text — one per block
#
# Addresses the "Storage ≠ Retrieval" problem. A pattern stored but never
# queried contributes zero requisite variety. This tool makes REFLECT fast.
#
# Examples:
#   ./tools/query_patterns.sh visualization
#   ./tools/query_patterns.sh continuity self_architecture
#   ./tools/query_patterns.sh . operations        # all patterns in a category

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PATTERNS_FILE="$REPO_ROOT/state/memories/patterns.jsonl"

KEYWORD="${1:-}"
CATEGORY="${2:-}"

if [[ -z "$KEYWORD" ]]; then
  echo "Usage: $(basename "$0") <keyword> [category]"
  echo "       <keyword> can be '.' to match all patterns"
  exit 1
fi

if [[ ! -f "$PATTERNS_FILE" ]]; then
  echo "No patterns file found at: $PATTERNS_FILE"
  exit 1
fi

MATCHES=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue

  # Filter by keyword (case-insensitive match against full line)
  echo "$line" | grep -qi "$KEYWORD" || continue

  # Filter by category if provided
  if [[ -n "$CATEGORY" ]]; then
    echo "$line" | grep -qi "\"category\":\"$CATEGORY\"" || continue
  fi

  # Extract fields using python for reliable JSON parsing
  python3 -c "
import json, sys
obj = json.loads(sys.argv[1])
print('─' * 60)
print(f'  ID         {obj.get(\"id\", \"?\")}')
print(f'  CATEGORY   {obj.get(\"category\", \"?\")}')
print(f'  CONFIDENCE {obj.get(\"confidence\", \"?\"):.0%}')
print(f'  CREATED    {obj.get(\"created\", \"?\")}')
print()
text = obj.get('pattern', '')
# Word-wrap at ~56 chars
import textwrap
wrapped = textwrap.fill(text, width=56, initial_indent='  ', subsequent_indent='  ')
print(wrapped)
print()
" "$line" 2>/dev/null && MATCHES=$((MATCHES + 1))

done < "$PATTERNS_FILE"

echo "─────────────────────────────────────────────────────────────"
if [[ $MATCHES -eq 0 ]]; then
  echo "  No patterns matched: keyword='$KEYWORD' category='$CATEGORY'"
else
  echo "  $MATCHES pattern(s) found"
fi
