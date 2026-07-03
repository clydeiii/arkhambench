# Fix batch 1 report

Implemented all 8 requested fixes from `specs/fixes_batch_1.md`.

## Changes

1. Prevented duplicate mythos encounter draws after an agenda-advance choice by checking `mythos_encounter_drawn:{round}` before setting it in `finish_mythos_after_agenda_choice`.
2. Removed mid-game `ArkhamRng(...)` construction from scenario flows. Agenda 2 and hard/expert skull ghoul search now use the live game RNG, with RNG threaded through action, attack, damage, and skill-test callbacks where those effects can occur.
3. Reworked attacks of opportunity to exempt only the targeted fight/evade/parley enemy. `engage` now provokes from already-engaged ready enemies; pass/advance-act/resign remain non-provoking; fast abilities remain free.
4. Added shared effective action-cost calculation for legal-action generation and execution. Frozen in Fear unaffordable move/fight/evade actions are not offered, and `spend_action` raises `EngineError` if the full cost cannot be paid.
5. Fixed agenda advancement doom handling so agenda doom is discarded on flip instead of carrying surplus. The Gathering still checks total doom in play, and doom on enemies/cards remains.
6. Added rule-event emit-time stamping via `RuleEventList`; log append now uses event-local round/phase when present.
7. Updated autofail skill-test output so failure margin is non-negative and the message says `failure (autofail)`.
8. Improved state rendering with `Card Name (instance_id)` labels for listed cards, threat area output, named attachments, enemy damage/status in locations, and ally damage/horror in play area.

## Tests

Added `tests/test_fixes_batch_1.py` with focused regressions for all fixes.

Verification run:

```text
python3 -m unittest discover -s tests
Ran 73 tests in 1.232s
OK

python3 -m arkham.fuzz --games 100
R3: 1
no_resolution: 99
```
