**AUDIT CLEAN**

All three campaign-layer dimensions reconcile for show-hy3-wendy. Supporting detail:

**1. XP ledger — verified exactly.**
- Scenario 1 (Return to The Gathering, no_resolution): VP 1 + 2 insight bonus = 3 XP (per adjudication #2). `xp_earned: 3` ✓.
- Scenario 2 (Return to Midnight Masks, resigned → R1): R1 pays victory display only; VP 0 → 0 XP ✓.
- Scenario 3 (Return to The Devourer Below, no_resolution, killed): 0 XP ✓.
- Purchases after scenario 1: Leo De Luca 01048(0) → 01054(1) same-title upgrade = 1 XP; Lucky! 01080(0) → 01084(2) same-title upgrade = 2 XP. Total spent 3 = `xp_spent_total`; `xp_unspent` 0; ledger never negative at any step; no purchases after scenario 2 (deck-3 identical to deck-2, consistent with 0 XP available) ✓.

**2. Deck legality over time.**
- All three decks materialize exactly 30 counted cards after excluding signatures (01014/01015), weakness 01096, and story asset Lita 01117 (status-line deck counts confirm: 33 total cards in scenario 1, 34 in scenarios 2–3, opening hands of 5 leaving d28/d29).
- Max 2 per title holds across levels: Leo De Luca 0+1 = 2 copies, Lucky! 0+2 = 2 copies ✓.
- Class/level access: everything is Survivor 0–5, Rogue 0–2 (Switchblade, Leo 0/1, Elusive, Backstab, Sneak Attack), or Neutral — all within Wendy's pool ✓. Opening deckbuild swaps were all level-0 for level-0 (free window per the guide) ✓.
- Signatures and Amnesia (01096) present in every deck; never removed ✓.
- Campaign deck lists a second weakness 01100 (Hypochondria) that appears in no deck file — this is correct, not a gap: it was gained in-scenario during run 3 (agenda "The Ritual Begins" willpower test failed by 1; random Madness weakness gained R4) and recorded in `weakness_gained`; the investigator was killed and the campaign ended, so no deck-4 exists to materialize it.

**3. Continuity.**
- Trauma: deltas 0/0, 0/0, then mental 1 in scenario 3 (defeated at 7/7 horror → mental trauma, correct type). Scenarios 2 and 3 both start at dmg 0/7, hor 0/7, matching zero accumulated trauma; the scenario-3 trauma has no next scenario. Total `trauma: {mental: 1}` ✓.
- Log flow: house standing → MM starts at Your House ✓; Ghoul Priest alive → drawn from the encounter deck in both MM (R4) and DB (R4) ✓; 6 cultists got away → DB setup placed 3 doom on agenda 1a (1 per 2 cultists, matching the previously-adjudicated setup table) ✓; past_midnight false → correctly derived (resigned at agenda 2, doom 6/8, midnight never struck) and no opening-hand discard in DB ✓; elderthing token added at DB setup and recorded in `chaos_bag_additions` ✓.
- Lita: earned via Gathering no_resolution (lead earns Lita), absent from deck-1, present in deck-2/deck-3 after `--include`, drawn in MM's opening hand — earned-then-included order is correct ✓.
- Killed investigator: Wendy killed by DB no_resolution (per adjudication #54), recorded in `killed_investigators`, phase complete, `next: null` — never returns ✓. Final-log fields (`cultists_got_away`, `past_midnight`) survived the DB recording, confirming the entry-25 fix ✓. `campaign_summary.json` agrees with `campaign.json` on every figure.

One out-of-scope observation for the transcript auditors: run 3, R4 Investigation logs `"Skids" played Elusive` in a Wendy solo game — a log-attribution artifact in the scenario transcript layer (likely a hardcoded name in the Elusive play message), not a campaign-layer issue, and state was unaffected (Wendy paid, moved, and the priest disengaged correctly).
