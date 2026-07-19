I'll audit the campaign layer for `show2-hy3-wendy`. Let me start by reading the campaign state and rules documents.
Now the per-scenario results and rules docs:
Let me check the run directories' contents and the initial setup of each transcript (for continuity checks only — the transcripts themselves are audited separately).
The docs show trauma/continuity facts. Now let me verify the card identities and levels for deck-legality and XP-cost reconstruction:
The card output doesn't show level. Let me get the remaining cards and check if there's a level flag:
Let me check the mission briefs (which state the scenario rules given to the player) and find the Jeremiah Pierce interrogation in sc2:
The mission brief confirms my XP reconstruction (unspent 1 entering sc2). Let me check sc3's mission and end-state:
The PDF is available (not in the prohibited list). Let me extract the Midnight Masks resolution rules:
The DB doom table (5-6 names → 3 doom) matches exactly. Now the Gathering resolution section and a check that the Ghoul Priest was actually shuffled into sc3's encounter deck:
All continuity facts reconcile so far. Let me verify the Psychosis gain event in sc3 (recorded as an earned campaign weakness) and confirm the agenda sequence:
All three runs' metadata confirm correct campaign-layer state at every step. The audit is complete — everything reconciles. Let me do one final verification of the deck-count arithmetic to be certain:
`AUDIT CLEAN`

All three dimensions reconcile exactly for `campaigns/show2-hy3-wendy`:

**1. XP LEDGER** — clean
- Leg 1 (Gathering, no_resolution): VP 0 + 2 insight bonus = 2 XP ✓ (campaign guide: no-resolution → Victory X + 2, lead earns Lita)
- Leg 2 (MM, R1): VP 2 = 2 XP ✓ (guide: defeat → "read Resolution 1", so R1 for the R7 defeat is *correct*; XP = Victory X)
- Leg 3 (DB, no_resolution): VP 0 = 0 XP ✓
- Purchases reconstructed from deck diffs: window 1 = Leo De Luca(1) @ max(1,1)=1 XP; window 2 = second Leo(1) copy @1 XP (second-copy = new purchase at full cost) + Dig Deep(2) 50009 @2 XP = 3 XP. Total spent 4.
- Stepwise unspent: 0→2→**1** (leg-2 meta/mission confirm)→3→**0** (leg-3 meta/mission confirm)→0. `xp_earned_total` 4, `xp_spent_total` 4, `xp_unspent` 0 — consistent, never negative.

**2. DECK LEGALITY** — clean
- deck-1/2/3: exactly 30 counted cards each (33/34/34 physical minus 2 signatures, 1 weakness, and Lita from decks 2–3); ≤2 copies per title across levels (Leo 01048+01054 ≤ 2, Dig Deep 01077+50009 ≤ 2 verified); all Rogue cards ≤ level 2, all Survivor ≤ level 5, per Wendy's options.
- Opening `deckbuild_swaps` are three 1-for-1 level-0 swaps (count-preserving, matches deck-1). Signatures 01014/01015 always present; basic weakness Amnesia (01096) never removed; Lita (01117) absent from deck-1, present decks 2–3 only after being earned; earned Psychosis (01099, gained in leg 3 per DB Madness agenda, entered threat area) persisted into `campaign.deck.weaknesses`. `campaign.deck` == deck-3 with weakness/story fields separated.

**3. CONTINUITY** — clean
- Trauma: +1 mental per leg (each a horror defeat at 7/7) = 3 total ✓; leg 2 opens at `hor1/7`, leg 3 at `hor2/7`, run metas confirm carried trauma.
- House standing → leg 2 starts at Your House ✓; Ghoul Priest alive → shuffled into leg-2 encounter deck (drawn from it R4, engaged); got-away 5 → leg-3 setup doom **3** per the guide table (5–6 names → 3 doom) ✓ and logged; past_midnight **false** is correct for R1 (only R2 records past midnight) → no opening-hand discard in leg 3 ✓; elderthing token added unconditionally ✓ (`chaos_bag_additions` matches); got-away list correctly omits the Masked Hunter (game ended at Agenda 2, guide adds it only at Agenda 1).
- DB no_resolution → "Arkham succumbed" + Wendy killed per guide ✓; killed investigator never returns, campaign `complete`. No cross-lane contamination (all runs `c-show2-hy3-wendy-{1,2,3}`, matching scenarios); ledger-#25 regression holds (DB recording did not clobber MM log fields).

Not re-reported per known adjudications: the duplicate `GAME OVER` line in leg 3's log is #119 (display, batch 15); the absence of a per-purchase XP ledger field is the #116 adopted improvement — totals here reconcile exactly without it (deck diffs + mission-brief unspent figures pin every step).
