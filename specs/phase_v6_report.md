# Phase V6 Report

Implemented by Claude (codex was out of credits when this phase launched — same
fallback as fixes batch 2).

## Built

- `return_to_the_gathering` registered as a second scenario sharing The Gathering's
  module: acts 2–3, all agendas, resolutions, scoring, campaign log, and the 01104
  chaos-token effects are the SAME code paths, now gated on a `GATHERING_FAMILY`
  constant in `model.py` (every `scenario == "the_gathering"` guard in the engine was
  swept to family membership).
- Setup per scenario card 50011: Study (Aberrant Gateway) revealed start; Guest
  Hall/Bedroom/Bathroom in play unrevealed; original-vs-Return Attic and Cellar chosen
  AT RANDOM per seed (logged at setup as `setup_variants`); encounter deck = core minus
  the Ghouls set (01160×3/01161×1/01162×3) plus Ghouls of Umôrdhoth (50038×3/50039×1/
  50040×3) and the Return deck cards (50022/50023/50024×2) — 32 cards.
- Double-sided location pairs: Hole in the Wall→Hallway, Far Above Your House→Field of
  Graves, Deep Below Your House→Ghoul Pits. Unrevealed-side names and connections
  govern until reveal (Hole in the Wall connects only to Guest Hall even if the Attic
  is already in play via the Study's gateway). Connection graph per the card scans in
  specs/phase_v6_return.md.
- Act 1 "Mysterious Gateway": advance only offered in the Guest Hall with 3 clues;
  back forced-moves the investigator (engaged enemies follow) into the Hole in the
  Wall, reveals it (flip → Attic/Cellar/Parlor enter play), then willpower (4) with
  1 random discard per point failed.
- Location behaviors: Study gateway 2-action draw-3 (provokes AoO) + spawn-fallback
  Forced (Flesh-Eater/Icy Ghoul spawn targets get pulled into play unrevealed);
  Guest Hall blocks the basic draw action (menu-filtered + EngineError guard);
  Bedroom failed-investigate random discard; Bathroom symbol-token turn-ender;
  Field of Graves wp(4) reveal test; Ghoul Pits agility(3) reveal test that pulls
  Swarm of Rats from deck AND discard, then shuffles. Original-variant Attic/Cellar
  keep their core enter-effects and stats.
- New encounter cards: Corpse-Hungry Ghoul (spawn Bedroom, Hunter, VP1), Ghoul from
  the Depths (spawn Bathroom, Retaliate, VP1), The Zealot's Seal (hand≤3 → 1 dmg +
  1 horror; else wp(2) → discard 2), Grave-Eater (random discard after its attacks,
  incl. AoO), Acolyte of Umôrdhoth (cannot be evaded at 0 cards in hand — blocks
  basic evade, Stray Cat, Blinding Light, and Cunning Distraction), Chill from Below
  (wp(3), discard per point, damage per card you cannot discard).
- Victory display generalized: any revealed, clue-less location with printed Victory
  goes in at game end (covers core Attic/Cellar and the new VP locations by JSON).
- Plumbing: `--scenario` on CLI + fuzzer, scenario registry entry, export reference
  card mapping (01104 applies to both scenarios).

## Rulings made (flagging per protocol)

- Act 1b's forced move carries engaged enemies with the investigator (consistent with
  the engine's move handling; RR "moves" during act resolution are still moves).
- "Cannot be evaded" (Acolyte) treated as absolute — also blocks automatic evades.
- The Bathroom forced fires on any investigation there (basic, Flashlight, Burglary),
  matching "while investigating".

## Tests

- 11 new tests in tests/test_phase_v6.py (setup counts + variant determinism, act-1
  gating + Breaking the Wall cascade, reveal chains, original-variant behavior, Ghoul
  Pits search, Study gateway draw + spawn fallback, Zealot's Seal both branches,
  Chill shortfall damage, Grave-Eater/Acolyte, Bathroom/Bedroom forced, new-game
  smoke for wendy + scoring parity).
- Full suite: 144 tests green.
- Fuzz: 50 the_gathering clean (regression); 30 × each of the five investigators on
  return_to_the_gathering clean (one R3 reached).
