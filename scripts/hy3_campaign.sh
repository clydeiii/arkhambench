#!/usr/bin/env bash
# Drive Hunyuan 3 (opencode, free tier) through 5 FULL Return-to-NotZ campaigns,
# one per investigator (show-hy3-<inv>, seeds 9301-9305). Sequential, session-
# per-phase, resume-hardened, quota-aware (free tier = 1000 req/day; on 429 the
# probe fails and we sleep until it recovers instead of burning sessions).
# Env-pinned: AHLCG_CAMPAIGN + AHLCG_RUN + AHLCG_NOTEBOOK, so concurrent codex
# lanes can't cross-contaminate via .current_run/.current_campaign.
set -uo pipefail
cd "$(dirname "$0")/.."

export OPENROUTER_API_KEY="$(cat auth/openrouter.key)"
OPENCODE="$HOME/.opencode/bin/opencode"
MODEL="openrouter/tencent/hy3:free"
export AHLCG_NOTEBOOK="$PWD/notebooks/hy3-campaigns.md"   # shared across all 5
mkdir -p notebooks logs
touch "$AHLCG_NOTEBOOK"
MAX_SESSIONS=14

HARNESS_RULES="
HARNESS RULES: run './ahlcg ...' commands DIRECTLY in bash, one per call, from the
repo root. Do NOT write helper scripts, shell functions, or files of any kind (file
writes are disabled and waste your session). Never run './ahlcg new' or './ahlcg
campaign new'. Honor system: play only from './ahlcg' command output and docs_agent/
— do not read arkham/, data/, runs/, bench/, campaigns/, or any state.json/log.jsonl."

quota_ok() {
  curl -sS --max-time 60 https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "Content-Type: application/json" \
    -d '{"model":"tencent/hy3:free","messages":[{"role":"user","content":"OK"}],"max_tokens":2}' \
    2>/dev/null | grep -qv '"code":429'
}

wait_for_quota() {
  until quota_ok; do
    echo "[quota] 429 — sleeping 30 min ($(date '+%H:%M'))"
    sleep 1800
  done
}

phase() { python3 -c "import json;print(json.load(open('$1/campaign.json'))['phase'])"; }
ncomplete() { python3 -c "import json;print(len(json.load(open('$1/campaign.json'))['scenarios']))"; }

run_campaign() {
  local inv="$1" seed="$2"
  local name="show-hy3-$inv" dir="campaigns/show-hy3-$inv"
  export AHLCG_CAMPAIGN="$PWD/$dir"

  if [ ! -f "$dir/campaign.json" ]; then
    ./ahlcg campaign new --dir "$dir" --investigator "$inv" \
      --difficulty standard --seed "$seed" >/dev/null
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
    # deterministic current run dir for this campaign (idx = scenarios done + 1)
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

You are playing a full campaign as $inv. The campaign and the current scenario run
already exist (never run 'ahlcg new' or 'ahlcg campaign new'). Do the following, in
order, stopping only when told:
0. If phase is 'deckbuild' (campaign start only): freely swap level-0 cards at no
   XP cost ('./ahlcg deckbuild options', './ahlcg deckbuild swap --in <code> --out
   <code>', './ahlcg deckbuild done').
1. If phase is 'scenario': play the current run to completion with './ahlcg do <n>'
   (always pass --why \"one short sentence\"), then run './ahlcg campaign record'.
2. If phase is (or becomes) 'upgrade': './ahlcg upgrade options', spend XP wisely
   ('./ahlcg upgrade buy <code> [--replace <code>|--remove <code>]'), decide Lita
   if offered ('./ahlcg campaign lita --include|--skip'), then './ahlcg upgrade done'.
3. If phase is 'replace' (killed/insane): './ahlcg campaign replace --investigator <name>'.
4. Then STOP — the harness re-invokes you for the next phase.
Your persistent notebook ('./ahlcg note show' / './ahlcg note add') is shared across
ALL FIVE of your campaigns (one per investigator) — read it first, record cross-game
and cross-investigator lessons. Compact means COMPRESS, not discard.$HARNESS_RULES"

    echo "--- $name session $session (phase: $before_phase, done: $before_n)"
    "$OPENCODE" run -m "$MODEL" "$prompt" >> "logs/campaign-$name.agent.log" 2>&1

    local after_phase after_n
    after_phase="$(phase "$dir")"
    after_n="$(ncomplete "$dir")"
    echo "    -> phase: $after_phase, done: $after_n"
  done
  echo "=== $name finished (phase: $(phase "$dir"), sessions: $session)"
}

run_campaign roland 9301
run_campaign daisy  9302
run_campaign skids  9303
run_campaign agnes  9304
run_campaign wendy  9305
echo HY3-CAMPAIGNS-DONE
