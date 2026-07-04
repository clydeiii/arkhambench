# Phase V6 — Scenario: Return to The Gathering

Prereq: phase V1 (scenario registry). Independent of V2–V5. Read DESIGN.md §12 (The
Gathering — the template this scenario extends) and the existing
`arkham/scenarios/the_gathering.py`. Rules authority: RR + vendored JSON
(`data/cards/rtnotz_encounter.json`) + the Return to NotZ rules insert
(`data/rules/ahc26_rules_insert.pdf`, transcribed below where it matters). Flag
conflicts.

Goal: `./ahlcg new --scenario return_to_the_gathering` (any investigator) plays the full
scenario. **Resolutions, scoring, campaign log, and chaos-token scenario effects are
IDENTICAL to The Gathering** — the insert says to use the original campaign guide with
only the setup exceptions on scenario card 50011. Reuse/share the existing resolution +
scoring code; do not fork it.

## Setup (scenario card 50011, verified against the insert)

Original The Gathering setup, with these exceptions:

1. Encounter sets: The Gathering, Rats, **Ghouls of Umôrdhoth** (replaces Ghouls —
   remove ALL core Ghouls-set cards), Striking Fear, Ancient Evils, Chilling Cold, plus
   the Return to The Gathering set. Consistency check: core Ghouls set has 7 cards;
   Ghouls of Umôrdhoth also 7 (50038 Grave-Eater ×3, 50039 Acolyte of Umôrdhoth ×1,
   50040 Chill from Below ×3). New deck cards from the Return set: 50022 Corpse-Hungry
   Ghoul ×1, 50023 Ghoul from the Depths ×1, 50024 The Zealot's Seal ×2. Ghoul Priest
   is in The Gathering set and is unchanged.
2. Act 1a "Trapped" is REPLACED by **50012 Mysterious Gateway**. Acts 2–3 and all three
   agendas are unchanged.
3. The original Study is REPLACED by **50013 Study (Aberrant Gateway)**; it starts in
   play revealed; the investigator begins there.
4. **50014 Guest Hall, 50015 Bedroom, 50016 Bathroom** start in play, unrevealed.
5. The original Hallway is removed from the game. The new Hallway card (50017, back =
   **Hole in the Wall**) is set aside.
6. **Choose one of the two Attic cards and one of the two Cellar cards AT RANDOM** (via
   the game RNG at setup): original core Attic vs 50018 Attic, original core Cellar vs
   50020 Cellar. Set the chosen ones aside; remove the others from the game. Also set
   aside: Parlor (unchanged), 50019 Field of Graves (back = Far Above Your House), 50021
   Ghoul Pits (back = Deep Below Your House). Record which variants were chosen in the
   run log.

## Location graph (transcribed + verified from card scans — connection icons)

- **Study (Aberrant Gateway)** [own icon: circle] ↔ Guest Hall only. Shroud 3, 1 clue.
  "[action][action]: Draw 3 cards. Only the lead investigator can activate this
  ability." (2-action activate; provokes AoO; usable by the solo investigator.)
  "Forced — When an enemy attempts to spawn at a location that is not in play: Put that
  location into play and spawn that enemy there." (Covers Flesh-Eater→Attic,
  Icy Ghoul→Cellar, 50022→Bedroom-in-play-already, etc. The put-into-play location
  enters unrevealed.)
- **Guest Hall** [T] ↔ Study, Bedroom, Bathroom, Hallway/Hole in the Wall. Shroud 1,
  0 clues. "Investigators in this location cannot take draw actions." (Basic draw
  action AND Study's draw ability are actions — block the basic draw action here; the
  Study ability is activated at the Study, so it is unaffected. Upkeep draw unaffected.)
- **Bedroom** [heart] ↔ Guest Hall. Shroud 2, 1 clue. "Forced — After you fail a skill
  test while investigating the Bedroom: Discard 1 card at random from your hand."
- **Bathroom** [star] ↔ Guest Hall. Shroud 1, 1 clue. "Forced — After you reveal a
  [skull]/[cultist]/[tablet]/[auto_fail] symbol while investigating the Bathroom: Lose
  all remaining actions and end your turn."
- **Hole in the Wall** (unrevealed face) [square] ↔ Guest Hall only.
  **Hallway** (revealed face) [square] ↔ Guest Hall, Attic, Cellar, Parlor — NOT Study.
  Shroud 1, 0 clues. "Forced — After you reveal this location: Put the set-aside Attic,
  Cellar, and Parlor locations into play." Unrevealed-side connections govern while
  unrevealed (RR).
- **Attic (Return version 50018)** [triangle] ↔ Hallway, Far Above Your House. Shroud 3,
  1 clue. "Forced — After you reveal the Attic: Put the set-aside Far Above Your House
  location into play." (Original core Attic, if chosen: unchanged from The Gathering —
  ↔ Hallway only; Far Above/Field of Graves then never enters play. Its own icon is
  also a triangle, so the Hallway connection works either way.)
- **Far Above Your House** (unrevealed face) [crescent] ↔ Attic.
  **Field of Graves** (revealed face) ↔ Attic. Shroud 2, 1 clue, **Victory 1**.
  "Forced — After you reveal Field of Graves: Test [willpower] (4). For each point you
  fail by, discard 1 card at random from each player's hand."
- **Cellar (Return version 50020)** [plus] ↔ Hallway, Deep Below Your House. Shroud 2,
  1 clue. "Forced — After you reveal the Cellar: Put the set-aside Deep Below Your House
  location into play." (Original core Cellar, if chosen: unchanged — ↔ Hallway only.)
