#!/usr/bin/env bash
# C7 audit wave: gpt-5.6-sol rules-audits every lane-1/lane-2 transcript,
# 4-way parallel via bash job control (audits are read-only).
set -uo pipefail
cd "$(dirname "$0")/.."
MODEL="codex:gpt-5.6-sol"
MAXJOBS=4

audit_one() {
  local run="$1"
  python3 scripts/audit_game.py --model "$MODEL" "$run" >/dev/null 2>&1
  if [ -f "$run/audit.md" ]; then echo "--- $run AUDITED"; else echo "--- $run AUDIT-FAILED"; fi
}

for run in runs/c7l1-* runs/c7l2-*; do
  [ -f "$run/result.json" ] || continue
  [ -f "$run/audit.md" ] && { echo "=== $run already audited"; continue; }
  while [ "$(jobs -rp | wc -l)" -ge "$MAXJOBS" ]; do
    wait -n 2>/dev/null || sleep 5
  done
  echo "--- auditing $run"
  audit_one "$run" &
done
wait
echo C7-AUDITS-DONE
