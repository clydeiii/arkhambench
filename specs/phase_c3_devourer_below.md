# Phase C3 — The Devourer Below + Return to The Devourer Below

Scenario 3 of Night of the Zealot as `the_devourer_below` and
`return_to_the_devourer_below`, one module in the style of the earlier scenarios.
Solo only; all five investigators. Depends on C1 (shared Cultist machinery: Dark Cult /
Devourer's Cult sets, doom-on-enemies) and C2 (campaign inputs; standalone flags below
make it playable without a campaign).

Authority: campaign guide pp.6–7 + card JSON. Conflicts → flag, don't guess.

## Campaign inputs (CLI flags, defaults for standalone)

- `--cultists-got-away "<name>,<name>,..."` (default: empty). Drives BOTH the setup
  doom AND act-1-advance spawns (below). Names must match unique cultists from MM
  (core 01137–01141, return 50044–50046, "The Masked Hunter", "Narôgath").
- `--past-midnight` (default off): after drawing the opening hand (post-mulligan),
  discard 2 random cards from it.
- `--ghoul-priest-alive` (default off): shuffle Ghoul Priest into the encounter deck.
- `--lita-in-deck` (default off, standalone convenience): include Lita Chantler (01117)
  in the player deck as a story asset. (Campaign runner passes the real deck.)
- Chaos bag: this scenario's setup adds 1 `elderthing` token to the bag ("for the
  remainder of the campaign" — the campaign runner persists it; standalone: just add it
  at setup).

## Setup (original)

Encounter sets → deck (solo counts):
- The Devourer Below (`tentacles`): Umôrdhoth's Wrath ×2 (01158)
- Ancient Evils ×3 (01166)
- Striking Fear: Rotting Remains ×3, Frozen in Fear ×2, Dissonant Voices ×2
- Ghouls: Ghoul Minion ×3, Ravenous Ghoul ×1, Grasping Hands ×3
- Dark Cult (`pentagram`): Acolyte ×3, Wizard of the Order ×1, Mysterious Chanting ×2
- ONE random Agents set (seeded choice of 4): Agents of Yog-Sothoth (Yithian Observer
  ×2 + Offer of Power ×2) / Agents of Shub-Niggurath (Relentless Dark Young ×1 + Goat
  Spawn ×3) / Agents of Cthulhu (Young Deep One ×2 + Dreams of R'lyeh ×2) / Agents of
  Hastur (Screeching Byakhee ×2 + The Yellow Sign ×2). Remove the other three sets.
- (+ Ghoul Priest if flagged.)
Total 29 (+1). Assert in a test.

Locations:
- Main Path (01149) in play; investigator begins there (revealed).
- Shuffle the 6 Arkham Woods (01150–01155); choose 4 at random (seeded), put into play
  UNREVEALED ("without looking at their revealed sides"); remove the other 2.
- Set aside: Ritual Site (01156), Umôrdhoth (01157).

Setup doom on agenda 1a from got-away count: 0 → 0; 1–2 → 1; 3–4 → 2; 5–6 → 3.

## Location graph (transcribed + verified from scans)

Every Arkham Woods BACK is identical ("Arkham Woods", symbol: red square) and connects
only to Main Path (slant). On reveal, the front's own symbol and inter-woods
connections take over. Fronts:

- Main Path (slant): text "connected to each other Woods location" + printed Ritual
  Site (cross) and woods-back (square). Net: Main Path ↔ every woods (revealed or not)
  and ↔ Ritual Site (once in play).
- Ritual Site (cross): ↔ Main Path only. Starts out of play; enters via act/agenda.
- Woods fronts (own symbol → extra connections besides Main Path, which apply only
  when the other woods is IN PLAY and its side showing has that symbol — i.e. treat a
  printed front-symbol edge as live only when the counterpart location's revealed
  front matches; unrevealed woods are reachable only via Main Path):
  - 01150 Unhallowed Ground (triangle): ↔ Cliffside (hourglass), Old House (diamond)
  - 01151 Twisting Paths (T): ↔ Old House (diamond), Tangled Thicket (equals)
  - 01152 Old House (diamond): ↔ Unhallowed Ground (triangle), Twisting Paths (T)
  - 01153 Cliffside (hourglass): ↔ Quiet Glade (moon), Unhallowed Ground (triangle)
  - 01154 Tangled Thicket (equals): ↔ Twisting Paths (T), Quiet Glade (moon)
  - 01155 Quiet Glade (moon): ↔ Tangled Thicket (equals), Cliffside (hourglass)
  - Return woods: 50033 Great Willow (heart): ↔ Lakeside (star); 50034 Lakeside
    (star): ↔ Great Willow (heart); 50035 Corpse-Ridden Clearing (comma): ↔ Wooden
    Bridge (circle); 50036 Wooden Bridge (circle): ↔ Corpse-Ridden Clearing (comma).
  Edges are symmetric and only exist when both endpoints' fronts are in play (a woods
  edge to a removed-from-game or unrevealed woods simply never lights up; this is
  faithful to symbol-based connections).

