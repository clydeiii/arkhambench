I'll start by reading the campaign state and the rules authorities in parallel.
Now the rules authority documents:
Now let me look up every card in the decks to verify classes, levels, and types. I'll batch the lookups:
The card CLI doesn't show XP levels. Let me check the rules reference for level/XP info and see what else is in docs_agent:
There's a `scenario_reference.md` — I need that for the continuity checks:
The scenario reference covers setup for scenarios 1-2. For the Devourer Below setup facts (adjudications #45, #110 establish the guide's rules), I'll verify against run logs. Let me examine each run's setup and opening state:
Scenario 2 and 3 setups look right so far (start location Your House, starting dmg 1, past-midnight discards, got-away doom, elderthing). Now I need to trace the XP purchases precisely. Let me check the campaign summary and run metadata for upgrade records:
Setup continuity looks right so far. Now let me verify the Ghoul Priest presence in scenarios 2/3 encounter decks, and check run 1's audit notes plus the end states:
Endings check out. Now the XP ledger — let me hunt for any upgrade transaction records:
The audit.md is a scenario audit. No upgrade records exist — the ledger must be reconstructed from deck diffs. Let me check run 3's mission.md for the Devourer Below encounter-pool size (to verify the Ghoul Priest shuffle):
Run 3 had a Corpse-Taker spawn at R2 mythos before the encounter draw — I need to know its source for the deck-size math:
The R2 Corpse-Taker spawn was agenda-driven ("Death to the Intruders"), not from the encounter deck. So run 3's encounter deck started at 30. To verify whether the Ghoul Priest was shuffled in, let me cross-check against other campaigns' Devourer Below runs where the priest was dead:
The cross-check is inconclusive (searches/reshuffles pollute the math). Let me check the timeline for a setup event with the initial deck size:
The timeline holds setup states — run 2 MM confirms `encounter_deck_count: 24` = 23 + priest ✓. Run 3 DB shows 32. Let me verify the DB base size across all campaigns' timelines grouped by priest status:
Definitive: priest-dead DB = 31, priest-alive DB = 32 (this campaign included) — the Ghoul Priest was correctly shuffled into the DB deck. Same check for MM and the Gathering:
All evidence is in. The corpus-wide triangulation is decisive: every other campaign's upgrade windows reconcile exactly with legal pricing, and this campaign's windows 1 reconciles — but window 2 does not. Here is the audit result.

---

## Campaign-layer audit: show2-hy3-roland (Return to NotZ, Roland, standard, seed 9401)

**Method:** campaign.json read in full; deck-1/2/3 materialized decks; all three result.json + run logs/timelines/meta; card text/levels via `./ahlcg card`; cross-checked setup deck sizes against the 53-campaign corpus to pin encounter-deck composition.

**XP earned (all verified correct):**
- Sc1 (Return Gathering, no_resolution, VP 0): 2 = VP 0 + 2 insight bonus (per adjudication #2; Lita earned by lead ✓)
- Sc2 (Return MM, R2, VP 4): 4 = VP 4, no resolution bonus (scenario_reference: "Midnight Masks has no resolution XP bonus") ✓
- Sc3 (Return DB, no_resolution, VP 0, killed): 0 ✓ — `xp_earned_total` 6 ✓

**Deck legality (all verified):** deck-1 = 30 counted + 2 signatures + 1 weakness; deck-2/3 = 30 counted + 2 signatures + 1 weakness + Lita (story asset, correctly uncounted). Physical Training title count = 01017×1 + 50001×1 = 2 (max-2-across-levels respected). All cards within Roland's Guardian 0–5 / Seeker 0–2 / Neutral access (Magnifying Glass Seeker-1 ✓, Extra Ammunition Guardian-1 ✓, 50001 Guardian-2 ✓). Signatures never removed; weakness 01102 never removed; Lita only in decks after being earned (deck-2 onward); Hypochondria (01100, gained R4 of scenario 3) correctly absent from deck-3 and present in the final campaign deck; opening deckbuild swap 01088→01016 is a legal free level-0 swap. In-game deck counts corroborate (d28/d29/d29 at opening hands).

**Continuity (all verified):** trauma physical +1 (sc1 defeat by damage, dmg 9/9) → run-2 setup `damage: 1`, log `dmg1/9` ✓; run-2 no trauma → run-3 setup `damage: 1` ✓; run-3 mental +1 (defeat at horror 5/5, single trauma — adjudication #54 behavior) → final trauma 1/1 ✓. House standing → MM starts at Your House ✓. Ghoul Priest alive → shuffled into both MM (setup encounter_deck_count 24 = 23 base + 1; corpus: priest-dead MM = 23) and DB (32 = 31 base + 1; corpus: priest-dead DB = 31) ✓. 5 got-away cultists → 3 setup doom on DB agenda 1a (guide's max-3 cap; logged with all 5 names) ✓; their act-advance spawn trigger never fired (Act 1 never advanced) — no violation. Past midnight → 2 opening-hand discards (Magnifying Glass, First Aid) ✓. Elderthing token in DB chaos bag only, and recorded in `chaos_bag_additions` ✓ (unconditional per adjudication #110). MM campaign fields survived DB recording (adjudication #25 fix working). Roland killed by DB no-resolution (per guide/adjudication #54) → `killed_investigators: ["roland"]`, campaign `complete`, never returns ✓. Scores 1/4/0 = XP − trauma (min 0) ✓, campaign_score 5 ✓.

## Finding 1 — XP ledger overcharge: post-scenario-2 upgrade window deducted 4 XP for purchases costing 3 XP (deck-2 → deck-3)

**Evidence:**
- deck-2 → deck-3 delta: **added** 01025 Vicious Blow ×1 (level 0, new → `max(1, level)` = **1 XP**), 01026 Extra Ammunition ×2 (level 1, new → **1 XP each**; campaign_guide's own example prices `upgrade buy 01026` at 1 XP); **removed** 01024 Dynamite Blast, 01088 Emergency Cache, 01030 Magnifying Glass (removals are free per the guide's buy-`--remove` example). No same-title upgrade path applies (no shared titles). **Legal cost = 3 XP.**
- **Charged = 4 XP:** run-2 meta `xp_unspent` 0 + sc2 earned 4 − run-3 meta `xp_unspent` 0 = 4. Final campaign.json: `xp_spent_total: 6`, `xp_unspent: 0` against reconstructable spend of 2 (window 1: 50001 Physical Training(2) `--replace` 01017 level-0, difference 2 — correct and consistent with run-2 meta) + 3 = **5**.
- The 1-XP gap exists at **scenario-3 setup** (run-3 meta/timeline "Unspent XP: 0" recorded before Roland's death), so the deliberate death-zeroing of unspent XP (adjudication #111) cannot explain it: with correct pricing Roland would have entered the Devourer Below with 1 unspent XP (zeroed at death anyway), and `xp_spent_total` should read 5, not 6.
- **Corpus corroboration:** reconstructing all 47 other campaigns' upgrade windows the same way (per-leg meta `xp_unspent` deltas vs. deck diffs), every window reconciles exactly under the same card prices (01025 = 1 XP: show-terra-skids win2, show-fable-roland win1; 01026 = 1 XP: show-luna-roland win2, show2-sonnet-roland win2; 50001-replace = 2 XP: loop1-roland, show-gpt-roland, this campaign's window 1). This window is the sole non-reconciling case in the corpus — 1 XP was deducted with no corresponding purchase in any materialized deck, and no purchase log exists to account for it.

**Grounding:** docs_agent/campaign_guide.md XP rules ("New cards cost max(1, level)"; "Same-title upgrades ... cost is the level difference, minimum 1"; Extra Ammunition example = 1 XP) and rules_reference.md Campaign Play ("each card costs experience equal to the card's level, to a minimum of 1"; level-0 minimum applies to new purchases). `xp_spent_total`/`xp_unspent` are inconsistent with the materialized decks by exactly 1 XP — either the upgrade window overcharged one purchase or the spent tally misrecords the window.

All other campaign-layer dimensions (earned XP, deck legality over time, trauma/log/killed-investigator/Lita continuity) are clean.
