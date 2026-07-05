# Fixes batch 5 — findings from the first transcript-audit pass (Fable auditing Haiku games)

Read specs/bug_adjudications.md and the three audit reports
(bench/haiku45-audit/game-0{1,2,3}/audit.md) first. Rules authority: RR + card JSON.
Engine + tests only; flag conflicts in specs/fixes_batch_5_report.md.

## 1. CRITICAL: action effects double-execute when an AoO resolves without a decision

Mechanism (verified): `execute` spends the action → `attacks_of_opportunity` →
`attack` → `resolve_attack` → `start_damage_assignment(resume=after_attack...)`.
When no decision interposes (no dodge offered, no soak assets), damage applies
directly and the resume chain runs `actions.execute(payload)` — the effect fires
(1st). The stack then unwinds to the ORIGINAL `execute`, whose
`if state.decision_queue ...: return` guard sees an empty queue and continues to run
the effect again (2nd). Haiku game-03 R8: Take Resource + Mob Enforcer AoO → res0→res2
(two resource_gained events, seq 404/405).

Fix: once `attacks_of_opportunity` hands the continuation to the AoO/resume chain
(i.e., there were attackers), the original `execute` must unconditionally stop —
make `attacks_of_opportunity` return True when it initiated attacks (the resume chain
owns the continuation from then on), and `execute` return immediately on True.
Audit all resume entry points (`after_attack`, effects.py damage-resume, deferred_resume,
dead-attacker branch from adjudication #8) so the effect runs EXACTLY once in every
combination: {no decision, dodge decision, soak decision, defeat reaction, dead
attacker mid-queue} × {single attacker, multiple attackers}. Add tests for each cell
you can reach; at minimum: no-decision single attacker (the double-fire), soak
decision path (single fire), dead-attacker resume (single fire, existing test).

## 2. Encounter cards discarded from the threat area go to the ENCOUNTER discard

`player.discard_from_threat` routes everything to the investigator's discard pile.
RR "Discard Piles": cards return to their OWNER's discard — encounter cards belong
to the encounter deck. Route by ownership: encounter-deck cards (Frozen in Fear,
Dissonant Voices, attached treacheries discarded from threat) → encounter_discard;
player weaknesses (Cover Up, Hospital Debts, Haunted, Necronomicon) → player discard.
Sweep other discard helpers for the same conflation (attachments discarded from
locations/enemies already go to investigator.discard in some paths — check
discard_location_attachments and enemy-attachment discards too; Obscuring Fog and
Locked Door are encounter cards). Verified instance: haiku45-audit/game-01 ec0019
(Dissonant Voices, 01165) ended in investigator.discard.

## 3. Weakness Revelations fire when the card ENTERS HAND by any route

RR "Weakness": when a weakness enters an investigator's hand, resolve its revelation
immediately as if drawn. The draw path does this (resolve_player_weakness_draw); the
Research Librarian search path does NOT — The Necronomicon was fetched to hand,
sat inert, and was later randomly discarded (its "cannot leave play with horror"
never applied). Route EVERY add-to-hand through the weakness check: Research
Librarian search, Arcane Initiate spell search, Old Book of Lore draws, Scavenging
(Items only — but future-proof it), mulligan replacements are already handled
(weaknesses never dealt), upkeep/effect draws already handled — verify each.

## 4. Research Librarian: optional reaction + player chooses the Tome

Current implementation auto-fetches the first Tome in deck order with no decision.
Card: "[reaction] After Research Librarian enters play: Search your deck for a
[[Tome]] asset and add it to your hand. Shuffle your deck." — a MAY reaction, and
searches that "add" a chosen card give the searching player the choice among legal
targets. Present a decision: one option per distinct Tome found (by card name/code)
plus "Decline". Shuffle the deck afterward either way (the search looked at the deck).
Route the chosen card through the §3 weakness check (choosing The Necronomicon puts
it into play in the threat area with 3 horror — RAW consequence of fetching it).

## 5. Mulligan is a single simultaneous declaration

RR "Mulligan": one opportunity to set aside ANY NUMBER of the drawn cards, THEN an
equivalent number are drawn together, then set-aside cards shuffle back. The current
one-at-a-time flow reveals each replacement before the next choice (information RAW
does not grant). Restructure: the opening-hand decision presents toggle options
("Set aside <card>" / "Keep hand and draw replacements") accumulating a set-aside
list WITHOUT drawing; on confirm, draw all replacements at once (weaknesses still
never dealt into the opening hand), log the full before/after, shuffle set-asides
back. Update tests that assumed sequential replacement.

## 6. End-of-turn Forced effects fire AFTER the post-final-action player window

phases.py currently runs resolve_dark_memory_end_turn and start_frozen_end_turn_test
BEFORE the inv_end fast window. Per the timing chart (and adjudication #6), the
window after the last action is still DURING the turn; "at the end of your turn"
Forced effects (Frozen in Fear test, Dark Memory reveal) fire after that window
closes. Reorder: present the inv_end during-turn window first (unless
turn_forcibly_ended); when it closes (pass or exhausted options), THEN dark memory /
frozen tests, then the phase transition. Mind the fastwin guard key so the window
is not re-presented after the forced effects. If Skids buys an action in that
window, the turn continues and the end-of-turn effects defer accordingly.

## Definition of done

Full suite green; fuzz with invariants: 50 the_gathering + 50 return + 25 × each
non-Roland investigator on return, all clean; scripts/replay_corpus.py runs with
divergences attributable to these fixes only (list them in the report — the batch
changes discard destinations, librarian decisions, mulligan structure, and
end-of-turn ordering, so expect several). Write specs/fixes_batch_5_report.md.
Do not git commit.
