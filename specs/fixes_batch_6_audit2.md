# Fixes batch 6 — findings from transcript-audit pass #2 (GPT-5.5 auditing Haiku)

Read the audits (bench/haiku45-audit2/game-0{1,2,3}/audit.md) and
specs/bug_adjudications.md. Engine + tests only. This is the last batch before the
main benchmark — keep changes tight and fully tested.

## 1. Card resource costs are paid at initiation, BEFORE attacks of opportunity

RR Appendix I: announce → pay ALL costs (actions AND resources) → AoOs (for actions)
→ resolve effects. Today `execute("play")` spends the action, resolves AoOs, and only
then `play_card` pays the resource cost (audit game-01: Agnes played Dark Memory,
the Ghoul from the Depths' AoO resolved, resources still 10 — the 2-resource cost
was visibly unpaid during the attack). Move resource-cost payment to initiation:
deduct before `attacks_of_opportunity`, thread through the resume payload
(cost_paid style) so the effect phase does not double-charge, and refund if the play
becomes impossible mid-sequence (e.g. unique blocked — check current ordering; if
validation happens in play_card, hoist the validation to initiation too). Cover the
asset-ability paths that spend resources similarly ONLY if they share the bug —
verify Shrivelling/weapons pay ammo/charges relative to AoOs and fix if ordered
after (fight abilities are AoO-exempt, so likely moot; check parley_mob's 4-resource
cost — parley is exempt too; the generic play action is the real case).

## 2. Leo De Luca leaving play only removes the bonus action if it is still unspent

FAQ (1.10, additional actions): the first qualifying action an investigator takes
automatically uses the additional action. So if Wendy has taken ANY action this turn,
Leo's unrestricted bonus has already been consumed — discarding Leo later in the turn
must not reduce actions_remaining. Current code claws back unconditionally
(cards/player.py discard path). Condition the clawback on no qualifying action having
been taken this turn (state.turn.action_index == 0 and it is the controller's turn).
Mirror the same reasoning for Daisy's Tome action (hers is restricted — it is
consumed only by a Tome activation; her investigator card never leaves play, so no
change needed) — just verify no similar clawback exists elsewhere.

## 3. Damage/horror from one source is assigned as ONE decision, applied simultaneously

RR "Dealing Damage/Horror": determine amount, assign ALL damage and horror tokens
(soak assets may be assigned up to their remaining capacity), THEN apply
simultaneously. Audit game-02: Grave-Eater dealt 1 damage + 1 horror; the engine
assigned+applied the damage (defeating Leo at 2/2), then presented horror assignment
with Leo already gone — RAW Wendy could assign both to Leo (1+1 exactly defeats him).
Restructure start_damage_assignment/present_damage_decision: build the full
allocation first (sequence of per-token choices is fine as UI, but WITHOUT applying
or removing anything between choices — targets stay legal based on capacity math,
not on interim removal), then apply all tokens at once: soak assets absorb their
assignments, are discarded together if defeated, investigator damage/horror applies
once, defeat checks and after-horror reactions (Agnes) fire after the simultaneous
application. Preserve save/load safety mid-allocation and the existing resume
plumbing. Update every test that assumed sequential application.

## Adjudicated, do NOT change (for context)

Audit game-03's Bathroom-timing finding was ruled correct-as-implemented: firing the
Forced on the FINAL token (after Wendy's possible cancel-and-redraw) is the right
cancellation semantics, and no reachable state reads actions_remaining between
reveal and resolution.

## Definition of done

Full suite green; fuzz with invariants 50 core + 50 return + 25 × each non-Roland
investigator on return; replay corpus divergences attributable to these fixes only,
listed in specs/fixes_batch_6_report.md. Do not git commit.
