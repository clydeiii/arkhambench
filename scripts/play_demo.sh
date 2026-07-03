#!/usr/bin/env bash
# Launch a coding agent to play one game of The Gathering.
# Usage: scripts/play_demo.sh <claude-model|codex> <run-name> [seed]
# Examples:
#   scripts/play_demo.sh claude-sonnet-5 sonnet-demo-1 7
#   scripts/play_demo.sh codex gpt55-demo-1 7
set -euo pipefail
cd "$(dirname "$0")/.."

AGENT="${1:?agent: claude model id or 'codex'}"
RUN="${2:?run name}"
SEED="${3:-$RANDOM}"

./ahlcg new --run "runs/$RUN" --seed "$SEED" >/dev/null
PROMPT="$(cat docs_agent/mission.md)

Your game has already been created: it is the current run (runs/$RUN). Do not create a
new one. Play it to completion now."

mkdir -p logs
if [ "$AGENT" = "codex" ]; then
  codex exec -s workspace-write "$PROMPT" 2>&1 | tee "logs/$RUN.agent.log"
else
  claude -p "$PROMPT" --model "$AGENT" \
    --allowedTools "Bash(./ahlcg:*) Read" \
    --max-turns 400 2>&1 | tee "logs/$RUN.agent.log"
fi

echo "=== agent session done; result: ==="
cat "runs/$RUN/result.json" 2>/dev/null || echo "(game not finished)"
echo "Game transcript: runs/$RUN/log.md — agent session log: logs/$RUN.agent.log"
