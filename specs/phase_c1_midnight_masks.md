# Phase C1 — The Midnight Masks + Return to The Midnight Masks

Implement scenario 2 of Night of the Zealot: **The Midnight Masks** and its Return
variant, as new scenario ids `the_midnight_masks` and `return_to_the_midnight_masks`,
following the architecture of `arkham/scenarios/the_gathering.py` (one module handling
both variants; register both in `arkham/scenarios/__init__.py` `SCENARIOS`).

Solo (1 investigator) only, like the rest of the engine. All five investigators must be
playable (`--investigator roland|daisy|skids|agnes|wendy`, killbray decks, same as the
Gathering scenarios).

Ground truth used below: NotZ campaign guide (`data/rules/night_of_the_zealot_campaign_
guide.pdf` pp.4–5), card JSON (`data/cards/core_encounter.json`, `rtnotz_encounter.json`),
and location connection symbols transcribed from card scans (verified from both endpoints
of every edge). **If any instruction below conflicts with the card JSON, STOP and flag the
conflict in your report instead of guessing** — that rule has caught real spec errors
before.

## Encounter-set code decoder (avoid this trap)

- `cultists` encounter_code = the **Cult of Umôrdhoth** set: the 5 unique named cultists
  01137–01141 (Drew, Herman, Peter, Victoria, Ruth). These form the **Cultist deck**,
  NOT the encounter deck.
- `pentagram` encounter_code = the **Dark Cult** set: Acolyte ×3 (01169), Wizard of the
  Order (01170), Mysterious Chanting ×2 (01171). These go in the encounter deck
  (original variant only).
- `the_devourers_cult` = Return replacement for Dark Cult: Disciple of the Devourer ×3
  (50041), Corpse-Taker (50042), Mask of Umôrdhoth ×2 (50043).
- `return_cult` = "Cult of Umôrdhoth (new)": 3 more unique cultists 50044–50046
  (Jeremiah Pierce, Billy Cooper, Alma Hill) — Return variant adds these to the
  Cultist deck.
- `return_to_the_midnight_masks` = Return scenario set: scenario card 50025, agenda
  variant 50026a/b, 4 location variants 50027–50030, Masked Horrors ×2 (50031).

## Campaign-log inputs (CLI flags on `ahlcg new`)

The scenario consumes three campaign facts. Add flags (used by the future campaign
runner; playable standalone with defaults):

- `--house-burned` (default: house still standing). Burned → Your House is removed from
  the map and the investigator begins play at Rivertown. Standing → Your House is in
  play and the investigator begins there.
- `--ghoul-priest-alive` (default: not alive). Alive → shuffle Ghoul Priest (01116) into
  the encounter deck after it is built.
- `--lita-forced-to-find-others` (default: off). Affects intro flavor only (Intro 1 vs
  Intro 2 in mission text); no mechanical effect. Store it in state for the mission.md
  text; fine to keep minimal.

Record all three in `result.json`'s campaign block (below) so runs are self-describing.

## Setup — The Midnight Masks (original)

Encounter deck (solo counts, after removing locations/act/agenda/scenario cards):
- The Midnight Masks (`arkham`): Hunting Shadow ×3 (01135), False Lead ×2 (01136)
- Dark Cult (`pentagram`): Acolyte ×3, Wizard of the Order ×1, Mysterious Chanting ×2
- Nightgaunts: Hunting Nightgaunt ×2 (01172), On Wings of Darkness ×2 (01173)
- Chilling Cold: Crypt Chill ×2 (01167), Obscuring Fog ×2 (01168)
- Locked Doors: Locked Door ×2 (01174)
- (+ Ghoul Priest 01116 if `--ghoul-priest-alive`)

Total 21 (+1). Shuffle. **Assert these counts in a test.**

Cultist deck (separate, face-down, shuffled): the 5 unique Cult of Umôrdhoth cultists
01137–01141.

