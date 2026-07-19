Let me read the rules docs and look up the cards in these decks.
The card output doesn't show XP level explicitly. Let me check how levels appear and look up the remaining codes.
Now the rules reference, then the run transcripts for continuity checks.
The hidden state is sealed — I'll respect that and check mission.md/timeline.jsonl instead.
Let me check whether other campaigns in this wave also swapped in leveled cards (to gauge whether the swap pool allows it), and verify encounter-deck setup counts.
All structural checks pass. Final verification of difficulty/seed wiring across the three run metas.
One last materiality check — was Leo actually played in scenario 1?
All checks are complete. Here is the campaign-layer audit.

---

# Campaign-layer audit — show2-sonnet-skids (Return to NotZ, standard, seed 9403)

Scope: campaign.json, deck-1/2/3.json, the three run dirs' result.json/meta.json/log/state artifacts (transcript internals excluded — run-1 already carries its own AUDIT CLEAN; runs 2–3 audited separately). Card facts via `./ahlcg card`.

## What verified clean (summary)

**XP ledger — fully determined and consistent at every step.**
- S1 (Gathering, no_resolution): VP 1 + 2 insight bonus (per adjudication #2) − Hospital Debts 0 = **3** = result.xp = xp_earned ✓
- S2 (MM, R2): VP 2 − Hospital Debts penalty 2 = **0** ✓ (floored, never negative)
- S3 (DB, no_resolution): VP 0 = **0** ✓
- Window 1 (deck-1→deck-2): +Elder Sign Amulet 01095 (level 3, new card = 3 XP), −Knife 01086 (free removal, deck stays 30). Elder Sign Amulet's 3-XP price is independently proven by show2-sonnet-wendy's window-1 (only net change = +01095, xp_spent_total exactly 3) and show2-luna-agnes's (Guts 1 + 01095 = 4). run-2 meta pins xp_unspent at **0** after the window ✓ — no hidden churn is arithmetically possible (3 earned = 3 spent).
- Window 2 (deck-2→deck-3): identical decks, 0 earned, 0 spent; run-3 meta xp_unspent **0** ✓
- Final: earned_total 3, spent_total 3, unspent 0; 3−3=0 at every step, never negative ✓

**Deck legality.** All three decks: exactly 30 counted cards ✓, signatures (01010/01011) present ✓, Mob Enforcer (01101) never removed ✓, Psychosis (01099, gained in S3 per result `weakness_gained`) present in the final campaign deck ✓, Lita (01117) only in deck-2/3 — after being earned in S1 and included — and exempt from the 30-count (34 physical = 30+2 sig+1 wk+1 Lita, per #123) ✓, max 2 copies per code ✓, all cards within Skids access (Rogue 0–5/Guardian 0–2/Neutral 0–5; highest = Elder Sign Amulet, Neutral lvl 3) ✓. Every player card that surfaced in any run (⊆ scan of all timeline snapshots + end states) belongs to that leg's deck file; zero foreign cards; metas bind deck-1/2/3 to legs 1/2/3 ✓.

**Continuity.**
- Trauma: S1 mental +1 → run-2 starts at hor1 (meta trauma `{mental:1}`, status `hor1/6`) ✓; S2 Δ0 → run-3 hor1 ✓; campaign trauma = Σ deltas = mental 1 ✓
- House standing → run-2 start location `your_house` ✓
- Ghoul Priest alive → shuffled in: cross-campaign natural experiment — every priest-alive MM leg has encounter deck 24 vs 23 for the one priest-dead leg (show-sol-skids); DB 32 vs 31. This campaign: 24 and 32 ✓
- Past midnight → exactly 2 random discards from the finalized opening hand in run-3 ✓
- Cultists got away (6) → 3 setup doom on agenda 1a, per the adjudicated campaign-guide table (#45) ✓; got-away spawns are owed only on Act-1 advance — run-3 ended at Act 1 stage 1, none owed ✓
- Elderthing token → added at run-3 setup, present in run-3's end bag, absent from runs 1–2 bags; `chaos_bag_additions: ["elderthing"]` ✓
- Killed: Skids killed by DB no-resolution (per #54) → `killed_investigators: ["skids"]`, phase complete, next null, no fourth leg ✓
- Campaign-log fidelity: every result.json campaign block (house standing, lita earned, priest alive, past_midnight, 6-name got-away list, arkham_succumbed, ritual_broken/umordhoth_repelled false, lita_sacrificed false) matches campaign.json exactly; scores 2/0/0 ✓; seeds 940301–03 and standard difficulty wired correctly ✓

## Finding 1 — Free deckbuild swap added a level-1 card (Leo De Luca, 01048) at campaign start (deckbuild phase → deck-1.json)

docs_agent/campaign_guide.md restricts the opening deckbuild window to level-0 cards: *"Use `./ahlcg deckbuild options` to see legal implemented **level-0** swap-ins"* and *"optionally use `deckbuild ...` to make **free level-0 swaps**. Swaps cost 0 XP and are only available at campaign start"* — after which *"level-0 additions happen through the normal upgrade window and cost 1 XP."*

campaign.json `deckbuild_swaps` records two pre-scenario-1 swaps: `in 01016 / out 01087` (.45 Automatic, level 0 — legal) and **`in 01048 / out 01045` (Leo De Luca — level 1)**. Leo De Luca is the level-1 Rogue ally (6-cost, "You may take an additional action during your turn"; adjudication ledger #44 itself refers to 01048 as *"the level-1 copy"*). deck-1.json carries `01048: 1`, and run-1's card stream confirms he entered the deck (drawn R2, committed R3).

**Effect:** a card priced at max(1, level) = 1 XP entered the campaign deck for 0 XP, bypassing the XP economy the guide states (pro-player; materiality modest here — Leo was committed once for +1 intellect in S1 but occupied a deck slot all three legs).

**Note for adjudication:** the identical `01048-for-01045` swap appears in show2-luna-skids (which also swapped in 01051), so the swap pool itself apparently admits leveled cards rather than this being a one-off validation lapse. One nuance in the engine's favor: decks_guide.md has Wendy's *starter* include Leo, so leveled cards exist in the fixed starters by design, and campaign-start deckbuilding proper permits any in-class level — meaning either `deckbuild swap`'s pool/validation fails to enforce the documented level-0 restriction, or the guide's "level-0 swaps" wording misstates the pool. As written, the recorded history violates the stated campaign-layer rule; the XP ledger itself remains exactly consistent because the swap was recorded at 0 XP.