Woods front behaviors (from JSON):
- Unhallowed Ground: Forced after you enter: test willpower(4), fail → 1 horror+1 dmg.
- Twisting Paths: Forced when you move OUT: test intellect(3), fail → cancel the move
  (action already spent).
- Old House: investigations here use WILLPOWER in place of the normal skill.
- Cliffside: investigations use AGILITY. Tangled Thicket: use COMBAT.
- Quiet Glade: `[action]`: heal 1 damage or 1 horror (limit once per turn).
- Great Willow (Return): Forced after you SUCCEED at a skill test on a treachery at
  this location: that treachery gains surge (group limit once/round).
- Lakeside (Return): Forced after revealing a chaos token while INVESTIGATING here:
  reveal and resolve an additional token (limit once per test — both apply).
- Corpse-Ridden Clearing (Return): enemies here cannot take more than 1 damage per
  attack against them.
- Wooden Bridge (Return): like Lakeside but for EVASION attempts.
- Main Path: `[action]`: Resign (→ no-resolution). Ritual Site: Forced at end of round:
  top up its clues to 2 per investigator (solo: 2) if fewer.

## Act / agenda decks

Agendas: 1 The Arkham Woods (01143, 4 doom) → 2 The Ritual Begins (01144, 5 doom) →
3 Vengeance Awaits (01145, 5 doom).

- Agenda 1→2: shuffle encounter discard into deck; discard from top until a MONSTER
  enemy is discarded; spawn it at Main Path with 1 doom on it.
- Agenda 2 front: each enemy +1 fight and +1 evade. 2→3: test willpower(6); on fail,
  add a random basic Madness weakness (core pool: Amnesia 01096 / Paranoia 01097) to
  your HAND (it is part of your deck for the rest of the campaign — emit it in the
  campaign block of result.json as `weakness_gained`).
- Agenda 3 advance ("Vengeance Awaits" Forced): if act 1 is current → put Ritual Site
  into play AND spawn set-aside Umôrdhoth there; if act 2 or 3 → discard all enemies
  at Ritual Site, spawn Umôrdhoth there. THEN the double-sided card becomes **"The
  Devourer Below"** — a combined current-act-AND-agenda: no further doom thresholds,
  no act clue objectives; sole Objective — if Umôrdhoth is defeated → R2. (Replace
  both decks with this single card; resign remains available.)

Acts: 1 Investigating the Trail (01146, clue cost 3/investigator → solo 3) →
2 Into the Darkness (01147) → 3 Disrupting the Ritual (01148).

- Act 1→2: spend 3 clues (group action at any location, standard act-advance
  mechanics as in existing scenarios). On advance: put Ritual Site into play (if not
  already); search the COLLECTION for each enemy named in `--cultists-got-away` and
  spawn ALL of them at Main Path. (Masked Hunter/Narôgath included — spawn them at
  Main Path, not engaged.)
- Act 2 objective: an investigator enters the Ritual Site → advance. On advance:
  shuffle encounter discard into deck; discard from top until 1 enemy is discarded;
  spawn it at the Ritual Site.
- Act 3: `[action]` spend 1 clue: test willpower(3) OR agility(3) (player choice);
  success → place 1 clue (from the token pool) on the act. Objective: 2 clues per
  investigator (solo: 2) on the act → advance → **R1**.

## Umôrdhoth (01157)

Unique Elite Ancient One. Fight 5, evade 6, health 6 + 4/investigator (solo 10),
damage 3 / horror 3. Hunter. **Massive** (solo semantics: it is considered engaged
with the investigator whenever they share a location — it attacks in the enemy phase
if co-located, the investigator's non-fight/evade actions at its location provoke AoO,
but it never "moves into the threat area"/exhausts-on-engage; evading it breaks
nothing — Massive enemies cannot be disengaged from; an evade SUCCESS still exhausts
it for the round but it re-engages by presence). Forced — at the end of each
investigator's TURN: ready Umôrdhoth (so exhaust-based safety lasts at most until turn
end). `[action]` if you CONTROL Lita Chantler (in play under your control): throw Lita
to it → **R3** immediately.

It cannot leave play by damage? No — it CAN be defeated (health 10 solo) → R2 via the
Devourer Below combined card's objective (also if defeated before agenda 3 flips —
i.e. spawned by agenda-3-at-act-1/2/3 path only; it only ever enters play via agenda 3
— then the combined card is already active; R2 check is safe as "when Umôrdhoth is
defeated → R2" unconditionally).

## Return to The Devourer Below (50032a) exceptions

1. Also gather the Return set: Umôrdhoth's Hunger ×2 (50037) into the encounter deck.
2. Woods pool = 10 (6 core + 50033–50036); choose 4 at random (seeded).
3. Ghouls set → **Ghouls of Umôrdhoth**: Grave-Eater ×3 (50038), Acolyte of Umôrdhoth
   ×1 (50039), Chill from Below ×3 (50040) (reuse existing Return-to-Gathering
   implementations of these cards).
