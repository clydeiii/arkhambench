# Phase B Report

## Built

- Replaced the phase A stub loop with a deterministic rules kernel that advances until a queued decision is required.
- Added the phase/round loop: investigation, enemy, upkeep, mythos, round advancement, round-1 mythos skip behavior by starting at investigation, and hand-size discard decisions.
- Added basic legal action generation and execution for investigate, move, fight, evade, engage, draw, resource, play, act advancement, and pass/end turn.
- Implemented attacks of opportunity and engaged-enemies-move-with-investigator behavior.
- Added a skill-test sub-state machine with repeated single-card commit choices, chaos draw with replacement, token modifiers, autofail, elder sign, ties succeed, committed icons/wild icons, margins, and callback-based results.
- Added enemy utilities for spawn, engage/disengage, exhaust/ready interactions, hunter BFS movement with deterministic location-code tie-breaks, Barricade-style blocked movement, attacks, damage, retaliate, and defeat/victory display routing.
- Added encounter draw/revelation framework with discard reshuffle, enemy spawn, Ancient Evils doom, Rotting Remains tests, Frozen in Fear threat-area placeholder, and a direct-damage placeholder hook.
- Added doom threshold checks after doom placement, two placeholder agenda stages, two placeholder act stages, and act advancement by clue spend.
- Added damage/horror assignment decisions with ally soak, asset destruction, investigator defeat, trauma bookkeeping, and game-end result data.
- Added a minimal trigger/window helper for optional windows and once-per-round bookkeeping.
- Added `tests/fixtures/engine_test.json` and phase B unit coverage for AoO, engaged movement, hunter pathing, reshuffle, doom advance, upkeep order, skill-test edge cases, soak/destruction, defeat, and deterministic logs.
- Changed hidden-state checksum mismatch handling to warn on stderr and continue loading `hidden.blob`, per the phase A answer.

## Deviations / Scope Notes

- The phase B scenario is `engine_test`, not full The Gathering. It uses real Core Set JSON for locations/cards/enemies where possible, but behavior remains placeholder-generic until phase C card implementations.
- The default `new` command now builds the phase B engine-test fixture with a 10-card vanilla deck. The `--deck` path is still recorded in metadata but is not used to build the phase B fixture deck.
- Player card plays are generic: assets/events can be paid for and moved to play/discard, ammo is initialized for simple firearm text, but real card text is deferred to phase C.
- Optional reactions such as Roland's enemy-defeat clue are not fully surfaced yet; `triggers.py` provides the once-per-round/window scaffolding for phase C card hooks.
- Damage assignment is modeled as repeated single-point decisions. This matches the CLI protocol and supports ally soak/destruction, but does not yet include specialized replacement/reaction effects.
- Logs remain deterministic and timestamp-free, but rule events are logged with the state round/phase at append time rather than storing an event-local phase snapshot.

## Hook Signatures For Phase C/D

- Skill tests start through `skill_test.start(state, events, skill=..., difficulty=..., source=..., on_success=..., on_failure=...)`; callbacks are small dictionaries consumed by `skill_test.apply_callback`.
- Encounter revelations enter through `encounter.resolve_revelation(state, rng, events, instance_id)`.
- Enemy damage/defeat flows through `enemies.damage_enemy(...)` and `enemies.defeat_enemy(...)`; phase C reactions should hook there.
- Damage assignment starts through `effects.start_damage_assignment(state, events, source=..., damage=..., horror=..., direct=False, resume=None)`.
- Doom changes should use `effects.place_doom(...)` so agenda advancement checks happen after every doom change.
- Optional windows can use `triggers.present_window(...)`, with once-per-round helpers `once_per_round_available` and `mark_once_per_round`.

## Verification

- `python3 -m compileall -q arkham tests`
- `python3 -m unittest discover -s tests`

No git commit was made, per instruction.
