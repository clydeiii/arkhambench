#!/usr/bin/env bash
# C7 lane 2: haiku coverage wave — 5 coverage decks (all 32 XP cards) through
# Return-to-MM and Return-to-DB standalone, coverage directive, confirmations ON.
set -uo pipefail
cd "$(dirname "$0")/.."
MODEL="${1:-claude-haiku-4-5-20251001}"
mkdir -p logs

MISSION="$(sed '/<!-- standalone-only:/,$d' docs_agent/mission.md)"

seed=12000
for inv in roland daisy skids agnes wendy; do
  for scen in return_to_the_midnight_masks return_to_the_devourer_below; do
    seed=$((seed + 1))
    tag="c7l2-$inv-${scen//return_to_the_/}"
    run="runs/$tag"
    if [ -f "$run/result.json" ]; then
      echo "=== $tag already complete"
      continue
    fi
    if [ ! -d "$run" ]; then
      ./ahlcg new --run "$run" --seed "$seed" --scenario "$scen" \
        --investigator "$inv" --deck "data/decks/coverage/$inv.json" >/dev/null
      echo "=== created $tag (seed $seed)"
    else
      echo "=== resuming $tag"
    fi
    export AHLCG_RUN="$PWD/$run"

    PROMPT="$MISSION

**COVERAGE DIRECTIVE (this run's real objective):** your deck is a test deck packed
with XP cards. Over this game, PLAY or trigger every XP card (level >0) in your deck
at least once when legal — even when tactically suboptimal — but never illegally.
Exercising XP cards and reporting engine bugs count for MORE than your score this
run. Track which XP cards you have exercised in your reasoning. Play the CURRENT run
to completion (never './ahlcg new'), use './ahlcg do <n> --why \"...\"' for every
choice, and confirmation prompts are ON — answer them deliberately."

    echo "--- playing $tag with $MODEL"
    claude -p "$PROMPT" --model "$MODEL" \
      --allowedTools "Bash(./ahlcg:*),Read(docs_agent/**)" \
      --disallowedTools "Bash(./ahlcg new:*),Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read(runs/**)" \
      --max-turns 400 >> "logs/$tag.agent.log" 2>&1
    if [ -f "$run/result.json" ]; then
      echo "--- $tag COMPLETE"
    else
      echo "--- $tag INCOMPLETE (will retry on rerun)"
    fi
    unset AHLCG_RUN
  done
done
echo C7-LANE2-DONE
