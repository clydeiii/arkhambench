Now let me read the rules docs, the campaign summary, and the prior audit files (to avoid re-reporting adjudicated findings).
The card output doesn't show XP levels, which I need for the purchase-cost ledger. Let me check for a verbose flag.
No level info there. Let me check the run mission files (they may list deck composition/levels) and the rules reference.
The RR confirms the XP/trauma rules. Now the NotZ campaign guide PDF (cited as the source of authority in the adjudications) and the scenario reference for the exact resolution/setup texts.
Bag verified (16 standard + elderthing = 17). Now the DB encounter-deck composition to see if 31 total cards implies the Ghoul Priest was shuffled in.
All checks are now complete. Every thread reconciled — including the two items that looked suspicious mid-audit (the "missing" Peter Warren, dissolved by the Return-MM random-removal rule; and the Masked Hunter entry, which the printed R1 text explicitly requires on Agenda 1). Full reconciliation below.

**Campaign:** show2-luna-daisy (Daisy Walker, Return to NotZ, standard, seed 9402) — 3 legs, killed in the finale.

**1. XP ledger — recomputed at every step**
- Leg 1 (Gathering, no_resolution, defeated by damage): VP = 1 (Attic in victory display, verified in state.json) + 2 insight bonus (campaign guide p.2: "2 bonus experience… hidden world of the Mythos") = **3** ✓ matches `xp_earned` 3.
- Upgrade window 1 (deck-1→2): +Bulletproof Vest 01094 (new card, level 3 → max(1,3)=**3 XP**), −Medical Texts 01035 (deck size maintained at 30 per RR). Unspent 3−3=0 ✓ corroborated by run-2 mission.md "Unspent XP: 0".
- Leg 2 (Midnight Masks, R1/resigned): XP = victory display only, no bonus (guide p.5) = Alma Hill Victory 1 = **1** ✓.
- Upgrade window 2 (deck-2→3): Magnifying Glass(1) 01040 replacing Magnifying Glass(0) 01030, level difference 1, min 1 = **1 XP**; title count 1+1=2 ✓ legal. Unspent 1−1=0 ✓ corroborated by run-3 mission.md.
- Leg 3 (Devourer Below, no_resolution): the printed no-resolution text contains no XP award (only "Arkham succumbed" + killed + loss) → **0** ✓ (VP was 0 anyway).
- Totals: earned 3+1+0=4 = `xp_earned_total` ✓; spent 3+1=4 = `xp_spent_total` ✓; `xp_unspent` 0, never negative at any step (0→3→0→1→0→0) ✓. Scenario scores (2/1/0) also match the documented XP−trauma benchmark ✓.

**2. Deck legality over time** — deck-1/2/3 each hold exactly 30 counted cards (signatures 01008/01009, weakness 01097 Paranoia, and story asset Lita 01117 excluded; verified sums). All cards are Seeker-0, Mystic-0, or Neutral — legal for Daisy; 01040 is Seeker-1, within her Seeker 0–5 access. Max 2 per title respected (deck-3: MG(0)×1 + MG(1)×1). Opening deckbuild swaps (out 2× Hyperawareness/2× Knife, in 2× MG/2× Deduction, all level 0, free, 1-for-1) are legal and exactly reflected in deck-1. Signatures present in all decks; Paranoia and The Necronomicon never removed; Lita enters only from deck-2 (earned in leg 1, story asset exempt from the 30-count — physical 34 correct, consistent with adjudication #123).

**3. Continuity**
- Trauma: leg-1 damage defeat (5/5) → +1 physical ✓; run-2 and run-3 both open at dmg1/5 ✓; leg-2 resign with no defeat → delta {0,0} ✓; leg-3 kill-by-resolution adds no trauma ✓; campaign trauma {P1,M0} = Σ deltas ✓.
- Log → setup flow: house standing → run-2 begins at Your House ✓; Ghoul Priest alive → shuffled into MM (drawn R3 — spawn defect already adjudicated #122) and registered as DB input ✓ (never drawn there); 5 got-away names → exactly 3 setup doom on DB agenda 1a per the printed 5–6 tier ✓ (logged); elderthing token added ✓ (bag verified: 16 standard + elderthing = 17) and recorded in `chaos_bag_additions` ✓; past_midnight false → no opening-hand discard ✓; got-away cultist spawns at Main Path not owed (act stayed 1 all of run 3) ✓.
- Got-away list verified name-by-name against MM R1 text: Cultist deck was 5 (8-card pool minus 3 removed unseen per Return setup — Peter Warren was legally among the removed, hence correctly absent), Alma Hill in victory display → interrogated ✓, remaining 4 cultists + "The Masked Hunter" (game ended on Agenda 1 — the printed R1 explicitly requires recording him in that case) = exactly the recorded 5 ✓.
- Killed investigator: Daisy killed by DB no-resolution ("each surviving investigator is killed") → `killed_investigators: ["daisy"]`, phase `complete`, `next: null`, no deck-4 — she never returns ✓.
- Ledger-25 class check: the DB record preserved the MM-shaped log fields (`cultists_got_away`, `past_midnight`) — the batch-7 gating fix demonstrably holding ✓.

AUDIT CLEAN
