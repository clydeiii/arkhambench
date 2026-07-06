#!/usr/bin/env bash
# Open-weights playtest driver via opencode + OpenRouter.
# Usage: scripts/opencode_playtest.sh <provider/model> <run-name> [seed] [investigator] [scenario]
# The agent plays one game with a BUG-HUNTING directive: verified engine-bug
# reports (./ahlcg bug) are worth more than score.
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${1:?model, e.g. openrouter/z-ai/glm-5.2 or openrouter/tencent/hy3:free}"
RUN="${2:?run name}"
SEED="${3:-$RANDOM}"
INVESTIGATOR="${4:-roland}"
SCENARIO="${5:-return_to_the_midnight_masks}"
DIFFICULTY="${6:-standard}"

export PATH="$HOME/.opencode/bin:$PATH"
export OPENROUTER_API_KEY="$(cat auth/openrouter.key)"
export AHLCG_RUN="runs/$RUN"   # pin every ./ahlcg call to THIS game (no .current_run races)
SAFE_MODEL="$(printf '%s' "$MODEL" | tr -c 'A-Za-z0-9._-' '_')"
mkdir -p logs notebooks

if [ ! -f "runs/$RUN/state.json" ]; then
  ./ahlcg new --run "runs/$RUN" --scenario "$SCENARIO" --investigator "$INVESTIGATOR" \
    --difficulty "$DIFFICULTY" --seed "$SEED" --notebook "notebooks/$SAFE_MODEL.md" >/dev/null
else
  printf '%s' "runs/$RUN" > .current_run
fi

PROMPT="$(cat docs_agent/mission.md)

--- PLAYTEST DIRECTIVE (overrides scoring priorities) ---
You are a PLAYTESTER for this rules engine, not just a player. While you play,
compare every game state and option list against your understanding of the official
Arkham Horror LCG rules and exact card text (verify with './ahlcg card <name>').
Whenever the engine deviates from the rules — an illegal option offered, a required
effect skipped, wrong math, a Forced ability that didn't fire, wrong timing — file a
bug report immediately:
    ./ahlcg bug \"<what happened, what the rules say, why it's wrong>\"
A verified bug report is worth more than any game score. Do not exploit bugs you
find; report them and play on as the rules intend where possible.

Your game has already been created: it is the current run (runs/$RUN). Do not create
a new one. Play it to completion now with './ahlcg do <n>' (state: './ahlcg state').
Keep cross-game lessons in the notebook ('./ahlcg note add ...').

HARNESS RULES: run './ahlcg ...' commands DIRECTLY in bash, one per call, from the
repo root. Do NOT write helper scripts, shell functions, aliases, or files of any
kind (file writes are disabled and attempts waste your session). Every './ahlcg'
command works standalone — no shell state is needed between calls. If a command
errors, read the error and try a corrected './ahlcg' call."

opencode run -m "$MODEL" "$PROMPT" > "logs/$RUN.agent.log" 2>&1 || echo "(agent exited nonzero)"

if [ -f "runs/$RUN/result.json" ]; then
  python3 -c "import json;r=json.load(open('runs/$RUN/result.json'));print('RESULT:', r['outcome'], 'score', r['score'])"
else
  echo "RESULT: incomplete"
fi
[ -f "runs/$RUN/bug_reports.md" ] && echo "BUG REPORTS FILED:" && grep -c "^## " "runs/$RUN/bug_reports.md" || echo "no bug reports"
