#!/usr/bin/env bash
# DeepSeek V4 Flash 0731 — b6 learning-bench lane, gated on endpoint
# availability (the 0731 endpoint needs the OpenRouter privacy toggle
# flipped; until then every probe 404s and we sleep).
cd "$(dirname "$0")/.."
export OPENROUTER_API_KEY="$(cat auth/openrouter.key)"
ready() {
  curl -sS --max-time 60 https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "Content-Type: application/json" \
    -d '{"model":"deepseek/deepseek-v4-flash-0731","messages":[{"role":"user","content":"OK"}],"max_tokens":2}' \
    2>/dev/null | grep -qv '"error"'
}
until ready; do
  echo "[gate] 0731 endpoint not available — sleeping 15 min ($(date '+%H:%M'))"
  sleep 900
done
echo "[gate] endpoint live at $(date); launching b6 lane"
python3 scripts/bench.py --agent openrouter/deepseek/deepseek-v4-flash-0731 \
  --label dsv4f-b6 --games 30 --max-continues 6
echo "DSV4F-B6-DONE rc=$?"
