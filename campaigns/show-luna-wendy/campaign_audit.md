All checks are complete. Here is the campaign-layer audit report for show-luna-wendy.

# Campaign audit — show-luna-wendy (Wendy Adams, Return to NOTZ, seed 9405)

**AUDIT CLEAN** — the XP ledger, all three materialized decks, and every cross-scenario continuity hook reconcile exactly. Two unverifiable setup magnitudes and one known-family cosmetic are noted below, none filed as findings.

## 1. XP ledger — reconciled to the point

- **S1 (Return to The Gathering, no_resolution):** 2 VP (victory display) + 2 insight bonus = **4 XP** ✓ (per adjudication #2). Benchmark score 4 − 1 trauma = 3 ✓.
- **S2 (Return to The Midnight Masks, R2):** 0 VP, and MM has no resolution bonus → **0 XP** ✓, score 0 ✓.
- **S3 (Return to The Devourer Below, no_resolution, killed):** 0 VP → **0 XP** ✓, score max(0, 0−1) = 0 ✓. Campaign score 3 ✓.
- **Spending** (deck-1 → deck-2, the only upgrade window with XP): Elusive 01050 new at level 0 = max(1,0) = 1; Leo De Luca 01048→01054 same-title upgrade = level 1−0 = 1; Lucky! 01080→01084 = level 2−0 = 2. Total **4 spent**, matching `xp_spent_total: 4`, `xp_unspent: 0`. Ledger sequence 0 → +4 → −4 → 0 → 0, never negative ✓. deck-2 = deck-3 with 0 XP available ✓ (nothing bought after S2).

## 2. Deck legality over time

- **Counted size:** exactly 30 in all three decks, correctly excluding signatures (01014 Wendy's Amulet, 01015 Abandoned and Alone), the basic weakness (01096 Amnesia), and story asset 01117 Lita. Transcript deck counts corroborate: run 1 opens h5+d28 = 33 (30+2+1); runs 2–3 open h5+d29 = 34 (with Lita) ✓.
- **Title cap across levels:** Leo De Luca 01048×1 + 01054×1 = 2 ✓; Lucky! 01080×1 + 01084×1 = 2 ✓; everything else ≤ 2 ✓.
- **Access:** Wendy = Survivor 0–5, Rogue 0–2, Neutral 0–5. All Rogue cards (Switchblade, Pickpocketing, Leo 0/1, Elusive, Backstab) are level ≤ 1 ✓; Lucky!(2) is Survivor ✓; deck-1 is all level-0 ✓. The six pre-campaign `deckbuild_swaps` (Guts←Dig Deep ×2, Unexpected Courage←Knife ×2, Switchblade←Scavenging ×2) are all level-0-for-level-0 free swaps, exactly reflected in deck-1 ✓.
- **Persistence:** signatures and Amnesia present in every deck, never removed ✓; Lita appears only from deck-2 onward, after being earned in S1 (`lita_earned`) and explicitly included (`lita_in_deck`) ✓; Psychosis (01099), gained mid-S3, lands in the final campaign deck's weakness list — no deck-4 exists to require more ✓.

## 3. Continuity

- **Trauma:** S1 delta physical 1 (simultaneous 8/8 defeat resolved as a *single* chosen trauma per the batch-10 rule ✓) → both run 2 and run 3 open at `dmg1/7 hor0/7` ✓. Final trauma 2/0 = 1+0+1 ✓.
- **House standing** → run 2 begins at **Your House** ✓ (scenario_reference.md line 95).
- **Ghoul Priest alive** → directly observed shuffled into Return MM: drawn from the encounter deck R4 and spawned at Your House. Never defeated there (0 enemies defeated) → `ghoul_priest_alive` stays true ✓.
- **Cultists got away (6):** the 5-card Return cultist deck (Cooper, Pierce, Warren, Turner, Devereux — Herman/Wolf-Man/Alma the three removed) plus Narôgath from the randomized agenda back; none defeated or interrogated, so all 6 recorded ✓. Flows verbatim into S3's setup inputs, producing **3 setup doom on agenda 1a** (5–6 got away → 3 doom, the guide table previously adjudicated in ledger 45) with a proper log line naming them ✓.
- **Past midnight** (R2 in MM) → recorded, flows to DB inputs, opening-hand discard fired at S3 setup, and the **elderthing token** was added at DB setup and recorded in `chaos_bag_additions` — present only in run 3's bag ✓.
- **Killed:** Wendy killed by DB no-resolution (per campaign guide, adjudication 54's second half), `killed_investigators: ["wendy"]`, `phase: complete`, `next: null` — she never returns ✓.
- **Ledger-25 fix holding:** `cultists_got_away`/`past_midnight` survived the Devourer recording in the final campaign log ✓.

## Noted, not filed (cannot ground in in-scope sources)

1. **Past-midnight discard was 2 cards** ("Look what I found!" and Backstab). No in-scope document states the count (docs_agent is silent on DB setup; the Return scenario card 50032a defers to the core guide with no modification of this rule; access to the guide PDF was denied this session). All four past-midnight showcase lanes consistently discard 2, and run 3's scenario auditor called it "previously-adjudicated" — but **no such adjudication exists in the ledger I was given**. My recollection of the core guide leans toward "each investigator discards 1 random card," so this deserves a one-line check against `data/rules/night_of_the_zealot_campaign_guide.pdf` by whoever holds it. Peer campaign audits (luna-agnes, terra-skids) flagged the identical gap.
2. Run 2's `state.json` carries a defaulted `"owner": "roland"` on 7 encounter-card instances in this Wendy solo game — same hardcoded-identity family as ledger 83/109, state-representation only, already noted by the terra-skids lane.
