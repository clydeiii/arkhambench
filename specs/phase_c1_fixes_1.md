# Phase C1 fixes batch 1 — Midnight Masks review findings

Claude's review of phase C1 found these gaps. Fix all, keep the suite green, extend
tests as noted, update specs/phase_c1_report.md with a "Fixes batch 1" section.

## 1. Location abilities are entirely missing (biggest gap)

Implement every printed location ability for the Midnight Masks family, following the
existing pattern used for Gathering locations (Study draw action etc. in
arkham/actions.py). All are [action] abilities on the investigator's current location
unless noted; enforce the printed limits (track per-game usage in state.limits, per-turn
where noted; these are per-location-instance limits):

- Your House (01124): draw 1 card AND gain 1 resource. Limit once per TURN.
- Southside/Historical Society (01126): draw 3 cards. Limit once per game.
- Southside/Ma's Boarding House (01127): search your deck for an Ally asset, add to
  hand, shuffle. Limit once per game. (Present a choice among matches like other
  search effects; searching with zero Allies left still consumes the limit.)
- St. Mary's Hospital (01128): heal 3 damage. Limit once per game. (Only offer when
  damage > 0.)
- Miskatonic University (01129): search top 6 of deck for a Tome or Spell, add to
  hand, shuffle. No printed limit (repeatable).
- Downtown/First Bank (01130): gain 3 resources. Limit once per game.
- Downtown/Arkham Asylum (01131): heal 3 horror. Limit once per game.
- Easttown (01132): PASSIVE — while you are in Easttown, Ally assets you play cost 2
  less (floor 0). Wire into the play-cost computation the same way other cost
  modifiers work.
- Graveyard (01133): no action (its Forced enter-test already implemented).
- Northside (01134): spend 5 resources → gain 2 clues from the token pool. GROUP limit
  once per game. ("From the token pool" = clues added to the investigator directly,
  not taken from the location.)
- Return variants:
  - Easttown/Police Station (50027): add 2 supply or ammo tokens to an asset you
    control (choice among assets that use ammo/supply charges). Limit once per game.
    If no such asset in play, the option is unavailable.
  - Northside/Train Station (50028): move to any revealed-or-unrevealed Arkham
    location (any location in play in this scenario). Limit once per game. This is a
    move effect (triggers enter effects, engage checks), not a basic move action —
    still provokes AoO normally as an activate action if engaged... it is an activate
    ([action]) ability, so AoO applies per the standard activate rules.
  - Miskatonic/Museum (50029): take 2 horror → gain 1 clue from the token pool. Limit
    once per game. (Horror is a cost: only offer if the investigator would survive it
    or per engine's existing cost-payment rules for self-damage costs; if sanity
    would hit 0, taking it is legal but defeats — match how Forbidden Knowledge-style
    self-costs are handled today.)
  - Rivertown/Abandoned Warehouse (50030): discard a card with at least 1 willpower
    icon from hand → remove X doom from a single Cultist enemy in play, X = that
    card's willpower icons. GROUP limit once per game. Only offer when a Cultist
    enemy with doom exists and hand has a willpower-icon card. Present card choice,
    then target choice if multiple.

The Masked Hunter clue-block does NOT affect any of these (none spend/discover clues —
Northside/Museum GAIN from pool, which is neither spending nor discovering... check:
"gain clues from the token pool" is not "discover"; keep them allowed).

Tests: one per ability (limit enforcement included), plus Easttown discount and a
Warehouse doom-removal path.

## 2. Ghoul Priest spawn redirect (Your House Forced)

When Ghoul Priest (01116) is drawn from the encounter deck in this scenario:
- If Your House is in play: spawn him AT Your House (not engaged; he's a Hunter, he'll
  come) per Your House's Forced ability.
- If the house burned: he has no spawn instruction → RR default: spawn engaged with
  the drawing investigator at their location.
Test both branches (house standing / burned) by stacking the encounter deck.

## 3. Ruth Turner on non-test evasion

Ruth's Forced ("after Ruth Turner is evaded") must also trigger for evasion that
doesn't use a skill test, e.g. Cunning Distraction ("all enemies at your location are
considered evaded"). Route ALL evade-success paths (test-based evade, Cunning
Distraction, Survival Instinct's evade if it evades, any 'considered evaded' effect —
NOT plain disengages like Elusive) through a single after-evaded hook that the
scenario can observe. Test: Cunning Distraction with Ruth engaged → Ruth in victory
display, other enemies merely exhausted+disengaged.

## 4. Ready enemies engage on spawn at the investigator's location

`spawn_enemy(..., engaged=False)` at the investigator's location currently leaves a
ready non-Aloof enemy unengaged until the next global engage check. Per RR, a ready
enemy at an investigator's location engages immediately. Change the spawn paths used
by Midnight Masks (named cultists spawning at the investigator's location, Acolyte/
Disciple fallback spawns when no empty location exists) so that a ready, non-Aloof
enemy spawning at the investigator's location engages right away, WITHOUT breaking
the deliberate engaged=False semantics used elsewhere (e.g. hunter spawns mid-attack
sequences in the Gathering — audit call sites; if a call site truly needs
no-engagement, it should pass a new explicit flag). Add a test: Peter Warren drawn
from the Cultist deck while the investigator is at Miskatonic University → spawns
engaged.

## Constraints

- Do not change scoring, resolutions, or the campaign block.
- Keep all 186 existing tests passing; add the new ones.
- Re-run both fuzz commands (50 games, both variants) clean.
- No git commits.
