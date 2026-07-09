#!/usr/bin/env bash
# C7 audit wave: gpt-5.6-sol rules-audits every lane-1/lane-2 transcript,
# 4-way parallel (audits are read-only; no .current_run usage).
set -uo pipefail
cd "$(dirname "$0")/.."
MODEL="codex:gpt-5.6-sol"

ls -d runs/c7l1-* runs/c7l2-* | while read -r run; do
  [ -f "$run/result.json" ] || continue
  [ -f "$run/audit.md" ] && { echo "=== $run already audited"; continue; }
  echo "$run"
done | xargs -P 4 -I{} sh -c '
  echo "--- auditing {}"
  python3 scripts/audit_game.py --model "'"$MODEL"'" "{}" >/dev/null 2>&1
  if [ -f "{}/audit.md" ]; then echo "--- {} AUDITED"; else echo "--- {} AUDIT-FAILED"; fi
'
echo C7-AUDITS-DONE
