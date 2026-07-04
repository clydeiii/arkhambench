# Phase V1 Report

## Built

- Added `ahlcg new --scenario the_gathering --investigator roland|daisy|skids|agnes|wendy`.
- Added the scenario registry in `arkham/scenarios/__init__.py` and routed `Game.new` plus scenario choices through it.
- Switched the default deck to `data/decks/killbray/<investigator>.json`; `data/decks/roland_ltp.json` remains loadable explicitly.
- Added setup validation that every deck slot has a registered implementation. Roland's killbray deck passes; Daisy/Skids/Agnes/Wendy currently fail on V2-V5 class cards as intended.
- Generalized setup and mulligan weakness filtering to all player weaknesses by JSON `subtype_code`.
- Loaded `data/cards/rtnotz.json` and `data/cards/rtnotz_encounter.json` into the card DB.
- Added investigator identity to run metadata and compact status output.
- Implemented the five core investigator stat lines and V1 abilities/effects:
  - Roland reaction and elder sign retained under the generalized investigator setup.
  - Daisy Tome-only fourth action and elder-sign Tome draw.
  - "Skids" fast bought action and elder-sign resource gain.
  - Agnes after-horror reaction.
  - Wendy token-cancel/redraw reaction and elder-sign auto-success when Wendy's Amulet is in play.
- Added the four V1 timing windows:
  - token-reveal reaction,
  - would-fail window for Lucky!,
  - revelation-cancel window for Ward of Protection,
  - after-horror reaction window.
- Implemented V1 cards: `01065`, `01080`, `01090`, `01091`, `01093`, `01096`, `01097`, `01098`, and `01101`.

## Flagged

- `01065 Ward of Protection`: the V1 spec says to offer Ward for encounter and weakness treachery draws, but vendored JSON says "Play when you draw a non-weakness treachery card." I followed JSON, so Ward is not offered for weakness treacheries.

## Tests

- Before V1 tests: 92 tests.
- After V1 tests: 99 tests.
- `python3 -m unittest discover -s tests`: 99 tests passing.
- `python3 -m arkham.fuzz --games 50`: passed, `no_resolution: 50`.
