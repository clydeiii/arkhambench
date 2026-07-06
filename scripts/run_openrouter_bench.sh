#!/usr/bin/env bash
# b2 gauntlet: 4 open-weights models through the identical b1 conditions
# (Return to The Gathering, seeds 1001-1010, R,D,S,A,W x2, per-label notebook,
# confirmations OFF for b1 parity). Sequential; resume-hardened by bench.py.
set -uo pipefail
cd "$(dirname "$0")/.."
GAMES="${1:-10}"
MAX_ATTEMPTS=6

run_agent() {
  local agent="$1" label="$2" attempt=1
  while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
    echo "=== $label attempt $attempt"
    python3 scripts/bench.py --agent "$agent" --label "$label" --games "$GAMES" && break
    attempt=$((attempt + 1))
  done
  local done_count
  done_count=$(ls bench/"$label"/game-*/result.json 2>/dev/null | wc -l | tr -d ' ')
  echo "=== $label: $done_count/$GAMES complete"
}

run_agent openrouter/tencent/hy3:free        hy3-b2
run_agent openrouter/z-ai/glm-5.2            glm52-b2
run_agent openrouter/moonshotai/kimi-k2.6    kimi26-b2
run_agent openrouter/deepseek/deepseek-v4-flash dsv4f-b2
echo B2-GAUNTLET-DONE
