Now let me look at the rules reference, the run directories, and the campaign summary.
Now let me examine the scenario transcripts' setup sections for continuity (trauma carry-over and campaign-log-driven setup).
Setup facts from the transcripts so far: scenario 2 starts at Your House with `hor1/5` (trauma carried); scenario 3 shows past-midnight discards, elderthing added, and "Setup placed 2 doom from cultists who got away" with 4 cultists listed. I need to verify that doom amount against the campaign guide's chart.
The hidden deck is sealed. Let me check the structured setup events in `log.jsonl` and `meta.json` for how the encounter deck was composed.
The level isn't shown in the first lines. Let me see the full card output format:
Chaos bags and trauma are all consistent. Let me check the run-3 threat area (Cover Up end-state), run-1/run-3 meta, and confirm the DB no-resolution text has no XP grant:
All guide checks pass. One last XP cross-check — scenario 2's victory display values must sum to the granted 4 XP:
**AUDIT CLEAN**

Campaign layer of `show2-luna-roland` verified across all three dimensions; every value reconciles against the campaign guide, the scenario reference, and exact card text.

**1. XP ledger** — consistent at every step:
- S1 (Gathering, no resolution): victory display = Flesh-Eater (victory 1) + Field of Graves (victory 1) = VP 2, + 2 insight bonus (adjudication #2) = **4** ✓
- S2 (MM, R2): Narôgath (victory 2) + Victoria Devereux (victory 1) + Miskatonic University (victory 1) = VP 4, no MM resolution bonus = **4** ✓
- S3 (DB, no resolution): VP 0; the guide's no-resolution block grants no XP = **0** ✓
- Window 1: Dynamite Blast 0→(2) (50002, replace 01024) = 2 XP + Beat Cop 0→(2) (01028, replace 01018) = 2 XP → 4 spent ✓
- Window 2: Physical Training 0→(2) (50001, replace 01017) = 2 XP + 2nd Beat Cop (2) (new copy at max(1,2) = 2 XP, removing the last 01018) → 4 spent ✓
- earned_total 8 = spent_total 8, unspent 0, never negative at any checkpoint; run metas show xp_unspent 0 entering each scenario.

**2. Deck legality** — all three decks exactly 30 counted cards (deck-1: 33 physical; deck-2/3: 34 physical = 30 + 2 signatures + 1 weakness + Lita, exempt per guide); deck-1 is byte-identical to the killbray base + the 6 recorded deckbuild swaps, all level-0↔level-0; ≤2 copies per title across levels at every step (Beat Cop 1+1 then 2+0, Physical Training 1+1); all cards Guardian/Seeker-0/neutral (Roland-legal); signatures 01006/01007 always present; weakness 01102 (Silver Twilight Acolyte) never removed; Lita appears only in decks 2–3, after being earned in S1; campaign.json's final deck block matches deck-3.json exactly.

**3. Continuity** — all verified in the transcripts/state:
- Trauma +1 mental (S1 horror defeat, Cover Up absent from threat area) → run-2 opens at `hor1/5`; +0 (S2) → run-3 opens at `hor1/5`; +1 mental (S3) → final {mental 2, physical 0} ✓
- House standing → S2 starts at Your House ✓; Ghoul Priest alive → shuffled into the MM deck (end-count 16 = 24 − 7 draws − 1 search; impossible at 23) and into the DB deck (spawned from it in R2) ✓
- 4 cultists got away → exactly 2 doom on Agenda 1a, matching the guide's 3–4-names row ✓; got-away/interrogated lists reconcile with the 5-card cultist deck (1 interrogated + 4 got away; Narôgath via victory display; 3 removed-unseen correctly unrecorded) ✓
- Past midnight → 2 opening-hand discards ✓; elderthing token present only in run-3's chaos bag and recorded in `chaos_bag_additions` ✓
- Roland killed (DB no-resolution — adjudicated #54) → `killed_investigators: ["roland"]`, phase `complete`, no scenario 4, no return ✓
- MM log fields (got_away, past_midnight) survive DB recording ✓; scores 3/4/0 match XP−trauma (floor 0), campaign score 7 ✓

The only anomaly sighted (duplicate `game_end` lines in run-3's jsonl) is ledger entry 119 — already adjudicated, display-only, and explicitly out of scope for re-report.
