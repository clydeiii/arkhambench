I have the campaign state, decks, and results. Now let me look up all the cards involved to verify class/level access and XP costs.
The card tool output doesn't show levels. Let me check for a level/XP field and look up the remaining deck cards.
The card display omits levels, which I need for XP verification. Let me test with a known leveled card and check what the upgrade command shows.
Card levels aren't displayed, but the campaign guide's own example confirms Extra Ammunition (01026) costs 1 XP. Now let me verify continuity signals in the run logs — starting horror, setup facts from the campaign log.
Both transcripts show correct trauma carry-over (run 2: hor1/5, run 3: hor2/5) and run 3 shows all the setup injections. Now let me verify the Ghoul Priest shuffle-in and cultist spawns.
Run 3's setup checks out (elderthing in the bag, past-midnight discards, got-away doom per the adjudicated campaign-guide table, and the double `game_end` line is known ledger #119 — do not re-report). Now let me verify the Ghoul Priest shuffle-in for run 2 and starting-horror states directly.
Starting horror continuity confirmed (0/1/2). Now I need to check whether the Ghoul Priest was actually shuffled into run 2's MM encounter deck — let me inspect the hidden state.
The hidden state is explicitly marked DO NOT READ — I'll respect that; the observable inputs (mission.md, meta.json, result.json inputs) all confirm the priest-alive flag was correctly passed. Let me run a final consolidated verification of deck counts, diffs, and the XP ledger, plus check Roland's deckbuilding line and the campaign summary.
All checks reconcile. Cover Up sat in the threat area with 2 clues when the clock struck midnight — its end-game Forced fully accounts for run 2's mental-trauma delta without a defeat.

---

**AUDIT CLEAN**

Campaign `show2-sonnet-roland` (Return to NotZ, Roland, standard, seed 9401) — campaign layer verified across all three dimensions:

**1. XP LEDGER — consistent at every step**
- S1 (Gathering, no_resolution): VP 2 + 2 insight = **4** ✓ (ledger #2)
- S2 (Midnight Masks, R2): VP 2, no bonus = **2** ✓
- S3 (Devourer Below, no_resolution): VP 0 = **0** ✓
- Upgrade window 1: 4 XP → bought Elder Sign Amulet 01095 (Neutral L3, 3 XP), removed Flashlight 01087 → 1 banked (matches run-2 meta `xp_unspent: 1`)
- Upgrade window 2: 1+2=3 XP → Extra Ammunition 01026 (1 XP, per the campaign guide's own example) out Guts 01089; Hyperawareness 50003 (Seeker L2, 2 XP) out one Barricade 01038 → 0 banked (matches run-3 meta)
- Totals: earned 6 = spent 6, unspent 0; never negative. Each purchase paired with a removal, keeping 30 counted cards.

**2. DECK LEGALITY — all three decks legal**
- deck-1/2/3: exactly 30 counted cards (33/34/34 physical; 01006+01007 signatures, 01102 basic weakness, and Lita exempt per her story-asset rule)
- Max 2 copies per title everywhere; all cards within Roland's Guardian 0–5 / Seeker 0–2 / Neutral 0–5 access (highest seeks: Hyperawareness L2 ≤ 2)
- Signatures and weakness never removed; 4 opening deckbuild swaps all L0↔L0 and class-legal; campaign final deck identical to deck-3

**3. CONTINUITY — all facts flowed correctly**
- Trauma 0→1 (S1 horror defeat, 6≥5) → run-2 start `hor1/5` → +1 (Cover Up end-game Forced, verified 2 clues on it at S2 end) → run-3 start `hor2/5` → +1 (S3 horror defeat) = 3 total ✓
- House standing → S2 starts at Your House ✓; Ghoul-Priest-alive flag passed into MM (never drawn; shuffle-in not observable without opening the sealed hidden state, which I declined to read)
- 5 got-away cultists → DB setup doom per the campaign-guide table (ledger #45 class), past-midnight → 2 opening-hand discards, elderthing token logged and present in run-3's bag only ✓
- Roland killed by DB no-resolution (ledger #54) → `killed_investigators: ["roland"]`, campaign `complete`, never returns; Lita absent from deck-1, present only after earned ✓

Known adjudications sighted and not re-reported: double `game_end` in run 3 (#119), got-away doom table (#45), Lita deck-count exemption (#123).
