#!/bin/bash
# dsv4f watchdog: opencode calls can wedge on 429s. If either DS lane's work
# dir goes stale >20 min while an opencode deepseek process exists, kill it;
# both runners recover (bench.py continues, campaign runner backs off).
cd /Users/clyde/ahlcg || exit 1
while true; do
  newest=0
  for dir in bench/dsv4f-b6 campaigns/show3-dsv4f-*; do
    [ -d "$dir" ] || continue
    m=$(find "$dir" -type f -exec stat -f %m {} + 2>/dev/null | sort -rn | head -1)
    [ -n "$m" ] && [ "$m" -gt "$newest" ] && newest=$m
  done
  if [ "$newest" -gt 0 ]; then
    age=$(( $(date +%s) - newest ))
    if [ "$age" -gt 1200 ] && pgrep -f "opencode run.*deepseek" >/dev/null 2>&1; then
      echo "$(date) dsv4f stale ${age}s — killing opencode deepseek call" >> logs/dsv4f-watchdog.log
      pkill -f "opencode run.*deepseek"
    fi
  fi
  sleep 300
done
