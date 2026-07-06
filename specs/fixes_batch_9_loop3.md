# Fixes batch 9 — playtest loop round 3 (ledger 46-48)

Three adjudicated findings (evidence in specs/bug_adjudications.md). One regression
test each; suite green (290 now); 6-scenario fuzz matrix; FIXED notes on the ledger;
append batch-9 section to specs/phase_c3_report.md.

## 1. Activate-ability costs pay at initiation, before AoOs (entry 46)

Extend the batch-6 cost-ordering fix from card plays to ALL activate abilities with
non-action costs: act abilities (cultist-deck 2-clue spend), location abilities
(Museum 2 horror, Northside 5 resources, Warehouse discard, Victoria/Peter/Herman
parley costs are parleys - no AoO - but their costs should still pay at initiation),
asset abilities with costs. Sequence per RR Appendix I: declare -> pay costs -> AoOs
-> effect. If paying the cost defeats the investigator (Museum horror), the game ends
before the effect. Tests: cultist-draw clue spend precedes the AoO in the event
stream; Museum horror at 4/6 sanity defeats before clue gain and before AoOs resolve.

## 2. Yithian Observer forced discard (entry 47)

When Yithian Observer attacks (enemy phase or AoO): discard 1 random card from hand
BEFORE the attack damage/horror is dealt; if hand is empty, the attack deals +1
damage and +1 horror. Tests: both branches.

## 3. Immediate spawn engagement (entry 48)

A ready non-Aloof enemy spawning at the investigator's location engages at the spawn
resolution point, before subsequent queued effects (agenda advances, further
encounter resolutions, spawn-location decisions for other cards). Verify the fix
covers agenda-back spawns (The Arkham Woods dig) and mid-mythos multi-card chains.
Test: agenda 1->2 dig spawns a Monster at Main Path with the investigator there ->
engagement event immediately follows the spawn event, before any later decision.
