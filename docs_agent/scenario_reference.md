# Scenario Reference — Night of the Zealot, Part I

Public setup information for the scenario you are playing — either **The Gathering** or
**Return to The Gathering** (`./ahlcg state` shows which). This is the same information a
human player has after performing setup: the contents of the encounter deck are known as a
pool, but their order and draws are not.

## Your investigator

The run assigns one of the five core investigators. Stats (Willpower/Intellect/Combat/
Agility · Health/Sanity), ability, and elder sign:

| Investigator | Stats | Ability (see card for exact text) | Elder sign |
|---|---|---|---|
| Roland Banks (Guardian) | 3/3/4/2 · 9/5 | Reaction after you defeat an enemy: discover 1 clue at your location (1×/round) | +1 per clue on your location |
| Daisy Walker (Seeker) | 3/5/2/2 · 5/9 | 1 extra action per turn, usable only on Tome ability activations | +0; on success draw 1 per Tome you control |
| "Skids" O'Toole (Rogue) | 2/3/3/4 · 8/6 | Fast, 1×/turn: spend 2 resources for 1 extra action | +2; on success gain 2 resources |
| Agnes Baker (Mystic) | 5/2/2/3 · 6/8 | Reaction after horror is placed on her: deal 1 damage to an enemy at your location (1×/phase) | +1 per horror on her |
| Wendy Adams (Survivor) | 4/3/1/4 · 7/7 | Reaction on token reveal, 1×/test: discard a card to cancel and redraw | +0; auto-success if Wendy's Amulet is in play |

Your 33-card deck (30 + 2 signature cards + 1 fixed basic weakness) is a community
"Better Starter Deck" — strategy summary in `docs_agent/decks_guide.md`, exact card text
via `./ahlcg card <name>`.

## Difficulty & chaos bag (Standard)

+1, 0, 0, −1, −1, −1, −2, −2, −3, −4, skull ×2, cultist, tablet, auto-fail, elder sign.

Scenario token effects (Easy/Standard — same reference card in both scenarios):

- **Skull:** −X, where X = number of Ghoul enemies at your location.
- **Cultist:** −1. If you fail, take 1 horror.
- **Tablet:** −2. If there is a Ghoul enemy at your location, take 1 damage.
- **Auto-fail:** you automatically fail.
- **Elder sign:** your investigator's effect (table above).

## The Gathering — encounter deck (27 cards, shuffled)

From encounter sets *The Gathering, Rats, Ghouls, Striking Fear, Ancient Evils, Chilling Cold*:

| Qty | Card | Type |
|---|---|---|
| 1 | Flesh-Eater | Enemy 4/4/1, dmg 1 / horror 2, Victory 1, spawns Attic |
| 1 | Icy Ghoul | Enemy 3/4/4, dmg 2 / horror 1, Victory 1, spawns Cellar |
| 3 | Swarm of Rats | Enemy 1/1/3, dmg 1, Hunter |
| 3 | Ghoul Minion | Enemy 2/2/2, dmg 1 / horror 1 |
| 1 | Ravenous Ghoul | Enemy 3/3/3, dmg 1 / horror 1 |
| 3 | Grasping Hands | Treachery: test Agility (3), 1 damage per point failed |
| 3 | Rotting Remains | Treachery: test Willpower (3), 1 horror per point failed |
| 2 | Frozen in Fear | Treachery: threat area; first move/fight/evade each round costs +1 action; end of turn Willpower (3) to shake |
| 2 | Dissonant Voices | Treachery: threat area; can't play assets/events; discards at end of round |
| 3 | Ancient Evils | Treachery: +1 doom on agenda (can advance it) |
| 2 | Crypt Chill | Treachery: test Willpower (4); fail → discard an asset (or 2 damage if none) |
| 2 | Obscuring Fog | Treachery: attaches to your location, +2 shroud until successfully investigated |
| 2 | Locked Door | Treachery: attaches to location with most clues; blocks investigation until Combat(4)/Agility(4) test |

You begin in the **Study** (shroud 2, 2 clues). **Act 1a — "Trapped"** advances by
spending 2 clues during your turn; the house map opens up from there.

## Return to The Gathering — differences

Same agendas, resolutions, token effects, and scoring. Setup and the encounter pool
change (scenario card *Return to The Gathering*):

- **Encounter deck (32 cards):** as above, but the *Ghouls* set (Ghoul Minion ×3,
  Ravenous Ghoul ×1, Grasping Hands ×3) is replaced by *Ghouls of Umôrdhoth*, and the
  Return set adds three cards:

| Qty | Card | Type |
|---|---|---|
| 3 | Grave-Eater | Enemy 2/2/2, dmg 1 / horror 1; after it attacks you, discard 1 random card |
| 1 | Acolyte of Umôrdhoth | Enemy 3/3/2, dmg 1 / horror 1; cannot be evaded while your hand is empty |
| 3 | Chill from Below | Treachery: test Willpower (3); discard 1 random card per point failed, 1 damage per card you cannot discard |
| 1 | Corpse-Hungry Ghoul | Enemy 4/3/3, dmg 2 / horror 2, Victory 1, Hunter, spawns Bedroom |
| 1 | Ghoul from the Depths | Enemy 3/4/2, dmg 1 / horror 1, Victory 1, Retaliate, spawns Bathroom |
| 2 | The Zealot's Seal | Treachery: hand ≤3 → 1 damage + 1 horror; hand ≥4 → Willpower (2) or discard 2 random |

  The new set punishes a small hand — manage your card economy.

- **Map:** you begin in the **Study (Aberrant Gateway)** (shroud 3, 1 clue), which lets
  the lead investigator spend 2 actions to draw 3 cards, and which pulls not-in-play
  spawn locations into play. It connects only to the **Guest Hall** (draw actions
  forbidden there), which connects to the **Bedroom** (failed investigates there discard
  a random card) and **Bathroom** (skull/cultist/tablet/auto-fail while investigating
  there ends your turn).
- **Act 1a — "Mysterious Gateway"** requires 3 clues, spendable only in the Guest Hall.
  Advancing opens a hole in the wall and forcibly moves you deeper into the house
  (willpower test on the way in). The Attic and Cellar you find beyond are chosen at
  random during setup from the original and Return versions — the deeper locations
  beyond them (worth Victory points) exist only behind the Return versions.
- Ghoul Priest and Lita Chantler are set aside, exactly as in The Gathering.

## Scoring (both scenarios)

At game end you earn experience (XP) = total Victory X in the victory display (defeated
Victory enemies; revealed, clueless Victory locations) + any resolution bonuses.

**Benchmark score = XP − trauma suffered + 3 if you earned Lita Chantler** (minimum 0).

The +3 reflects Lita's campaign value: she is a powerful story ally that joins your deck
for the rest of the campaign in some outcomes but not others — which outcomes is yours to
discover. Trauma is permanent campaign damage: defeat causes it (physical if by damage,
mental if by horror), some resolution choices cause it, and some signature weaknesses
cost trauma or XP at game end (see your deck's entry in `docs_agent/decks_guide.md`).
Getting killed by the agenda while still trapped in the house scores 0. Resigning is
safe but forfeits unearned victory points.
