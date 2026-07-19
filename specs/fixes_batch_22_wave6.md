# Fixes batch 22 — ledger 139 (reveal clobbers placed clues)

Tests in tests/test_fixes_batch_22.py. Full suite green.

arkham/scenarios/the_devourer_below.py reveal_location_fields: change
`location.clues = int(card.get("clues") or 0)` to ADD the printed value to
any tokens already on the location. Check the_gathering.py and
the_midnight_masks.py reveal paths for the same assignment pattern and fix
identically (grep "clues = int"). Ensure reveal fields are applied exactly
once per location (existing revealed-guard) so clues aren't double-added.

Tests: (a) place a clue on an unrevealed DB woods location (Disciple
Forced path), reveal it -> clues = placed + printed; (b) normal reveal with
no placed tokens unchanged; (c) same for a Gathering/MM location if their
reveal paths had the pattern.

## Fix 2 — ledger 140/141: sourced-effect log dedup

Apply the batch-18 fix-4 pattern: when a sourced effect (Daisy elder-sign
draw, Drawn to the Flame discovery) logs its own line, the generic
draw/discover line must not also fire. One line per event, keep the
sourced wording. Tests: one log line per elder-sign draw and per DttF
discovery; amounts still actual.

## Fix 3 — ledger 143: Central traits + On Wings destination choice

data/cards: add "Central." to the traits of 01126, 01127, 01130, 01131,
01132, 01134 and their Return to MM variants (check 50027/50028 and any
other ring replacements — verify against printed cards). On Wings of
Darkness (01173): when >1 legal Central destination exists (excluding
current location per RR Move), present the destination choice; auto-move
only with a single candidate. Tests: choice presented listing all legal
Central locations; single-candidate auto-move unchanged; trait data
matches print for all six ring locations.

## Fix 4 — ledger 142: scenario_reference defeat note

docs_agent/scenario_reference.md Midnight Masks: add the printed guide's
sentence — if no resolution was reached (all investigators resigned or
defeated), Resolution 1 is read; defeat still applies its usual trauma.