4. Dark Cult → **The Devourer's Cult** (reuse C1 implementations): Disciple of the
   Devourer ×3, Corpse-Taker (here it moves toward MAIN PATH; doom dump when at Main
   Path), Mask of Umôrdhoth ×2.
5. **Vault of Earthly Demise** (50032b): attached to Umôrdhoth from setup. When
   Umôrdhoth enters play: place 1 resource per act remaining in the act deck (current
   act counts: act 1 → 3, act 2 → 2, act 3 → 1; if the combined card already replaced
   the acts — cannot happen, it enters play at that moment: use the act stage at the
   moment agenda 3 advanced). Effect: Umôrdhoth gets +X health per investigator (solo:
   +X) and +X fight, X = resources on the Vault. Vault cannot leave play.
6. Umôrdhoth's Hunger (50037): Revelation — discard 1 random card from hand; an
   investigator with NO cards in hand is **killed** (defeat, cause: killed — campaign
   consequences); heal 1 damage from EACH enemy in play.

## Scenario chaos-token effects (01142)

Easy/Standard:
- skull: −X, X = number of Monster enemies in play.
- cultist: −2; place 1 doom on the nearest enemy (any enemy).
- tablet: −3; if a Monster enemy is at your location, take 1 damage.
- elderthing: −5; if an Ancient One enemy is in play, reveal another token (its
  modifier also applies — standard reveal-another semantics).

Hard/Expert:
- skull: −3; if you FAIL, after the test search encounter deck+discard for a Monster
  enemy and draw (spawn) it; shuffle.
- cultist: −4; place 2 doom on the nearest enemy.
- tablet: −5; if a Monster enemy is at your location, take 1 damage AND 1 horror.
- elderthing: −7; if an Ancient One enemy is in play, reveal another token.

Implement all four difficulties.

## Resolutions

- **No resolution** (resigned or defeated — including Umôrdhoth's Hunger kills): Arkham
  succumbed; each surviving investigator is KILLED; campaign lost. Score 0. Campaign
  block: `arkham_succumbed: true`, `investigator_killed: true`.
- **R1** (act 3 completed — ritual broken): 2 MENTAL trauma; XP = victory display + 5
  bonus; win. `ritual_broken: true`.
- **R2** (Umôrdhoth defeated): 2 physical + 2 mental trauma; XP = victory display + 10
  bonus; win. `umordhoth_repelled: true`.
- **R3** (Lita sacrificed): 2 physical + 2 mental trauma; add a random basic Madness
  weakness to the deck permanently (`weakness_gained`); XP = victory display (no
  bonus); investigators survive (not a win, not killed). `lita_sacrificed: true`.
- Score = max(0, XP − trauma) as usual (R2's 10 XP vs 4 trauma rewards the kill; the
  no-resolution 0 punishes resigning — faithful to the guide).
- Victory display candidates: Umôrdhoth has no VP (check JSON — 01157 has none);
  VP from Agents sets (Byakhee 1, Yithian 1, Dark Young 1, Deep One... check JSON
  victory fields and honor them), Masked Hunter/Narôgath if respawned and defeated
  here (VP2), named cultists spawned via got-away (VP1 each). Locations: none have VP
  in this scenario (verify from JSON; woods have none).

## Mission docs, tests, report

- mission.md briefing: doom pressure math (agendas 4/5/5 + Ancient Evils ×3), the
  ritual-site clue plan vs Umôrdhoth-kill plan vs Lita sacrifice tradeoffs, resign =
  campaign death warning, got-away spawns forewarning, Return vault warning.
- Tests: setup counts (29/31 solo ±priest; agents-set selection seeded); got-away doom
  table (0/1/3/5 names → 0/1/2/3 doom); past-midnight discard 2; woods selection
  4-of-6 / 4-of-10 seeded, unrevealed until entered, back-connections = Main Path
  only; inter-woods front edges light up per the symbol table (test at least
  Old House↔Twisting Paths and a Return pair, plus NO edge between e.g. Old House and
  Quiet Glade); location behaviors (skill-substitution investigations, Twisting Paths
  move-cancel, Quiet Glade heal, Lakeside/Wooden Bridge double-reveal, Corpse-Ridden
  damage cap, Great Willow surge); act chain (act1 clue spend + got-away spawn at Main
  Path; act2 enter Ritual Site spawn; act3 clue-on-act ability both skills, R1 at 2);
  agenda chain (agenda1 monster-dig spawn+doom; agenda2 stat aura + willpower(6)
  weakness gate; agenda3 spawn paths at act1 vs act2/3, combined card active, R2 on
  defeat); Umôrdhoth massive/ready/attack semantics + Lita action → R3; Vault X math
  by act stage and fight/health application; token effects ×4 difficulties;
  resolutions incl. trauma/XP/weakness/killed flags; fuzz 50 games × both variants ×
  5 investigators clean.
- Report: `specs/phase_c3_report.md`. No commits.
