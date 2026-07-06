#!/usr/bin/env bash
# Drive a coding agent through a FULL (Return to) Night of the Zealot campaign:
# Gathering -> upgrades -> Midnight Masks -> upgrades -> Devourer Below.
# Usage: scripts/campaign_demo.sh <claude-model|codex> <campaign-name> [seed] [investigator] [difficulty]
# Resume-hardened: re-running continues an existing campaign from its current phase.
set -euo pipefail
cd "$(dirname "$0")/.."

AGENT="${1:?agent: claude model id or 'codex'}"
NAME="${2:?campaign name}"
SEED="${3:-$RANDOM}"
INVESTIGATOR="${4:-roland}"
DIFFICULTY="${5:-standard}"
MAX_SESSIONS=12   # hard stop: sessions per campaign (3 scenarios + upgrades + retries)

DIR="campaigns/$NAME"
SAFE_AGENT="$(printf '%s' "$AGENT" | tr -c 'A-Za-z0-9._-' '_')"
mkdir -p notebooks logs

if [ ! -f "$DIR/campaign.json" ]; then
  ./ahlcg campaign new --dir "$DIR" --investigator "$INVESTIGATOR" \
    --difficulty "$DIFFICULTY" --seed "$SEED" >/dev/null
  echo "created campaign $DIR (seed $SEED, $INVESTIGATOR, $DIFFICULTY)"
else
  printf '%s' "$DIR" > .current_campaign
  echo "resuming campaign $DIR"
fi

phase() { python3 -c "import json;print(json.load(open('$DIR/campaign.json'))['phase'])"; }
ncomplete() { python3 -c "import json;print(len(json.load(open('$DIR/campaign.json'))['scenarios']))"; }

session=0
while [ "$(phase)" != "complete" ] && [ "$session" -lt "$MAX_SESSIONS" ]; do
  session=$((session + 1))
  before_phase="$(phase)"
  before_n="$(ncomplete)"

  if [ "$before_phase" = "scenario" ]; then
    # Create the next scenario run mechanically; the agent plays + records + upgrades.
    ./ahlcg campaign next >/dev/null
  fi

  RUN_DIR="$(cat .current_run 2>/dev/null || true)"
  PROMPT="$(cat docs_agent/campaign_guide.md)

--- CURRENT CAMPAIGN STATUS ---
$(./ahlcg campaign status)

--- CURRENT MISSION ---
$(cat "$RUN_DIR/mission.md" 2>/dev/null || echo '(no active run)')

You are playing a full campaign. Your campaign directory is $DIR and the current
scenario run has already been created (do NOT run 'ahlcg new' or 'ahlcg campaign new').
Do the following, in order, stopping only when told:
1. If the campaign status above says phase 'scenario': play the current run to
   completion with './ahlcg do <n>' (use './ahlcg state' to look around), then run
   './ahlcg campaign record'.
2. If phase is (or becomes) 'upgrade': inspect './ahlcg upgrade options', spend XP
   wisely ('./ahlcg upgrade buy <code> [--replace <code>|--remove <code>]'), decide
   about Lita if offered ('./ahlcg campaign lita --include|--skip'), then run
   './ahlcg upgrade done'. Banking XP is allowed and sometimes wise.
3. If phase is 'replace' (your investigator was killed or driven insane): choose a
   replacement with './ahlcg campaign replace --investigator <name>'.
4. Then STOP — do not start the next scenario; the harness will re-invoke you.
Record cross-game lessons in your notebook with './ahlcg note add'."

  echo "=== session $session (phase: $before_phase, scenarios done: $before_n) ==="
  if [ "$AGENT" = "codex" ]; then
    codex exec -s workspace-write "$PROMPT" 2>&1 | tee -a "logs/campaign-$NAME.agent.log" >/dev/null
  else
    claude -p "$PROMPT" --model "$AGENT" \
      --allowedTools "Bash(./ahlcg:*),Read(docs_agent/**),Read(notebooks/**),Read($DIR/runs/**)" \
      --disallowedTools "Bash(./ahlcg new:*),Bash(./ahlcg campaign new:*),Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read($DIR/runs/**/state.json),Read($DIR/runs/**/log.jsonl)" \
      --max-turns 400 2>&1 | tee -a "logs/campaign-$NAME.agent.log" >/dev/null
  fi

  after_phase="$(phase)"
  after_n="$(ncomplete)"
  echo "    -> phase: $after_phase, scenarios done: $after_n"
  if [ "$after_phase" = "$before_phase" ] && [ "$after_n" = "$before_n" ]; then
    echo "    (no progress this session; retrying)"
  fi
done

echo "=== campaign finished (phase: $(phase)) ==="
./ahlcg campaign status || true
cat "$DIR/campaign_summary.json" 2>/dev/null || echo "(no summary yet)"
