All checks are complete. Here is the campaign-layer audit report.

---

# Campaign audit — campaigns/show-sol-daisy (Daisy, Return to NotZ, seed 9402)

## Finding 1 — Scenario 2 recorded from the wrong campaign lane: this campaign ingested `show-luna-daisy`'s game, orphaning its own, with material downstream effects (trauma, score, and plausibly the investigator's death)

**Campaign step:** `campaign record` after scenario 2 (`return_to_the_midnight_masks`); propagates into scenario 3 setup and all final totals.

**Evidence:**

- `campaign.json` scenario 2 entry points at `/Users/clyde/ahlcg/campaigns/show-luna-daisy/runs/c-show-luna-daisy-2` — a different campaign directory — even though this campaign's own completed run exists at `campaigns/show-sol-daisy/runs/c-show-sol-daisy-2` (status "ended", full result.json, never ingested anywhere).
- The two runs are seed-matched (both seed 940202) but are different games with different outcomes. Sol's own run: Daisy **resigned** R4, score 1, VP 1, XP 1, `trauma: {}`. Luna's run: Daisy **defeated**, score 0, VP 1, XP 1, trauma +1 physical. The campaign recorded luna's values (`score: 0`, `trauma_delta: {physical: 1}`).
- Provenance is unambiguous: sol's run-2 `meta.json` names `deck: .../show-sol-daisy/decks/deck-2.json`; luna's names luna's deck-2 (the two lanes' decks differ — different deckbuild swaps).
- The contamination propagated into play: run-3 `meta.json` shows trauma `physical: 2` entering the Devourer Below, and the run-3 transcript opens at `dmg2/5`. The true carry-in from this lane's own games is 1 physical (scenario 1 only).
- The playing agent observed it live: sol run-2's closing note / bug_reports.md (18:21:06) protests that "R1 resignation added 1 physical trauma… despite the run ending by resign rather than defeat" — the trauma it saw was luna's defeated result being recorded into its campaign.

**Impact within this campaign:**

1. **Trauma:** final `trauma.physical` 3 should be 2; scenario 3 should have started at dmg 1/5, not 2/5. Daisy died in run 3 at exactly dmg 5/5 — with the correct starting trauma she survives that hit, so the contaminated point plausibly caused the death, the `killed_investigators: [daisy]` entry, and the `arkham_succumbed` campaign outcome.
2. **Score:** scenario 2 score recorded 0 (luna's) vs. the actual 1; `campaign_score` 1 should be 2. This feeds the showcase/bench comparisons (`bench/sol56-b4` vs `luna56-b4`), so the model-lane results are cross-contaminated in both directions.
3. **XP ledger:** arithmetically unaffected only by luck — both games happened to earn XP 1 (VP 1, R1). The campaign log fields (`cultists_got_away`, interrogated, past_midnight) also happened to be identical in both games, so no log divergence.
4. **The mirror lane is equally contaminated:** `show-luna-daisy/campaign.json` has the byte-identical scenarios array — it recorded **sol's** runs 1 and 3 as its own scenarios 1 and 3. Neither daisy campaign is a faithful record of a single lane's play. The same signature appears in the roland lanes (`show-luna-roland` scenario 1 points at `show-sol-roland/runs/c-show-sol-roland-1`).

**Rules/spec basis:** campaign_guide.md flow step 4 — `campaign record` must ingest **the run's** result.json for the scenario this campaign just played; trauma carries per "Trauma persists and starts future scenarios as damage" from the investigator's own scenario deltas.

**Note on ledger entry 108:** the root cause is the adjudicated cross-lane `.current_run` race (do-not-re-report), and I am not re-reporting the code defect. What I am reporting is that this campaign's **artifact is contaminated** — these lanes (runs stamped 2026-07-10 18:13–18:26 UTC) either predate the AHLCG_RUN fix or the showcase driver's `campaign record` step doesn't pass `--run`/`AHLCG_RUN`, since the race still bit both daisy lanes and at least one roland lane. Both daisy campaigns need re-recording from their own runs (or rerun), and the sol-vs-luna bench comparison for daisy is invalid as stored.

---

## Everything else — CLEAN

- **XP ledger:** scenario 1 no-resolution Gathering = VP 0 + 2 insight = 2 ✓ (matches adjudication 2); scenario 2 R1 = VP 1 = 1 ✓; scenario 3 killed = 0 ✓. Purchases: Blinding Light 01066(0) → 01069(2) via replace = level diff 2 XP (2→0 unspent, matches run-2 meta); Medical Texts 01035 new level-0 = max(1,0) = 1 XP (1→0 unspent, matches run-3 meta). Totals earned 3 / spent 3 / unspent 0 ✓, never negative at any step.
- **Deck legality:** all three decks count exactly 30 (signatures 01008/01009, weakness 01097 Paranoia, story asset 01117 Lita excluded); max-2-per-title holds across levels (Blinding Light 0 + 2 = 2 copies); every card is Seeker 0–5, Mystic 0–2 (Blinding Light 2 is the ceiling), or Neutral — legal for Daisy; signatures and Paranoia present in all three decks, never removed; Lita appears only from deck-2 onward, after being earned in scenario 1 and explicitly included (`lita_in_deck: true`).
- **Continuity (as far as it is auditable given Finding 1):** scenario 1 started dmg 0/5 at Study; scenario 2 started dmg 1/5 at Your House (house standing ✓); Ghoul Priest alive → shuffled into the MM encounter deck (drawn R3 in both candidate runs) ✓; DB setup placed 3 doom for 5 got-away cultists (⌈5/2⌉) ✓, added the elderthing token ✓ (also in `chaos_bag_additions`), past_midnight false → no opening-hand discard ✓; Lita in the scenario 3 deck and drawn in play ✓; killed investigator recorded, campaign correctly terminal (`next: null`, phase complete).

One finding, but a high-severity one: the campaign's recorded history is not the history this lane actually played.
