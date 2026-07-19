Now let me look at the rules reference and look up all the cards involved in the decks.
The card tool doesn't show levels directly — let me check for a flag, look up the remaining deck cards, and read the campaign summary and run metadata.
The meta files are gold — they corroborate trauma and campaign-log flow. Now I need the level of 01069 (Blinding Light). Let me check the mission decks and run state for level info.
Now let me check the scenario-reference/rules for the campaign-log setup effects, and inspect the run transcripts' setup sections for continuity.
Setup continuity checks out so far. Let me read the scenario reference for the campaign-guide setup tables (got-away doom, past midnight) and the playing guide.
Let me read the playing guide (may list card levels/upgrade costs) and check the remaining continuity facts in the transcripts.
Let me check the hidden state blobs (setup-time composition) and the agenda/act codes in run 2.
The transcripts redact the encounter deck. Let me verify the Ghoul Priest shuffle in DB via deck-size arithmetic across all campaigns' Devourer Below runs (priest-alive vs priest-dead).
The remaining+drawn metric is polluted by searches/spawns, so it can't isolate the priest. Let me check whether any Devourer Below game actually drew the Ghoul Priest from its encounter deck (proving the DB shuffle path works), and confirm run 3's encounter draws.
All continuity threads check out. One last verification — the elder-thing token in run 3's actual chaos bag, and run-3's final investigator state.
**AUDIT CLEAN** — campaigns/show2-hy3-daisy (Return to Night of the Zealot, Daisy Walker, standard, seed 9402)

All three dimensions verified against campaign.json, deck-1/2/3.json, the three run result.json/meta.json/state.json files, and the transcripts' setup sections.

**1. XP LEDGER — consistent at every step, never negative**
- S1 (Return Gathering, no_resolution): VP 1 + 2 insight = **3 XP** ✓ (campaign guide; per adjudication #2).
- S2 (Return MM, R1): VP 0, and MM has no resolution XP bonus (scenario_reference "Scoring") = **0 XP** ✓.
- S3 (Return DB, no_resolution): VP 0; no-resolution kills the investigator (per adjudication #54) = **0 XP** ✓.
- Totals: earned 3 = 3+0+0 ✓; spent 3; unspent 0 = earned − spent ✓. meta.json shows xp_unspent 0 entering S2 and S3 ✓.
- Purchase reconstruction (deck-1→2): Magnifying Glass(0)→(1) and Blinding Light(0)→(1), two same-title upgrades at min-1 cost = 2 XP visible vs 3 XP recorded. The 1-XP residue is the adjudication-#116 class (net-zero churn purchases are invisible to deck-diff reconstruction; this campaign predates the adopted purchase-ledger improvement). Not re-reported per instructions. deck-2→3 unchanged with 0 XP earned ✓.

**2. DECK LEGALITY — all three decks legal**
- deck-1: 30 counted (15×2) + Daisy's Tote Bag + The Necronomicon + Paranoia (fixed basic weakness) = 33 ✓ (transcript h5+d28). deck-2/3: 30 counted + signatures + Paranoia + Lita Chantler (story asset, exempt from count per campaign guide) = 34 ✓ (transcript h5+d29; arithmetic per adjudication #123).
- Max 2 copies by title across levels: Magnifying Glass 01030+01040=2 ✓, Blinding Light 01066+01069=2 ✓.
- Access (Seeker 0-5 / Mystic 0-2 / Neutral 0-5, per 01002 card back): all cards in-access — highest cards are level 1 (Magnifying Glass 1, Blinding Light 1, Ward of Protection — Mystic ≤2) ✓.
- Free deckbuild swaps all level-0 (2×Knife, 2×Scrying out; 2×Magnifying Glass, 2×Deduction in) ✓. Signatures never removed; Paranoia in all three decks; Hypochondria (earned mid-S3 per result-3 `weakness_gained`) correctly absent from deck-3 and persisted in the final campaign deck ✓; Lita appears only from deck-2, after being earned in S1 ✓.

**3. CONTINUITY — all campaign-log facts flowed correctly**
- Trauma 0→1→2→3 physical; S2 transcript starts `dmg1/5`, S3 starts `dmg2/5` ✓; final trauma {3 physical, 0 mental} ✓.
- House standing → S2 starts at Your House ✓. Ghoul Priest alive → shuffled into the MM encounter deck: 23+1 cards −3 drawn = 21, an exact deck-count reconciliation, and it spawned (engaged with Daisy, post-batch-16 behavior) ✓; in DB it simply wasn't among the 4 drawn encounter cards (input flag present; the DB shuffle path is demonstrably working in sibling campaigns' DB games where the priest is drawn as an encounter card).
- 6 cultists got away (5 cultist-deck members + the set-aside Masked Hunter; enemies_defeated 0, nothing in the victory display) → 3 setup doom on agenda 1a per the campaign-guide table ✓ (logged; per adjudication #45); act-1 never advanced so no got-away respawns were owed.
- past_midnight false (agenda ended at stage 1) → no opening-hand discard in S3 ✓. Elder-thing token added unconditionally (per adjudication #110): logged at setup and physically present in run-3's chaos bag ✓.
- Daisy killed by DB no-resolution → `killed_investigators: ["daisy"]`, campaign `phase: complete`, no deck-4 — she never returns ✓. arkham_succumbed recorded ✓; xp_unspent already 0 at death (per adjudication #111 design).

No campaign-layer rules-enforcement defects found.
