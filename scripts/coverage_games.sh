#!/usr/bin/env bash
# XP-card coverage games: each coverage deck plays Return to the Midnight Masks
# and Return to the Devourer Below standalone. Sequential (shared .current_run).
# Usage: scripts/coverage_games.sh [agent] [seed-base]
set -euo pipefail
cd "$(dirname "$0")/.."

AGENT="${1:-claude-haiku-4-5}"
BASE="${2:-9500}"
mkdir -p logs notebooks

i=0
for inv in roland daisy skids agnes wendy; do
  for scen in return_to_the_midnight_masks return_to_the_devourer_below; do
    i=$((i + 1))
    run="coverage-$inv-${scen#return_to_the_}"
    if [ -f "runs/$run/result.json" ]; then
      echo "== skip $run (complete)"
      continue
    fi
    extra=""
    if [ "$scen" = "return_to_the_devourer_below" ]; then
      extra="--lita-in-deck --cultists-got-away \"Herman Collins,Victoria Devereux\""
    fi
    if [ ! -f "runs/$run/state.json" ]; then
      eval ./ahlcg new --run "runs/$run" --scenario "$scen" --investigator "$inv" \
        --deck "data/decks/coverage/$inv.json" --seed "$((BASE + i))" \
        --notebook "notebooks/coverage.md" $extra >/dev/null
    else
      printf '%s' "runs/$run" > .current_run
    fi
    echo "== $run (seed $((BASE + i)))"
    MISSION="runs/$run/mission.md"
    [ -f "$MISSION" ] || MISSION="docs_agent/mission.md"
    PROMPT="$(cat "$MISSION")

Your game has already been created: it is the current run (runs/$run). Do not create
a new one. Your deck intentionally contains upgraded (XP) cards — play them when
useful; they are a focus of this playtest. Play the game to completion now. If any
card or rule behaves differently from its printed text, file it with './ahlcg bug'."
    claude -p "$PROMPT" --model "$AGENT" \
      --allowedTools "Bash(./ahlcg:*),Read(docs_agent/**),Read(notebooks/**),Read(runs/$run/log.md)" \
      --disallowedTools "Bash(./ahlcg new:*),Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read(runs/$run/state.json),Read(runs/$run/log.jsonl)" \
      --max-turns 400 > "logs/$run.agent.log" 2>&1 || echo "   (agent exited nonzero)"
    if [ -f "runs/$run/result.json" ]; then
      python3 -c "import json;r=json.load(open('runs/$run/result.json'));print('   ->',r['outcome'],'score',r['score'])"
    else
      echo "   -> INCOMPLETE"
    fi
  done
done
echo COVERAGE-GAMES-DONE
