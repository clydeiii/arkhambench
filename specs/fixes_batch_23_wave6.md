# Fixes batch 23 — ledger 146-149, 151 (K3 round 15)

Tests in tests/test_fixes_batch_23.py. Full suite green. Do not touch
campaigns/, bench/, notebooks/, viewer/.

## Fix 1 — 147: engaged aloof enemies DO make attacks of opportunity
actions.py aoo_attackers (~line 771): remove the `not is_aloof(...)`
filter (the iteration is already engaged-only; Aloof restricts
engagement/being-attacked while unengaged, nothing about AoOs). Verify
fight-target generation for unengaged aloof (the #66 behavior) is
untouched. Test: mask-aloof engaged ready enemy + play action -> AoO fires.

## Fix 2 — 148: elder-sign rider honors extra tokens
skill_test.py apply_elder_sign_success (~1211): trigger when eldersign is
the base token OR in result.extra_tokens (reuse the revealed_symbol
helper). Same fix for the Wendy's Amulet elder-sign auto-success gate
(~461). Tests: extra-token elder sign pays Skids's 2 resources on
success; Wendy auto-succeeds on an extra-token elder sign.

## Fix 3 — 151: pending damage assignments queue, never clobber
effects.py start_damage_assignment (~490): if pending_damage is already
set, append the new assignment to a queue drained when the current
assignment completes (both the decision branch and the direct branch),
BEFORE consuming resume. Test: soak asset in play, Devourer tablet 1 dmg
+ Shrivelling 1 horror in one resolve -> both assignable, nothing lost.

## Fix 4 — 146/149: log fidelity
Obscuring Fog Forced discard: single log line (129-class dedup). Evade
success: log the enemy's exhaustion alongside the disengage. Tests:
exactly one Fog discard line; evade logs exhaust.
