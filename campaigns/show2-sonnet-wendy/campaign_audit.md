I'll start by exploring the campaign directory structure and reading the key files.
Now let me read the three deck files and the campaign summary:
Let me look up all the card codes involved, and read the result.json files for the three scenarios:
Let me verify card levels (XP) and Wendy's deckbuilding options:
The card text shows Wendy can take Rogue 0-2 — so Leo/Hard Knocks are legal. Now let me get card XP levels for the XP audit:
Let me check the rules reference, then cross-reference card levels via purchase ledgers in other campaigns:
Let me check how other campaigns record purchases with these card codes, to establish card levels:
I need ground truth on card levels (especially Hard Knocks 01049 and Elder Sign Amulet 01095). Let me search run artifacts and docs for level evidence:
Let me check agent notebooks for recorded upgrade prices of Elder Sign Amulet (01095):
The notebook confirms Elder Sign Amulet = 3 XP, Leo 01048 = level 0. Now let me verify continuity — check the opening of scenarios 2 and 3 for trauma carry-over and campaign-log setup effects:
Continuity looks good so far. Let me verify the Ghoul Priest and got-away cultist handling in scenarios 2 and 3:
Let me verify the endings of runs 1 and 2, the meta.json inputs, and check run-3 for got-away cultist spawns:
Run-3's transcript confirms all DB setup continuity. Let me check the scenario audits already done (scope boundaries) and verify the Ghoul Priest was shuffled into the DB encounter deck:
Let me verify run-1's opening deck counts against deck-1.json, and check run-2's setup lines + run-1's Lita earn:
All three scenario audits are complete (run-1 found the already-adjudicated #134 exploit; runs 2 and 3 CLEAN), and my campaign-layer verification is done. Everything reconciles.

## Campaign-layer audit: show2-sonnet-wendy (Return to NotZ, standard, seed 9405)

**1. XP LEDGER — verified, consistent at every step.**
- S1 (Gathering, no_resolution): VP 1 + 2 insight bonus = 3 XP (matches result.json `xp: 3`; the +2 insight rule is adjudication #2). Trauma: mental 1 (insanity defeat, hor 7/7 vs dmg 6/7 — single track).
- Upgrade window 1: deck-1→deck-2 diff is exactly −1× Pickpocketing + 1× Elder Sign Amulet (01095) + Lita (story asset, free). Amulet is level 3 → new-card cost max(1,3) = **3 XP**. Corroborated three ways: the lane notebook records "Bought Elder Sign Amulet (3XP…)", two sibling show2 campaigns charged identically, and no hidden churn is arithmetically possible (spent 3 = earned 3; any invisible ≥1-XP transaction would break equality — the #116 pattern excluded).
- S2 (Midnight Masks, R2 midnight): victory display 0, no resolution bonus → 0 XP (consistent with prior adjudicated-clean R2 audits). S3 (Devourer, no_resolution, killed): VP 0 → 0 XP.
- Sequence 0 → +3 → −3 → +0 → +0: `xp_earned_total 3 / xp_spent_total 3 / xp_unspent 0`, never negative; campaign_summary.json agrees.

**2. DECK LEGALITY — verified for all three decks.**
- Counted cards exactly 30 in deck-1/2/3; physical counts reconcile with in-game status lines (deck-1: 33 physical → h5/d28; decks-2/3: 34 physical incl. Lita → h5/d29). Lita correctly exempt from the 30-count.
- Signatures (01014/01015) present in every deck; basic weakness 01096 never removed; max 2 copies/title at every step; all cards inside Wendy's Survivor 0–5 / Rogue 0–2 / Neutral 0–5 access (all rogue cards here are level 0; Amulet is neutral level 3).
- The three free deckbuild swaps (01050←01086, 01076←01086, 01049←01078) are all level-0 and are exactly reflected in deck-1.
- Lita appears only in decks 2–3, after being earned in S1 and included (`lita_in_deck: true`). The Paranoia (01097) gained mid-S3 via agenda 2b (result-3 `weakness_gained`) correctly persisted into the final campaign deck record without retro-editing deck-3.json.

**3. CONTINUITY — verified.**
- Trauma: S1 mental +1 → run-2 opens `hor1/7`; S2 +0 → run-3 opens `hor1/7`; campaign trauma equals the sum of deltas.
- House standing → MM starts at Your House (run-2 first status line). Ghoul Priest alive → positively confirmed shuffled into the MM encounter deck (drawn as an encounter card, run-2 R4). DB: input delivered (result-3 `inputs.ghoul_priest_alive: true`); not drawn in a 4-round game — nothing observable violated.
- 6 cultists got away → 3 doom on DB agenda 1a, logged with all six names (`doom3/4` at R1). Past midnight → 2 logged opening-hand discards. Elderthing token → logged setup addition (unconditional per #110) and `chaos_bag_additions`/`elderthing_added` agree.
- Killed investigators never return: DB no-resolution kill (per #54) → `killed_investigators: ["wendy"]`, phase `complete`, no further runs.
- Score cross-check: per-scenario scores 2/0/0 = XP−trauma; `campaign_score 2` consistent.

The run-2-end harness note (run-3 momentarily resolving as the old MM run) is the previously adjudicated .current_run race class (#108/#113): the final run-3 artifacts are a complete, correctly bound Devourer game (created 11 s after run-2 ended, coherent seq-1→end log, correct result and campaign record). Not re-reported per instructions.

AUDIT CLEAN
