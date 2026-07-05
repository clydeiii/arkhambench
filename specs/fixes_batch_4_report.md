# Batch 4 report — replay corpus and light invariant wiring

## Implemented

- Added `scripts/replay_corpus.py`.
  - Scans completed run directories (`result.json` + `log.jsonl`) under `--dirs`.
  - Replays recorded decisions in-process through `Game.new()` / `Game.apply()`.
  - Reports every run as `CLEAN`, `DIVERGED`, or `ERROR`.
  - Detects prompt mismatches, currently-illegal recorded options, chosen-label drift,
    and apply-time replay failures.
  - Exits 0 by default and supports `--strict` for CI failure on non-clean runs.
  - Supports `--out` JSON snapshots with per-run details and summary counts.

- Added light suite replay coverage.
  - `tests/fixtures/replay_corpus/game-01`
  - `tests/fixtures/replay_corpus/game-02`
  - `tests/test_replay_corpus.py` asserts both fixture streams replay `CLEAN`.

- Updated the fuzz smoke test to the requested 5-game invariant smoke.
  - Existing `arkham/fuzz.py` semantic invariants were left intact.

## Verification

- `python3 scripts/replay_corpus.py --dirs tests/fixtures/replay_corpus`
  - 2 `CLEAN`, 0 `DIVERGED`, 0 `ERROR`

- `python3 scripts/replay_corpus.py --dirs bench runs --out /tmp/arkham_replay_batch4.json`
  - 2 `CLEAN`, 15 `DIVERGED`, 0 `ERROR`
  - Existing bench divergences are visible per run and the command exits 0.

- `python3 -m unittest discover -s tests`
  - 159 tests passed.

- `python3 -m arkham.fuzz --games 30 --scenario the_gathering --investigator roland --invariants-only`
  - `invariants ok: 30 games`

- `python3 -m arkham.fuzz --games 30 --scenario return_to_the_gathering --investigator roland --invariants-only`
  - `invariants ok: 30 games`
