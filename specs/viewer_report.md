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

## Parts C/D Implemented

- Added the dependency-free static viewer:
  - `viewer/index.html`
  - `viewer/app.js`
  - `viewer/style.css`
- Viewer features:
  - Run selector, first/previous/next/last buttons, step slider, jump-to-round selector,
    ArrowLeft/ArrowRight keyboard navigation, and linkable `#run=<name>&step=<n>` hashes.
  - Fixed Gathering map layout with connection lines, revealed/unrevealed states,
    shroud/clue/victory details, attachments, enemies, engaged rings, and investigator
    marker.
  - Scenario panel for agenda, act, chaos bag, victory display, encounter deck count,
    and examinable encounter discard.
  - Event ticker, decision prompt/options with chosen option highlighted and declined
    options dimmed, active skill-test strip, and prominent final result block.
  - Player board with stat deltas, play area, hand, threat area, deck/discard counts,
    examinable hand/discard piles, and engaged enemies shown in threat.
  - ArkhamDB card thumbnails with text fallback; every card chip/thumb opens a modal
    with full-size image plus exported engine card/instance data.
  - Delta highlighting for changed stats/location state and cards entering player zones.
- Added `scripts/view.sh`, which exports passed bench/run directories when missing,
  rebuilds `viewer/data/index.json`, and serves `http://localhost:8765/viewer/`.
- Added README "Watching a game" section with the viewer commands.

## Parts C/D Verification

- Validated both existing `viewer/data/*.json` exports against the viewer resolution
  paths used by `app.js`:
  - decision chosen indexes are one-based and labels match options.
  - player, encounter, victory, enemy, attachment, agenda, act, and location card
    references resolve to exported card data.
- Parsed `viewer/index.html` and verified local `style.css` and `app.js` references exist.
- Re-ran `python3 -m unittest discover -s tests`
  - 92 tests passed.
- Attempted a local `python3 -m http.server 8765` fetch smoke test, but this sandbox
  denied localhost socket access with `PermissionError: [Errno 1] Operation not permitted`.

No git commit was made, per instruction.
