#!/bin/bash
# b7 watchdog: if a lane's bench dir goes stale >30 min while its runner is
# alive, kill the wedged agent CLI. bench.py's continue loop then RESUMES the
# retained session, so a kill costs nothing but the wedged call.
cd /Users/clyde/ahlcg || exit 1
while true; do
  for spec in "fable5-b7|claude -p .*claude-fable-5" "sol56-b7|codex exec.*gpt-5.6-sol"; do
    label="${spec%%|*}"
    pat="${spec#*|}"
    dir="bench/$label"
    [ -d "$dir" ] || continue
    newest=$(find "$dir" -type f -exec stat -f %m {} + 2>/dev/null | sort -rn | head -1)
    [ -n "$newest" ] || continue
    age=$(( $(date +%s) - newest ))
    if [ "$age" -gt 1800 ] && pgrep -f "label $label" >/dev/null 2>&1; then
      echo "$(date) $label stale ${age}s — killing agent (pattern: $pat)" >> logs/b7-watchdog.log
      pkill -f "$pat"
    fi
  done
  sleep 300
done
