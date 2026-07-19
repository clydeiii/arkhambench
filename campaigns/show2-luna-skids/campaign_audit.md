Now let me read the rules docs and look up all the cards in the decks.
The card tool doesn't display level. Let me check its options to find level output:
Let me read the Gathering's no-resolution text (page 1-2 of the PDF) to ground the scenario-1 XP math:
All checks complete. Every number reconciles against the campaign guide PDF, the Rules Reference, and exact card text. Two suspicions I chased down refuted themselves against primary sources (the 3-vs-5 doom question is exactly what the guide's table prescribes; the "missing" sixth cultist doesn't exist in the Return roster).

## AUDIT CLEAN

**Campaign:** show2-luna-skids (Return to NotZ, standard, seed 9403) — Gathering no_resolution → MM R1 → DB no_resolution, Skids killed in the finale.

**1. XP LEDGER — consistent at every step**
- S1 (Gathering, no_resolution): guide grants VP + 2 insight + Lita to lead. VP 1 + 2 − 2 (Hospital Debts, verified in threat area at game end with 0 resources, `<b>Forced</b>`: fewer than 6 → "earn 2 fewer experience") = **1** ✓ result/campaign agree.
- S2 (MM, R1 — correct resolution for a defeat per "If no resolution… read R1"): VP-only per guide. 1 − 2 (Debts again in threat, 0 resources) → floored to **0** ✓ (XP cannot be negative).
- S3 (DB, no_resolution): block carries no XP line; VP 0 − 2 (Debts in threat with **5** resources — still <6, penalty legit) → **0** ✓.
- Purchase ledger (deck-1→deck-2): Leo De Luca (01048, level 0) → Leo De Luca (01054, level 1) — same-title upgrade, cost = level difference 1, min 1 = **1 XP**, affordable from the 1 XP banked. deck-2→deck-3: no change (0 XP available). Totals: earned 1, spent 1, unspent 0; never negative ✓. Four pre-campaign `deckbuild_swaps` are all level-0↔level-0, free per the guide ✓.

**2. DECK LEGALITY OVER TIME — all three decks pass**
- deck-1/2/3 each have exactly **30 counted cards** (physical 33/34/34, matching in-game `d28`/`d29`/`d29` status lines after the 5-card openers). Signatures (01010, 01011) and basic weakness 01101 present in all three and never removed. Lita (01117) absent from deck-1, present from deck-2 on — earned in S1, included pre-S2, exempt from the 30-count ✓. Max 2/title respected (Leo never exceeds 1 copy). Class access: all Guardian cards level 0 (≤2 ✓), Leo(1) within Rogue 0–5 ✓, neutrals 0 ✓. S3-earned Paranoia (01097) persists into the final campaign deck's weaknesses ✓.

**3. CONTINUITY — all flows verified**
- Trauma: S1 defeat at horror 6/6 → +1 mental; S2 opens `hor1/6` ✓. S2 defeat at damage 8/8 → +1 physical; S3 opens `dmg1/8 hor1/6` ✓. Totals 1M/1P = sum of deltas ✓.
- House standing → MM start at Your House ✓; Ghoul Priest alive → present in both scenarios' `inputs` (never surfaced in 5/7 encounter draws — consistent; shuffle execution itself is hidden-state, no contradicting evidence).
- Cultists: interrogated [Billy Cooper] = the victory display's cult07 ✓; got-away = the 4 remaining Return-roster uniques + The Masked Hunter (game ended at Agenda **stage 1**, satisfying R1's explicit "If it is Agenda 1" clause) = 5 names ✓ → DB table: "exactly 5 or 6 names → place **3 doom** on Agenda 1a" — engine logged and placed exactly 3 ✓.
- past_midnight correctly false (midnight never struck) → no opening-hand discard in DB ✓; elder-thing token added unconditionally per guide ✓ (logged, flagged, recorded). Arkham succumbed + Skids killed per DB no-resolution ✓; killed investigator never returns — campaign `complete`, `next: null`, no deck-4, `killed_investigators: ["skids"]` ✓. MM-era log fields survived DB recording (the ledger-25 gating fix working) ✓.

No rules-enforcement defects found in the campaign layer.
