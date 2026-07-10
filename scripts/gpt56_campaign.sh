#!/usr/bin/env bash
# Drive one GPT-5.6 model through 5 FULL Return-to-NotZ campaigns (one per
# investigator), notes fed forward via a per-model shared notebook.
# Usage: scripts/gpt56_campaign.sh <gpt-5.6-model> <shortname>
# e.g.   scripts/gpt56_campaign.sh gpt-5.6-sol sol
# Seeds 9401-9405 are IDENTICAL across models for seed-matched comparisons.
# Env-pinned (AHLCG_CAMPAIGN/AHLCG_RUN/AHLCG_NOTEBOOK) so model lanes can run
# in parallel; codex inherits env (verified 2026-07-09).
set -uo pipefail
cd "$(dirname "$0")/.."
MODEL="${1:?gpt-5.6 model id}"
SHORT="${2:?short name (sol/terra/luna)}"
export AHLCG_NOTEBOOK="$PWD/notebooks/${SHORT}56-campaigns.md"
mkdir -p notebooks logs
touch "$AHLCG_NOTEBOOK"
MAX_SESSIONS=14

HARNESS_RULES="

HARNESS RULES: run './ahlcg ...' commands directly, one per call, from the repo
root. Never run './ahlcg new' or './ahlcg campaign new'. Honor system: play only
from './ahlcg' command output and docs_agent/ — do not read arkham/, data/,
tests/, specs/, runs/, bench/, campaigns/, or any state.json/log.jsonl/hidden.blob."

phase() { python3 -c "import json;print(json.load(open('$1/campaign.json'))['phase'])"; }
ncomplete() { python3 -c "import json;print(len(json.load(open('$1/campaign.json'))['scenarios']))"; }

run_campaign() {
  local inv="$1" seed="$2"
  local name="show-$SHORT-$inv" dir="campaigns/show-$SHORT-$inv"
  export AHLCG_CAMPAIGN="$PWD/$dir"

  if [ ! -f "$dir/campaign.json" ]; then
    if ! ./ahlcg campaign new --dir "$dir" --investigator "$inv" \
      --difficulty standard --seed "$seed" >/dev/null; then
      echo "=== $name CREATE FAILED"; return
    fi
    echo "=== created campaign $dir (seed $seed)"
  else
    echo "=== resuming campaign $dir (phase $(phase "$dir"))"
  fi

  local session=0
  while [ "$(phase "$dir")" != "complete" ] && [ "$session" -lt "$MAX_SESSIONS" ]; do
    session=$((session + 1))
    local before_phase before_n
    before_phase="$(phase "$dir")"
    before_n="$(ncomplete "$dir")"
    if [ "$before_phase" = "scenario" ]; then
      ./ahlcg campaign next >/dev/null
    fi
    local idx run_dir
    idx=$(( $(ncomplete "$dir") + 1 ))
    run_dir="$dir/runs/c-$name-$idx"
    [ -d "$run_dir" ] && export AHLCG_RUN="$PWD/$run_dir" || unset AHLCG_RUN

    local prompt
    prompt="$(cat docs_agent/campaign_guide.md)

--- CURRENT CAMPAIGN STATUS ---
$(./ahlcg campaign status)

--- CURRENT MISSION ---
$(cat "$run_dir/mission.md" 2>/dev/null || echo '(no active run)')

You are playing a full campaign as $inv — campaign $((1)) of your FIVE campaigns
(one per investigator). The campaign and current scenario run already exist. Do
the following in order, stopping only when told:
0. If phase is 'deckbuild': freely swap level-0 cards at no XP cost
   ('./ahlcg deckbuild options/swap/done').
1. If phase is 'scenario': play the current run to completion with
   './ahlcg do <n> --why \"one short sentence\"', then './ahlcg campaign record'.
2. If phase is (or becomes) 'upgrade': './ahlcg upgrade options', spend XP wisely,
   decide Lita if offered, './ahlcg upgrade done'.
3. If phase is 'replace': './ahlcg campaign replace --investigator <name>'.
4. Then STOP — the harness re-invokes you for the next phase.
Your persistent notebook ('./ahlcg note show' / 'note add') is SHARED ACROSS ALL
FIVE of your campaigns — read it first, write cross-campaign lessons (scenario
structure, upgrade value, what killed you). Compact means COMPRESS, not discard;
old versions stay readable via './ahlcg note archive'.$HARNESS_RULES"

    echo "--- $name session $session (phase: $before_phase, done: $before_n)"
    codex exec -s workspace-write -m "$MODEL" "$prompt" >> "logs/campaign-$name.agent.log" 2>&1
    echo "    -> phase: $(phase "$dir"), done: $(ncomplete "$dir")"
  done
  echo "=== $name finished (phase: $(phase "$dir"), sessions: $session)"
}

run_campaign roland 9401
run_campaign daisy  9402
run_campaign skids  9403
run_campaign agnes  9404
run_campaign wendy  9405
echo "GPT56-CAMPAIGNS-DONE ($SHORT)"
