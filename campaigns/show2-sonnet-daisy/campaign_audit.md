I'll start by reading the campaign state and the rules documentation.
Let me check the rules directory and the campaign guide PDF for the exact Devourer Below setup text.
Only ONE cultist was ever drawn (Alma Hill) — Peter Warren should remain in the Cultist deck and count as "got away". Let me verify Peter Warren's existence/set and search the guide for related rules.
Run 3 stayed on Act 1 — no got-away spawns owed. Now let me verify the Devourer Below's no-resolution XP rule from the guide.
All three mission files carry the hardcoded DB briefing — that's adjudication #136 (known). Let me do one final card-text check on Your House (the run-2 auditor claimed a printed spawn Forced; adjudication #122 says otherwise — checking for my own completeness, not to re-report).
Your House (01124) does carry that printed Forced — so the run-2 scenario auditor's reading stands on its own; adjudication #122 territory either way, and scenario-layer regardless. Not my lane, not re-reported.

My campaign-layer audit is complete. Everything reconciles:

---

**AUDIT CLEAN** — campaigns/show2-sonnet-daisy (Daisy, Return to NotZ, seed 9402, standard)

**Dimension 1 — XP LEDGER: consistent at every checkpoint.**
- S1 (Gathering, no_resolution): Victory 1 (Attic) + 2 insight = **3** ✓ (campaign guide no-resolution bullet; adjudication #2 pattern).
- S2 (MM, R1 resign): Victory 1 (Alma Hill, victory 1) = **1** ✓ (R1 grants Victory X only, no bonus).
- S3 (DB, no_resolution): **0** ✓ (guide's DB no-resolution block has no XP line — only "Arkham succumbed" + kill).
- Purchases: W1 deck-diff shows Encyclopedia (new lvl 0 = max(1,0) = 1 XP) − Flashlight; run-2 meta snapshots unspent 3→1, i.e. 2 spent — the 1-XP gap is the deck-diff-invisible churned-purchase pattern adjudicated NOT-A-BUG in #116 (no campaign ships a purchase ledger; totals only reconcile with a real 2-XP spend). W2: Hyperawareness(0)→50003(2) same-title upgrade = level diff 2 XP ✓, unspent 2→0.
- earned_total 4 = 3+1+0 ✓; spent_total 4 = 2+2 ✓; unspent 0 = 4−4 (naturally zero; death-zeroing per #111 moot); trajectory 0→3→1→2→0 never negative ✓.

**Dimension 2 — DECK LEGALITY: all three decks legal.**
- deck-1: 30 counted (15 titles ×2), ≤2/title, all lvl-0 within Seeker 0-5/Mystic 0-2/Neutral 0-5; signatures 01008+01009 and 1 basic weakness (Paranoia) present ✓.
- deck-2: 30 counted (+Encyclopedia −Flashlight); Lita added only after being earned in S1, correctly uncounted (34 physical) ✓; weakness/signatures persist ✓.
- deck-3: 30 counted; Hyperawareness title total 2 across levels ✓; 50003 Seeker lvl 2 legal for Daisy ✓; Lita persists ✓. Final campaign deck = deck-3 + second Paranoia (Madness basic weakness gained via DB agenda 2b in S3) ✓. Played-card instances in each state.json are subsets of the materialized decks ✓.

**Dimension 3 — CONTINUITY: all flows verified.**
- Trauma: +1 physical (S1 damage defeat, 5/5) → run-2 starts dmg1/5 ✓; Δ0 (S2 resign) → run-3 starts dmg1/5 ✓; +1 physical (S3) → total 2 ✓; mental 0, horror starts 0/9 ✓.
- House standing → MM start at Your House ✓. Ghoul Priest alive → shuffled into MM deck (drawn R3 ✓) and DB deck (input recorded ✓). Got-away list = 4 cultist-deck remainders + Masked Hunter per the "if it is Agenda 1" rule ✓ (Peter Warren correctly absent — Return setup removes 3 of 8 candidates unseen); DB doom table 5-6 names → exactly 3 doom ✓. Act-1-back got-away spawns never owed (Act 1 never advanced) ✓. past_midnight false → no opening-hand discard ✓. Elderthing token added unconditionally ✓ (actually revealed in play R1) and recorded in chaos_bag_additions ✓. Lita in decks only post-earning ✓. Killed Daisy never returns; campaign complete ✓. MM log fields survive DB recording (#25 behavior) ✓. No cross-lane run contamination (all runs c-show2-sonnet-daisy-N, seeds 940201-3) ✓.

Known-adjudication items observed but not re-reported: duplicate `game_end` line on the DB defeat (#119), hardcoded DB briefing in all three mission.md files (#136), MM Ghoul-Priest spawn special case (#122, scenario layer), window-1 churned purchase (#116 pattern).
