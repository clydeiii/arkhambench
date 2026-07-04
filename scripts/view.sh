#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p viewer/data

slug() {
  python3 - "$1" <<'PY'
import re
import sys
name = sys.argv[1].strip()
slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-")
print(slug or "run")
PY
}

export_run_if_needed() {
  local run_dir="$1"
  local label="$2"
  local out_file="viewer/data/$(slug "$label").json"
  if [[ -f "$out_file" ]]; then
    echo "already exported: $out_file"
    return
  fi
  echo "exporting $run_dir -> $out_file"
  python3 -m arkham.export --run "$run_dir" --out viewer/data --label "$label"
}

for arg in "$@"; do
  if [[ ! -d "$arg" ]]; then
    echo "skipping non-directory: $arg" >&2
    continue
  fi
  shopt -s nullglob
  games=("$arg"/game-*)
  shopt -u nullglob
  if [[ ${#games[@]} -gt 0 ]]; then
    bench_name="$(basename "$arg")"
    for game_dir in "${games[@]}"; do
      [[ -d "$game_dir" ]] || continue
      export_run_if_needed "$game_dir" "$bench_name-$(basename "$game_dir")"
    done
  else
    export_run_if_needed "$arg" "$(basename "$arg")"
  fi
done

python3 - <<'PY'
from pathlib import Path
from arkham.export import rebuild_index
rebuild_index(Path("viewer/data"))
PY

# Cache card images locally (arkhamdb throttles hotlinked bursts). Cheap when
# already cached; new exports fetch only their new codes.
python3 scripts/fetch_card_images.py || echo "image cache fetch failed; viewer will fall back to arkhamdb/text" >&2

echo "Serving ArkhamBench viewer at http://localhost:8765/viewer/"
python3 -m http.server 8765