- **Deep Below Your House** (unrevealed face) [slash] ↔ Cellar.
  **Ghoul Pits** (revealed face) ↔ Cellar. Shroud 4, 1 clue, **Victory 1**.
  "Forced — After you reveal Ghoul Pits: Test [agility] (3). For each point you fail by,
  search the encounter deck and discard pile for a copy of Swarm of Rats and draw it.
  Shuffle the encounter deck." (Each drawn Swarm resolves fully — spawns engaged.)
- **Parlor**: unchanged from The Gathering (resign ability, Lita).

## Act 1 — 50012 Mysterious Gateway (clue cost 3)

"Objective — Only investigators in the Guest Hall may spend the requisite number of
clues, as a group, to advance." The advance-act action is only offered while the
investigator is in the Guest Hall with ≥3 clues.

Back ("Breaking the Wall"): put the set-aside Hole in the Wall into play; the
investigator (solo: automatically the chosen one; must be in Guest Hall — they are, per
the objective) immediately moves into Hole in the Wall (not a move action, no AoO — but
engaged enemies do NOT follow on a non-move-action placement? RR: "moves" during
act/agenda resolution still carry engaged enemies — engaged enemies move with the
investigator; follow the engine's existing forced-move handling and FLAG your ruling)
and reveals it → Hallway flip triggers its Forced (Attic/Cellar/Parlor into play). Then
test willpower (4); for each point failed by, discard 1 random card from hand. Then
Act 2 proceeds exactly as The Gathering's Act 2 (same card).

## New encounter cards

- **50022 Corpse-Hungry Ghoul** (enemy: fight 4, health 3, evade 3, dmg 2, horror 2,
  **Victory 1**): "Spawn — Bedroom. Hunter."
- **50023 Ghoul from the Depths** (enemy: fight 3, health 4, evade 2, dmg 1, horror 1,
  **Victory 1**): "Spawn — Bathroom. Retaliate."
- **50024 The Zealot's Seal** (treachery ×2): "Revelation — Each investigator with 3 or
  fewer cards in hand must take 1 damage and 1 horror. Each investigator with 4 or more
  cards in hand tests [willpower] (2). Each investigator who fails must discard 2 cards
  at random from his or her hand."
- **50038 Grave-Eater** (enemy ×3: fight 2, health 2, evade 2, dmg 1, horror 1):
  "Forced — After Grave-Eater attacks you: Discard 1 card at random from your hand."
  (Fires on enemy-phase attacks AND attacks of opportunity, after the attack resolves.)
- **50039 Acolyte of Umôrdhoth** (enemy ×1: fight 3, health 3, evade 2, dmg 1, horror
  1): "Prey — Fewest cards in hand. While engaged with an investigator with no cards in
  his or her hand, Acolyte of Umôrdhoth cannot be evaded." (Evade actions targeting it
  are not offered when hand is empty; fight/other options unaffected.)
- **50040 Chill from Below** (treachery ×3): "Revelation — Test [willpower] (3). For
  each point you fail by, you must discard 1 card at random from your hand. For each
  card you cannot discard, take 1 damage."

Spawn locations are in play from setup (Bedroom/Bathroom), so 50022/50023 spawn normally
(unrevealed locations can host enemies; Study's Forced is the fallback for
not-in-play spawns).

## Registry, scoring, docs hooks

- Register in `arkham/scenarios/__init__.py` as `return_to_the_gathering`.
- Scoring/resolutions/trauma/Lita: shared with The Gathering (same R1/R2/R3/no-res, XP =
  victory display + bonuses, Score = max(0, XP − trauma + 3·Lita)). Victory display now
  can include Field of Graves, Ghoul Pits, 50022, 50023.
- Chaos token scenario reference stays card 01104 (skull = ghouls at your location,
  etc.); `export.py`'s SCENARIO_REFERENCE_CARDS gets an entry for the new scenario.
- The mulligan/weakness/opening-hand and mission flow are investigator-generic already
  (V1); no changes.

## Tests

1. Setup determinism: same seed → same Attic/Cellar variant choice; both variants
   reachable across seeds; chosen variants logged.
2. Act 1: advance blocked outside Guest Hall and with <3 clues; back resolves the move,
   reveal-cascade (Attic/Cellar/Parlor enter play), willpower test discards.
3. Reveal Forced chain: revealing Return-Attic puts Far Above into play (unrevealed,
   crescent↔triangle connection live); revealing Field of Graves runs the wp(4) test;
   Ghoul Pits rats-search pulls Swarm of Rats from deck AND discard.
4. Guest Hall blocks the basic draw action but not upkeep draw or Study's ability.
5. Bathroom symbol Forced ends the turn (actions → 0) on skull during investigate
   there; Bedroom random discard on failed investigate.
6. Grave-Eater discard-after-attack on both enemy-phase and AoO attacks; Acolyte
   unevadeable at 0 cards in hand; Zealot's Seal both branches.
7. Full playthrough integration test to any resolution; result.json scoring parity
   with The Gathering formula; VP from Field of Graves/Ghoul Pits counted.
8. Fuzz: `python3 -m arkham.fuzz --games 50 --scenario return_to_the_gathering` clean
   (add the scenario flag to the fuzzer if absent).
9. Full existing suite green.

Write `specs/phase_v6_report.md`. Do not git commit.
