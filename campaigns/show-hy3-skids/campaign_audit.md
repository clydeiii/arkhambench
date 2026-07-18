**AUDIT CLEAN**

I audited the campaign layer of `show-hy3-skids` (Return to Night of the Zealot, Skids, standard, seed 9303, 3 scenarios, investigator killed) across all three dimensions. Everything reconciles. What I verified:

**1. XP ledger — consistent at every step (0 / 0 / 0)**
- **Scenario 1** (Return to The Gathering, no_resolution): Victory display confirmed empty in the final state — the two defeated enemies (Acolyte of Umôrdhoth 50039, Swarm of Rats 01159) carry no Victory X, the Ghoul Priest survived, and the seed chose the *non*-Victory Attic/Cellar variants (50018/50020, no Victory line). So XP = VP 0 + 2 insight bonus (per the established no-resolution ruling) − 2 Hospital Debts = 0. The Hospital Debts penalty is legitimate: it was drawn R1, and the final state shows it in the threat zone with 0 resources (< 6) at game end.
- **Scenario 2** (Return to Midnight Masks, R1 via resignation): XP = Victory display (empty — 0 enemies defeated, all 6 cultists got away) − 2 Hospital Debts (drawn R2, in threat with 0 resources at end) → 0.
- **Scenario 3** (Return to Devourer Below, no_resolution): investigator killed per the campaign guide; no XP.
- No purchases were ever made (`xp_spent_total` 0, decks byte-identical across scenarios apart from Lita), and no ledger value ever goes negative.

**2. Deck legality over time**
- All three decks: exactly 30 counted cards (signatures 01010/01011, weakness 01101, and story asset Lita 01117 excluded), max 2 copies per title, all level 0.
- Every card is legal for Skids (Rogue 0–5 / Guardian 0–2 / Neutral): .45 Automatic, Beat Cop, Dynamite Blast, Vicious Blow (Guardian 0); Switchblade, .41 Derringer, Leo De Luca, Hard Knocks, Elusive, Backstab, Sneak Attack, Opportunist (Rogue 0); Flashlight, Emergency Cache, Overpower, Unexpected Courage (Neutral). The opening deckbuild swaps (Leo De Luca←Knife ×2, Backstab←Burglary ×2, Unexpected Courage←Guts ×2) were all 0-for-0, no XP due.
- Signatures present in every deck; weakness 01101 never removed. Psychosis (01099) was gained mid-scenario-3 via the Return DB Madness effect (log R4: "entered the threat area / Gained Psychosis") and correctly persisted into the campaign deck's weakness list; it's correctly absent from deck-3.json, which was materialized before that scenario. Lita appears only in decks 2–3, after being earned in scenario 1 and explicitly included.

**3. Continuity**
- Trauma: S1 defeat by damage (8/8) → +1 physical; S2 resign → 0; S3 defeat by horror (7/6) → +1 mental; final {physical 1, mental 1} matches. Runs 2 and 3 both open at `dmg1/8 hor0/6`; run 1 at `dmg0 hor0`.
- Log facts flowed into setup correctly: house standing → MM starts at Your House; Ghoul Priest alive → shuffled into the MM encounter deck (drawn R3); 6 got-away cultists → 3 doom on DB agenda 1a (matches the previously adjudicated campaign-guide table) with the full 6-name list carried verbatim; elderthing token added at DB setup and recorded in `chaos_bag_additions`; past_midnight false → no opening-hand discard occurred; Lita was in the DB deck and opening hand.
- Skids was killed in the final scenario; `killed_investigators` records it, `phase` is complete, `next` is null — no post-death reappearance possible. `campaign_summary.json` agrees with `campaign.json` on every field.

No new findings; the only XP-suppressing mechanism in play (Hospital Debts −2, three times) is grounded in the card's printed Forced effect and verified against each game's final state.
