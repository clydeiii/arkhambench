#!/usr/bin/env bash
# Wave-7 instrumented campaign lanes: subscription frontier models, 5 full
# Return-to-NotZ campaigns each (seeds 9401-9405, matched to b4/w6), newest
# engine, with per-session telemetry (tokens, wall time, CLI-reported cost)
# appended to logs/show3-telemetry.jsonl by scripts/show3_telemetry.py.
# Thinking level: claude lanes run harness-default adaptive thinking; codex
# lanes run model_reasoning_effort=high (~/.codex/config.toml).
# Usage: scripts/show3_campaign.sh <fable|sonnet|opus|sol|terra|luna>
set -uo pipefail
cd "$(dirname "$0")/.."
LANE="${1:?lane: fable|sonnet|opus|sol|terra|luna}"

case "$LANE" in
  fable)  HARNESS=claude; MODEL=claude-fable-5;  REASONING="adaptive (harness default)";;
  sonnet) HARNESS=claude; MODEL=claude-sonnet-5; REASONING="adaptive (harness default)";;
  opus)   HARNESS=claude; MODEL=claude-opus-4-8; REASONING="adaptive (harness default)";;
  sol)    HARNESS=codex;  MODEL=gpt-5.6-sol;     REASONING="high (config.toml)";;
  terra)  HARNESS=codex;  MODEL=gpt-5.6-terra;   REASONING="high (config.toml)";;
  luna)   HARNESS=codex;  MODEL=gpt-5.6-luna;    REASONING="high (config.toml)";;
  hy3)    HARNESS=opencode; MODEL="openrouter/tencent/hy3"; MODEL_SUBSTR="hy3"; REASONING="provider default";;
  k3)     HARNESS=opencode; MODEL="openrouter/moonshotai/kimi-k3"; MODEL_SUBSTR="kimi-k3"; REASONING="provider default";;
  *) echo "unknown lane: $LANE"; exit 1;;
esac

MAX_SESSIONS=14
mkdir -p notebooks logs logs/show3-sessions
OPENCODE="$HOME/.opencode/bin/opencode"
if [ "$HARNESS" = "opencode" ]; then
  export OPENROUTER_API_KEY="$(cat auth/openrouter.key)"
fi

credits_json() {
  curl -sS --max-time 30 https://openrouter.ai/api/v1/credits \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" 2>/dev/null
}

openrouter_ready() {  # live 1-token probe: catches 429s, monthly budget caps, exhausted credits
  local slug
  case "$LANE" in
    hy3) slug="tencent/hy3";;
    k3)  slug="moonshotai/kimi-k3";;
    *) return 0;;
  esac
  curl -sS --max-time 60 https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "Content-Type: application/json" \
    -d "{\"model\":\"$slug\",\"messages\":[{\"role\":\"user\",\"content\":\"OK\"}],\"max_tokens\":2}" \
    2>/dev/null | grep -qv '"error"'
}

wait_for_provider() {
  [ "$HARNESS" = "opencode" ] || return 0
  until openrouter_ready; do
    echo "[provider] $LANE not ready (429 or credits exhausted) — sleeping 30 min ($(date '+%H:%M'))"
    sleep 1800
  done
}
export AHLCG_NOTEBOOK="$PWD/notebooks/show3-$LANE-campaigns.md"
touch "$AHLCG_NOTEBOOK"

HARNESS_RULES="
HARNESS RULES: run './ahlcg ...' commands directly, one per call, from the repo
root. Never run './ahlcg new' or './ahlcg campaign new'. Honor system: play only
from './ahlcg' command output and docs_agent/ — do not read arkham/, data/,
tests/, specs/, runs/, bench/, campaigns/, or any state.json/log.jsonl/hidden.blob."

phase() { python3 -c "import json;print(json.load(open('$1/campaign.json'))['phase'])"; }
ncomplete() { python3 -c "import json;print(len(json.load(open('$1/campaign.json'))['scenarios']))"; }

