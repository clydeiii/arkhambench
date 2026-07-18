Audit complete. All dimensions checked; two findings, one primary and one minor.

## Finding 1 — Final `campaign record` drops banked XP: `xp_unspent` zeroed, breaking the ledger identity

**Campaign step:** recording of scenario 3 (`return_to_the_devourer_below`) → final `campaign.json`

**Evidence (all from this campaign's own files):**
- Per-scenario earned XP recomputes cleanly: 3 (Gathering: VP 1 + 2 no-resolution insight) + 2 (MM R2: Narôgath VP 2, no resolution bonus per the scenario reference) + 0 (DB, killed) = **5** = `xp_earned_total` ✓
- Purchases recompute cleanly from the deck diffs: deck-1→deck-2 replaced one Blinding Light (01066, L0) with Blinding Light (01069, L2) = 2 XP; deck-2→deck-3 did the same for the second copy = 2 XP. Total **4** = `xp_spent_total` ✓
- The step-by-step ledger is confirmed by the run meta files: `runs/c-show-luna-agnes-2/meta.json` records `xp_unspent: 1` entering scenario 2, and `runs/c-show-luna-agnes-3/meta.json` records `xp_unspent: 1` entering scenario 3 — correct at every step (0 → 3 → 1 → 3 → 1 → 1), never negative.
- Scenario 3 earned 0 XP and no upgrade window followed, so the final value must remain **1**. `campaign.json` records `xp_unspent: 0` — the campaign guide's own banking rule ("You may bank XP") implies unspent = earned − spent, and 5 − 4 = 1 ≠ 0.

**Corroboration that this is systematic, not a one-off:** `show-sol-skids` shows the same signature — earned 6 (5+0+1), spent 5, pre-scenario-3 `meta.json` unspent 0, scenario 3 earned 1, final `xp_unspent: 0`. In both cases the final scenario's record step lost exactly the residual XP (agnes: a pre-existing bank of 1 clobbered to 0; skids: 1 XP earned in the final scenario added to `xp_earned_total` but never to `xp_unspent`). Every other showcase campaign happened to end with earned == spent, which masks the defect. Possibly the killed-investigator/campaign-complete path resets or skips the unspent update; no rule in the campaign guide authorizes forfeiting banked XP without adjusting the earned/spent totals to match.

## Finding 2 — `enemies_defeated: 0` in scenario 2's result despite Narôgath being defeated (stat layer only)

**Campaign step:** `runs/c-show-luna-agnes-2/result.json`

Run-2's log shows "Narôgath was defeated" (R5: 3 Shrivelling hits ×2 dmg + Agnes's reaction = 7 = his solo health 4+3), and he sits in the victory display (`50026b`, Victory 2 — which correctly produced `victory_points: 2`, `xp: 2`, and the `cultists_interrogated: [Narôgath]` entry since he carries the Cultist trait). But `enemies_defeated` is 0. Run-1's counter worked (3 defeats → 3), so the agenda-back special instance (`setaside_agenda_enemy`) bypasses the defeat counter. XP/score are unaffected; this only corrupts the result stats consumed downstream (e.g. the benchmark dossier).

## Everything else — clean

- **Deck legality:** all three decks have exactly 30 counted cards (signatures 01012/01013, weakness 01098 Haunted, and story asset 01117 excluded); max 2 per title holds including the split Blinding Light 0/2 in deck-2; every card is within Agnes's access (Mystic 0–5, Survivor 0, Neutral — Blinding Light 2 is the only XP card); signatures and Haunted persist in all three decks; Lita appears only in decks 2–3, after being earned (run-1 story zone) and included. The pre-campaign free swaps (Baseball Bat ×2 → Blinding Light ×2, Knife ×2 → Ward of Protection ×2) are level-0-for-level-0 and legal. Opening deck counts in the transcripts match (28 undrawn of 33 in run 1; 29 of 34 in runs 2–3 with Lita added).
- **Continuity:** trauma 1 physical after scenario 1 appears as starting `dmg1/6` in both later transcripts; final trauma 2 = 1+0+1 ✓. House standing → run 2 starts in Your House ✓. `ghoul_priest_alive` propagates into both later scenarios' setup inputs ✓ (never drawn; undrawn deck contents are hidden, so shuffle-in isn't directly observable). 5 cultists got away → 3 setup doom on agenda 1a, logged ✓; past midnight → opening-hand discard fired ✓; elderthing token added at DB setup and recorded in `chaos_bag_additions` ✓. Agnes killed in the final scenario, campaign completed with `next: null` — no return ✓. Benchmark scores also recompute (XP − trauma, min 0: 2/2/0, campaign score 4) ✓.
- **Noted, not reported:** the Past Midnight discard was 2 cards; the allowed docs don't state the count and all four past-midnight campaigns across the showcase consistently discard 2, so I have no authority to ground a finding against it — flagging for whoever holds the Return campaign guide PDF.
