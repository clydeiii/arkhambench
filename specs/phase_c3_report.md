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
