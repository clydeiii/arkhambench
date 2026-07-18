#!/usr/bin/env bash
# Kimi K3 audit feeder for the wave-6 auditor trial: as show2-* campaign legs
# complete (result.json present), audit each transcript with Kimi K3 via
# opencode/openrouter; when a campaign completes, audit its campaign layer.
# Sequential (avoids 429 storms), polls every 5 min, validates output shape and
# retries invalid audits up to 4 times. Runs until killed.
set -uo pipefail
cd "$(dirname "$0")/.."
export OPENROUTER_API_KEY="$(cat auth/openrouter.key)"
K3="opencode:openrouter/moonshotai/kimi-k3"
mkdir -p logs

MAXJOBS=3

valid_report() {  # audit output must contain a verdict line to count
  grep -q -e "AUDIT CLEAN" -e "^## Finding" "$1" 2>/dev/null
}

attempts() { cat "$1" 2>/dev/null || echo 0; }

slot_wait() {  # bash 3.2: no wait -n; poll job count
  while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge "$MAXJOBS" ]; do sleep 20; done
}

# clear stale locks from a previous feeder that died mid-audit
for lock in campaigns/show2-*/runs/*/.k3_lock campaigns/show2-*/.k3_lock; do
  d="${lock%/.k3_lock}"
  if [ -d "$lock" ] && [ ! -f "$d/audit.md" ] && [ ! -f "$d/campaign_audit.md" ]; then
    rmdir "$lock" 2>/dev/null
  fi
done

audit_leg() {
  local run="$1" att_file="$1/.k3_audit_attempts"
  local n; n="$(attempts "$att_file")"
  if [ "$n" -ge 4 ]; then return 0; fi
  mkdir "$run/.k3_lock" 2>/dev/null || return 0
  echo "[feeder] $(date '+%m-%d %H:%M') auditing $run (attempt $((n+1)))"
  echo $((n+1)) > "$att_file"
  python3 scripts/audit_game.py "$run" --model "$K3" \
    >> "logs/show2-audit-feeder.detail.log" 2>&1
  if valid_report "$run/audit.md"; then
    echo "[feeder] AUDIT-READY $run"
  else
    echo "[feeder] invalid/empty audit for $run — will retry ($(attempts "$att_file")/4)"
    rm -f "$run/audit.md"
    rmdir "$run/.k3_lock" 2>/dev/null
    sleep 600
  fi
}

audit_campaign_layer() {
  local camp="$1" att_file="$1/.k3_audit_attempts"
  local n; n="$(attempts "$att_file")"
  if [ "$n" -ge 4 ]; then return 0; fi
  mkdir "$camp/.k3_lock" 2>/dev/null || return 0
  echo "[feeder] $(date '+%m-%d %H:%M') campaign-layer audit $camp (attempt $((n+1)))"
  echo $((n+1)) > "$att_file"
  python3 scripts/audit_game.py --campaign "$camp" --campaign-only --model "$K3" \
    >> "logs/show2-audit-feeder.detail.log" 2>&1
  if valid_report "$camp/campaign_audit.md"; then
    echo "[feeder] AUDIT-READY $camp (campaign layer)"
  else
    echo "[feeder] invalid/empty campaign audit for $camp — will retry ($(attempts "$att_file")/4)"
    rm -f "$camp/campaign_audit.md"
    rmdir "$camp/.k3_lock" 2>/dev/null
    sleep 600
  fi
}

while true; do
  for run in campaigns/show2-*/runs/*/; do
    run="${run%/}"
    [ -f "$run/result.json" ] || continue
    [ -f "$run/log.md" ] || continue
    [ -f "$run/audit.md" ] && continue
    slot_wait
    audit_leg "$run" &
  done
  for camp in campaigns/show2-*/; do
    camp="${camp%/}"
    [ -d "$camp" ] || continue
    [ -f "$camp/campaign_summary.json" ] || continue
    [ -f "$camp/campaign_audit.md" ] && continue
    slot_wait
    audit_campaign_layer "$camp" &
  done
  wait
  sleep 300
done
