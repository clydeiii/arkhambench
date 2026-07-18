All evidence is in hand. The audit is complete — every dimension checks out except one major data-integrity issue at the scenario-1 boundary.

## Finding 1 — Scenario 1 is recorded from a different campaign's run (cross-lane contamination; ledger-108 residue never repaired in data)

**Campaign step:** scenario 1 record (`campaigns/show-terra-roland/campaign.json`, scenarios[0])

**What the record says:** Terra-roland's scenario 1 (`return_to_the_gathering`, no_resolution, XP 2, +2 mental trauma) points at `run: /Users/clyde/ahlcg/campaigns/show-sol-roland/runs/c-show-sol-roland-1` — a run directory belonging to the **show-sol-roland** campaign.

**Evidence that the recorded game is genuinely sol's, not terra's:**
- Terra's own run dir `runs/c-show-terra-roland-1` exists but has **no result.json**; its state.json is `in_progress`, Round 4, mid-skill-test (Investigate Bathroom, commit-cards decision pending). The game was abandoned, never completed, never recorded.
- `c-show-sol-roland-1/meta.json` binds that run to `deck: .../show-sol-roland/decks/deck-1.json`, which **differs from terra's deck-1** (sol: 2× .45 Automatic / 1× Flashlight; terra: 1× .45 / 2× Flashlight). The recorded game was played with the other lane's deck.
- Timestamps show the race: terra-1 last updated 17:53:18; sol-1 created at that exact second (the `.current_run` pointer flip from ledger 108, which names this campaign as the wedged victim).
- **show-sol-roland's campaign.json records the same run as *its* scenario 1** — one physical game is double-counted into two campaigns.

**Why it matters (campaign-layer impact):** every downstream campaign fact in terra-roland derives from sol's game — the 2 XP that funded the Beat Cop(0)→Beat Cop(2) upgrade, the 2 mental trauma carried into Midnight Masks, and the log facts (lita_earned, ghoul_priest_alive, your_house_standing). For a model-comparison benchmark, terra's lane is credited with a scenario it did not play, and its actual game 1 sits orphaned and unfinished. The harness bug itself is adjudicated and fixed (ledger 108); this finding is that the **data was never repaired** — analogous to ledger 58, where contaminated results were flagged "must be rerun." Terra's scenario 1 (and everything downstream of it, i.e. the whole campaign) is built on the contaminated record.

---

Everything else is **clean**. What I verified:

**XP ledger.** Scenario 1: no_resolution Gathering = VP 0 + 2 insight = 2 XP (matches adjudication #2 — though the game is sol's, see Finding 1). Scenario 2: MM resolution R1 (defeated before midnight is the no-resolution route to R1), VP 0, 0 interrogated → 0 XP. Scenario 3: DB no_resolution, killed, 0 XP. The single purchase is a same-title upgrade — Beat Cop(0) 01018 → Beat Cop(2) 01028 via replace — costing the level difference of 2. Ledger at every step: 0 → earned 2/unspent 2 → spent 2/unspent 0 → final earned 2 / spent 2 / unspent 0, never negative. ✓

**Deck legality over time.** All three decks count exactly 30 (signatures 01006/01007, weakness 01102, and Lita 01117 excluded). Signatures and the basic weakness are present in every deck and never removed. Max 2 per title holds across levels (Beat Cop 0 ×1 + Beat Cop 2 ×1). All cards are within Roland's access (Guardian up to 5 — covers Beat Cop 2; Seeker 0 — Magnifying Glass, Working a Hunch, Deduction; neutrals). The eight deckbuild swaps are all level-0 cards in the free pre-campaign window. Lita appears only from deck-2 onward, after being earned and included, and persists to deck-3. ✓

**Continuity.** Trauma accumulates 2+1+1 = 4 mental, matching campaign totals, and shows up as starting horror in each next scenario (run-2 opens at hor2/5, run-3 at hor3/5). Campaign-log facts flowed into setup correctly: run-2 starts at Your House (house standing), received ghoul_priest_alive/lita inputs, deck count d29 after a 5-card opening hand confirms the 34-card deck including Lita; run-3 setup logged 3 doom for the 6 got-away cultists (correct 5–6 bracket), added the elderthing token, applied no past-midnight hand discard, and carried the full got-away list. The DB record did not clobber the MM log fields (ledger-25 fix holds). Roland's death in the final scenario is recorded (killed_investigators, arkham_succumbed), phase is complete, next is null. ✓

One finding total, and it's an artifact of the already-adjudicated ledger-108 race rather than a new engine rule violation — but the terra-roland campaign's results should be treated as contaminated until scenario 1 is rerun and re-recorded in its own lane.
