**AUDIT CLEAN**

All three campaign-layer dimensions reconcile for show-sol-wendy (Return to Night of the Zealot, standard, seed 9405). Summary of what was verified:

**1. XP ledger — consistent at every step**
- Scenario 1 (Return to The Gathering, no_resolution): victory display = Cellar (V1) → VP 1 + 2 no-resolution insight bonus = **3 XP** ✓ (matches adjudication #2's rule). Benchmark score 3 − 1 trauma = 2 ✓.
- Scenario 2 (Return to The Midnight Masks, R1 via resign): VP 0, MM has no resolution bonus → **0 XP** ✓, score 0 ✓.
- Scenario 3 (Return to The Devourer Below, no_resolution): empty victory display → **0 XP** ✓, score max(0, 0−1) = 0 ✓.
- Purchases (deck-1 → deck-2): Leo De Luca 01048→01054 same-title upgrade, level diff 1 = 1 XP; Lucky! 01080→01084 (level 2 — the "+2, draw 1 card" version) = 2 XP. Spent 3 = earned 3; `xp_unspent` 0, never negative; spend occurred after the earn. Totals in campaign.json and campaign_summary.json agree (3/3/0), campaign_score 2 = per-scenario sum ✓.

**2. Deck legality over time**
- deck-1: exactly 30 counted (15 titles ×2) after excluding signatures (01014, 01015) and Amnesia (01096). The 8 opening deckbuild swaps (Knife→Leather Coat, Scavenging→Stray Cat, Dig Deep→Sneak Attack, Cunning Distraction→Unexpected Courage) are all level-0 and fully reflected.
- deck-2/deck-3: 30 counted each; ≤2 copies per title across levels (Leo 0+1, Lucky 0+2, both = 2); Leo De Luca (1) is Rogue level 1, within Wendy's Rogue 0–2 access; Lucky! (2) within Survivor 0–5. Signatures present in all decks; Amnesia never removed; Lita (01117) is a story asset excluded from the 30-count and present in decks 2–3 only after being earned. deck-3 = deck-2 exactly, matching 0 XP earned after scenario 2.
- The final campaign record's double weakness (`["01096","01096"]`) is legitimate: run 3's result records a second Amnesia gained mid-scenario (`weaknesses_added: ["01096"]`, the DB agenda Madness gain), after deck-3 was materialized, and no deck-4 exists (Wendy killed).

**3. Continuity**
- Trauma: mental 1 after scenario 1 (defeated at 7/7 horror) → both scenario 2 and 3 open with `hor1/7` on the first status line; scenario 1 opened at `hor0/7`. Scenario 3's defeat total (5 dmg / 7 horror incl. the trauma point) → mental +1, campaign total mental 2 ✓.
- Campaign log flow: house standing → scenario 2 starts at **Your House** ✓; Ghoul Priest alive → shuffled into MM (13 log appearances) *and* into DB — verified by differential: DB decks in sibling campaigns with a dead priest (sol-skids, gpt-daisy, fable-agnes) start at 31 encounter cards, alive-priest runs at 32, and this run started at 32 ✓; 6 cultists got away → scenario 3 setup placed 3 doom (1 per 2) on agenda 1a and logged all six names, matching result-2's list exactly ✓; past_midnight false → normal opening hand, no discard ✓; elder thing token added at DB setup, present in the run-3 chaos bag and persisted to `chaos_bag_additions` ✓.
- The got-away list itself is internally consistent with Return MM setup: 5 cultist-deck cards (the 3 missing names — Herman Collins, Wolf-Man Drew, Alma Hill — are exactly the 3 removed at random) plus Narôgath from the agenda-1 reverse.
- Wendy killed by DB no-resolution (`arkham_succumbed` true, ritual not broken, Umôrdhoth not repelled, Lita not sacrificed — all consistent) → `killed_investigators: ["wendy"]`, campaign phase complete, `next: null`; she never returns.
- Upgraded cards genuinely materialized into play: Leo De Luca (1) (01054) appears in run 3's opening hand snapshot.

No campaign-layer rules-enforcement defects found.
