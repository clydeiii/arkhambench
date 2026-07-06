# Fixes batch 10 — hard-difficulty playtest round (ledger 49-54)

Six adjudicated items (evidence in specs/bug_adjudications.md 49-54). One regression
test each; suite green (295 now); 6-scenario fuzz matrix; FIXED ledger notes;
batch-10 section in specs/phase_c3_report.md.

1. (49) On Wings of Darkness: damage/horror assignment resolves BEFORE the
   disengage+move ("Then" ordering).
2. (50) Every investigate-type skill test (basic action, Flashlight, Burglary, any
   card-driven Investigate) derives its skill from the scenario investigation-skill
   hook (Cliffside agility / Old House willpower / Tangled Thicket combat).
3. (51) Search-and-draw effects present a choice when 2+ DISTINCT eligible cards
   exist (by name): Gathering hard-skull Ghoul search, DB hard-skull Monster
   search, Mysterious Chanting, Mask of Umordhoth, and any other search helpers.
   Single-candidate searches stay automatic.
4. (52) Implement Offer of Power (01178) fully: choose one — draw 2 player cards
   AND place 2 doom on the current agenda (explicit can-advance), OR take 2 horror.
   Then SWEEP: enumerate every card code composable into any of the six scenarios'
   encounter decks (incl. agents sets, Ghoul Priest, got-away spawns) and assert in
   a new test that each resolves through a real handler, never the placeholder
   path. Implement anything else the sweep exposes and list it in the report.
5. (53) The AoO (and enemy-phase) attacker queues must include EACH engaged ready
   enemy instance — no per-code collapsing. Test: two engaged Grave-Eaters -> two
   attacks.
6. (54) Simultaneous defeat (damage >= health AND horror >= sanity in the same
   assignment): present the trauma-type choice (solo decision), record exactly one
   trauma. Scenario-explicit kill flags (DB no-resolution) unaffected.
