# Phase V3 Report

## Built

- Registered all Skids V3 deck cards: `01010`, `01011`, `01044`, `01045`, `01047`, `01049`, `01050`, `01052`, and `01053`.
- Implemented On the Lam as a round-scoped fast event that prevents non-Elite enemies from attacking Skids, including attacks of opportunity and enemy-phase attacks. Suppressed enemies do not exhaust; Elite enemies still attack.
- Implemented Hospital Debts as a threat-area weakness with a twice-per-round fast banking ability and a game-end 2 XP penalty when fewer than 6 resources are banked. XP is floored at 0 before score is recomputed.
- Implemented Switchblade and .41 Derringer fight actions, including Derringer ammo, the +2 combat label, and succeed-by-2 bonus damage.
- Implemented Burglary as an exhausted asset action that initiates an investigate test, provokes attacks of opportunity under the engine's existing investigate behavior, and replaces clue discovery with exactly 3 resources.
- Implemented Hard Knocks as repeatable pre-reveal fast boosts for combat and agility.
- Implemented Elusive as a fast event that disengages all engaged enemies without exhausting them, then moves Skids to a selected revealed location with no enemies, ignoring connections. If no destination is eligible, it still disengages.
- Implemented Sneak Attack as a normal play action targeting only exhausted enemies at Skids' location; other ready engaged enemies make attacks of opportunity first.
- Implemented Opportunist's succeed-by-3 return-to-hand effect.
- Added focused V3 regression coverage in `tests/test_phase_v3.py`.

## Flagged

- No conflicts found between `specs/phase_v3_skids.md`, `docs_agent/rules_reference.md`, and the vendored JSON in `data/cards/`.

## Tests

- `./ahlcg new --investigator skids`: passed.
- `python3 -m unittest discover -s tests`: passed, 116 tests.
- `python3 -m arkham.fuzz --games 50`: passed, `no_resolution: 50`.
- `python3 -m arkham.fuzz --games 50 --investigator skids`: passed, `R3: 1`, `no_resolution: 49`.
