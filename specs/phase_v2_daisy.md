# Phase V2 — Daisy Walker package

Prereq: phase V1 (investigator framework, timing windows) is merged. Read
`specs/phase_v1_investigators.md` §2–§3 and `specs/phase_v1_report.md` first, plus
DESIGN.md §10 (card framework). Rules authority: `docs_agent/rules_reference.md` (RR) +
vendored JSON. Flag spec-vs-RR/JSON conflicts in your report; follow RR/JSON.

Goal: every card in `data/decks/killbray/daisy.json` is implemented; `./ahlcg new
--investigator daisy` passes deck validation and a full game is playable.

Already implemented (verify, don't rebuild): all seeker cards 01030–01039, neutrals,
Ward of Protection 01065 (V1), Daisy's ability + elder sign (V1).

## Cards

- **01008 Daisy's Tote Bag** (asset, 2, Item, icons W/I/wild): "You have 2 additional
  hand slots, which can only be used to hold [[Tome]] assets." Extend the slot system
  with restricted slots (only Tome-trait assets may occupy them; when playing a Tome
  prefer a free restricted slot so regular hand slots stay available; when a restricted
  slot's source leaves play, apply the normal slot-overflow discard rule per RR "Slots").
- **01009 The Necronomicon (John Dee Translation)** (weakness asset, Hand slot, Tome):
  "Revelation — Put The Necronomicon into play in your threat area, with 3 horror on it.
  It cannot leave play while it has 1 or more horror on it. Treat each [elder_sign] you
  reveal on a chaos token as a [auto_fail]. [action]: Move 1 horror from The Necronomicon
  to Daisy Walker. Then, if The Necronomicon has no horror on it, discard it."
  - It enters the THREAT AREA (not a hand slot) via Revelation when drawn; it is an
    asset weakness, so the weakness-draw path must handle asset Revelations.
  - While in play: elder sign tokens resolve as autofail (chaos interpretation override
    — total skill value 0, no elder-sign effect). This is a state-dependent token
    override; keep it a queryable hook, The Gathering's skull is the existing analog.
  - The move-horror action provokes AoO (activate ability), horror goes to Daisy as
    normal horror (can trigger defeat!), discard only when it reaches 0.
  - Its Tome trait does NOT make it usable by Daisy's Tome action (it has an [action]
    ability, so RAW it IS usable with her additional Tome action — allow it).
- **01061 Scrying** (asset, 1, Arcane slot, Spell, uses 3 charges): "[action] Exhaust
  Scrying and spend 1 charge: Look at the top 3 cards of any investigator's deck or the
  encounter deck. Return them to the top of that deck in any order." Solo: targets are
  your deck or the encounter deck (choice decision). The peek is LEGAL player knowledge:
  the decision must name the 3 cards and enumerate all orderings (≤6 options, "first
  listed = topmost"). Encounter-deck order lives in the hidden blob — route the peek
  through the engine so the public decision shows names while the blob stays the only
  place full deck order exists. Activate → provokes AoO.
- **01066 Blinding Light** (event, 2, Spell): "Evade. This evasion attempt uses
  [willpower] instead of [agility]. If you succeed, deal 1 damage to the enemy just
  evaded. If a [skull]/[cultist]/[tablet]/[elder_thing]/[auto_fail] symbol is revealed
  during this evasion attempt, lose 1 action this turn." Evade-keyword event: playing it
  IS an evade action (AoO-EXEMPT per the action-type rule). Base stat swap to willpower;
  symbol-watch hook during ST.3 (Shrivelling in V4 reuses this); "lose 1 action" =
  deduct from remaining actions this turn (floor 0).

## Tests

1. Daisy full-game fuzz (`--investigator daisy`, N=25) clean; deck validation passes.
2. Tote Bag: 2 Tomes + 2 regular hand assets coexist; 3rd regular hand asset still
   forces the usual slot decision; Tote Bag leaving play forces overflow discard.
3. Necronomicon: revelation → threat area with 3 horror; elder sign reveals resolve as
   autofail while in play; 3 move-horror actions (with AoO when engaged) then discard;
   horror moved can defeat Daisy.
4. Scrying on encounter deck: seeded game — peek shows exactly the top 3, chosen
   reorder is respected by subsequent encounter draws, charges deplete, exhaust enforced.
5. Blinding Light: uses willpower, damage on success, symbol reveal costs an action,
   play is AoO-exempt while engaged.
6. Daisy Tome action works with Necronomicon's activate ability.
7. Full suite + fuzz 50 green.

Write `specs/phase_v2_report.md`. Do not git commit.
