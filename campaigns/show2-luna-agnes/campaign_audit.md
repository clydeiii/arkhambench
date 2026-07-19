Let me read the rules docs and look up the cards.
The card tool doesn't show levels. Let me check the rules reference and the run state files, which may carry card xp metadata.
The MM start shows `hor1/8` (mental trauma ✓) and DB start shows `dmg1 hor1` (✓) plus got-away doom 3 and elderthing token. Now I need card levels for the XP audit. Let me check the run metadata and card instances in state.json.
Run 2's log never mentions the Ghoul Priest, and run 1's never mentions Lita. Let me check whether the priest was actually shuffled into the MM encounter deck, and what acts run 1 reached.
Lita is entirely absent from run 1 despite the Parlor entering play at R4 — but in-game placement is scenario-layer. Let me pin down the exact sequence, then verify the Ghoul Priest shuffle via the hidden state.
Run 2 setup verified. Now the run 3 (Devourer Below) setup snapshot and run 1 baseline.
All three audit dimensions fully reconcile. Here is my campaign-layer audit report.

---

**Audit target:** `campaigns/show2-luna-agnes` (Return to NotZ, Agnes Baker, standard, seed 9404) — 3 legs, campaign complete.

## 1. XP LEDGER — consistent at every step

- **Leg 1 (Return to the Gathering, no_resolution):** result.json VP 2 + 2 insight bonus = **4 XP** ✓ (matches campaign-guide no-resolution text; adjudication #2 precedent). `xp_earned: 4` ✓.
- **Upgrade window 1** (deck-1 → deck-2): +1 Guts 01089 (level 0, new card = max(1,0) = **1 XP**), +1 Elder Sign Amulet 01095 (neutral level 3 — the Revised-Core sanity mirror of Bulletproof Vest(3); cost 2/4-sanity/2-icon statline is far above level-0 rate, compare Leather Coat/Holy Rosary — new card = max(1,3) = **3 XP**), −2 Leather Coat (free removals holding 30 counted), +Lita 01117 (earned story asset, free, uncounted). Total **4 XP** = xp_spent_total ✓. Independently corroborated: run-2 `meta.json` snapshots the campaign state at scenario-2 start as `xp_unspent: 0` (4 earned − 4 spent) ✓.
- **Window 2:** 0 XP earned in leg 2; deck-3 is byte-identical to deck-2 ✓ (nothing bought, nothing owed).
- **Final:** `xp_earned_total 4 = 4+0+0` ✓, `xp_spent_total 4` ✓, `xp_unspent 0` ✓; never negative at any checkpoint (run-2 meta, run-3 meta both 0) ✓.

## 2. DECK LEGALITY OVER TIME — all three decks legal

- **deck-1:** 33 physical = 30 counted + Heirloom of Hyperborea (signature) + Dark Memory (signature weakness) + Haunted (basic weakness) ✓. All pairs ≤2/title ✓. All cards within Agnes's printed options (Mystic 0–5, Survivor 0–2, Neutral 0–5) ✓.
- **Free deckbuild swaps** (recorded `deckbuild_swaps`): Ward of Protection×2 ↔ Knife×2, Lucky!×2 ↔ Stray Cat×2 — all level-0 both directions ✓.
- **deck-2/deck-3:** 34 physical = 30 counted + 2 signatures + Haunted + Lita ✓ (Lita exempt from the 30 per campaign guide; ledger #123 precedent). Signatures and weaknesses never removed across all decks ✓; Lita appears only in deck-2 onward, after being earned in leg 1 ✓.

## 3. CONTINUITY — all flows verified against transcripts/state

- **Trauma:** leg-1 horror defeat (9 ≥ 8) → +1 mental → run-2 setup `hor1/8` ✓ (meta trauma 1M/0P ✓); leg-2 damage defeat (6 ≥ 6) → +1 physical → run-3 setup `dmg1/6 hor1/8` ✓ (meta 1M/1P ✓); campaign total 1M/2P = sum of deltas ✓.
- **House standing** → run-2 starts at Your House ✓. **Ghoul Priest alive** → present in run-2 and run-3 campaign inputs ✓ (never drawn/spawned in-game; no contradiction). **6 cultists got away** → DB setup log "Setup placed 3 doom from cultists who got away" naming all six, agenda opens at doom 3/4 ✓ (campaign-guide table; #45(a) precedent; run-3 transcript audit independently reconciled the full doom ledger). **past_midnight false** → no DB opening-hand discard ✓ (leg 2 ended by defeat, midnight never struck). **Elderthing token** added ✓ (run-3 bag = 16 base + elderthing; `chaos_bag_additions` recorded; unconditional per #110). **Killed investigators:** legs 1–2 defeats correctly NOT kills; leg-3 DB no_resolution kill per printed guide (#54) → `killed_investigators: ["agnes"]` ✓; campaign ended, she never returns ✓. **Lita:** earned via leg-1 no-resolution text (#2) → `lita_earned`/`lita_in_deck` ✓, absent from deck-1, present in deck-2/3 ✓; her in-game placement never triggered in leg 1 because act 2 never advanced (consistent with #1/#120 behavior — no priest spawn either, hence "still alive" ✓).
- Campaign log fields all match the result.json chain (`ghoul_priest_alive`, `your_house_standing`, `cultists_got_away` ×6, `past_midnight: false`, `arkham_succumbed: true`). MM defeat labeled R1 is correct per printed guide p.5 (adjudication #142 — not re-reported).

**AUDIT CLEAN**
