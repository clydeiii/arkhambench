#!/usr/bin/env bash
# kimi3-b5: Kimi K3 through the identical b1/b2/b3/b4 gauntlet (seeds 1001-1010,
# R,D,S,A,W x2, confirmations OFF for parity). Launch-day upstream 429s expected:
# retry loop is completion-count based; pair with the stall watchdog.
set -uo pipefail
cd "$(dirname "$0")/.."
GAMES="${1:-10}"
MAX_ATTEMPTS=10

label="kimi3-b5"
agent="openrouter/moonshotai/kimi-k3"
attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  echo "=== $label attempt $attempt"
  python3 scripts/bench.py --agent "$agent" --label "$label" --games "$GAMES" || true
  have=$(ls bench/"$label"/game-*/result.json 2>/dev/null | wc -l | tr -d ' ')
  [ "$have" -ge "$GAMES" ] && break
  sleep 60
  attempt=$((attempt + 1))
done
echo "=== $label: $(ls bench/"$label"/game-*/result.json 2>/dev/null | wc -l | tr -d ' ')/$GAMES complete"
echo KIMI3-B5-DONE
