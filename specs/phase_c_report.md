# Phase C Report

## Built

- Registered every phase C player and encounter card code in `arkham/cards/player.py` and
  `arkham/cards/encounter_cards.py`.
- Implemented Roland deck card behavior across actions, plays, fast abilities, reactions,
  static modifiers, uses, and skill riders:
  - Cover Up redirect and game-end trauma.
  - Silver Twilight Acolyte weakness spawn, Hunter support through existing enemy movement,
    and doom after uncanceled attacks.
  - Ammo/supply assets, First Aid self-discard, Flashlight empty-but-in-play behavior.
  - Weapon actions for Roland's .38 Special, .45 Automatic, Machete, Knife, and Dynamite
    Blast location damage including self-damage.
  - Physical Training and Hyperawareness repeatable boost windows in both commit and
    post-reveal skill-test windows.
  - Skill riders for Vicious Blow, Deduction, Guts, and Manual Dexterity, including max
    1/test on Guts and Manual Dexterity.
  - Static modifiers and reactions for Beat Cop, Magnifying Glass, Dr. Milan Christopher,
    Guard Dog, Evidence!, Dodge, Mind over Matter, Working a Hunch, Barricade, Old Book of
    Lore, Research Librarian, and Medical Texts.
- Implemented The Gathering encounter card behavior for the phase C pool:
  - Spawn locations and enemy keywords for Ghoul Priest, Flesh-Eater, Icy Ghoul, Swarm of
    Rats, Ghoul Minion, and Ravenous Ghoul.
  - Lita Chantler uncontrolled Parley, controlled combat static, Monster attack damage
    rider, and no-horror soak per DESIGN notes.
  - Grasping Hands, Rotting Remains, Frozen in Fear, Dissonant Voices, Ancient Evils,
    Crypt Chill, Obscuring Fog, and Locked Door.
- Extended the dispatcher for new decision kinds: skill boosts, post-reveal resolution,
  Dodge attack windows, enemy-defeat reactions, and Crypt Chill asset discard.
- Preserved phase B CLI determinism tests by keeping the engine-test fixture simple and
  moving Dodge out of the old seeded opening-hand path.

## Conflicts / Notes

- `DESIGN.md` has no `## 11` heading in this checkout; phase C work used `DESIGN.md` §10,
  the adjacent scenario notes in §12 where relevant, and `specs/phase_c.md`.
- Roland's .38 Special JSON says the +3 combat condition is "1 or more clues on your
  location"; DESIGN/phase C says to use a Cultist enemy at Roland's location. Implemented
  the DESIGN/phase C Cultist condition and tested it with Silver Twilight Acolyte.
- Lita Chantler JSON has 3 sanity, but phase C explicitly says "3 health, no sanity —
  cannot soak horror." Implemented the phase C version and prevented horror assignment to
  Lita.
- Old Book of Lore JSON searches the top 3 cards and draws one; DESIGN §10 notes simplify
  it to "draws 1." Implemented the DESIGN simplification.
- Cover Up JSON is an optional reaction, but phase C cross-cutting requirements require the
  redirect to apply to clue discoveries. Implemented automatic redirect so every discovery
  source is covered consistently.

## Verification

- `python3 -m compileall -q arkham tests`
- `python3 -m unittest discover -s tests`

Final suite status: 58 tests passing.

No git commit was made, per instruction.
