# Phase C — Card implementations

Prereq: phase B. Implement EVERY card in DESIGN.md §10 tables (player deck + encounter
cards) against the phase-B hook framework, in `arkham/cards/player.py` and
`arkham/cards/encounter_cards.py`, registered by card code in `registry.py`.

Ground truth for each card = its `text` in `data/cards/core.json` /
`core_encounter.json`, disambiguated by the Notes column in DESIGN §10. Read both. If the
JSON text and DESIGN notes conflict, flag it in your report rather than guessing.

Key cross-cutting requirements:

- **Uses**: ammo/supply counters decrement correctly and gate abilities. First Aid
  self-discards when empty (JSON text); Flashlight does NOT (it stays with 0 supplies).
- **Cover Up**: optional reaction replaces clue DISCOVERY at your location (any source:
  investigate, Roland's ability, Evidence!, Working a Hunch, Deduction extras) — clues
  removed from Cover Up instead of gained; discard Cover Up when it hits 0 clues; game-end
  forced trauma if ≥1 clue remains. The redirect applies to the whole discovery
  (N clues → remove min(N, clues-on-Cover-Up); remainder is discovered normally).
- **Silver Twilight Acolyte**: spawns engaged with Roland on revelation; Hunter toward
  Roland when unengaged (it can be evaded and left behind); after ANY of its attacks
  (enemy phase, AoO, retaliate-n/a) → +1 doom on current agenda (advance check).
- **Skill commit riders** (Vicious Blow, Deduction, Guts, Manual Dexterity) hook
  on_commit_success and respect max-1-per-test where stated.
- **Boost abilities** (Physical Training, Hyperawareness) must appear in BOTH the commit
  window and the post-reveal window, repeatable while resources last, and expire at test
  end. Magnifying Glass/Dr. Milan/Beat Cop static modifiers apply only in their stated
  contexts.
- **Mind over Matter**: substitution lasts until end of round; applies to fight AND evade
  AND any combat/agility test (e.g. Grasping Hands? NO — substitution applies to skill
  tests that USE combat or agility: yes, including treachery tests. Implement as: when
  determining base skill for a test whose skill is combat or agility, use intellect).
- **Dodge**: playable in the attack-declared window (enemy phase attacks, AoOs,
  retaliates); cancels the whole attack.
- **Dynamite Blast**: choose location; damages each enemy AND each investigator there
  (Roland included if he picks his own location — allow it, label clearly).
- **Machete**: +1 damage only if the attacked enemy is engaged with Roland and is the ONLY
  enemy engaged with him.
- **Old Book of Lore / Medical Texts / First Aid** target "an investigator at your
  location" — solo, that's Roland; keep the target parameter explicit anyway.
- **Frozen in Fear**: additional action cost for the FIRST move/fight/evade action each
  round (track per-round); end-of-turn willpower(3) test to discard.
- **Dissonant Voices**: blocks playing assets/events (hand plays), not committing skills;
  auto-discards at end of round.
- **Locked Door**: attaches to in-play location with most clues lacking one (ties:
  deterministic by location code); blocked investigation; grants an [action] test
  combat(4) OR agility(4) (choose) at the attached location to discard.
- **Obscuring Fog**: +2 shroud; discard after the attached location is successfully
  investigated (any investigator).
- **Ancient Evils**: +1 doom, immediate advance check.
- **Grasping Hands / Rotting Remains**: damage/horror equal to points failed by (0 on
  success), assignable to soak normally.
- **Crypt Chill**: fail → choose & discard 1 asset you CONTROL (in play, not hand); if
  none in play → 2 damage.
- **Lita Chantler**: while uncontrolled at Parlor, grants the Parley test (Intellect 4);
  on success Roland takes control (slotless ally, 3 health, no sanity — cannot soak
  horror). Controlled statics: +1 combat at her location; optional reaction on successful
  attack vs Monster trait at her location: +1 damage.
- **Roland's .38 Special**: +3 combat instead of +1 if a Cultist-trait enemy is at
  Roland's location (Acolyte has traits "Humanoid. Cultist."? READ the JSON traits — if
  the Acolyte is the only Cultist in the pool, test with it).

Tests: ≥1 focused unit test per card; the edge cases listed in DESIGN §17. Commit
"Phase C: card implementations" + specs/phase_c_report.md when green.
