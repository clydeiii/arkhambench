# Phase V5 — Wendy Adams + survivor/rogue package

Prereq: phase V1 (required; Lucky! and the token-reveal reaction already exist there).
Read `specs/phase_v1_investigators.md`, prior reports. Rules authority: RR + JSON; flag
conflicts.

Goal: every card in `data/decks/killbray/wendy.json` implemented; `--investigator wendy`
passes validation and full games are playable.

Already implemented: Lucky! 01080 (V1), neutrals, Wendy ability + elder sign (V1).

## Cards

- **01014 Wendy's Amulet** (asset, 2, Accessory, Relic): "You may play the topmost event
  in your discard pile as if it were in your hand. Forced — After you play an event or
  discard an event from play: Place it on the bottom of your deck instead of in your
  discard pile." While in play: (1) event-play options must also offer the TOPMOST event
  of the discard pile (cost paid normally, all play rules apply); (2) events that would
  hit the discard pile from PLAY (resolved events, whether played from hand or discard)
  go to the BOTTOM of the deck instead. Events discarded from HAND (e.g. to Amnesia,
  hand-size, Wendy's own ability) still go to discard — "from play" only. Also enables
  Wendy's elder sign auto-success (hook exists from V1).
- **01015 Abandoned and Alone** (weakness treachery, Madness): "Revelation — Take 2
  direct horror and remove all cards in your discard pile from the game." Direct horror
  = cannot be assigned to asset soak (RR "Direct Damage/Horror"); discard pile is
  REMOVED FROM GAME (new zone or just empty + log; removed cards are gone for
  Scavenging/Amulet).
- **01046 Pickpocketing** (asset, 2, Talent, Illicit): "[reaction] After you evade an
  enemy, exhaust Pickpocketing: Draw 1 card." Any successful evasion (basic action,
  Stray Cat, Cunning Distraction, Elusive does NOT evade — it disengages; verify per RR
  "Evade" vs "Disengage").
- **01048 Leo De Luca** (asset, 6, Ally, health 2 sanity 2): "You may take an additional
  action during your turn." Unrestricted 4th action (stacks with Skids' bought action
  and Daisy's Tome action in principle — the action-source machinery from V1).
- **01051 Backstab** (event, 3): "Fight. This attack uses [agility] instead of [combat].
  This attack deals +2 damage." Fight-keyword event → the play IS a fight action,
  AoO-EXEMPT; agility-based; +2 damage on success (3 total).
- **01073 Scavenging** (asset, 1, Talent): "[reaction] After you successfully
  investigate by 2 or more, exhaust Scavenging: Choose an [[Item]] card in your discard
  pile and add it to your hand." Success-by margin uses the audited margin rules;
  choice among Item-trait cards in discard.
- **01075 Rabbit's Foot** (asset, 1, Accessory, Charm): "[reaction] After you fail a
  skill test, exhaust Rabbit's Foot: Draw 1 card." After-fail reaction window (V1 built
  the would-fail window at ST.6; this one fires after failure is FINAL, ST.7 — reuse the
  test-aftermath hooks; order vs "Look what I found!" is player's choice if both open).
- **01077 Dig Deep** (asset, 2, Talent): fast resource pumps for willpower and agility —
  Physical Training pattern, pre-reveal only.
- **01078 Cunning Distraction** (event, 5): "Evade. Automatically evade all enemies at
  your location." Evade-keyword → AoO-exempt play; no test; exhausts + disengages every
  enemy at the location (engaged or not), Elite included (no non-Elite restriction
  here). Pickpocketing triggers (you evaded ≥1 enemy — fires once per exhaust since it
  exhausts itself).
- **01079 "Look what I found!"** (event, 2, Fortune): "Fast. Play after you fail a skill
  test by 2 or less while investigating. Discover 2 clues in your location." After-fail
  fast window, condition: investigate test, failed by ≤2 (autofail counts — value 0 vs
  difficulty can fail by >2; use real margin), discovers 2 clues (capped by clues
  present).
- **01081 Survival Instinct** (skill, agility): "If this skill test is successful during
  an evasion attempt, the evading investigator may immediately disengage from each other
  enemy engaged with him or her, and may move to a connecting location." Both effects
  OPTIONAL (decision: disengage others? move where?). Disengage ≠ evade (enemies stay
  ready; Pickpocketing does not fire for them).

## Tests

1. Wendy fuzz N=25 clean; validation passes.
2. Amulet: topmost discard event playable (and only the topmost); played events loop to
   deck bottom; hand-discarded events still reach discard pile; elder sign auto-succeeds
   with Amulet in play.
3. Abandoned and Alone: 2 horror bypass soak assets; discard pile emptied to
   removed-from-game; Scavenging/Amulet cannot see removed cards.
4. Backstab: agility math, 3 damage, AoO-exempt; Sneak-Attack-style plain events still
   provoke (regression).
5. Look what I found!: offered on investigate fail by ≤2 only; yields 2 clues (or 1 if
   only 1 remains); interacts with Rabbit's Foot (both offered, player order).
6. Survival Instinct: optional mass disengage + optional connecting move on successful
   evade.
7. Leo De Luca grants a 4th action every turn while in play; soak works.
8. Pickpocketing fires on basic evade + Cunning Distraction, not on Elusive/Survival
   Instinct disengages.
9. Full suite + fuzz 50 green.

Write `specs/phase_v5_report.md`. Do not git commit.
