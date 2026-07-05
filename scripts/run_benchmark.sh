#!/usr/bin/env bash
# ArkhamBench main run: 10 games x 4 agents, Return to The Gathering, identical
# seeds and interleaved investigator rotation for every agent. Sequential by
# design (agents share CWD/.current_run). Each agent's bench is retried until
# all its games have result.json (bench.py resumes: finished games are skipped,
# in-progress games are handed back to the agent — safe across crashes/outages).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

GAMES="${GAMES:-10}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-6}"

run_agent() {
  local agent="$1" label="$2"
  local attempt=1
  while :; do
    local done_count
    done_count=$(ls "bench/$label"/game-*/result.json 2>/dev/null | wc -l | tr -d ' ')
    if [ "${done_count:-0}" -ge "$GAMES" ]; then
      echo "=== $label complete ($done_count/$GAMES)"
      return 0
    fi
    if [ "$attempt" -gt "$MAX_ATTEMPTS" ]; then
      echo "=== $label INCOMPLETE after $MAX_ATTEMPTS attempts ($done_count/$GAMES)" >&2
      return 1
    fi
    echo "=== $label attempt $attempt ($done_count/$GAMES done)"
    python3 scripts/bench.py --agent "$agent" --label "$label" --games "$GAMES"
    attempt=$((attempt + 1))
    sleep 10
  done
}

overall=0
run_agent claude-fable-5 fable5-b1 || overall=1
run_agent claude-opus-4-8 opus48-b1 || overall=1
run_agent claude-sonnet-5 sonnet5-b1 || overall=1
run_agent codex gpt55-b1 || overall=1

echo "=== benchmark chain finished (status $overall)"
exit "$overall"
