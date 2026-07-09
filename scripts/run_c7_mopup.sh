#!/usr/bin/env bash
# C7 mop-up: 5 targeted haiku games, each naming the exact dormant XP cards its
# deck must exercise. Post-batch-12 engine, so also a live smoke test.
set -uo pipefail
cd "$(dirname "$0")/.."
MODEL="claude-haiku-4-5-20251001"
mkdir -p logs
MISSION="$(sed '/<!-- standalone-only:/,$d' docs_agent/mission.md)"

declare -A CARDS=(
  [roland]="Police Badge"
  [daisy]="Hyperawareness"
  [skids]="Cat Burglar AND Hard Knocks"
  [agnes]="Mind Wipe (level 1) AND Book of Shadows"
  [wendy]="Rabbit's Foot (level 3)"
)

seed=14000
for inv in roland daisy skids agnes wendy; do
  seed=$((seed + 1))
  tag="c7mop-$inv"
  run="runs/$tag"
  if [ -f "$run/result.json" ]; then echo "=== $tag already complete"; continue; fi
  if [ ! -d "$run" ]; then
    if ! ./ahlcg new --run "$run" --seed "$seed" --scenario return_to_the_midnight_masks \
      --investigator "$inv" --deck "data/decks/coverage/$inv.json" >/dev/null; then
      echo "=== $tag CREATE FAILED"; continue
    fi
    echo "=== created $tag (seed $seed)"
  else
    echo "=== resuming $tag"
  fi
  export AHLCG_RUN="$PWD/$run"
  PROMPT="$MISSION

**NARROW COVERAGE DIRECTIVE (overrides score):** this run exists to exercise
specific XP cards that have never been played: ${CARDS[$inv]}. Your PRIMARY
objective is to legally PLAY those cards and USE their abilities this game —
mulligan for them, spend resources on them, trigger their abilities — even at
the cost of losing. Play the CURRENT run to completion (never './ahlcg new'),
use --why on every choice."
  echo "--- playing $tag"
  claude -p "$PROMPT" --model "$MODEL" \
    --allowedTools "Bash(./ahlcg:*),Read(docs_agent/**)" \
    --disallowedTools "Bash(./ahlcg new:*),Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read(runs/**)" \
    --max-turns 400 >> "logs/$tag.agent.log" 2>&1
  [ -f "$run/result.json" ] && echo "--- $tag COMPLETE" || echo "--- $tag INCOMPLETE"
  unset AHLCG_RUN
done
echo C7-MOPUP-DONE
