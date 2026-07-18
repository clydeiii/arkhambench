The audit is complete. All evidence gathered — here is the report.

---

## Finding 1 — Scenario 1 record is another campaign's game (cross-lane contamination; ledger-108 family, new post-fix instance)

**Campaign step:** `campaign record` after scenario 1 → `campaign.json` scenarios[0] (also propagated to `campaign_summary.json`)

**What the record says:** `campaign.json` scenario 1 points at `campaigns/show-sol-roland/runs/c-show-sol-roland-1` — a run belonging to the **show-sol-roland** campaign — and its recorded values (trauma_delta mental **2**, score **0**, xp 2) match that Sol run's result.json exactly (Sol's game: defeated R14, insane-defeat horror + Cover Up = 2 mental trauma, score 2−2=0).

**What actually happened in this campaign:** show-luna-roland played its own scenario 1 — `runs/c-show-luna-roland-1` exists, its meta.json names this campaign's deck (`show-luna-roland/decks/deck-1.json`, created 17:51:37, ended 17:56:27), and its result.json says: defeated R7, trauma mental **1**, score **1**, xp 2. That result was never ingested anywhere; the run is orphaned. The timestamps show the race: Sol's seed-matched run-1 (same seed 940101, same investigator) ended at 17:57:50, *after* Luna's own game ended, and Luna's record call picked up Sol's run.

**Downstream consequences (all verified in the artifacts):**
- Roland began Return to the Midnight Masks with **2 starting horror instead of 1** (run-2 log line 1: `hor2/5`; run-2 meta trauma mental 2). He resigned at R6 explicitly "before the engaged enemies inflict lethal horror" — the extra trauma point plausibly shaped play.
- Final campaign trauma is 4 mental; the correct figure from this campaign's own games is 3 (1+1+1).
- Scenario 1 benchmark score recorded 0 instead of 1; `campaign_summary.json` campaign_score 1 instead of 2 — this contaminates the luna56-b4 benchmark row.

**Why this is reportable despite ledger 108:** the root mechanism (campaign record resolving the wrong lane's run pointer) is the adjudicated ledger-108 race — but these runs were recorded 2026-07-10, *after* commit 308b7c1 shipped the AHLCG_RUN fix. Either the showcase driver's record step doesn't pass `AHLCG_RUN`/`--run` (fix incomplete at the driver layer), or the record path resolves runs by a route the fix didn't cover. Per the entry-58 precedent, this campaign's scenario-1 record (and the benchmark data derived from it) is contaminated; note the identical `xp: 2` in both results made the XP ledger accidentally correct.

**Cross-check:** show-sol-roland's own campaign.json points at all three of its own runs, so Sol's game 1 was double-counted (recorded by both campaigns), not swapped.

---

Everything else is clean. For the record, what I verified:

**XP ledger** — Scenario 1: no-resolution Gathering = VP 0 + 2 insight = 2 ✓ (both candidate results agree on 2, so the contamination doesn't corrupt XP). Purchase 1: Beat Cop (2) `01028` replacing Beat Cop (0) `01018`, same-title upgrade, level diff = 2 XP; unspent 0 confirmed in run-2 meta ✓. Scenario 2: R1 with 2 VP, Midnight Masks has no resolution bonus = 2 ✓. Purchase 2: second Beat Cop (2) = 2 XP; unspent 0 in run-3 meta ✓. Scenario 3: killed, VP 0 = 0 ✓. Totals 4 earned / 4 spent / 0 unspent, never negative ✓.

**Deck legality** — All three decks: exactly 30 counted cards (signatures 01006/01007, weakness 01102, and Lita 01117 excluded) ✓. Deck-2's Beat Cop split (01018×1 + 01028×1) is 2 copies by title across levels — legal ✓. All cards are Guardian 0–5, Seeker 0 (Magnifying Glass, Deduction), or neutral — within Roland's access ✓. Signatures and the Silver Twilight Acolyte weakness present in every deck, never removed ✓. Lita appears only after being earned in scenario 1 and chosen for inclusion (decks 2–3, story_assets) ✓. The six deckbuild swaps (First Aid→Beat Cop ×2, Barricade→Vicious Blow ×2, Physical Training ×2 → .45 Auto/Dynamite) are free level-0 swaps correctly reflected in deck-1 ✓.

**Continuity** — Trauma accumulation 2+1+1=4 is internally consistent with the recorded deltas and appears as starting horror in each next transcript (2/5 in MM, 3/5 in DB) — internally correct, though the "2" itself is the contaminated value. House standing → MM began at Your House ✓. Ghoul Priest alive → MM encounter deck totals 24 (18 remaining + 6 drawn = 23 Return-MM cards + priest), consistent with the shuffle-in ✓. Five cultists got away → 3 doom on DB agenda 1a (matches the campaign guide's 5–6→3 tier), logged at setup ✓. past_midnight false → no opening-hand discard in DB ✓. Elderthing token added and actually revealed in DB R2 ✓. Victoria Devereux interrogation and the got-away list persist to the final log (the entry-25 fix holds — DB recording didn't clobber MM fields) ✓. Roland killed in scenario 3 → killed_investigators, arkham_succumbed, campaign complete with no further scenarios ✓.

One cosmetic observation, not filed as a finding: the three run pointers mix relative and absolute path formats (`campaigns/...` vs `/Users/clyde/ahlcg/campaigns/...`) in both this campaign and Sol's — harmless but worth normalizing if anything ever joins on those paths.
