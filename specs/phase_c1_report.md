# Phase C1 Report - The Midnight Masks

## Built

- Added scenario ids `the_midnight_masks` and `return_to_the_midnight_masks`.
- Implemented original and Return setup:
  - encounter deck counts,
  - separate hidden Cultist deck,
  - campaign inputs for burned house, Ghoul Priest alive, and Lita forced to find others,
  - seeded location and agenda variants,
  - Return cultist-deck random removal.
- Implemented Midnight Masks scenario rules:
  - Cultist-deck act action and 6-unique-cultist objective,
  - agenda 1 hunter/Narogath spawn and agenda 2 midnight resolution,
  - resign resolution,
  - doom on enemies contributing to agenda advance and clearing on advance,
  - named cultist parley/evade/forced routes,
  - core and Return Dark Cult / Devourer's Cult encounter behavior,
  - Mask of Umordhoth health/Retaliate/Aloof modifiers,
  - scenario chaos-token effects for all four difficulties,
  - result campaign block with interrogated/got-away/past-midnight/Ghoul Priest fields.
- Added CLI flags:
  - `--house-burned`
  - `--ghoul-priest-alive`
  - `--lita-forced-to-find-others`
- Updated `docs_agent/mission.md` and `docs_agent/scenario_reference.md` for Midnight Masks briefing material.
- Added focused regression coverage in `tests/test_phase_c1_midnight_masks.py`.

## Deviations / Conflicts

- No spec-vs-card-JSON conflicts were found.
- The card data stores double-sided agenda cards as `01121a`/`01121b` and `50026a`/`50026b`; implementation follows those JSON codes.
- The Return Miskatonic University implementation follows JSON as specified: shroud 3, 1 clue, no Victory, take-2-horror-for-clue action text.

## Tests

- Before count: not captured before implementation.
- After: `python3 -m unittest discover -s tests`
  - 203 tests run
  - OK

## Fixes batch 1

- Implemented all printed Midnight Masks and Return location abilities, including per-location limits in `state.limits`, search choices, token-pool clue gains, Return Police Station/Train Station/Museum/Warehouse actions, and the Easttown Ally asset play-cost discount.
- Added the Your House Ghoul Priest spawn redirect; when Your House is burned, Ghoul Priest falls through to the default engaged-with-investigator spawn.
- Added a shared evasion hook so test-based evades and automatic/considered-evaded effects such as Cunning Distraction and Stray Cat trigger Ruth Turner's Forced ability without affecting plain disengage effects.
- Adjusted Midnight Masks cultist/fallback spawn paths so ready non-Aloof enemies that spawn at the investigator's location engage immediately.
- Added focused regression coverage in `tests/test_phase_c1_fixes_1_midnight.py`.
- Verification after fixes:
  - `python3 -m unittest discover -s tests` => 203 tests, OK
  - `python3 -m arkham.fuzz --games 50 --scenario the_midnight_masks` => `R1: 50`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_midnight_masks` => `R1: 50`

## Fuzz

All requested Midnight Masks fuzz runs were clean with `--games 50 --invariants-only`.

- `the_midnight_masks`: roland, daisy, skids, agnes, wendy - OK
- `return_to_the_midnight_masks`: roland, daisy, skids, agnes, wendy - OK

Exact default-investigator spec commands also completed:

- `python3 -m arkham.fuzz --games 50 --scenario the_midnight_masks` => `R1: 50`
- `python3 -m arkham.fuzz --games 50 --scenario return_to_the_midnight_masks` => `R1: 50`
