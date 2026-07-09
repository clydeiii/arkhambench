#!/usr/bin/env bash
# C7 lane 1: realistic-deck wave — MM and DB with decks upgraded the way real
# campaigns upgraded them (data/decks/upgraded/). Drivers: gpt-5.6-luna and
# gpt-5.6-terra (codex) + haiku fill (claude). Sequential; confirmations ON.
# NOTE: codex agents may rely on .current_run — do not run other lanes that
# call './ahlcg new' concurrently with this one.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs

MISSION="$(sed '/<!-- standalone-only:/,$d' docs_agent/mission.md)"
DIRECTIVE="

**REALISTIC-DECK PLAYTEST:** your deck was upgraded with XP by a real prior
campaign — play it well and to win. Verified engine-bug reports (./ahlcg bug)
are worth more than score. Play the CURRENT run to completion (never
'./ahlcg new'); use './ahlcg do <n> --why \"one short sentence\"' for every
choice; confirmation prompts are ON — answer them deliberately."

play() {
  local model="$1" inv="$2" scen="$3" seed="$4"
  local short="${scen//return_to_the_/}" tagmodel="${model##*:}"
  local tag="c7l1-${tagmodel}-${inv}-${short}"
  local run="runs/$tag"
  local decktag="mm"; [ "$short" = "devourer_below" ] && decktag="db"
  if [ -f "$run/result.json" ]; then echo "=== $tag already complete"; return; fi
  if [ ! -d "$run" ]; then
    if ! ./ahlcg new --run "$run" --seed "$seed" --scenario "$scen" \
      --investigator "$inv" --deck "data/decks/upgraded/$inv-$decktag.json" >/dev/null; then
      echo "=== $tag CREATE FAILED (skipping agent launch)"
      return
    fi
    echo "=== created $tag (seed $seed)"
  else
    echo "=== resuming $tag"
  fi
  printf '%s' "$run" > .current_run
  export AHLCG_RUN="$PWD/$run"
  echo "--- playing $tag"
  if [[ "$model" == codex:* ]]; then
    codex exec -s workspace-write -m "${model#codex:}" "$MISSION$DIRECTIVE" \
      >> "logs/$tag.agent.log" 2>&1
  else
    claude -p "$MISSION$DIRECTIVE" --model "$model" \
      --allowedTools "Bash(./ahlcg:*),Read(docs_agent/**)" \
      --disallowedTools "Bash(./ahlcg new:*),Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read(runs/**)" \
      --max-turns 400 >> "logs/$tag.agent.log" 2>&1
  fi
  unset AHLCG_RUN
  [ -f "$run/result.json" ] && echo "--- $tag COMPLETE" || echo "--- $tag INCOMPLETE (rerun to retry)"
}

seed=13000
for pair in \
  "codex:gpt-5.6-luna roland" "codex:gpt-5.6-luna daisy" "codex:gpt-5.6-luna skids" \
  "codex:gpt-5.6-terra agnes" "codex:gpt-5.6-terra wendy" "codex:gpt-5.6-terra roland" \
  "claude-haiku-4-5-20251001 daisy" "claude-haiku-4-5-20251001 agnes" "claude-haiku-4-5-20251001 wendy"; do
  set -- $pair
  model="$1"; inv="$2"
  for scen in return_to_the_midnight_masks return_to_the_devourer_below; do
    seed=$((seed + 1))
    play "$model" "$inv" "$scen" "$seed"
  done
done
echo C7-LANE1-DONE
