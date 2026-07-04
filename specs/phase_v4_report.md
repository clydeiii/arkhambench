# Phase V4 Report

## Built

- Registered Agnes Baker's killbray deck cards: `01012`, `01013`, `01058`, `01059`, `01060`, `01062`, `01063`, `01064`, `01067`, `01072`, `01074`, and `01076`.
- Implemented Agnes signature cards:
  - Heirloom of Hyperborea optional reaction after Spell card plays.
  - Dark Memory as a player event weakness in hand, with playable doom placement and repeated end-of-turn forced horror while held.
- Implemented Mystic/Survivor assets and events:
  - Forbidden Knowledge secrets, fast horror/resource ability, and discard at zero secrets.
  - Holy Rosary willpower bonus and sanity soak.
  - Shrivelling charge-based willpower Fight action, +1 damage, symbol/autofail horror using the existing symbol-watch timing.
  - Arcane Studies willpower/intellect pre-reveal boosts.
  - Arcane Initiate doom on enter and fast top-3 Spell search/shuffle.
  - Drawn to the Flame encounter-first deferred resolution, including Ward windows, then 2 clue discovery.
  - Fearless success horror heal.
  - Leather Coat health soak.
  - Baseball Bat two-hand slot use, +2 combat/+1 damage Fight, and post-attack skull/autofail discard.
  - Stray Cat fast automatic evasion for non-Elite enemies at Agnes's location.
- Extended shared systems for V4 needs:
  - Accessory and Body slot enforcement.
  - Hand slot widths, including `Hand x2`.
  - Soak targets for any asset with health/sanity, not only Ally assets.
  - Deferred "after encounter draw" continuation for event effects that must wait for encounter resolution.

## Flagged

- Metadata summary mismatch: the V4 spec describes Heirloom of Hyperborea as "Accessory, Relic"; vendored JSON has slot `Accessory` and traits `Item. Relic.` I followed JSON. No behavior conflict.
- No RR/JSON conflict found for Dark Memory's player-event weakness handling; RR says player-card weaknesses are added to hand after any Revelation effects, and Dark Memory has no Revelation effect.

## Tests

- `./ahlcg new --investigator agnes --run /private/tmp/ahlcg-agnes-smoke`: passed.
- `python3 -m unittest discover -s tests`: passed, 125 tests.
- `python3 -m arkham.fuzz --games 50`: passed, `no_resolution: 50`.
- `python3 -m arkham.fuzz --games 50 --investigator agnes`: passed, `no_resolution: 50`.
