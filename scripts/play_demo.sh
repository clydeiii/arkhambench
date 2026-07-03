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

# Each agent gets its own persistent notebook, bound to the run via meta.json.
SAFE_AGENT="$(printf '%s' "$AGENT" | tr -c 'A-Za-z0-9._-' '_')"
mkdir -p notebooks
./ahlcg new --run "runs/$RUN" --seed "$SEED" --notebook "notebooks/$SAFE_AGENT.md" >/dev/null
PROMPT="$(cat docs_agent/mission.md)

Your game has already been created: it is the current run (runs/$RUN). Do not create a
new one. Play it to completion now."

mkdir -p logs
if [ "$AGENT" = "codex" ]; then
  codex exec -s workspace-write "$PROMPT" 2>&1 | tee "logs/$RUN.agent.log"
else
  claude -p "$PROMPT" --model "$AGENT" \
    --allowedTools "Bash(./ahlcg:*),Read(docs_agent/**),Read(notebook.md),Read(runs/$RUN/log.md)" \
    --disallowedTools "Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read(runs/**/hidden.blob),Read(runs/**/state.json),Read(runs/**/log.jsonl)" \
    --max-turns 400 2>&1 | tee "logs/$RUN.agent.log"
fi

echo "=== agent session done; result: ==="
cat "runs/$RUN/result.json" 2>/dev/null || echo "(game not finished)"
echo "Game transcript: runs/$RUN/log.md — agent session log: logs/$RUN.agent.log"
