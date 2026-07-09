# Fixes batch 12 — C7 audit wave (ledger 86–105)

Evidence and verdicts: specs/bug_adjudications.md entries 86–106. One regression
test per item (except where noted); full suite must stay green; run the 6-scenario
fuzz matrix after. Do NOT git commit. Card text ground truth: data/cards/*.json.

1. (86) Alma Hill (50046) parley: convert the synchronous 3-draw loop
   (the_midnight_masks.py parley_cultist) into a resumable sequence — draw one
   encounter card, resume the next draw only when decision_queue, active_skill_test,
   and pending_damage are all clear (reuse the pending_mask_after_spawn/
   after_encounter_draw resume machinery; store draws-remaining + Alma id in
   state.limits). Add Alma to the victory display only after the third card fully
   resolves ("Then"). ALSO: revelation presenters (present_revelation_cancel,
   hunting_shadow, etc.) must append/queue behind, never overwrite, a non-empty
   decision_queue. Tests: 3-draw parley where draw 1 is Masked Horrors with 0-clue
   investigator (doom lands), draw 2 Hunting Shadow (damage lands), draw 3 Obscuring
   Fog (Ward prompt); and a Crypt Chill mid-test variant (Alma enters victory only
   after the test resolves).
2. (87) In actions.move() (and the parallel path near actions.py:2291), call
   engage_ready_enemies_at_roland immediately after move/reveal and BEFORE scenario
   after_enter_location hooks. Test: enter Graveyard with ready Herman → engagement
   logged before the willpower test starts.
3. (89) attach_mask_to_enemy: add place_doom: bool = True; pass False from all
   fallback-search call sites (mask_of_umordhoth no-Cultist branch,
   resolve_cultist_search_choice, pending_mask_after_spawn continuation). Test:
   fallback search attaches with NO doom; in-play attach still places 1.
4. (91) Cultist-token nearest-enemy ties (MM apply_token_aftermath +
   apply_token_reveal_effects; DB same): when >1 tied nearest, present a target
   choice (mysterious_chanting pattern); mid-test variant routes through the
   token-reaction decision channel and defers doom until answered. Tests: tie →
   decision presented; unique nearest → automatic as today.
5. (92) spawn_enemy_from_top_until (the_devourer_below.py): route the found spawn
   through spawn_enemy_resolving_forced (Disciple 50041 doom/clue choice, Acolyte
   01169 doom) instead of bare spawn_enemy; keep the agenda-1-back doom param.
   Test: act-2-back spawn of Disciple at agenda 2 with 0 clues → 1 doom on it;
   with clues → doom + clue-placement choice resolves per card.
6. (93) resolve_spawn_at_location: if spawn_enemy_resolving_forced queued a
   decision, defer the mask attach via pending_mask_after_spawn and drain it after
   the disciple choice resolves (both scenarios' resolve_scenario_choice). Test:
   mask fallback drawing a Disciple on agenda 1 → disciple decision first, then
   attach (+ no fallback doom per item 3).
7. (94) Remove can_advance=True from Corpse-Taker doom transfers
   (the_devourer_below.py:697, the_midnight_masks.py:1335). Test: transfer reaching
   threshold during enemy phase → agenda unchanged; advances at next mythos 1.3.
8. (95) Guard end_mythos_phase scenario hooks with a once-per-round limits key
   (mythos_ prefix so it purges at round start) and fire exactly once, AFTER the
   mythos_end fast window is passed (phases.py transition branch). Covers
   Corpse-Taker and Wizard of the Order. Test: mythos with Corpse-Taker + one fast
   use in the window → exactly 1 doom.
9. (96) devourer_agenda2 callback (skill_test.py ~796): if the madness-weakness
   gain queued a revelation decision, defer advance_to_agenda3 via a marker
   (Mysterious Gateway/entry-62 pattern) and advance after the decision drains.
   Test: agenda-2 failure gaining Amnesia → keep-1-card decision presented while
   still Agd2; flip afterward.
10. (97) spawn_enemy_from_top_until: replace raw `doom +=` with
    place_doom_on_enemy(..., source="Death to the Intruders") so it logs. Test:
    agenda-1-back spawn logs the doom event. (Same function as item 5 — land
    together.)
11. (98) Milan (01033): on successful investigate, queue an optional reaction
    decision ("Gain 1 resource" / "Pass") instead of auto-applying
    (skill_test.py:619-621); use the existing reaction-presentation pattern; skip
    when text-blanked. Test: choice presented; accept gains 1; pass gains 0.
12. (99) move_without_engaged_enemies: apply the Twisting Paths (01151)
    before-move hook exactly like move(); store pending move mode in limits so
    finish_twisting_paths_move resumes the effect-move (destination need not be
    connected); on fail cancel only the move (Elusive's disengage + play cost
    stand). Fixes Elusive and Cat Burglar. Tests: Elusive from Twisting Paths →
    test fires; fail → still disengaged, still at Twisting Paths, card spent.
13. (100) Great Willow (50033) after_skill_test: replace the source-string
    heuristic with an explicit marker — revelation test starters mark the active
    test with the originating encounter instance; grant the surge draw only when
    marker present + source is a treachery + investigator at 50033 (keep group
    once/round). Frozen in Fear end-of-turn test → no draw. Tests: revelation test
    success at Great Willow → 1 extra draw; FiF end-of-turn success there → none.
14. (101) heal_roland (effects.py:708-714): log actual amount healed
    (min(requested, current)) for both damage and horror branches; event amount=
    field matches. Test: heal 3 at 1 damage → "healed 1".
15. (102) Token reveal sequencing: reveal base token → present when-window
    reactions (Wendy 01005, Sure Gamble) → once the token stands, apply
    location "after you reveal" extras (Lakeside 50034 etc.) with a per-test
    used-flag on the active test dict persisting across Wendy redraws (limit once
    per test). Tests: Wendy cancel offered before any extra token; redraw after a
    used extra → no second extra; extra applies to the post-redraw token when
    unused.
16. (103) actions.execute: set payload["cost_paid"] = True immediately after
    spend_action so every resume copy (AoO, damage-assignment, deferred) inherits
    it; keep the museum resume + AoO assignments as redundancy. Test: Miskatonic
    Museum (50029) ability with 3 actions → exactly 1 action spent after the
    horror assignment resumes.
17. (104) Screeching Byakhee (01175): engine-level conditional in
    enemy_fight_value/enemy_evade_value — +1/+1 while engaged with an investigator
    whose remaining sanity ≤ 4; respect mind_wiped blanking. Tests: at remaining
    sanity 4 → fight/evade 4; at 5 → 3; mind-wiped → 3.
18. (105) defeat_enemy (enemies.py:542-559): before the encounter-discard branch,
    if the instance is a player-owned weakness (player_cards.is_weakness /
    weakness code list), route to owner's discard via discard_to_owner_pile.
    Sweep discard_enemy_from_play (DB) and discard_encounter_card (MM) for the
    same check. Test: defeat Mob Enforcer (01101) → owner discard, NOT encounter
    discard; reshuffle effects can never redraw it.
