#!/usr/bin/env bash
# hy3-b3: rerun Hunyuan 3 through the identical b1/b2 gauntlet, isolating ONE
# variable vs hy3-b2 — the new notebook-compaction semantics (compact help text
# + mission.md compress-not-discard guidance + line-delta output + note archive
# recovery). Engine otherwise unchanged since b2. Free tier only ($0).
set -uo pipefail
cd "$(dirname "$0")/.."
GAMES="${1:-10}"
MAX_ATTEMPTS=8

label="hy3-b3"
agent="openrouter/tencent/hy3:free"
attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  echo "=== $label attempt $attempt"
  python3 scripts/bench.py --agent "$agent" --label "$label" --games "$GAMES" || true
  have=$(ls bench/"$label"/game-*/result.json 2>/dev/null | wc -l | tr -d ' ')
  [ "$have" -ge "$GAMES" ] && break
  attempt=$((attempt + 1))
done
done_count=$(ls bench/"$label"/game-*/result.json 2>/dev/null | wc -l | tr -d ' ')
echo "=== $label: $done_count/$GAMES complete"
echo HY3-B3-DONE
