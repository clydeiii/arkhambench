# Phase D Report

## Built

- Applied the four phase C adjudications in favor of card JSON:
  - Roland's .38 Special uses the "1 or more clues on your location" +3 combat condition.
  - Lita Chantler has 3 health and 3 sanity and can soak horror.
  - Old Book of Lore searches the top 3 deck cards, presents the candidates as a private
    decision, draws the chosen card, and shuffles the rest back.
  - Cover Up is an optional reaction decision for each clue discovery instead of an
    automatic redirect.
- Replaced `ahlcg new`'s stub run with a real `the_gathering` setup using the Roland
  Learn-to-Play deck, weakness-redraw opening hand, mulligan decision, standard default
  difficulty, and the 27-card Gathering encounter deck.
- Implemented The Gathering scenario state and transitions:
  - Study-only setup, set-aside Hallway/Attic/Cellar/Parlor, Ghoul Priest, and Lita.
  - Act 1 Study discard/removal and forced move to revealed Hallway.
  - Act 2 end-of-round objective, Parlor reveal, Lita entry, and Ghoul Priest spawn.
  - Act 3 final R1/R2 decision after Ghoul Priest defeat.
  - Agenda 1 choice, Agenda 2 reshuffle/mill/draw, Agenda 3 end-of-enemy/end-of-round
    forced effects and doom-out branches.
  - Parlor movement barrier, Parlor resign, Attic/Cellar repeated entry effects, and
    Gathering chaos-token modifiers/aftermath.
- Added scoring and persistence:
  - `result.json` is written at game end.
  - `ahlcg score` prints outcome, resolution, XP, score, and trauma.
  - XP/score cover R1, R2, R3, and no-resolution outcomes with victory-location scoring
    for revealed/clueless Attic and Cellar.
- Added `arkham.fuzz` runnable as `python3 -m arkham.fuzz --games N`, with random legal
  choices across all four difficulties and per-step invariants.
- Added/updated tests for the adjudicated cards, scenario transitions, scoring branches,
  `result.json`, and fuzzer smoke coverage.

## Notes

- The phase-B fixture remains available as `build_engine_test_state` for older engine unit
  tests, but CLI `new` now creates The Gathering.
- Mulligan is modeled as repeated one-card choices from the original opening hand plus a
  "Keep opening hand" option, matching the existing repeated-choice decision style.
- The 50-game random fuzz sample ended in no-resolution every time, which is expected for
  uniformly random solo play.

## Verification

- `python3 -m compileall -q arkham tests`
- `python3 -m unittest discover -s tests`
- `python3 -m arkham.fuzz --games 50`

Final suite status: 65 tests passing. Fuzzer sanity run: `no_resolution: 50`.

No git commit was made, per instruction.
