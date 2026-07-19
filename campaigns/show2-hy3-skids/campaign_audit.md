Now let me look up the cards in the decks to verify legality, and check the run metadata.
Signatures confirmed (01010 On the Lam, 01011 Hospital Debts). Now let me check card levels for XP costing, and inspect the transcripts for continuity.
Now let me trace the continuity facts in each run more thoroughly — got-away cultist spawns in run 3, Ghoul Priest in run 2's deck, and run 1's outcomes.
The timeline holds initial states. Let me extract the key setup facts from all three runs systematically.
Run 2's 24-card deck = 23 base + Ghoul Priest ✓. For run 3's 32, I need the Return DB baseline. Let me check other DB runs in the repo for comparison, and whether got-away cultists spawn in DB elsewhere.
Baseline Return DB deck = 31; our run 3 = 32 = 31 + Ghoul Priest ✓. Now check a comparison run with got-away cultists for spawn/doom behavior.
Let me verify the baseline Skids starter deck against other campaigns' deck-1 (before any swaps) to validate the free swap.
Let me verify the victory-point cards and the campaign summary.
Final cross-checks: run-to-deck binding (upgraded Beat Cop present in runs 2-3, absent in run 1; Lita absent in run 1 deck, present in 2-3).
AUDIT CLEAN

All three dimensions reconcile against the campaign guide, RR, and card text. Verification summary:

**1. XP ledger** — consistent at every step, never negative.
- S1 (Gathering, no_resolution): VP 2 (Ghoul from the Depths V1 + Ghoul Pits V1) + 2 insight bonus (campaign guide "If no resolution was reached") − 2 Hospital Debts (in threat area with 0/6 resources at game end, per its printed Forced) = **2** = result.xp = campaign.xp_earned ✓
- S2 (MM, R1 via defeat): VP 2 (Alma Hill V1 + Northside V1) + 0 (MM has no resolution bonus) − 2 Hospital Debts (0 banked) = **0** ✓
- S3 (DB, no_resolution): VP 0 − 2 → recorded 0 (unspent was already 0; immaterial) ✓
- Sole purchase (deck-1→deck-2): Beat Cop(0) 01018 → Beat Cop(2) 01028, same-title upgrade, cost = level difference 2 (min 1) = **2 XP**. xp_earned_total 2 = xp_spent_total 2, xp_unspent 0 ✓

**2. Deck legality** — deck-1 = 30 counted + On the Lam/Hospital Debts + Mob Enforcer (33); exactly one recorded free opening swap (First Aid in, Knife out; First Aid is Guardian 0, within Skids's Guardian 0–2). deck-2/deck-3 = 30 counted + 2 sig + 1 weakness + Lita (34 physical; Lita exempt from the 30). Max 2/title across levels holds (Beat Cop 0×1 + 2×1). All cards Rogue/Guardian ≤2/Neutral. Signatures and weakness never removed; Lita persists; Psychosis (01099, gained in DB per its agenda effect, entered threat area R4) is recorded in campaign weaknesses with no later deck required. Instantiated physical deck totals in each run match (33/34/34).

**3. Continuity** — all facts flow correctly:
- Trauma: +1M (S1 horror defeat, hor 7/6) → run 2 starts hor1; +1P (S2 simultaneous defeat, player chose physical) → run 3 starts dmg1/hor1; +1P (S3 damage defeat, dmg 8/8) → final P2/M1 = sum of deltas ✓
- House standing → run 2 begins at Your House; Ghoul Priest alive → shuffled into MM deck (24 = 23+1) and DB deck (32 = 31+1, baseline confirmed against 29 standalone DB runs at 31)
- 5 cultists got away → 3 doom on DB agenda 1a, exact per the campaign-guide tier table (5–6 names → 3 doom); past_midnight false → no opening-hand discard; elderthing token added (logged, present in the 17-token bag, recorded in chaos_bag_additions)
- Got-away cultist spawns in DB ride the act-1 advance (confirmed pattern in show-fable-skids-3); act 1 never advanced in run 3, so no spawns — correct
- MM endgame: agenda 2 sat at 8/8 but enemy doom only advances at 1.3 (#35 behavior); defeat in the enemy phase came first → R1, past_midnight false ✓
- Lita earned at S1's no-resolution, included only from deck-2; Skids killed by DB no-resolution ("each surviving investigator is killed") → killed_investigators [skids], phase complete, next null, never returns
- Run binding: seeds 940301–03, chronological, runs inside the campaign dir — no foreign-lane ingestion

Noted but not re-reported (known adjudications): the duplicate `GAME OVER` line at run 3's defeat (#119).
