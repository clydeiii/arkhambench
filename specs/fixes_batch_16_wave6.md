# Fixes batch 16 — ledger 122 (Ghoul Priest MM spawn override)

Single fix. Tests in tests/test_fixes_batch_16.py. Full suite green.

arkham/scenarios/the_midnight_masks.py encounter_revelation (~line 986):
delete the `code == "01116"` special case so a Ghoul Priest drawn from the
encounter deck falls through to the DEFAULT enemy-revelation path (no spawn
instruction -> spawns engaged with the drawing investigator, in their threat
area at their location, per RR "Spawn"). Verify the default path does exactly
that for 01116 (Prey - Highest combat / Hunter / Retaliate are unaffected).
Do not touch the Gathering set-aside/act-spawn path or Devourer handling.

Tests: (a) MM with ghoul_priest_alive, force 01116 to top of encounter deck,
mythos draw -> priest engaged with drawer at drawer's location; (b) Gathering
act-2b spawn still puts the set-aside priest in the Hallway unengaged;
(c) regression: another no-spawn-instruction enemy still engages drawer.
