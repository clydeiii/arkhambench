# Phase V4 — Agnes Baker + mystic/survivor package

Prereq: phases V1 (required) and V2 (Blinding Light's symbol-watch hook is reused by
Shrivelling — if V2 is not merged yet, build the hook here and flag it). Read
`specs/phase_v1_investigators.md`, prior reports. Rules authority: RR + JSON; flag
conflicts.

Goal: every card in `data/decks/killbray/agnes.json` implemented; `--investigator agnes`
passes validation and full games are playable.

Already implemented: neutrals (Knife/Flashlight/Emergency Cache/Overpower/Unexpected
Courage per V1), Agnes ability + elder sign (V1).

## Cards

- **01012 Heirloom of Hyperborea** (asset, 3, Accessory, Relic): "[reaction] After you
  play a [[Spell]] card: Draw 1 card." Optional reaction, fires on playing Spell events
  AND Spell assets (Shrivelling, Ward, Blinding Light, Dark Memory — anything with the
  Spell trait), not on committing them.
- **01013 Dark Memory** (weakness EVENT, 2, Spell): This weakness sits in HAND (event
  weaknesses have no Revelation — drawing it just adds it to hand; verify against RR
  "Weakness"). Playing it: "Place 1 doom on the current agenda. This effect can cause
  the current agenda to advance." — explicit card permission, same machinery as Ancient
  Evils (can_advance=True). "Forced — If Dark Memory is in your hand at the end of your
  turn, reveal it and take 2 horror." End-of-turn hook: reveal (log it — the card stays
  in hand, horror repeats every turn it remains) and take 2 horror (triggers Agnes's
  reaction window if an enemy is present — a fun interaction, make sure it works).
  Playing it costs 2 resources + an action and PROVOKES AoO (no Fight/Evade keyword).
- **01058 Forbidden Knowledge** (asset, 0, Talent, uses 4 secrets): "[fast] Exhaust
  Forbidden Knowledge and take 1 horror: Move 1 secret from Forbidden Knowledge to your
  resource pool, as a resource. If Forbidden Knowledge has no secrets, discard it."
  The self-horror triggers Agnes's damage reaction (once per phase) — intended combo,
  test it. Discard when secrets reach 0 (after the move).
- **01059 Holy Rosary** (asset, 2, Accessory, sanity 2): static +1 willpower; 2 sanity
  soak (existing asset-soak machinery).
- **01060 Shrivelling** (asset, 3, Arcane, Spell, uses 4 charges): "[action] Spend 1
  charge: Fight. This attack uses [willpower] instead of [combat] and deals +1 damage.
  If a [skull]/[cultist]/[tablet]/[elder_thing]/[auto_fail] symbol is revealed during
  this attack, take 1 horror." Fight ability → AoO-exempt. Willpower-based attack (base
  5 for Agnes), +1 damage on success, symbol-watch → 1 horror to Agnes (again: her
  reaction can fire — but note her limit once per PHASE).
- **01062 Arcane Studies** (asset, 2, Talent): fast resource pumps for willpower and
  intellect — Physical Training pattern, pre-reveal only.
- **01063 Arcane Initiate** (asset, 1, Ally, health 1 sanity 2): "Forced — After Arcane
  Initiate enters play: Place 1 doom on it." Doom ON AN ASSET counts toward the agenda
  threshold check at Mythos 1.3 (total doom in play — the engine already sums doom in
  play; verify assets are included) and is removed when the agenda advances
  (clear-all-doom). "[fast] Exhaust: Search the top 3 cards of your deck for a [[Spell]]
  card and draw it. Shuffle your deck." Present found Spells as a choice (or none —
  reveal count only, cards seen go back shuffled; log names seen as player-legal
  knowledge like Old Book of Lore's search).
- **01064 Drawn to the Flame** (event, 0): "Draw the top card of the encounter deck.
  Then, discover 2 clues at your location." The encounter card resolves fully
  (revelation/spawn — Ward of Protection CAN respond to a treachery drawn this way),
  then discover 2 clues (even if the encounter card defeated... no: if Agnes is
  defeated, game ends before discovery; otherwise discover proceeds). Plain event play
  → provokes AoO.
- **01067 Fearless** (skill, willpower): on success heal 1 horror from Agnes.
- **01072 Leather Coat** (asset, 0, Body, health 2): pure 2-health soak.
- **01074 Baseball Bat** (asset, 2, TWO Hand slots, Weapon/Melee): "[action]: Fight. +2
  [combat]. +1 damage. If a [skull] or [auto_fail] symbol is revealed during this
  attack, discard Baseball Bat after the attack resolves." Two-handed (slot system);
  symbol-watch → discard AFTER the attack fully resolves (damage still applies on a
  skull success).
- **01076 Stray Cat** (asset, 1, Ally, health 1): "[fast] Discard Stray Cat:
  Automatically evade a non-[[Elite]] enemy at your location." Auto-evade = exhaust the
  enemy + disengage, no test, no AoO (fast ability), works on unengaged enemies at the
  location too (they just exhaust).

## Tests

1. Agnes fuzz N=25 clean; validation passes.
2. Dark Memory: end-of-turn 2 horror repeats while held; play advances agenda at
   threshold via can_advance; Agnes reaction fires off its horror.
3. Forbidden Knowledge: horror→resource loop, Agnes reaction combo, auto-discard at 0.
4. Shrivelling: willpower-based math in the fight label, +1 dmg, symbol → 1 horror,
   charge depletion, AoO-exempt.
5. Baseball Bat: occupies 2 hand slots (can't hold Knife simultaneously), skull success
   still damages then discards.
6. Arcane Initiate: doom counts at 1.3 threshold check (agenda advances a round early),
   cleared on advance; spell search finds/misses correctly with seeded deck.
7. Drawn to the Flame: treachery resolves first (Ward window opens), then 2 clues.
8. Stray Cat auto-evades unengaged non-Elite; refused for Ghoul Priest (Elite).
9. Heirloom draws on Spell asset AND Spell event plays, not on commits.
10. Full suite + fuzz 50 green.

Write `specs/phase_v4_report.md`. Do not git commit.
