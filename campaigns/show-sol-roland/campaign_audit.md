All checks complete. Everything in the campaign layer reconciles.

# Campaign-layer audit — show-sol-roland

**AUDIT CLEAN**

## What was verified

**1. XP ledger.** Scenario 1 (Return to the Gathering, no_resolution): victory display confirmed empty in end-state — the three defeated enemies (Silver Twilight Acolyte, Grave-Eater, Swarm of Rats) carry no Victory, and the seed-chosen Return Attic (50018) / Cellar (50020) are the non-Victory gateway variants, both still unrevealed at game end. XP = VP 0 + 2 insight = 2, matching adjudication #2. The single purchase is Beat Cop (0→2): deck-2 shows 01018 dropping 2→1 and 01028 appearing, a same-title upgrade costing level difference 2. Ledger sequence: earn 2 → unspent 2 → spend 2 → unspent 0 (confirmed as `xp_unspent: 0` in runs 2 and 3 meta). Scenario 2 (R1, resigned, VP 0) and scenario 3 (killed) earn 0. Final totals 2/2/0 are consistent and never negative.

**2. Deck legality over time.** All three decks count exactly 30 (deck-1: 33 slots − signature 01006 − Cover Up 01007 − Silver Twilight Acolyte 01102; decks 2–3 additionally exclude story asset Lita 01117). Every card is Guardian, Seeker level 0, or Neutral — legal for Roland (Guardian 0–5 / Seeker 0–2); Beat Cop (2) is Guardian 2. Max-2-per-title holds including Beat Cop split across levels (1×01018 + 1×01028). Signatures and both weaknesses present in every deck; nothing removed. The nine opening deckbuild swaps are all level-0, in-class swap-ins. Deck-3 is identical to deck-2, correct for 0 XP earned in scenario 2.

**3. Continuity.** Scenario 1 starts 0 damage/0 horror; its 2 mental trauma is fully accounted for in the transcript (defeat by horror at 5/5 sanity + Cover Up's end-of-game Forced, both logged). Scenario 2 starts at Your House (house standing) with 2 horror, and its player deck size (h5 + d29 = 34) proves Lita was shuffled in. Resign → trauma delta 0. Scenario 3 starts at Main Path with 2 horror, logs "Setup placed 3 doom from cultists who got away" (6 cultists → 3 doom, 1 per 2) and "added 1 elderthing token" (mirrored in `chaos_bag_additions`); past_midnight false → no opening-hand discard, and none occurred. Defeat by horror → +1 mental (total 3), then the Devourer no-resolution kill correctly puts Roland on `killed_investigators` with `arkham_succumbed`, and the campaign terminates (`next: null`). The got-away list and MM-shaped log fields survive the Devourer recording intact (entry-25 fix holding). Ghoul-priest-alive and lita-in-deck inputs are correctly passed into runs 2 and 3 (meta.json / mission.md); the priest never surfacing in 7 + 2 encounter draws is unremarkable, and the hidden deck can't be inspected directly.

## Non-finding observations (not rules defects)

- Scenario 3's `run` path is stored relative in campaign.json/campaign_summary.json while scenarios 1–2 are absolute — cosmetic metadata inconsistency, likely a side effect of the ledger-108 AHLCG_RUN change landing mid-campaign.
- Every mission.md (including scenarios 1 and 2) carries the same static "The Devourer Below briefing" block — a deliberate plan-ahead template, not a scenario mix-up, but worth knowing it front-loads finale information into earlier briefs.
- Scenario 3's log prints "GAME OVER: Roland Banks was defeated" twice — transcript-layer cosmetic duplication, out of campaign-layer scope.