Locations put into play (all unrevealed except the starting location, which is revealed;
backs mirror fronts for connections — verified):
- Your House (01124) — only if house standing
- Rivertown (01125)
- Southside — random one of 01126 (Historical Society) / 01127 (Ma's Boarding House),
  seeded RNG; remove the other from the game
- Downtown — random one of 01130 (First Bank) / 01131 (Arkham Asylum); remove the other
- St. Mary's Hospital (01128), Miskatonic University (01129), Easttown (01132),
  Graveyard (01133), Northside (01134)

Act deck: Act 1 only — Uncovering the Conspiracy (01123). Agenda deck: Agenda 1
Predator or Prey? (01121a, 6 doom) → Agenda 2 Time Is Running Short (01122, 8 doom).

1 player: no Acolyte pre-spawn (that rule is for 2+ players only).

## Location graph (transcribed + double-verified from scans)

Symbols: Rivertown=circle, Your House=slant, Southside=square, St. Mary's=cross,
Miskatonic=diamond, Downtown=triangle, Northside=T, Easttown=moon, Graveyard=hourglass.

Connections (all symmetric):
- Your House ↔ Rivertown
- Rivertown ↔ Your House, Easttown, Southside, Miskatonic University, Graveyard
- Southside ↔ Rivertown, Miskatonic University, St. Mary's Hospital
- St. Mary's Hospital ↔ Southside, Miskatonic University
- Miskatonic University ↔ Rivertown, Southside, St. Mary's Hospital, Northside
- Downtown ↔ Easttown, Northside   (note: Downtown does NOT connect to Rivertown)
- Easttown ↔ Rivertown, Downtown
- Graveyard ↔ Rivertown (dead end)
- Northside ↔ Downtown, Miskatonic University

The Return variant locations (50027 Easttown, 50028 Northside, 50029 Miskatonic,
50030 Rivertown) keep exactly their original's symbol and connections (verified).
Rivertown (both versions) is the only `Central.` location (On Wings of Darkness target).

## Act / agenda machinery

**Act 1 — Uncovering the Conspiracy (01123).**
- Repeatable act ability, `[action]` (group; solo = the investigator): spend 2 clues
  (from the investigator's pool, per RR clue spends) → draw the top card of the Cultist
  deck; the drawn cultist spawns per its Spawn instruction. If the Cultist deck is
  empty, the ability does nothing (make the option unavailable).
- Objective — auto-check after any change: if 6 unique `Cultist` enemies are in the
  victory display, advance → resolution R1. (5 named cultists + the agenda-1 hunter =
  the plausible 6; the Return variant can also bank Return uniques. Count unique
  Cultist-trait enemies in the victory display.)

**Agenda 1 — Predator or Prey? (01121a / 50026a), 6 doom.**
- Grants an anywhere `[action]`: **Resign** ("you head to safety with the information
  you've gathered") → end scenario, resolution R1, resigned=true.
- On advance: the agenda card flips into its enemy back and spawns:
  - original: **The Masked Hunter** (01121b) — unique Elite Cultist, fight 4, health
    4 +2/investigator (solo: 6), evade 2, damage 2/horror 1. Spawn engaged with the
    prey ("most clues" — solo: the investigator, no test, no AoO on spawn-engage).
    Hunter keyword. Aura: while engaged with it, the investigator **cannot discover or
    spend clues** (blocks investigation discovery, the act's 2-clue spend, Peter
    Warren's parley, tablet-token clue drops still occur — those are "place", not
    "spend"/"discover").
  - Return variant (if the 50026 agenda was selected at setup): **Narôgath** (50026b) —
    unique Elite Monster/Cultist, fight 3, health 4 +3/investigator (solo: 7), evade 3,
    damage 1/horror 2, VP2. Spawn engaged with prey ("nearest to another Cultist enemy"
    — solo: the investigator). Hunter. Aura: while Narôgath is **ready**, an
    investigator at its location **or a connecting location** cannot **Parley** with
    `Cultist` enemies (exhausted Narôgath switches the aura off).
- Then agenda 2 (01122) becomes current with 0 doom (doom does NOT carry over; RR).

**Agenda 2 — Time Is Running Short (01122), 8 doom.**
- Same Resign action.
- On advance ("The Clock Strikes Midnight") → resolution R2.

Doom on enemies (Acolytes, Wizard, cultist-token placements, Mysterious Chanting, etc.)
**counts toward the agenda threshold** (campaign guide explicitly warns about this).
Reuse/extend the engine's total-doom logic; agenda advance clears ALL doom in play
including doom on enemies (RR), but cultists keep... no: advancing clears all doom from
all cards in play. (RR 1.4 "when an agenda advances, remove all doom from all cards in
play." Apply exactly that.)

## Enemy behaviors (Cultist deck + Dark Cult)

- **Acolyte** (01169): Spawn at any EMPTY location (no investigator, no enemy) — engine
  picks the nearest empty location to the investigator? NO: "any empty location" is a
  player choice in multiplayer; solo, present a decision listing empty locations for
  the player to choose. Forced after entering play: place 1 doom on it.
- **Wizard of the Order** (01170): Spawn any empty location (player choice). Retaliate.
  Forced at end of mythos phase: +1 doom on it.
- **Mysterious Chanting** (01171): Revelation — place 2 doom on the NEAREST Cultist
  enemy (fewest connections hops from the investigator; tie → player chooses). If no
  Cultist enemy in play: search encounter deck and discard for a Cultist enemy and
  draw it (it spawns); shuffle deck.
- **"Wolf-Man" Drew** (01137): Spawn Downtown. Forced when he attacks: heal 1 damage
  from him. VP1.
- **Herman Collins** (01138): Spawn Graveyard. `[action]` discard 4 cards from hand:
  Parley — add Herman to victory display. VP1.
- **Peter Warren** (01139): Spawn Miskatonic U. `[action]` spend 2 clues: Parley — add
  to victory display. VP1.
- **Victoria Devereux** (01140): Spawn Northside. `[action]` spend 5 resources: Parley —
  add to victory display. VP1.
- **Ruth Turner** (01141): Spawn St. Mary's. Forced after she is evaded: add to victory
  display. VP1. (Evade-success → straight to victory display, she leaves play.)
- Parley is an action type exempt from attacks of opportunity (engine already treats it
  so). A parley that requires spending clues is blocked while engaged with the Masked
  Hunter (cannot spend clues) and blocked entirely near a ready Narôgath.
- Spawn-location redirects: if a named cultist's spawn location is not in play (e.g.
  Your House burned — none spawn there; all five spawn spots always exist) — n/a, but
  Return variant location swaps keep the same names, so Spawn by NAME (e.g. "Northside"
  matches either Northside version).

## Treacheries

- **Hunting Shadow** (01135, Peril ×3): choose — spend 1 clue OR take 2 damage.
- **False Lead** (01136 ×2): if you have no clues → surge (draw another). Else test
  intellect(4); for each point failed, place 1 of your clues on your location.
- **Masked Horrors** (50031 ×2, Return only): if you have 2+ clues → take 2 horror;
  if no horror dealt → place 1 doom on current agenda (can advance it).
- **Crypt Chill / Obscuring Fog / Hunting Nightgaunt / On Wings of Darkness / Locked
  Door**: identical to their Return-to-The-Gathering implementations — reuse. On Wings
  of Darkness moves the investigator to Rivertown (the only Central location; also
  disengages non-Nightgaunt enemies first).
- **Locked Door** attaches to the location in play with most clues without one;
  blocked location cannot be investigated; `[action]` combat(4) or agility(4) to
  discard.
- **The Devourer's Cult** (Return only):
  - **Disciple of the Devourer** (50041 ×3, 1 health): Spawn at FARTHEST empty
    location (from the investigator; tie → player chooses). Forced after spawn: choose
    — 1 doom on it OR place 1 of your clues on its location. If current agenda is not
    agenda 1: do BOTH (no choice).
  - **Corpse-Taker** (50042): Spawn farthest empty location. End of mythos phase:
    +1 doom on it. End of enemy phase: moves once toward Rivertown; if at Rivertown,
    move ALL doom from it to the current agenda instead (can advance agenda — check).
  - **Mask of Umôrdhoth** (50043 ×2, Item/Mask treachery): attach to the FARTHEST
    Cultist enemy (from investigator) without... (no limit printed; attach to farthest
    Cultist) and place 1 doom on that enemy. If no Cultist in play: search encounter
    deck + discard for a Cultist enemy, draw it (spawns), attach to it, shuffle.
    Attached enemy: +2 health; if unique → gains Retaliate; if non-unique → gains
    **Aloof**. Implement Aloof: the enemy does not engage investigators (no engage on
    spawn/hunter move-in/ready); an investigator at its location may engage it as a
    basic Engage action; while unengaged it does not attack in the enemy phase and
    fighting it provokes no AoO from it (it's not engaged); other engaged enemies still
    AoO on a fight aimed at an aloof enemy per normal AoO rules.

## Scenario chaos-token effects (01120)

Easy/Standard:
- skull: −X, X = highest doom among Cultist enemies in play (0 if none).
- cultist: −2. Place 1 doom on the nearest Cultist enemy (no enemy → no doom).
- tablet: −3. If you fail, place 1 of your clues on your location (if you have any).

Hard/Expert:
- skull: −X, X = TOTAL doom in play (agenda + enemies + anywhere).
- cultist: −2. Place 1 doom on EACH Cultist enemy in play; if none, reveal another
  token (treat like the engine's existing reveal-another flow).
- tablet: −4. If you fail, place ALL your clues on your location.

Implement all four difficulties now (bag composition per difficulty already exists).
Elder Sign: per-investigator ability, same as existing engine behavior.

## Resolutions & scoring

- **R1** — reached by: act 1 objective (6 unique cultists), OR resign, OR investigator
  defeated (campaign guide: "If no resolution was reached... Read Resolution 1").
  Defeat still applies standard defeat trauma (physical/mental per cause) and, if the
  cause kills/drives insane, the campaign-side effects are C2's concern.
- **R2** — agenda 2 advances (midnight). Record `past_midnight: true`.
- XP for both R1 and R2 = victory display total ONLY. **No +2 insight bonus in this
  scenario** (unlike The Gathering) — the campaign guide grants none here.
- Victory display candidates: named cultists VP1 each, Masked Hunter VP2, Narôgath VP2,
  Miskatonic University VP1, Downtown (Arkham Asylum 01131) VP1, Graveyard VP1,
  Northside VP1, Easttown (Police Station 50027, Return) VP1. (Victory locations count
  only if cleared of clues, per existing engine rule.)
- Score = max(0, XP − trauma) as usual; result.json carries the same dimensions as the
  Gathering plus a `campaign` block:

```json
"campaign": {
  "scenario": "return_to_the_midnight_masks",
  "inputs": {"house_burned": false, "ghoul_priest_alive": false, "lita_forced": false},
  "cultists_interrogated": ["Herman Collins", "..."],
  "cultists_got_away": ["Victoria Devereux", "The Masked Hunter", "..."],
  "past_midnight": false,
  "ghoul_priest_defeated_here": false
}
```

- `cultists_interrogated` = unique Cultist enemies in the victory display (by name).
- `cultists_got_away` = unique cultists still in the Cultist deck or in play at scenario
  end; **plus "The Masked Hunter" (or "Narôgath") if the game ended during agenda 1**
  (it never spawned). A spawned-but-undefeated hunter in play also counts (it is a
  unique Cultist enemy in play).
- `ghoul_priest_defeated_here` = Ghoul Priest is in the victory display (campaign runner
  will cross out "still alive").

## Setup — Return to The Midnight Masks (50025) exceptions

1. Also gather the Return set: Masked Horrors ×2 into the encounter deck.
2. Agenda 1: choose randomly (seeded) between 01121a (back: Masked Hunter) and 50026a
   (back: Narôgath), "without looking at their other sides"; remove the other.
3. Location variants, each chosen randomly (seeded) original vs Return, independently:
   Easttown 01132 / 50027 (Police Station, VP1, +2 supply/ammo action),
   Northside 01134 / 50028 (Train Station, move-anywhere action),
   Miskatonic 01129 / 50029 (Museum: shroud 3, clues 1, no VP, take-2-horror-for-clue
   action — per JSON), Rivertown 01125 / 50030 (Abandoned Warehouse: shroud 4,
   discard-willpower-icons-to-remove-doom action, still Central).
   Also random Southside and Downtown variants as in the original setup.
4. Dark Cult set is REPLACED by The Devourer's Cult set in the encounter deck (6 for 6).
5. Cultist deck: 5 named core cultists + 3 Return cultists (Jeremiah Pierce spawns
   "Your House. Otherwise, Rivertown." — if house burned, Rivertown; Billy Cooper →
   Easttown; Alma Hill → Southside), shuffled; **remove 3 at random unseen** → 5-card
   Cultist deck. The removed 3 still count as "got away"?? NO — flag: removed-from-game
   cards are neither interrogated nor "remaining in the Cultist deck or in play"; they
   do NOT appear in the campaign log. (Rules-as-written; also achievement text
   confirms only 6 uniques findable per game.)
6. "Search for an Acolyte" instructions → "any 1-health Cultist enemy" (Disciple of the
   Devourer). Solo: only relevant if some card searches — Mysterious Chanting is out in
   Return, Mask of Umôrdhoth searches for "a Cultist enemy" generically. Keep as a
   comment; no solo-reachable code path is expected to need it.
7. Return unique-cultist behaviors:
   - **Jeremiah Pierce** (50044): `[action]` Parley (no cost): add to victory display,
     then test willpower(4); place 1 doom on current agenda per point failed (can
     advance).
   - **Billy Cooper** (50045): no parley; Forced — after a Monster enemy is defeated at
     his location: add Billy to victory display.
   - **Alma Hill** (50046): `[action]` Parley (no cost): draw the top 3 encounter cards
     (resolve each), THEN add Alma to the victory display.

## Mission docs

Extend `docs_agent/` mission generation (whatever mission.md template machinery exists)
with a Midnight Masks briefing: objective (find cultists — parley/fight/evade routes and
each named cultist's parley cost), the Cultist-deck act ability, doom-on-enemies warning,
resign action, past-midnight consequence, and the standalone-only footer marker like the
existing scenarios (`<!-- standalone-only:` convention).

## Tests (add to tests/, keep the suite green)

1. Setup counts: encounter deck composition for both variants (21 original / 23 Return,
   ±Ghoul Priest); Cultist deck 5 both variants; act/agenda decks; start location under
   both `--house-burned` values; location variant selection is seed-deterministic.
2. Act clue-spend draws + spawns a cultist at its printed location; empty Cultist deck
   disables the option.
3. Agenda 1 advance spawns the hunter engaged (both hunter variants); clue
   discovery/spend blocked while engaged with Masked Hunter; Narôgath parley aura on/off
   with ready/exhausted at location and connecting location.
4. Six unique cultists in victory display → R1; agenda 2 out → R2 + past_midnight; resign
   → R1; defeat → R1 + trauma.
5. Doom on enemies advances the agenda (Acolyte doom + agenda doom crossing threshold);
   agenda advance clears doom everywhere.
6. Each named cultist's parley/evade/forced route lands it in the victory display with
   costs enforced (Herman 4 cards, Peter 2 clues, Victoria 5 resources, Ruth on evade,
   Drew heals on attack, Jeremiah doom test, Alma 3 encounter draws then display, Billy
   on monster-defeat-at-location).
7. Token effects, all four difficulties (skull doom-scan, cultist doom placement /
   each-cultist + reveal-another, tablet clue drop / all-clues drop).
8. Mask of Umôrdhoth: attach+doom, +2 health, Retaliate on unique, Aloof on non-unique
   (no auto-engage; engage action available; no enemy-phase attack while unengaged).
9. Corpse-Taker movement toward Rivertown and doom dump at Rivertown; Disciple spawn
   choice/both branches by agenda stage.
10. campaign block in result.json: interrogated/got-away lists across the scenarios'
    ends (incl. never-spawned hunter in got_away when ending at agenda 1).
11. Fuzz: `python3 -m arkham.fuzz --games 50 --scenario return_to_the_midnight_masks`
    (and original) clean for all 5 investigators.

## Report

Write `specs/phase_c1_report.md`: what was built, deviations (each flagged conflict),
test counts before/after, fuzz results. Do NOT git commit — Claude reviews and commits.
