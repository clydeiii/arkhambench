AUDIT CLEAN

I recomputed every campaign-layer transition in show-hy3-roland and found no rules-enforcement defects. Full reconciliation:

**XP ledger — balances exactly, never negative.**
- Scenario 1 (Return to the Gathering, no resolution): 1 VP + 2 insight bonus = **3 XP** ✓ (matches adjudication #2's rule).
- Scenario 2 (Return to the Midnight Masks, R1): victory display held Herman Collins (VP 1) = **1 XP** ✓.
- Scenario 3 (Return to the Devourer Below, no resolution): 0 VP, investigator killed = **0 XP** ✓.
- Purchases: deck-1→2 bought Beat Cop 01018 (new level-0 = 1 XP, removing one Guts to hold 30) and Dynamite Blast(2) 50002 replacing 01024 (level diff = 2 XP) — exactly the 3 XP banked. Deck-2→3 upgraded Magnifying Glass 01030→01040 (diff = 1 XP) — exactly the 1 XP banked. Totals 4 earned / 4 spent / 0 unspent match campaign.json and campaign_summary.json at every step.

**Deck legality — all three decks legal.**
- Counted cards are exactly 30 in each deck (excluding signature 01006, signature weakness 01007, basic weakness 01102 Silver Twilight Acolyte, and story asset Lita 01117; run headers confirm the arithmetic — draw pile 28 after opening hand in scenario 1 with 33 total cards, 29 in scenarios 2–3 with 34 including Lita).
- Max 2 per title holds everywhere, including the Magnifying Glass 0/1 split (1+1) and the single Dynamite Blast after the upgrade.
- Class access: all Guardian 0–2, Seeker 0–1, and Neutral 0 cards — within Roland's Guardian 0–5 / Seeker 0–2 / Neutral access.
- Signatures and both weaknesses present in all three decks, never removed; Lita appears only in decks 2–3, after being earned in scenario 1 and included (`lita_in_deck: true`).
- The opening deckbuild swaps (2× Knife 01086 out, 2× Vicious Blow 01025 in) are free level-0-for-level-0 swaps in the pre-campaign window, per the guide.

**Continuity — every log fact flowed correctly.**
- Trauma: scenario 1's mental +2 is fully grounded (defeat by horror at 6/5 sanity = 1, plus the logged "Cover Up caused 1 mental trauma" — Cover Up entered play R1 with 3 clues and was never cleared). Scenarios 2 and 3 each add 1 mental (defeated at exactly 5/5 horror). Accumulation 0→2→3→4 matches, and the transcripts show starting horror 0, 2, and 3 respectively with 0 starting damage throughout.
- Midnight Masks setup: house standing → Roland begins at Your House ✓; `ghoul_priest_alive: true` passed as a setup input (the Priest never surfaced in a 3-round, 2-encounter-draw game, so his absence from public state is expected, not a defect). Defeat with the agenda short of midnight correctly resolved as R1 with `past_midnight: false` (MM's no-resolution maps to R1), and the cultist accounting closes: 6-card cultist deck, Herman Collins parleyed into the victory display = interrogated, the other 5 recorded as got away.
- Devourer Below setup: 3 doom placed for 5 got-away cultists (guide table: 5–6 → 3 doom, logged explicitly), elderthing token added and recorded in `chaos_bag_additions`, no past-midnight opening-hand discard, and the inputs block mirrors the campaign log exactly — notably the MM fields survived the DB record intact (good live evidence for the entry-25 batch-7 fix).
- Ending: DB no-resolution kills the investigator (per adjudication #54's ruling) → `investigator_killed`, `arkham_succumbed`, Roland in `killed_investigators`, campaign phase `complete` with `next: null`. No post-death activity anywhere.

One observation, not a finding: the per-scenario `score` field (1/0/0) doesn't track victory points (scenario 2 had VP 1, score 0) — it appears to be a bench progress metric, not a rules quantity, so it's outside the campaign-rules surface.
