# Phase A Report

## Built

- Added the `ahlcg` executable wrapper and the `arkham/` package layout from `DESIGN.md` §2.
- Implemented phase A concrete modules:
  - `model.py`: serializable dataclasses for game state, investigator, card instances, locations, enemies, agenda/act, chaos bag, turn state, and pending decisions.
  - `rng.py`: seeded `random.Random` wrapper with serializable state.
  - `serialize.py`: public JSON atomic writes plus obfuscated hidden blob encoding/decoding and checksum support.
  - `data.py`: vendored card/deck JSON loading and card lookup by code or case-insensitive name fragment.
  - `log.py`: JSONL event append plus markdown transcript append/rendering.
  - `notebook.py`: persistent notebook add/show/compact with history archive.
  - `game.py`: `Game.new`, `Game.load`, `Game.save`, `Game.current_decision`, and `Game.apply` using the required stub decision loop.
  - `cli.py`: `new`, `state`, `actions`, `do`, `log`, `card`, `score`, and `note` commands with run-dir and notebook resolution.
- Added empty shells for later phase modules: phases, actions, skill tests, chaos, enemies, encounter, effects, triggers, card registry/modules, and The Gathering scenario.
- Added `tests/` coverage for state round-trip, hidden/public split, notebook archiving, CLI stub round-trip, card lookup, and atomic write behavior.

## Deviations

- The scenario is named `stub` in phase A state because game rules and The Gathering setup are explicitly deferred. The public state still uses Study/Roland/agenda/act-shaped data so later phases have the expected frame.
- `state` rendering is intentionally basic. It covers the required sections at a skeleton level, but detailed unrevealed-side handling, full discard listing, and action math belong with the rules/card implementation phases.
- `score` prints the specified in-progress stub and does not create `result.json`; scoring is phase D.

## Open Questions

- Should public `state.json` eventually be the exact public renderer source, or should it remain a lossy public projection while `hidden.blob` carries the authoritative full `GameState`?
- How strict should hidden-state tamper handling be in benchmark runs: hard failure, warning plus continue, or repair from public state when possible?
- For phase B, should the decision queue store only opaque engine payloads, or also enough public metadata to let old decisions remain readable in saved state snapshots?
