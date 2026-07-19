Now let me look up all the card codes appearing in the decks.
Card identities established. Now let me examine the run state files and transcripts for XP/victory verification and continuity checks.
Run 2's victory display contains `setaside_agenda_enemy` (50026b) — worth checking. Let me read run 3's state and check what 50026 is.
Masked Hunter is Victory 2 — VP 2 = XP 2 checks out. Now let me examine the setup sections of each transcript for continuity.
Key continuity facts verified in run 3's setup. Let me check run 2's setup for the Ghoul Priest shuffle and house handling, and run 1's opening.
The log.md files omit setup details. Let me check the jsonl event logs for setup events and trace the Masked Hunter victory in run 2.
The hidden blob is marked DO NOT READ — I'll respect that and rely on visible evidence. Let me check the DB transcript for got-away cultist spawns and the agenda flow.
No named got-away cultists appear in run 3 beyond the setup doom line. Let me examine the agenda-advance sections closely.
Let me verify the one defeated enemy in run 1 had no Victory value (VP 0 claim), and check run 2's Masked Hunter/Narôgath defeat path.
Run 2 ended with "Time Is Running Short" at stage 2 — let me verify the midnight ending sequence and check the run-2 cultist deck mechanics briefly.
Let me check whether the Past Midnight discards in run 3 offered a player choice.
The Past Midnight discards were auto-selected with no player decision. Let me check the RR discard rule and look for any other docs that quote the DB setup text.
The guide settles several checks. Let me verify the resolution XP text for all three scenarios.
All resolution XP rules verified against the guide. One loose end: the `enemies_defeated` counter. Let me check how run 3's Grave-Eater died.
Let me check the campaign_summary.json for consistency with campaign.json.
The audit is complete. All evidence reconciles — one display-level discrepancy found. Here is my report:

---

## Finding 1 — `result.json` `enemies_defeated` undercounts defeats from asset fights and reaction damage (runs c-show2-sonnet-agnes-2, c-show2-sonnet-agnes-3) — DISPLAY

**Evidence.**
- Run 2 (return_to_the_midnight_masks): log.md R7 Investigation — "Fight with Shrivelling: success by 2… Narôgath took 2 damage. **Narôgath was defeated.**" and `limits.last_defeated_enemy_location: "southside"` matches — yet `result.json` reports `"enemies_defeated": 0`.
- Run 3 (return_to_the_devourer_below): log.md R4 Enemy — Grave-Eater defeated by Agnes's reaction damage ("Grave-Eater was defeated"); R9 Investigation — Acolyte of Umôrdhoth defeated by Shrivelling ("Acolyte of Umôrdhoth was defeated"); `last_defeated_enemy_location: "great_willow"` reflects the Acolyte — yet `result.json` reports `"enemies_defeated": 0`.
- Run 1 (control): the lone basic-**Fight**-action defeat (R6, "Fight Swarm of Rats") *was* counted (`enemies_defeated: 1`).

The counter increments on basic Fight-action defeats only; asset-fight (Shrivelling) and reaction-damage (Agnes) defeats are missed in 2 of 3 runs. **Impact:** stats/display only — XP derives from the victory display, which is correct in all three runs (run 1: empty, VP 0; run 2: Narôgath Victory 2, VP 2; run 3: empty, VP 0), and no campaign-log field consumes this counter.

---

Everything else audits **CLEAN**:

**1. XP LEDGER — clean.** Scenario 1: Victory 0 + 2 insight (Gathering no-resolution rule, verified in guide) = 2 XP ✓; lead earns Lita ✓. Scenario 2: R2 = Victory X only (Narôgath 50026b, printed Victory 2, in victory display via combat-defeat interrogation) = 2 XP, no bonus ✓. Scenario 3: DB no-resolution kills each surviving investigator, no XP ✓. Purchases: window 1 = Blinding Light (0)→(2) same-title upgrade at level-difference 2 XP; window 2 = Guts (0) + Perception (0) at 1 XP each with a removal per purchase. Deck-diff costs sum exactly to `xp_spent_total` 4 — no hidden churn. Totals 4 earned / 4 spent / 0 unspent, consistent and never negative at every step ✓.

**2. DECK LEGALITY — clean.** deck-1: 30 counted + 2 signatures (Heirloom/Dark Memory) + 1 basic weakness (Haunted) = 33, and consistent with the three recorded free deckbuild swaps (each swapped-out title retains 1 copy, implying 2 pre-swap — a legal 30-card base). deck-2/3: 30 counted + 2 signatures + 1 weakness + Lita (exempt per guide) = 34. Max 2 copies per title ✓; Agnes's access (Mystic 0–5 / Survivor 0 / neutral 0) respected including Blinding Light (2) ✓; signatures present, weaknesses never removed, Psychosis (earned during DB agenda-2) persists into the final campaign deck, Lita appears only from deck-2 onward ✓. Run-time card usage matches each leg's deck (Baseball Bat/Knife absent from run 3; Guts/Perception present) ✓.

**3. CONTINUITY — clean.** Mental trauma 1 (horror defeat at 8/8 in run 1) → both run 2 and run 3 start at horror 1 (timeline state + status lines) ✓. House standing → run 2 starts at Your House with that location in play ✓. Ghoul Priest alive → run-2 encounter deck count 24 = 23 (documented Return MM pool) + 1 ✓; never drawn. 5 cultists got away (4 in cultist deck + 1 in play at MM end — matches the guide's "Cultist deck or in play" recording) → DB setup placed exactly 3 doom per the guide table (5–6 names → 3 doom) ✓. Past midnight → 2 **random** discards from the starting hand (guide text is random, so no player decision owed) ✓. Elderthing token added unconditionally ✓ (setup log, run-3 bag, `chaos_bag_additions`). DB no-resolution → Agnes killed, `arkham_succumbed`, campaign `complete` with `next: null` ✓; MM-era log fields (cultists_got_away, past_midnight) survived DB recording ✓.
