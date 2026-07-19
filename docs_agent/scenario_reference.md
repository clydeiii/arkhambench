# Scenario Reference — Night of the Zealot

Public setup information for the scenario you are playing (`./ahlcg state` shows which).
This is the same information a
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

Scenario token effects (Easy/Standard — The Gathering / Return to The Gathering):

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

## The Midnight Masks — public setup

You begin in **Your House** if it is still standing, or **Rivertown** if it burned down.
Your objective is to find as many unique Cultist enemies as possible and add them to the
victory display. There is a separate, hidden **Cultist deck** of five named cultists.
The act ability costs one action and 2 clues: draw the top Cultist-deck card and spawn it
at its printed location. Named cultists can usually be handled by fighting or by a printed
route:

- Herman Collins: Parley by discarding 4 cards from hand.
- Peter Warren: Parley by spending 2 clues.
- Victoria Devereux: Parley by spending 5 resources.
- Ruth Turner: evade her to add her to the victory display.
- "Wolf-Man" Drew: fight him; he heals 1 damage when he attacks.

Agenda 1 and agenda 2 both offer **Resign**. Resigning ends at Resolution 1 with the
information gathered so far. Doom on enemies counts toward agenda thresholds; agenda
advancement clears doom from every card in play. If agenda 2 advances, it is past
midnight and the scenario ends at Resolution 2.

If no resolution was reached because each investigator resigned or was defeated, read
Resolution 1; an investigator defeated during the scenario still suffers the usual trauma.

The original encounter deck has 21 cards: Hunting Shadow ×3, False Lead ×2, Acolyte ×3,
Wizard of the Order ×1, Mysterious Chanting ×2, Hunting Nightgaunt ×2, On Wings of
Darkness ×2, Crypt Chill ×2, Obscuring Fog ×2, and Locked Door ×2. Ghoul Priest may also
be shuffled in from campaign state.

Scenario token effects (Easy/Standard):

- **Skull:** −X, where X is the highest doom on a Cultist enemy in play.
- **Cultist:** −2; place 1 doom on the nearest Cultist enemy.
- **Tablet:** −3; if you fail, place 1 of your clues on your location.

Hard/Expert changes: Skull is −total doom in play; Cultist places 1 doom on each Cultist
enemy, or reveals another token if none are in play; Tablet is −4 and drops all your
clues on failure.

## Return to The Midnight Masks — differences

The Return setup keeps a 5-card Cultist deck, but starts from the five core cultists plus
Jeremiah Pierce, Billy Cooper, and Alma Hill, then removes three at random unseen. Agenda
1 is randomly either The Masked Hunter or Narogath on the reverse side. Easttown,
Northside, Miskatonic University, and Rivertown are each randomly the original or Return
version; Southside and Downtown are randomized as in the original scenario.

The encounter deck has 23 cards: Hunting Shadow ×3, False Lead ×2, Disciple of the
Devourer ×3, Corpse-Taker ×1, Mask of Umordhoth ×2, Hunting Nightgaunt ×2, On Wings of
Darkness ×2, Crypt Chill ×2, Obscuring Fog ×2, Locked Door ×2, and Masked Horrors ×2.

Return named cultist routes:

- Jeremiah Pierce: Parley to add him to victory, then test Willpower (4); failed points
  place doom on the agenda.
- Billy Cooper: add him to victory after a Monster enemy is defeated at his location.
- Alma Hill: Parley to draw and resolve the top 3 encounter cards, then add her to
  victory.

## Scoring (both scenarios)

At game end you earn experience (XP) = total Victory X in the victory display (defeated
Victory enemies; revealed, clueless Victory locations) + any resolution bonuses. The
Midnight Masks has no resolution XP bonus.

**Benchmark score = XP − trauma suffered** (minimum 0).

Trauma is permanent campaign damage: defeat causes it (physical if by damage, mental if
by horror), some resolution choices cause it, and some signature weaknesses cost trauma
or XP at game end (see your deck's entry in `docs_agent/decks_guide.md`). Getting killed
by the agenda while still trapped in the house scores 0. Resigning is safe but forfeits
unearned victory points. Whether Lita Chantler joins your campaign is tracked and
reported per outcome (which outcomes earn her is yours to discover) but does not add to
the score.
