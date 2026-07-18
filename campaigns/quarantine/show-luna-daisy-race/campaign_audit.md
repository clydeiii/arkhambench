Audit complete. Both daisy campaigns cross-recorded each other's runs — that's the one finding. Everything else reconciles.

---

## Finding 1 — Campaign records ingested the other lane's runs (cross-lane `.current_run` race, recurring after the ledger-108 fix)

**Step:** `campaign record` after scenarios 1, 2, and 3 — `campaigns/show-luna-daisy/campaign.json` scenarios array.

**Evidence:**
- show-luna-daisy scenario 1 points at `campaigns/show-sol-daisy/runs/c-show-sol-daisy-1` and scenario 3 at `.../c-show-sol-daisy-3`. Symmetrically, **show-sol-daisy's campaign.json scenario 2 points at `campaigns/show-luna-daisy/runs/c-show-luna-daisy-2`**. Both campaigns recorded the identical three runs (sol-1, luna-2, sol-3), so two "independent" benchmark campaigns share game data and each counted a foreign game.
- Luna's own scenario-1 run (`c-show-luna-daisy-1`) is abandoned: meta `status: "in_progress"`, last updated 18:13:48, **no result.json**. Sol-1 was created at 18:13:50 — two seconds later — and its result (XP 2, +1 physical trauma, Lita earned, house standing) is what luna's campaign ingested. Every downstream artifact of this campaign (deck-2 purchases, MM starting trauma, the campaign log) descends from a game the luna model never played.
- Luna's own scenario-3 run (`c-show-luna-daisy-3`) **did** complete with its own result.json (2 rounds), but the campaign recorded sol-3 instead (3 rounds, ended 18:26:05, after luna-3's 18:22:13 — i.e., luna's record ran late and picked up the pointer sol had rewritten). The two results happen to agree on xp 0 / +1 physical / killed, so scenario 3's numbers are coincidentally unaffected; scenario 1's are wholly foreign.

**Rule basis:** campaign flow (docs_agent/campaign_guide.md, "Flow" step 4): `campaign record` ingests **the run's** result.json — the run started by this campaign's `campaign next`. This is the same failure class as ledger entry 108 (adjudicated CONFIRMED, "fixed live mid-program" on 2026-07-09), but these runs are dated **2026-07-10**, after that fix — either the fix isn't in the record path this driver used, or the driver doesn't set `AHLCG_RUN` for `campaign record` and the shared `.current_run` pointer won the race again. Per the entry-58 precedent, contaminated results were previously ruled rerun-required.

**Impact:** benchmark integrity, not rules enforcement — luna-daisy's campaign score partially measures sol's play, sol-daisy's partially measures luna's, and the same three games are double-counted across two model lanes. Both daisy campaigns (and any cross-model comparison built on them, e.g. the b4 gauntlet numbers) are suspect.

---

Everything else is clean. What I verified:

**XP ledger — clean.** Scenario XP recomputes correctly from the recorded results: Gathering no-resolution = VP 0 + 2 insight = 2 (matches adjudication #2); Midnight Masks R1 = VP 1 (Alma Hill parleyed into the victory display, and the reference confirms MM has no resolution bonus) = 1; Devourer no-resolution with investigator killed = 0. Spending: after scenario 1, second Deduction + second Shrivelling (two new level-0 cards, 1 XP each, Hyperawareness/Medical Texts removed free) = 2; after scenario 2, Magnifying Glass (1) for max(1,1) = 1 XP, removing one Flashlight. Earned 3 / spent 3 / unspent 0 at every checkpoint, never negative; per-run meta.json xp_unspent values agree.

**Deck legality — clean.** All three decks count exactly 30 (deck-1: 33 total minus Tote Bag, Necronomicon, Paranoia; deck-2/3 likewise, with Lita excluded as a story asset). Max 2 per title holds throughout; all cards are Seeker 0–5 / Mystic 0 / neutral within Daisy's access, with the single level-1 card (Magnifying Glass (1)) legal. Both signatures and the Paranoia weakness are present in every deck and never removed. Deck-1 correctly reflects the two free campaign-start swaps (one Deduction in for one Hyperawareness, one Shrivelling in for one Medical Texts). Lita (01117) appears only in decks 2 and 3, after being earned in scenario 1 and explicitly included.

**Continuity — clean** (relative to the recorded results). Trauma chain 0 → 1 → 2 → 3 physical matches per-scenario deltas; the MM transcript opens at dmg 1/5 and the DB transcript at dmg 2/5. House standing → MM begins at Your House; Ghoul Priest alive → present in the MM encounter deck (drawn R3); five got-away cultists → 3 setup doom on DB agenda 1a (the 5–6 bracket, consistent with the entry-45 precedent) plus the got-away Main Path spawn hook; past midnight false → no opening-hand discard; elderthing token added to the bag and logged. Daisy was killed in the final scenario, is in killed_investigators, and never returns. The final campaign log preserves the MM fields through DB recording (the entry-25 fix holds). Benchmark scores also reconcile: XP − trauma per scenario = 1, 0, 0 → campaign score 1.
