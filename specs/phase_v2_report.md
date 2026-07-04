# Phase V2 Report

## Built

- Registered Daisy's V2 deck cards: `01008`, `01009`, `01061`, and `01066`.
- Extended slot handling for Ally, Hand, and Arcane assets, including Daisy's Tote Bag restricted Tome hand slots and overflow discard decisions when slot capacity changes.
- Implemented The Necronomicon weakness:
  - Revelation puts it into Daisy's threat area with 3 horror.
  - Elder sign chaos tokens become autofail while it is in play.
  - Its action moves horror to Daisy, provokes attacks of opportunity, and discards it when empty.
  - Daisy's additional Tome action can be spent on its action ability.
- Implemented Scrying with 3 charges, exhaustion, Arcane slot use, investigator/encounter deck targeting, and public top-card ordering decisions.
- Implemented Blinding Light as an Evade action event:
  - Uses willpower against enemy evade.
  - Is attack-of-opportunity exempt.
  - Deals 1 damage after a successful evade.
  - Loses 1 remaining action on symbol/autofail reveal.
- Added `python3 -m arkham.fuzz --investigator <slug>`.
- Marked encounter cards that are awaiting a revelation-cancel decision with an explicit transient `encounter_drawn` zone so fuzz invariants remain accurate.

## Flagged

- `01009 The Necronomicon`: the V2 spec says it enters the threat area "not a hand slot." The Rules Reference "Slots" entry says each asset in a play area or threat area with a slot symbol is held in a slot of that type, and vendored JSON gives The Necronomicon `slot: Hand`. I followed RR/JSON: while in Daisy's threat area, The Necronomicon is a Hand-slot asset and can force slot overflow, but cannot be discarded while it has horror.

## Tests

- Before V2 tests: 99 tests reported in V1.
- After V2 tests: 106 tests passing.
- `./ahlcg new --investigator daisy --run /private/tmp/ahlcg-daisy-v2-smoke`: passed.
- `python3 -m unittest discover -s tests`: passed, 106 tests.
- `python3 -m arkham.fuzz --games 50`: passed, `no_resolution: 50`.
- `python3 -m arkham.fuzz --games 50 --investigator daisy`: passed, `no_resolution: 50`.
