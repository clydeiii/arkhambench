# Phase V5 Report

## Built

- Registered Wendy Adams's killbray deck cards: `01014`, `01015`, `01046`, `01048`, `01051`, `01073`, `01075`, `01077`, `01078`, `01079`, and `01081`.
- Implemented Wendy's Amulet:
  - Offers the topmost event in Wendy's discard pile as playable while the Amulet is in play.
  - Routes played events to the bottom of the investigator deck instead of the discard pile.
  - Leaves events discarded from hand in the discard pile.
  - Preserves the V1 elder-sign auto-success hook.
- Implemented Abandoned and Alone as direct horror plus discard-pile removal from the game.
- Implemented Rogue/Survivor assets:
  - Pickpocketing after evades, including Cunning Distraction and Stray Cat-style automatic evades, not plain disengages.
  - Leo De Luca's additional action and Ally soak.
  - Scavenging's succeed-by-2 investigate reaction and Item return choice.
  - Rabbit's Foot after-fail reaction.
  - Dig Deep willpower/agility pre-reveal boosts.
- Implemented Wendy events/skills:
  - Backstab as an agility Fight event, AoO-exempt, 3 damage on success.
  - Cunning Distraction as an AoO-exempt Evade event that automatically evades all enemies at Wendy's location.
  - "Look what I found!" in the after-fail window for failed investigate tests by 2 or less.
  - Survival Instinct's optional disengage-other-enemies and optional connecting move after a successful evasion attempt.
- Extended fuzz zone invariants to recognize event cards held in active-test limbo until their event skill test resolves.
- Added focused V5 regression coverage in `tests/test_phase_v5.py`.

## Flagged

- `01014 Wendy's Amulet`: the V5 spec summary lists traits as `Accessory, Relic`, but vendored JSON has slot `Accessory` and traits `Item. Relic.` I followed JSON.

## Tests

- `./ahlcg new --investigator roland --run /private/tmp/ahlcg-v5-smoke-roland`: passed.
- `./ahlcg new --investigator daisy --run /private/tmp/ahlcg-v5-smoke-daisy`: passed.
- `./ahlcg new --investigator skids --run /private/tmp/ahlcg-v5-smoke-skids`: passed.
- `./ahlcg new --investigator agnes --run /private/tmp/ahlcg-v5-smoke-agnes`: passed.
- `./ahlcg new --investigator wendy --run /private/tmp/ahlcg-v5-smoke-wendy`: passed.
- `python3 -m unittest discover -s tests`: passed, 133 tests.
- `python3 -m arkham.fuzz --games 50`: passed, `no_resolution: 50`.
- `python3 -m arkham.fuzz --games 50 --investigator wendy`: passed, `no_resolution: 50`.
