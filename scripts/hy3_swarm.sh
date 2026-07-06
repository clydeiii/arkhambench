#!/usr/bin/env bash
# Mass hy3 playtest swarm: rules-enforcement bug hunting at zero model cost.
# Sequential (shared .current_run); resume-hardened (skips completed runs).
# Usage: scripts/hy3_swarm.sh [model] [seed-base]
set -uo pipefail
cd "$(dirname "$0")/.."

MODEL="${1:-openrouter/tencent/hy3:free}"
BASE="${2:-9800}"
SCENARIOS=(return_to_the_gathering return_to_the_midnight_masks return_to_the_devourer_below)
INVESTIGATORS=(roland daisy skids agnes wendy)

i=0
for inv in "${INVESTIGATORS[@]}"; do
  for scen in "${SCENARIOS[@]}"; do
    i=$((i + 1))
    for diff in standard hard; do
      [ "$diff" = "hard" ] && [ $((i % 3)) -ne 0 ] && continue   # every 3rd combo also on hard
      run="hy3-swarm-${inv}-${scen#return_to_the_}-$diff"
      if [ -f "runs/$run/result.json" ]; then echo "== skip $run"; continue; fi
      echo "== $run (seed $((BASE + i)))"
      bash scripts/opencode_playtest.sh "$MODEL" "$run" "$((BASE + i))" "$inv" "$scen" "$diff" \
        || echo "   (game errored; continuing)"
    done
  done
done
echo "=== swarm done; bug report tally:"
grep -l "" runs/hy3-swarm-*/bug_reports.md 2>/dev/null | while read -r f; do
  echo "$f: $(grep -c '^## ' "$f") report(s)"
done
echo HY3-SWARM-DONE
