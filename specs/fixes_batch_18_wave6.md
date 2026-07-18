# Fixes batch 18 — ledger 126-128 (K3 round 5)

Tests in tests/test_fixes_batch_18.py. Full suite green. Do not touch
campaigns/, bench/, notebooks/, viewer/.

## Fix 1 — ledger 126: add the two missing framework fast windows

arkham/phases.py:
(a) upkeep 4.1: at the START of run_upkeep_phase, before the ready/draw/
resource steps, offer present_fast_window(state, "upkeep_start",
during_turn=False); return if queued (the upkeep_done idempotency guard must
NOT be set before the window resolves — order carefully so re-entry after the
window pass runs the steps exactly once).
(b) enemy-phase end 3.3→3.4: after all engaged-enemy attacks resolve and
before the scenario end_enemy_phase hooks, offer
present_fast_window(state, "enemy_post", during_turn=False).
Both use the existing fastwin: guard-key mechanics (auto-skip when no legal
options; keys cleared at round start — add the new boundary keys to the
round-start limits filter if the existing fastwin: prefix filter doesn't
already cover them).

Tests (integration through advance_until_decision): with a ready
Forbidden Knowledge (01058) holding secrets in play: (a) window presented at
upkeep start, using it moves a secret to resources and takes 1 horror, then
upkeep steps run exactly once; (b) window presented after the last enemy
attack, before agenda-3/scenario end-of-phase moves; (c) with no legal fast
options both windows auto-skip silently; (d) regression: upkeep steps do not
double-run after a hand-size discard decision (existing upkeep_done guard).

## Fix 2 — ledger 128: halt resolution at game end

arkham/effects.py Abandoned and Alone (01015) revelation (~line 108-122):
after start_damage_assignment resolves, if state.status != "in_progress",
skip the remove-discard-pile step and the zone moves (the game is over).
arkham/phases.py run_upkeep_phase: between steps (ready/draw/resource/hand
size), bail if state.status != "in_progress". Audit the OTHER weakness
revelations in the same function for the same pattern (any that apply
damage/horror then continue mutating) and guard them identically.

Tests: Wendy at horror 5/7 draws Abandoned and Alone with cards in discard →
defeat ends the game, discard pile NOT removed, no post-end resource gain,
exactly one game_end event.

## Improvement 3 — ledger 127: correct the playing guide

docs_agent/playing_guide.md: the sentence claiming every non-exempt action
provokes "including PLAYING A CARD" must be corrected: playing an event with
a bold Fight/Evade designator (Backstab, Cunning Distraction, Blinding
Light) is taking a fight/evade action and does NOT provoke; playing other
cards does. Keep it one or two sentences, agent-readable.

## Fix 4 — ledger 129: single log line for Roland's defeat reaction

arkham/enemies.py resolve_enemy_defeated_reaction (~line 650): the
discover_clue call already logs "discovered 1 clue."; the roland_reaction
log_event duplicates it. Emit ONE line with the reaction-specific wording
(suppress discover_clue's generic line for this call or drop the second —
match how other reaction discoveries log). Test: defeat with Roland reaction
-> exactly one discovery log line, one clue granted.

## Fix 5 — ledger 130: Gathering agenda b-side completes before advance

arkham/scenarios/the_gathering.py:
(a) Agenda 1 -> 2: present the 1b choice while agenda 1 is still current;
apply the chosen effect (horror/discard); THEN clear doom, set agenda 2,
log "Agenda advanced". (Doom clearing timing: RR removes doom as part of the
advance — keep clear_all_doom with the advance, after the b-side effect.)
(b) Agenda 2 -> 3 (advance_agenda_2): resolve the full b-side (shuffle, dig,
draw/spawn/engage the Ghoul via its revelation) BEFORE setting state.agenda
to They're Getting Out! and logging the advance.
Mind decision-queue re-entrancy: the 1b choice resolution path
(finish_mythos_after_agenda_choice) must still run mythos continuation
exactly once. Tests: transcripts show b-side effect lines strictly before
"Agenda advanced" for both advances; status snapshots during the 1b decision
still show Agd1; mythos continues correctly after.

## Improvement 6 — ledger 132: instance ids on doom/attachment log lines

arkham/log.py render_event: doom_placed and treachery_attached lines must
include the target instance id when data.enemy is present, matching the
existing spawn/engage/attack rendering (e.g. "Placed 1 doom on Disciple of
the Devourer [ec0006] (Mask of Umôrdhoth)."). the_midnight_masks.py
attach_mask_to_enemy: name the target enemy + id instead of "a Cultist
enemy". Tests: rendered lines carry the id; jsonl unchanged.
