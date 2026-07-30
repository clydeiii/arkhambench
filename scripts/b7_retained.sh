#!/bin/bash
# b7 retained-session learning bench: same 30 games/seeds as b6, but game N+1
# resumes game N's agent session (ARC-AGI-3 "retained reasoning + compaction"
# test). One lane per invocation; launch with nohup and disown.
cd /Users/clyde/ahlcg || exit 1
mkdir -p logs
case "$1" in
  fable)
    python3 scripts/bench.py --agent claude-fable-5 --label fable5-b7 \
      --games 30 --max-continues 6 --max-turns 500 --retain-session
    ;;
  sol)
    python3 scripts/bench.py --agent codex:gpt-5.6-sol --label sol56-b7 \
      --games 30 --max-continues 6 --max-turns 500 --retain-session
    ;;
  *)
    echo "usage: b7_retained.sh fable|sol" >&2
    exit 2
    ;;
esac
echo "B7 LANE $1 DONE rc=$? $(date)"
