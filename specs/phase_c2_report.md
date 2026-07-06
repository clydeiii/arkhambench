# Phase C2 Report — Campaign Mode and XP Upgrades

## Built

- Added `./ahlcg campaign ...`:
  - `new`, `status`, `next`, `record`, `lita`, and `replace`.
  - Persistent `campaign.json`, `.current_campaign`, scenario run directories, deterministic
    per-scenario seeds, campaign deck materialization, trauma carryover, Lita choice,
    killed-investigator replacement, and completion summary writing.
- Added `./ahlcg upgrade ...`:
  - `options`, `buy`, `remove`, and `done`.
  - XP banking, same-title replacement pricing, new-card pricing, 30-card invariant,
    2-per-title cap across levels, class/level legality, and protected signatures,
    weaknesses, and story assets.
- Added purchasable XP pool registration for all requested C2 cards.
- Added implemented behavior hooks for the C2 card pool where the current engine can
  model the interaction:
  - Extra Ammunition, Police Badge, Shotgun, Disc of Itzamna, Encyclopedia, Cryptic
    Research, Cat Burglar, Sure Gamble, Hot Streak(2/4), Mind Wipe(1/3), Book of
    Shadows, Grotesque Statue, Aquinnah(1), Close Call, Will to Survive, Bulletproof
    Vest, Elder Sign Amulet.
  - Upgraded variants reuse existing base-card paths where appropriate: Beat Cop(2),
    Magnifying Glass(1), Leo De Luca(1), Blinding Light(2), Lucky!(2), upgraded talents,
    Dynamite Blast(2), Barricade(3), Rabbit's Foot(3).
- Added The Devourer Below scenario adapter stub. It raises:
  - `The Devourer Below is not implemented until phase C3`
- Added `docs_agent/campaign_guide.md` and linked it from `docs_agent/playing_guide.md`.
- Campaign run `mission.md` now includes campaign context: scenario number, carried
  trauma, unspent XP, and relevant campaign log facts.

## Deviations / Limits

- Arbitrary non-campaign custom deck files still reject XP cards for backward-compatible
  starter/custom deck validation. Campaign materialized decks include an explicit
  `campaign_deck` marker and can contain purchased XP cards.
- The Devourer Below is intentionally not playable in C2.
- Multi-investigator targeting text is resolved as solo targeting where applicable.
- Mind Wipe is implemented through engine-facing effects: blanked enemy text disables
  modeled keywords/text hooks, and Mind Wipe(3) also reduces enemy damage/horror by 1.
- Grotesque Statue uses the engine RNG to reveal two tokens and presents a choice; the
  ignored token is not resolved.

## JSON / Spec Conflict

- Shotgun `01029`: phase C2 notes say max 6 damage, but `data/cards/core.json` says
  max 5. Implementation follows the card JSON authority and caps Shotgun damage at 5.

## Tests

- Before C2 edits: existing suite target was 213 tests.
- After implementation:

```
python3 -m unittest discover -s tests
Ran 213 tests in 1.753s
OK
```

- Additional smoke checks:
  - `campaign new -> status -> next` creates a Return to The Gathering run with campaign
    deck and mission context.
  - Synthetic `campaign record` moves to upgrade phase, carries XP/trauma/log facts, and
    `upgrade options` lists legal purchases.

## Test battery

- Added `tests/test_phase_c2_campaign.py` covering the spec's campaign lifecycle, XP
  math, deck legality named cases, Roland 6 XP options-list golden, Lita
  inclusion/transfer, killed-investigator replacement, earned weakness persistence into
  the next scenario deck, and master-seed determinism.
- Added `tests/test_phase_c2_xp_cards.py` covering behavior for the C2 XP card pool:
  Shotgun, Sure Gamble, Will to Survive, Aquinnah, Disc of Itzamna, Grotesque Statue,
  Police Badge, Close Call, Bulletproof Vest, Elder Sign Amulet, Cryptic Research,
  Beat Cop(2), Lucky!(2), Leo De Luca(1), Dynamite Blast(2), Mind Wipe(1/3),
  Encyclopedia, Book of Shadows, Cat Burglar, Hot Streak(2/4), Extra Ammunition,
  upgraded talents, Magnifying Glass(1), Blinding Light(2), and Rabbit's Foot(3).
- Bug fixed while adding tests: Shotgun (`01029`) now spends 1 ammo when used for an
  asset fight; it previously calculated damage but left ammo unchanged.
- Final verification:

```
python3 -m unittest discover -s tests
Ran 239 tests in 1.724s
OK
```

## Fixes batch 1

- Fixed carried trauma so it applies as starting damage/horror only; per-scenario
  `state.trauma`, result trauma, score, and campaign recording now track only new
  trauma earned in that scenario.
- Replaced damage/horror and summary-string death heuristics with explicit
  `investigator_killed` / `investigator_insane` result flags plus accumulated-trauma
  thresholds against printed health/sanity.
- Corrected The Gathering Lita campaign log states: R2 records `not_earned`, R3
  records `forced_to_find_others`, and R3 still marks Lita earned for the replacement.
- Added replacement guards for killed investigators and selecting the still-current
  investigator.
- Added record-time scenario mismatch protection and preserved lifetime
  `xp_spent_total` when a replacement is required.
- Upgrade options now list legal but unaffordable purchases with `affordable: false`;
  the CLI annotates those rows while `buy` still rejects insufficient XP.
- Added regressions for all six review findings.
- Final verification after fixes:

```
python3 -m unittest discover -s tests
Ran 246 tests in 1.819s
OK
```
