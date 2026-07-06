#!/usr/bin/env bash
# Showcase campaigns for the viewer: Fable 5 and GPT-5.5, one campaign per
# investigator each. Sequential (shared .current_run / .current_campaign).
set -uo pipefail
cd "$(dirname "$0")/.."

run_one() {
  local agent="$1" name="$2" seed="$3" inv="$4"
  if [ -f "campaigns/$name/campaign_summary.json" ]; then
    echo "== skip $name (complete)"
    return
  fi
  echo "== $name ($agent, $inv, seed $seed)"
  bash scripts/campaign_demo.sh "$agent" "$name" "$seed" "$inv" standard 2>&1 | tail -3
}

run_one claude-fable-5 show-fable-roland 9201 roland
run_one claude-fable-5 show-fable-daisy  9202 daisy
run_one claude-fable-5 show-fable-skids  9203 skids
run_one claude-fable-5 show-fable-agnes  9204 agnes
run_one claude-fable-5 show-fable-wendy  9205 wendy
run_one codex          show-gpt-roland   9211 roland
run_one codex          show-gpt-daisy    9212 daisy
run_one codex          show-gpt-skids    9213 skids
run_one codex          show-gpt-agnes    9214 agnes
run_one codex          show-gpt-wendy    9215 wendy
echo SHOWCASE-CAMPAIGNS-DONE
