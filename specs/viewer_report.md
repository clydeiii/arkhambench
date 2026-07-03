# Run Viewer Report

## Parts A/B Implemented

- Added `timeline.jsonl` capture from `Game.new` and `Game.apply`.
  - Each line includes the step index, round, phase, status line, chosen option, rendered
    event summaries, next pending decision, and `GameState.public_dict()`.
  - Timeline appends use one `os.write` call per line and log IO failures to stderr
    without failing the game.
- Added `arkham/export.py`, runnable with:
  - `python3 -m arkham.export --run <run-dir> [--out viewer/data] [--label NAME]`
  - `python3 -m arkham.export --all-bench bench/<label> [--out viewer/data]`
- Exporter behavior:
  - Reads existing `timeline.jsonl` directly when present.
  - Replays legacy runs without timeline data from `meta.json` plus recorded
    `decision_made` events in `log.jsonl`.
  - Verifies replay by comparing each reconstructed pending prompt against the matching
    recorded `decision_presented` prompt.
  - Emits partial exports with `complete: false` and `divergence_step` when replay
    diverges.
  - Does replay work in a temporary run directory, leaving the original run untouched.
  - Produces decision-centric run JSON with bundled card metadata and result data.
  - Rebuilds `viewer/data/index.json` from existing exported run files in stable order.
- Exported the two current `bench/sonnet5-mini` games to `viewer/data/`:
  - `sonnet5-mini-game-01.json`: replay complete, 50 steps, outcome `R2`, score 6.
  - `sonnet5-mini-game-02.json`: replay complete, 59 steps, outcome `R2`, score 7.

## Tests

- Added Part D coverage for Parts A/B in `tests/test_viewer_export.py`:
  - Timeline lines are written by `new`/`apply`, parse as JSON, include state, and have
    count `decisions + 1`.
  - Replay export on a scripted mini-game preserves chosen option indexes and labels.
  - Replay divergence detection triggers on a doctored log and records the divergence.
  - `index.json` rebuild includes exported metadata and step counts.
  - Card bundles cover all card codes visible in snapshots.
  - Existing `viewer/data/*.json` exports validate against the expected step schema.

## Verification

- `python3 -m unittest discover -s tests`
  - 92 tests passed.
- `python3 -m arkham.fuzz --games 50`
  - completed cleanly with `no_resolution: 50`.

No git commit was made, per instruction.
