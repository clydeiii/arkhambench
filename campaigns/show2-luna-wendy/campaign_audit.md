I'll start by exploring the campaign directory structure and reading the core files.
Now the rules docs:
Let me read the scenario reference and check the campaign-flow rules:
Now let me look up all the cards involved in the decks. I'll batch the lookups:
The card output needs the level field — let me see full output:
The level pips aren't shown. Let me check the CLI options:
No level display. Let me get the remaining card identities first, then figure out levels:
I have card identities but need levels. Let me check run metadata and logs for deck listings with levels:
`upgrade options` is read-only (errored cleanly, no mutations). I need card levels via a legit channel. Let me create a scratch campaign in the pre-approved temp dir to query the level lists:
The starter is confirmed all level-0. Now I need levels for the purchased cards (01054, 01084) — let me flip the scratch campaign to upgrade phase and query prices:
All three purchase prices confirmed: 01054 = level 1 (1 XP upgrade), 01084 = level 2 (2 XP upgrade), 01093 = level 0 (1 XP new). Now let me restore the global pointers and verify continuity in the transcripts:
Run 2 opens at Your House with dmg 1/7 — trauma and house-standing continuity confirmed. Now the Ghoul Priest shuffle-in and run-3 setup:
Ghoul Priest was shuffled into the MM deck (drawn R4) ✓. Now run-3 setup facts:
Run-3 setup shows trauma (dmg1/hor1), got-away doom, and elderthing token. Now check the got-away cultist spawns in DB and the per-run campaign inputs:
All campaign inputs flowed correctly. Let me check run-3's end state for the got-away cultist spawn mechanism and agenda status:
The game reached the final act but no got-away cultist spawns appear in the log. Let me check the DB act/agenda card text for the spawn trigger:
The act was replaced via agenda 3's Forced while still at Act 1 — so act-1b's cultist spawn legally never fired. One final cross-check: deck sizes in the status lines of each run:
All deck counts reconcile. Final verification — victory displays in each run's end state to recompute XP independently:
All three dimensions fully reconcile. Final verification is complete — no discrepancies found anywhere.

## AUDIT CLEAN

**Campaign:** show2-luna-wendy (Return to NotZ, standard, seed 9405) — 3 legs, Wendy killed in the finale.

### 1. XP LEDGER — verified at every step

| Leg | Result recompute | XP |
|---|---|---|
| 1 · Return Gathering, no_resolution | VP 1 (Attic 01113, Victory 1, in victory display) + 2 insight XP (per adjudicated no-resolution rule) + Lita earned | **3** ✓ |
| 2 · Return MM, R1 | VP 1 (Jeremiah Pierce in victory display) + 0 (MM has no resolution bonus) | **1** ✓ |
| 3 · Return DB, no_resolution | VP 0 (empty victory display) | **0** ✓ |

Purchases (reconstructed from deck diffs, prices confirmed via `upgrade options` on a scratch campaign):
- **Window 1** (3 XP banked): Leo De Luca 01054 (same-title upgrade of 01048, level diff 0→1 = **1 XP**) + Lucky! 01084 (upgrade of 01080, level diff 0→2 = **2 XP**) = 3 XP → unspent 0 ✓
- **Window 2** (1 XP banked): Unexpected Courage 01093 (new, level 0 → max(1,0) = **1 XP**, removed 01077) → unspent 0 ✓

Stepwise unspent: 0→3→0→1→0→0 — never negative; corroborated independently by `xp_unspent: 0` in run-2 and run-3 `meta.json` campaign inputs. Totals: earned 4 = spent 4, unspent 0 ✓ (kill-zeroing moot at 0).

### 2. DECK LEGALITY — verified per deck

- **deck-1**: 30 counted + 2 signatures (01014/01015) + Amnesia = 33 ✓; matches the fixed starter + the 4 recorded free deckbuild swaps (01078→01050 ×2, 01086→01089 ×2); every counted card confirmed in the engine's level-0 pool ✓
- **deck-2/deck-3**: 30 counted + signatures + Amnesia + Lita = 34 ✓ (physical counts confirmed in-game: d28/d29/d29 after opening draws)
- Title caps across levels: Leo De Luca 01048×1+01054×1 = 2 ✓; Lucky! 01080×1+01084×1 = 2 ✓; all others ≤2 ✓
- Access (Survivor 0–5, Rogue 0–2, Neutral 0–5): 01054 Rogue-1 ✓, 01084 Survivor-2 ✓, 01093 Neutral-0 ✓
- Signatures never removed ✓; Amnesia never removed ✓; Lita persists deck-2→3 ✓; Psychosis 01099 (gained in leg 3) carried into the final campaign deck ✓

### 3. CONTINUITY — verified against transcripts

- Trauma: phys 1 → run-2 starts `dmg1/7 hor0/7` ✓; +mental 1 → run-3 starts `dmg1/7 hor1/7` ✓; totals 2/1 match deltas ✓
- House standing → MM start at Your House ✓; Ghoul Priest alive → shuffled into MM deck (drawn R4) ✓
- Got-away (5 cultists) → 3 setup doom on DB agenda 1a with all 5 named ✓ (per adjudicated campaign-guide table); act-1b cultist spawn legally never fired — agenda 3's Forced replaced the act while still at Act 1 (log: "Ritual Site entered play… The Devourer Below replaced the act and agenda") ✓
- past_midnight false → no opening-hand discard in DB ✓; elderthing token added (unconditional bullet) ✓
- Wendy killed by DB no-resolution → `killed_investigators: ["wendy"]`, phase `complete`, `next: null` — never returns ✓
- Lita absent from deck-1, present deck-2 onward, exactly after earning ✓

Method note: card levels aren't printed by `./ahlcg card`; I confirmed purchase prices/levels through a scratch campaign's `deckbuild options`/`upgrade options` in the temp dir (repo pointers backed up and restored; `git status` confirms no files modified).
