#!/usr/bin/env bash
# Wave-6 playtest campaigns for the Kimi K3 auditor trial. Three player lanes —
# Hunyuan 3 (opencode, free tier), GPT-5.6 Luna (codex), Sonnet 5 (claude CLI) —
# each play 5 FULL Return-to-NotZ campaigns (one per investigator), notes fed
# forward via a per-model shared notebook. Seeds 9401-9405 are IDENTICAL across
# lanes and seed-matched to the b4 GPT-5.6 family campaign wave.
# Env-pinned (AHLCG_CAMPAIGN/AHLCG_RUN/AHLCG_NOTEBOOK) so lanes run in parallel.
# Usage: scripts/show2_campaign.sh <hy3|luna|sonnet>
set -uo pipefail
cd "$(dirname "$0")/.."
LANE="${1:?lane: hy3|luna|sonnet}"

case "$LANE" in hy3|luna|sonnet) ;; *) echo "unknown lane: $LANE"; exit 1;; esac

MAX_SESSIONS=14
mkdir -p notebooks logs
export AHLCG_NOTEBOOK="$PWD/notebooks/show2-$LANE-campaigns.md"
touch "$AHLCG_NOTEBOOK"

OPENCODE="$HOME/.opencode/bin/opencode"
if [ "$LANE" = "hy3" ]; then
  export OPENROUTER_API_KEY="$(cat auth/openrouter.key)"
fi

quota_ok() {
  curl -sS --max-time 60 https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "Content-Type: application/json" \
    -d '{"model":"tencent/hy3:free","messages":[{"role":"user","content":"OK"}],"max_tokens":2}' \
    2>/dev/null | grep -qv '"code":429'
}

wait_for_quota() {
  [ "$LANE" = "hy3" ] || return 0
  until quota_ok; do
    echo "[quota] 429 — sleeping 30 min ($(date '+%H:%M'))"
    sleep 1800
  done
}

if [ "$LANE" = "hy3" ]; then
  HARNESS_RULES="
HARNESS RULES: run './ahlcg ...' commands DIRECTLY in bash, one per call, from the
repo root. Do NOT write helper scripts, shell functions, or files of any kind (file
writes are disabled and waste your session). Never run './ahlcg new' or './ahlcg
campaign new'. Honor system: play only from './ahlcg' command output and docs_agent/
— do not read arkham/, data/, tests/, specs/, runs/, bench/, campaigns/, or any
state.json/log.jsonl/hidden.blob."
else
  HARNESS_RULES="
HARNESS RULES: run './ahlcg ...' commands directly, one per call, from the repo
root. Never run './ahlcg new' or './ahlcg campaign new'. Honor system: play only
from './ahlcg' command output and docs_agent/ — do not read arkham/, data/,
tests/, specs/, runs/, bench/, campaigns/, or any state.json/log.jsonl/hidden.blob."
fi

agent_session() {  # $1 prompt, $2 log file
  case "$LANE" in
    hy3)
      "$OPENCODE" run -m "openrouter/tencent/hy3:free" "$1" >> "$2" 2>&1 ;;
    luna)
      codex exec -s workspace-write -m gpt-5.6-luna "$1" >> "$2" 2>&1 ;;
    sonnet)
      claude -p "$1" --model claude-sonnet-5 --max-turns 400 \
        --allowedTools "Bash(./ahlcg:*),Read(docs_agent/**),Read(notebooks/**),Read(campaigns/show2-sonnet-*/runs/**)" \
        --disallowedTools "Bash(./ahlcg new:*),Bash(./ahlcg campaign new:*),Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read(bench/**),Read(**/state.json),Read(**/log.jsonl),Read(**/hidden.blob)" \
        >> "$2" 2>&1 ;;
  esac
}

phase() { python3 -c "import json;print(json.load(open('$1/campaign.json'))['phase'])"; }
ncomplete() { python3 -c "import json;print(len(json.load(open('$1/campaign.json'))['scenarios']))"; }

run_campaign() {
  local inv="$1" seed="$2"
  local name="show2-$LANE-$inv" dir="campaigns/show2-$LANE-$inv"
  export AHLCG_CAMPAIGN="$PWD/$dir"

  if [ ! -f "$dir/campaign.json" ]; then
    if ! ./ahlcg campaign new --dir "$dir" --investigator "$inv" \
      --difficulty standard --seed "$seed" >/dev/null; then
      echo "=== $name CREATE FAILED"; exit 1
    fi
    echo "=== created campaign $dir (seed $seed)"
  else
    echo "=== resuming campaign $dir (phase $(phase "$dir"))"
  fi

  local session=0
  while [ "$(phase "$dir")" != "complete" ] && [ "$session" -lt "$MAX_SESSIONS" ]; do
    session=$((session + 1))
    wait_for_quota
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

You are playing a full campaign as $inv — one of your FIVE campaigns (one per
investigator). The campaign and current scenario run already exist. Do the
following in order, stopping only when told:
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
    agent_session "$prompt" "logs/campaign-$name.agent.log"
    echo "    -> phase: $(phase "$dir"), done: $(ncomplete "$dir")"
  done
  echo "=== $name finished (phase: $(phase "$dir"), sessions: $session)"
}

run_campaign roland 9401
run_campaign daisy  9402
run_campaign skids  9403
run_campaign agnes  9404
run_campaign wendy  9405
echo "SHOW2-DONE ($LANE)"