agent_session() {  # $1 prompt, $2 agent log, $3 campaign name, $4 session no
  local start end
  start=$(date +%s)
  if [ "$HARNESS" = "opencode" ]; then
    :  # handled below (needs credits capture around the call)
  elif [ "$HARNESS" = "claude" ]; then
    local sjson="logs/show3-sessions/$3-s$4.json"
    claude -p "$1" --model "$MODEL" --max-turns 400 --output-format json \
      --allowedTools "Bash(./ahlcg:*),Read(docs_agent/**),Read(notebooks/**),Read(campaigns/show3-$LANE-*/runs/**)" \
      --disallowedTools "Bash(./ahlcg new:*),Bash(./ahlcg campaign new:*),Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read(bench/**),Read(**/state.json),Read(**/log.jsonl),Read(**/hidden.blob)" \
      > "$sjson" 2>>"logs/campaign-$3.agent.err"
    end=$(date +%s)
    python3 scripts/show3_telemetry.py claude "$sjson" --meta \
      lane="$LANE" harness="$HARNESS" model="$MODEL" reasoning="$REASONING" \
      campaign="$3" session="$4" start="$start" end="$end" seconds="$((end-start))" \
      agent_log="logs/campaign-$3.agent.log"
  else
    local marker="logs/show3-sessions/$3-s$4.marker"
    touch "$marker"
    codex exec -s workspace-write -m "$MODEL" "$1" >> "logs/campaign-$3.agent.log" 2>&1
    end=$(date +%s)
    python3 scripts/show3_telemetry.py codex "logs/campaign-$3.agent.log" "$marker" --meta \
      lane="$LANE" harness="$HARNESS" model="$MODEL" reasoning="$REASONING" \
      campaign="$3" session="$4" start="$start" end="$end" seconds="$((end-start))"
  fi
  if [ "$HARNESS" = "opencode" ]; then
    local creds_before creds_after
    creds_before=$(credits_json | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['total_usage'])" 2>/dev/null || echo "")
    "$OPENCODE" run -m "$MODEL" "$1" >> "logs/campaign-$3.agent.log" 2>&1
    end=$(date +%s)
    creds_after=$(credits_json | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['total_usage'])" 2>/dev/null || echo "")
    python3 scripts/show3_telemetry.py opencode "$start" "$end" "$MODEL_SUBSTR" --meta \
      lane="$LANE" harness="$HARNESS" model="$MODEL" reasoning="$REASONING" \
      campaign="$3" session="$4" start="$start" end="$end" seconds="$((end-start))" \
      openrouter_usage_before="$creds_before" openrouter_usage_after="$creds_after"
  fi
}

run_campaign() {
  local inv="$1" seed="$2"
  local name="show3-$LANE-$inv" dir="campaigns/show3-$LANE-$inv"
  export AHLCG_CAMPAIGN="$PWD/$dir"

  if [ ! -f "$dir/campaign.json" ]; then
    if ! ./ahlcg campaign new --dir "$dir" --investigator "$inv" \
      --difficulty standard --seed "$seed" >/dev/null; then
      echo "=== $name CREATE FAILED"; exit 1
    fi
    echo "=== created campaign $dir (seed $seed) at $(date '+%H:%M:%S')"
  else
    echo "=== resuming campaign $dir (phase $(phase "$dir"))"
  fi

  local session=0
  while [ "$(phase "$dir")" != "complete" ] && [ "$session" -lt "$MAX_SESSIONS" ]; do
    session=$((session + 1))
    wait_for_provider
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

    echo "--- $name session $session (phase: $before_phase, done: $before_n) at $(date '+%H:%M:%S')"
    agent_session "$prompt" "logs/campaign-$name.agent.log" "$name" "$session"
    local after_phase after_n
    after_phase="$(phase "$dir")"
    after_n="$(ncomplete "$dir")"
    echo "    -> phase: $after_phase, done: $after_n"
    if [ "$after_phase" = "$before_phase" ] && [ "$after_n" = "$before_n" ]; then
      if tail -c 2000 "logs/campaign-$name.agent.log" 2>/dev/null | grep -qi "usage limit\|rate.limit\|overloaded\|quota"; then
        echo "    (no progress + limit signature; backing off 15 min)"
        sleep 900
      else
        echo "    (no progress; backing off 4 min)"
        sleep 240
      fi
    fi
  done
  echo "=== $name finished (phase: $(phase "$dir"), sessions: $session) at $(date '+%H:%M:%S')"
}

run_campaign roland 9401
run_campaign daisy  9402
run_campaign skids  9403
run_campaign agnes  9404
run_campaign wendy  9405
echo "SHOW3-DONE ($LANE)"
