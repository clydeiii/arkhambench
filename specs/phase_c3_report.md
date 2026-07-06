# Phase C3 Report

## Implemented

- Replaced the Devourer Below stub with playable `the_devourer_below` and `return_to_the_devourer_below` setup, act/agenda flow, locations, resolutions, and campaign output.
- Reused the Midnight Masks cult machinery for The Devourer's Cult where applicable: Disciple of the Devourer, Mask of Umordhoth, doom-on-enemy math, spawn-location choices, Aloof attachment behavior, and cultist search/draw helpers.
- Added C3 engine hooks for scenario actions, movement/reveal behavior, encounter revelations, agenda advancement, enemy defeat, enemy phase, end-of-round effects, chaos-token aftermath, and skill-test callbacks.
- Wired campaign setup inputs and outputs:
  - cultists got away
  - past midnight
  - Ghoul Priest alive
  - Lita in deck through the campaign deck/standalone flag
  - elderthing persistence through `chaos_bag_additions`
  - `weakness_gained`/`weaknesses_added` persistence
  - C2 killed-flag fixes for no-resolution and Umordhoth's Hunger, while R3 Lita sacrifice survives
- Added mission briefing warnings for doom pressure, no-resolution/resign consequences, got-away cultist spawns, and Return vault scaling.
- Added `tests/test_phase_c3_devourer_below.py` covering the requested setup, graph, location, act/agenda, Umordhoth, Return vault, chaos-token, resolution, and campaign-adapter cases.

## Spec / JSON Notes

- The spec says to follow JSON on conflicts. Core card JSON for `01158` Umordhoth's Wrath has a real revelation effect: willpower(5), and for each point failed choose discard a card or take 1 damage and 1 horror. I implemented that JSON text.
- The Return Corpse-Taker text allows Rivertown or Main Path; this scenario uses Main Path per the C3 spec.

## Validation

- `python3 -m unittest discover -s tests` => 261 tests passing.
- Core fuzz, all clean:
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --investigator roland --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --investigator daisy --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --investigator skids --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --investigator agnes --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --investigator wendy --invariants-only`
- Return fuzz, all clean:
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --investigator roland --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --investigator daisy --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --investigator skids --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --investigator agnes --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --investigator wendy --invariants-only`

No git commit was made.

Fixes batch 1

## Fixes Batch 7 — Campaign Loop 1

- Fixed campaign-log family clobbering: Midnight Masks fields and Devourer outcome
  fields now apply only from their producing scenario family.
- Corrected display/statics issues: Deduction logs only actual additional clues,
  duplicate Magnifying Glass copies stack, and On Wings of Darkness skips no-op
  Rivertown moves.
- Split scenario chaos-symbol timing: unconditional token effects resolve at
  final-token reveal before success determination; fail-conditional effects remain
  at result time. Agenda advancement caused by reveal-time doom is deferred until
  the active skill test completes.
- Added deferred continuation handling for result-time token aftermath, Wrath
  damage choices, and AoO damage/horror reactions so pending decisions do not drop
  follow-up effects.
- Swept Midnight Masks helpers reused by Devourer so doom/objective/finalize tails
  dispatch through `arkham.effects` and stay scenario-aware.
- Added `tests/test_fixes_batch_7.py` covering adjudication entries 25-33,
  including the Devourer-vs-Midnight agenda leak and six-scenario dispatch canary.

Validation:

- `python3 -m unittest discover -s tests` => 278 tests passing.
- Full six-scenario fuzz matrix, all clean:
  - `python3 -m arkham.fuzz --games 50 --scenario the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --invariants-only`

No git commit was made.
