# ArkhamBench Engine — Design Document

**Goal:** A rules-enforcing engine + CLI harness that lets LLM coding agents play *Arkham
Horror: The Card Game* (AHLCG) solo — scenario **"The Gathering"** (Night of the Zealot,
Part I) and **"Return to The Gathering"** (Return to the Night of the Zealot), with any of
the **five core-set investigators** — so we can reproduce Epoch AI's EBR-Bench
continual-learning experiments with AHLCG ("ArkhamBench"). Agents interact through a CLI;
the engine enforces all rules, tracks all state, adjudicates skill tests with a seeded
chaos bag, and writes complete game logs. A persistent, compactable **notebook** is a
first-class feature.

Design owner: Claude (planning). Implementation: codex/GPT-5.5 with Claude review.

---

## 1. Principles

1. **The engine is the referee.** Agents never adjudicate rules. They pick from enumerated
   legal choices. Score differences must reflect decision quality, not rules mistakes.
2. **Decision-point loop.** The engine advances the game until player input is required,
   then persists and exits. The agent runs `./ahlcg actions`, picks, runs `./ahlcg do <id>`,
   repeat. Stateless CLI invocations; all state on disk in the run directory.
3. **Determinism.** Every run has a seed. Same seed + same action sequence = identical game.
   All randomness (shuffles, chaos tokens, random discards) flows through one seeded RNG.
4. **Hidden information stays hidden.** Deck orders and RNG state live in an obfuscated
   blob. The public state file and all CLI output contain only player-legal information.
5. **Complete, readable logs.** Every event goes to a JSONL log and a human-readable
   markdown transcript. Clyde must be able to read `log.md` and follow the whole game.
6. **Scoped rules implementation, honest about scope.** We implement the AHLCG rules subset
   needed for The Gathering and Return to The Gathering with the five core investigators'
   "Better Starter Decks" (killbray, revised-core pool) — completely and correctly.
   Architecture leaves room for more cards/scenarios but does not build them.

## 2. Tech & repo layout

- Python ≥ 3.10, **stdlib only** at runtime. Tests use `unittest` (`python3 -m unittest discover -s tests`).
- No network access at runtime. Card data is vendored JSON (arkhamdb-json-data format).

```
ahlcg                      # executable: exec python3 -m arkham "$@"
arkham/
  __main__.py  cli.py      # argparse CLI, run-dir resolution, rendering
  model.py                 # dataclasses: GameState, Investigator, EnemyInstance, CardInstance, Location, ...
  game.py                  # Game facade: load/save, advance loop, decision queue
  rng.py                   # seeded RNG wrapper (random.Random), serializable
  serialize.py             # public state.json + hidden blob (base64(zlib(json)), key-XOR)
  log.py                   # JSONL event log + markdown transcript renderer
  notebook.py              # notebook add/show/compact (+ history archive)
  phases.py                # round structure: mythos / investigation / enemy / upkeep
  actions.py               # basic action generation & execution, attacks of opportunity
  skill_test.py            # skill test state machine (ST.1–ST.8) incl. commit/boost windows
  chaos.py                 # chaos bag, difficulty bags, scenario token effects hook
  enemies.py               # spawn/engage/exhaust/hunter movement/enemy attacks/damage
  encounter.py             # encounter draw, revelation resolution, treachery framework
  effects.py               # effect primitives (damage, horror, draw, discover, doom, heal, move...)
  triggers.py              # reaction/forced/fast windows, once-per-round limits
  cards/
    registry.py            # code -> CardImpl registry; CardImpl hooks (see §10)
    player.py              # Roland LTP deck card implementations
    encounter_cards.py     # The Gathering + Rats/Ghouls/StrikingFear/AncientEvils/ChillingCold
  scenarios/
    the_gathering.py       # setup, act/agenda deck, location graph, resolutions, scoring
  data.py                  # load vendored JSON card DB
data/cards/core.json  data/cards/core_encounter.json
data/decks/roland_ltp.json
docs_agent/rules_reference.md      # full RR for agents (already present)
docs_agent/playing_guide.md        # how to drive the CLI (written in phase E)
docs_agent/scenario_reference.md   # public setup info (encounter set contents, difficulty)
runs/                     # per-run dirs (gitignored)
tests/
specs/                    # phase specs for codex
```

### Run directory layout (`runs/<name>/`)

```
state.json      # public view (also drives `state` rendering)
hidden.blob     # obfuscated: true deck orders, encounter deck, RNG state, set-asides
log.jsonl       # machine events
log.md          # human transcript
meta.json       # seed, difficulty, deck, created-at, engine version, status
result.json     # written at game end: outcome, XP, score, metrics (see §13)
```

The notebook is **not** in the run dir — it persists across runs (see §14).
`AHLCG_RUN` env var or `--run` flag selects the run dir; `ahlcg new` also writes the path
to `.current_run` in CWD, which is the default fallback. All commands operate on the
current run.

## 3. CLI protocol (the agent interface)

```
./ahlcg new [--seed N] [--difficulty easy|standard|hard|expert] [--run runs/NAME]
./ahlcg state          # formatted public game state (see §4)
./ahlcg actions        # the current decision point: numbered options
./ahlcg do <n>         # execute option n; prints resulting events + next decision point
./ahlcg log [--tail N] [--md]
./ahlcg card <code or name fragment>   # oracle text from card DB (public info only)
./ahlcg score          # current metrics; final if game over
./ahlcg note add "text"            # append timestamped note
./ahlcg note show
./ahlcg note compact --file F | -  # replace notebook body (archives previous version)
```

Rules for `do`:
- Every `do` output ends with either the next numbered decision point or `GAME OVER` + summary.
  (Agents shouldn't need a separate `actions` call each step, but it's available.)
- Invalid input → error + re-print options. Never crashes, never corrupts state.
- `do` appends to log; state saved atomically (write temp + rename) before printing.

**Decision points** are uniform: a `prompt` line (whose decision, what's being decided,
during what phase/step), then numbered options with human-readable labels, e.g.

```
[Round 3 · Investigation · Roland Banks · 2 actions left]
Choose an action:
  1. Investigate Study (shroud 2) — test Intellect(3+1=4) vs 2
  2. Move to Hallway
  3. Fight Ghoul Minion (fight 2, 2 dmg) — test Combat(4) vs 2
  ...
  9. Play Emergency Cache (0 res) — Gain 3 resources
 10. Take resource (gain 1)
 11. Pass (end turn)
```

Options embed the key numbers an agent needs (test stat vs difficulty, costs, uses left)
to reduce state-querying burden, but `state` and `card` always have the full picture.

## 4. `state` rendering

Sections: Scenario header (difficulty, round, phase, whose turn, actions left) · Agenda
(name, doom X/threshold) · Act (name, clues X/needed) · Locations (revealed/unrevealed,
shroud, clues, connections, investigators/enemies/attachments present; unrevealed locations
show only their unrevealed-side info) · Roland (hp/sanity, resources, clues, hand count,
stats, engaged enemies, exhausted?) · Play area (assets w/ uses/ammo/damage/horror, threat
area cards w/ clues/doom) · Hand (cards w/ cost+icons) · Chaos bag composition · Victory
display · Discard piles (counts; contents listable via `log`/`card` — both discards are
public zones, so `state --full` lists them) · Deck counts.

## 5. Rules subset — general framework

Solo play only (one investigator, Roland Banks, who is lead investigator). Standard round:

1. **Mythos phase** (skipped on round 1): place 1 doom on agenda → check agenda advance →
   investigator draws 1 encounter card and resolves it (revelation / spawn).
2. **Investigation phase**: Roland takes 3 actions (tracked; extra-action effects exist in
   the card pool but none in this deck — don't build generic support beyond a counter).
3. **Enemy phase**: unengaged ready Hunter enemies move (see §9) → each ready engaged enemy
   attacks its engaged investigator.
4. **Upkeep phase**: ready all exhausted cards → Roland draws 1 card & gains 1 resource →
   check hand size (max 8, choose & discard down) → round ends (end-of-round triggers,
   e.g. Dissonant Voices discards; agenda 3 doom-per-ghoul effect).

Player windows (for fast cards/abilities and reactions) exist: any time during Roland's
turn between actions; at defined points in other phases per RR. **Pragmatic rule:** the
engine surfaces a window as a decision point only when at least one optional trigger/fast
play is actually legal; otherwise it auto-passes silently. Forced effects auto-resolve
(with any embedded choices surfaced as decision points).

### Basic actions (investigation phase)

- **Investigate**: skill test Intellect vs location shroud. Success: discover 1 clue
  (→ Cover Up redirect may apply, §11).
- **Move**: to a connecting location. Two rules interact here (implement both):
  (a) **Attacks of opportunity**: whenever an investigator engaged with one or more ready
  enemies takes any action OTHER than Fight, Evade, Parley/Resign, or activating an
  ability with a Fight/Evade designator, each such enemy makes an attack of opportunity —
  a full attack dealing its damage AND horror. Move, Investigate, Draw, Resource, Play,
  and other Activate actions all provoke. Fast cards/abilities (no action) never provoke.
  (b) **Engaged enemies move with you**: if an engaged investigator moves, engaged enemies
  move with him and remain engaged. Disengaging requires the Evade action (or an effect).
- **Fight**: choose engaged or unengaged enemy at your location (attacking an enemy engaged
  with you; attacking an unengaged enemy at your location is allowed). Test Combat vs
  enemy fight. Success: deal damage (base 1 + modifiers). Failure vs enemy engaged with
  another investigator would hit them — solo: n/a. **Retaliate** (Ghoul Priest): after an
  investigator fails a skill test while attacking a READY enemy with Retaliate, that enemy
  performs an attack against the attacking investigator (exhausted enemies do not
  retaliate; a retaliate attack is a full attack: damage + horror).
- **Evade**: test Agility vs enemy evade, engaged enemies only. Success: exhaust enemy +
  disengage (aloofness n/a). Automatic-evasion effects: none in pool.
- **Engage**: engage an unengaged enemy at your location (no test).
- **Draw**: draw 1 card. **Resource**: gain 1. Both provoke AoO.
- **Play**: play an asset or (non-fast) event from hand, paying cost. Provokes AoO
  (fast cards played in windows do not use an action and don't provoke).
- **Activate**: use an [action]-designated ability on an in-play card (e.g. .45 Automatic
  fight, Flashlight investigate, First Aid, Old Book of Lore, Medical Texts, Locked Door
  test). Fight/Investigate/Evade designators inherit those actions' AoO behavior.
- **Parley**: Lita's granted parley action (only surfaced at Parlor while Lita uncontrolled).
- **Resign**: only via Parlor's [action] ability once Parlor is revealed.
- Advancing the act by **spending clues** is a group ability during any investigator
  window in the investigation phase, not an action, EXCEPT Act 2 "The Barrier" which per
  its Objective happens when the round ends (see §12). Act 1 "Trapped": default rule —
  surfaced as a free option whenever Roland has ≥2 clues during his turn.

### Skill tests (skill_test.py) — ST.1–ST.8

1. Determine skill + difficulty (apply static modifiers: Obscuring Fog shroud, Flashlight
   shroud reduction, Machete/.45 boosts, Physical Training pumps, committed icons...).
2. **Commit window** (decision point, repeatable): commit 0+ cards from hand with matching
   icons or wild icons (skills like Guts "max 1 committed per test" enforced); also offers
   legal fast abilities (Physical Training, Hyperawareness pumps). Ends with "Done".
3. Reveal chaos token (seeded draw, with replacement — token returned at end of test).
4. Apply token effect (scenario-defined, §12; autofail ⇒ test fails regardless).
   **No player window exists after the reveal** (RR timing chart: windows only before
   ST.3) — boosts must be committed before seeing the token.
5. Compute modified skill value = base + committed icons + active boosts + token modifier
   (min 0). **Autofail: total skill value is considered 0** (RR ST.6).
6. Success iff modified value ≥ modified difficulty (ties succeed) and token ≠ autofail.
   Record success margin (needed for Grasping Hands / Rotting Remains "per point";
   on autofail the fail-by margin is computed from value 0).
7. Apply results (action-specific + committed-card riders like Vicious Blow/Deduction/
   Guts/Manual Dexterity draw riders, elder-sign effect already applied as modifier in 5;
   Roland's elder sign: +1 per clue on your location).
8. Test ends: committed cards → discard; "for this test" effects expire.

### Damage, horror, defeat

- Damage/horror to Roland may be assigned among Roland + his in-play Ally assets with
  health/sanity (Beat Cop 2/2, Guard Dog 3/1, Research Librarian 1/1, Dr. Milan 1/2 —
  read exact values from JSON), respecting that each point is assigned wholly; direct
  damage (none in pool? treachery damage IS assignable; only "direct" keyword bypasses —
  none in this pool) → decision point when allies present, else auto.
- Asset destroyed when damage ≥ health or horror ≥ sanity → discard (Guard Dog reaction
  triggers before it dies if damage assigned to it during an enemy attack).
- Roland defeated when damage ≥ 9 or horror ≥ 5 → game ends, no-resolution outcome
  (+1 physical or mental trauma per cause; both = both). Cover Up end-of-game check still applies.

### Card plays & economy

- Costs paid from resource pool. Slots enforced: 2 hand slots, 1 ally slot, 1 body, 1
  accessory, 2 arcane (only hand+ally matter in this pool). Playing into a full slot →
  option to discard existing occupant(s) or abort.
- Uses (ammo/supplies) tracked per asset. Exhaust/ready tracked. "Limit once per round"
  tracked (Roland's ability).
- Unique (✦): only one copy of a unique card in play (Lita; allies are non-unique here
  except Milan/Beat Cop/etc. are unique by ✦? — read `is_unique` from JSON and enforce).

## 9. Enemies

- **Spawn**: encounter enemy spawns at its Spawn location (Flesh-Eater→Attic, Icy
  Ghoul→Cellar); if that location is not in play, discard it (no effect). No spawn text →
  spawns engaged with the drawing investigator (at his location). Silver Twilight Acolyte:
  spawns engaged with Roland (weakness, Prey: bearer).
- **Engage**: enemy at Roland's location + unengaged + ready → engages immediately when it
  spawns there or moves there or Roland moves to it (solo: any ready unengaged non-aloof
  enemy at Roland's location engages him; no aloof in pool).
- **Hunter movement** (enemy phase): each ready, unengaged Hunter moves 1 location along
  shortest path toward nearest investigator (solo: Roland); if it reaches him it engages.
  Barricade: non-Elite enemies cannot move INTO the attached location (Hunter stays put).
  Agenda 3 forced: end of enemy phase, unengaged Ghouls move 1 toward the Parlor
  (Barricade still blocks non-Elite).
- **Enemy attacks** (enemy phase): each ready engaged enemy attacks: deal its damage/horror
  (assignment decision), then the enemy EXHAUSTS (RR 3.3; AoO and retaliate attacks do
  not exhaust). With multiple attackers, the attacked investigator chooses the order.
- **Defeat**: enemy damage ≥ health → defeated → victory display if it has Victory X, else
  encounter discard. Roland reaction (defeat an enemy → discover 1 clue, 1/round) and
  Evidence! window trigger here.
- Exhausted enemies: don't attack, don't hunt, don't engage, don't make AoOs; ready in upkeep.

## 10. Card implementation framework

`registry.py`: `@card("01020")` decorated classes implementing hooks; a card gets its
static data (name, cost, icons, health, text...) from the JSON DB, and its behavior from
the impl. Hooks (all optional): `can_play/on_play`, `actions()` (granted [action]
abilities), `fast_abilities(window)`, `reactions(event, window)`, `forced(event)`,
`static_modifiers(query)` (e.g. +1 intellect, +1 combat while investigating, shroud mods,
"cannot" effects), `on_commit_success/failure`, `on_enter_play/leave_play`, `on_reveal`
(treachery revelation), `token_effect` (scenario card). Engine queries these at defined
points; effects execute via `effects.py` primitives so logging is uniform.

**Every card in scope** (exact behaviors; codex: read full rules text from the JSON DB and
implement per these notes):

Player deck (data/decks/roland_ltp.json, 33 cards):
| Code | Card | Notes |
|---|---|---|
|01001|Roland Banks|9/5, 3/3/4/2. Reaction (optional, 1/round): after you defeat an enemy → discover 1 clue at your location. Elder sign: +1 per clue on your location.|
|01006|Roland's .38 Special|Asset, hand, 4 ammo. Action, 1 ammo: Fight +1 combat (+3 combat instead if ≥1 clue on your location), +1 damage.|
|01007|Cover Up|Weakness treachery. Revelation: threat area, 3 clues. OPTIONAL reaction (player chooses each time): when you would discover clues at your location → discard that many from Cover Up instead. Forced, game end: if ≥1 clue on it → 1 mental trauma. When last clue removed → discard it.|
|01102|Silver Twilight Acolyte|Weakness enemy 2/3/2? (read JSON: fight/health/evade, dmg/horror). Prey: bearer only. Hunter. Forced after it attacks: +1 doom on agenda. Spawns engaged with Roland on draw.|
|01016|.45 Automatic|Hand, 4 ammo. Action, 1 ammo: Fight +1 combat, +1 damage.|
|01017|Physical Training|Talent, no slot. Fast, 1 resource: +1 willpower this test; or +1 combat this test.|
|01018|Beat Cop|Ally ✦ 2/2. Passive +1 combat. Fast, discard: 1 damage to an enemy at your location.|
|01019|First Aid|Talent, 3 supplies; discard when empty. Action, 1 supply: heal 1 damage OR 1 horror from an investigator at your location.|
|01020|Machete|Hand. Action: Fight +1 combat; +1 damage if attacked enemy is the ONLY enemy engaged with you.|
|01021|Guard Dog|Ally 3/1. Reaction (optional) when an enemy attack deals damage assigned to Guard Dog: deal 1 damage to that enemy.|
|01022|Evidence!|Fast event, play after you defeat an enemy: discover 1 clue at your location.|
|01023|Dodge|Fast event, play when an enemy attacks you: cancel that attack.|
|01024|Dynamite Blast|Event, action: choose your or connecting location: 3 damage to EACH enemy and EACH investigator there (Roland can hit himself — warn in option label).|
|01025|Vicious Blow|Skill (+1 combat icon): if test successful during an attack → +1 damage.|
|01030|Magnifying Glass|Fast asset, hand. +1 intellect while investigating.|
|01031|Old Book of Lore|Tome, hand. Action, exhaust: investigator at your location searches top 3 cards of deck, draws 1, shuffles rest back.|
|01032|Research Librarian|Ally 1/1. Reaction on enter play (optional): search deck for a Tome, add to hand, shuffle.|
|01033|Dr. Milan Christopher|Ally ✦ 1/2. +1 intellect. Reaction (optional) after you successfully investigate: gain 1 resource.|
|01034|Hyperawareness|Talent. Fast, 1 resource: +1 intellect or +1 agility this test.|
|01035|Medical Texts|Tome, hand. Action: choose investigator at your location, test Intellect(2): success heal 1 damage; failure DEAL 1 damage to them.|
|01036|Mind over Matter|Fast event, your turn: until end of round use Intellect in place of Combat and Agility.|
|01037|Working a Hunch|Fast event, your turn: discover 1 clue at your location.|
|01038|Barricade|Event: attach to your location. Non-Elite enemies cannot move into it. Forced: when you leave the location → discard it.|
|01039|Deduction|Skill (+1 intellect): if successful while investigating → discover 1 additional clue.|
|01086|Knife ×2|Hand. Action: Fight +1 combat. Action, discard Knife: Fight +2 combat, +1 damage.|
|01087|Flashlight ×2|Hand, 3 supplies. Action, 1 supply: Investigate with location shroud −2 (min 0).|
|01088|Emergency Cache ×2|Event: gain 3 resources.|
|01089|Guts ×2|Skill (+2 willpower? read icons from JSON: skill_willpower=2), max 1/test: success → draw 1.|
|01092|Manual Dexterity ×2|Skill (+2 agility), max 1/test: success → draw 1.|

Encounter cards (§12 lists set composition):
| Code | Card | Notes |
|---|---|---|
|01116|Ghoul Priest|4/5/4, 2/2 dmg/horror, Hunter, Retaliate, Elite, Victory 2. Prey highest combat (solo: n/a).|
|01117|Lita Chantler|Story ally (no slot), 3 health / 3 sanity (soaks both). Uncontrolled at Parlor: grants Parley action (Intellect(4) → take control). Controlled: +1 combat to investigators at your location; optional reaction: +1 damage when investigator at your location successfully attacks a Monster.|
|01118|Flesh-Eater|4/4/1, 1/2, Victory 1. Spawn: Attic.|
|01119|Icy Ghoul|3/4/4, 2/1, Victory 1. Spawn: Cellar.|
|01159|Swarm of Rats ×3|1/1/3, 1/0. Hunter.|
|01160|Ghoul Minion ×3|2/2/2, 1/1.|
|01161|Ravenous Ghoul|3/3/3, 1/1. Prey lowest health (solo n/a).|
|01162|Grasping Hands ×3|Revelation: test Agility(3), take 1 damage per point failed.|
|01163|Rotting Remains ×3|Revelation: test Willpower(3), take 1 horror per point failed.|
|01164|Frozen in Fear ×2|Revelation: threat area. First move/fight/evade action each round costs +1 action. Forced end of your turn: test Willpower(3), success → discard it.|
|01165|Dissonant Voices ×2|Revelation: threat area. You cannot play assets or events. Forced end of round: discard it.|
|01166|Ancient Evils ×3|Revelation: +1 doom on agenda (may trigger advance).|
|01167|Crypt Chill ×2|Revelation: test Willpower(4). Fail: discard 1 asset you control (your choice); if you control none → take 2 damage.|
|01168|Obscuring Fog ×2|Revelation: attach to your location (limit 1 Fog per location): +2 shroud. Forced: after attached location successfully investigated → discard it.|
|01174|Locked Door ×2|Revelation: attach to in-play location with most clues without a Locked Door. It can't be investigated. Action ability on it: test Combat(4) or Agility(4) → discard it.|

(Also in "torch" set but engine-driven: scenario card 01104 = chaos token effects,
agendas 01105–01107, acts 01108–01110, locations 01111–01115.)

## 12. Scenario: The Gathering

- **Encounter sets**: The Gathering (torch), Rats, Ghouls, Striking Fear, Ancient Evils,
  Chilling Cold. Encounter deck = those sets minus scenario/act/agenda/location cards,
  minus set-asides (Ghoul Priest, Lita) = Flesh-Eater, Icy Ghoul, Swarm of Rats ×3, Ghoul
  Minion ×3, Ravenous Ghoul, Grasping Hands ×3, Rotting Remains ×3, Frozen in Fear ×2,
  Dissonant Voices ×2, Ancient Evils ×3, Crypt Chill ×2, Obscuring Fog ×2, Locked Door ×2
  = **27 cards**. Reshuffle discard when deck empties.
- **Setup**: Study in play, revealed, clues = 2 (per-investigator ×1). Roland in Study.
  All other locations set aside. Ghoul Priest + Lita set aside. Agenda 1a / Act 1a.
  Roland: 5 resources, draw opening hand 5 (mulligan once — choose any to replace, then
  weaknesses drawn in opening hand are set aside, replaced, and shuffled back).
- **Chaos bag** (Night of the Zealot):
  - easy: +1,+1,0,0,0,−1,−1,−1,−2,−2, skull,skull,cultist,tablet,autofail,eldersign
  - standard: +1,0,0,−1,−1,−1,−2,−2,−3,−4, skull,skull,cultist,tablet,autofail,eldersign
  - hard: 0,0,0,−1,−1,−2,−2,−3,−3,−4,−5, skull,skull,cultist,tablet,autofail,eldersign
  - expert: 0,−1,−1,−2,−2,−3,−3,−4,−4,−5,−6,−8, skull,skull,cultist,tablet,autofail,eldersign
- **Scenario token effects** — Easy/Standard: skull −X (X = Ghoul enemies at your
  location); cultist −1, on fail take 1 horror; tablet −2, if Ghoul at your location take
  1 damage. Hard/Expert: skull −2, on fail search encounter deck+discard for a Ghoul and
  draw it, shuffle; cultist: reveal another token, on fail take 2 horror; tablet −4, if
  Ghoul at your location take 1 damage and 1 horror. Elder sign: Roland's (+1/clue on
  your location).
- **Locations** (connections are NOT in the JSON — hardcode):
  Study: no connections. Hallway ↔ Attic, Hallway ↔ Cellar, Hallway ↔ Parlor.
  Clues per investigator: Study 2, Attic 2, Cellar 2, Hallway 0, Parlor 0.
  Attic (Victory 1): Forced after you enter → 1 horror. Cellar (Victory 1): Forced after
  you enter → 1 damage. Parlor unrevealed side: cannot move into Parlor. Locations enter
  play unrevealed; revealing (on enter) places clues.
- **Act 1 "Trapped" (needs 2 clues)** → on advance: put Hallway/Attic/Cellar/Parlor into
  play (unrevealed), discard each enemy in Study (with all attachments/damage), move Roland
  to Hallway (Hallway revealed; entering via act does NOT trigger "after you enter" forced
  effects? It does — "enter" includes being moved. Hallway has no such effect; fine),
  remove Study from game (clues on it are lost; attachments discarded).
- **Act 2 "The Barrier" (3 clues)**: Objective — when the round ends, investigators in the
  Hallway may spend 3 clues as a group to advance (decision point at end of round).
  On advance: reveal Parlor, Lita into play at Parlor, **spawn Ghoul Priest in the Hallway**
  (it engages Roland if he's there — spawn unengaged in Hallway; if Roland in Hallway it
  engages him).
- **Act 3 "What Have You Done?"**: Objective — if Ghoul Priest is defeated, advance →
  decision: R1 (burn the house) or R2 (refuse).
- **Agenda 1 "What's Going On?!" (3 doom)** → back: choose — discard 1 random card from
  hand, OR take 2 horror. Then Agenda 2.
- **Agenda 2 "Rise of the Ghouls" (7 doom)** → back: shuffle encounter discard into deck;
  discard from encounter deck until a Ghoul enemy is discarded; Roland draws (spawns) it.
  Then Agenda 3.
- **Agenda 3 "They're Getting Out!" (10 doom)**: Forced end of enemy phase — each
  unengaged Ghoul moves 1 toward Parlor. Forced end of round — +1 doom per Ghoul in
  Hallway or Parlor. On doom full: if Act 1 or 2 → **R3**; if Act 3 → Roland (if not
  resigned) defeated + 1 physical trauma → treat as no-resolution outcome for log/score.
- **Doom check** (RR 1.3): the threshold compares TOTAL doom in play (agenda + all other
  cards); on advance, remove ALL doom from play. The agenda advances ONLY at mythos step
  1.3, or when a doom-placing card explicitly permits it (Ancient Evils: "This effect can
  cause the current agenda to advance"). Silver Twilight Acolyte's forced doom and Agenda
  3's end-of-round doom do NOT advance the agenda immediately — they wait for the next
  mythos check.
- **Outcomes**:
  - **R1** (chose burn): record: house burned down; Lita earned; lead suffers 1 mental
    trauma; XP = victory display + 2 bonus.
  - **R2** (chose refuse): record: house standing; Lita earned; +1 XP extra (lead) on top
    of victory display + 2 bonus.
  - **R3** (agenda-out at act ≤2): Roland killed. XP 0. Campaign-log: Lita forced to find
    others.
  - **No resolution** (defeated or resigned): house standing; Ghoul Priest still alive
    (recorded only if actually alive); Lita earned; XP = victory display + 2 bonus.
    Trauma from defeat cause. Cover Up game-end check applies in ALL outcomes.
  - Victory display: Attic/Cellar count if their clues were cleared? — RR: locations go to
    victory display if they have Victory X and **no clues** on them at game end.
    Flesh-Eater/Icy Ghoul 1 each, Ghoul Priest 2 when defeated.

## 13. Scoring & metrics (result.json)

Primary **score = XP earned − total trauma suffered** (floor 0), where XP per §12 and
trauma includes Cover Up/R1/defeat trauma. R3/killed ⇒ score 0. Secondary metrics logged
for analysis: outcome, resolution, rounds played, actions taken, damage/horror taken (and
per-round rate — our "fatigue" analog), clues discovered, cards played, resources gained,
tests attempted/passed by type, enemies defeated, Ghoul Priest defeated?, victory points,
Lita recruited?, encounter cards drawn. `ahlcg score` prints these.

## 14. Notebook (first-class, persistent)

- Location: `AHLCG_NOTEBOOK` env var or `--notebook`; default `./notebook.md` (workspace
  root, NOT the run dir) — it must survive across runs for continual-learning experiments.
- `note add "text"`: appends under a heading `## [<ISO-time>] Run <run-name> · Round <n>`
  (engine injects current run/round context automatically if a run is active).
- `note show`: prints the whole notebook.
- `note compact --file F` (or `-` for stdin): replaces the notebook body with the provided
  content; the previous version is archived to `notebook_history/<timestamp>.md` next to
  the notebook. This is the agent-driven compaction from the EBR-Bench design.
- Notebook content is never interpreted by the engine. It's the agent's memory.

## 15. Logging

- `log.jsonl`: one event per line: `{seq, round, phase, type, data}` — action_taken,
  test_started/committed/token/resolved, damage, horror, clue, doom, draw (public info
  only: card identities logged when they become public), enemy_moved, spawned, advanced,
  decision_presented, decision_made, note_added, game_end...
- `log.md`: readable transcript, e.g.
  `**R3 · Investigation · action 2/3** — Roland investigates the Study (Int 4+1 vs shroud 2). Commits Deduction. Token: −1 → 4 vs 2: SUCCESS. Discovers 2 clues (Deduction). Cover Up: redirected 2 clues to Cover Up (1 left).`
- Chaos token draws logged with the token and the resulting modified values.
- `ahlcg log --tail 20` default prints markdown tail.

## 16. Hidden state & integrity

`hidden.blob` = base64(zlib(json)) of {player deck order, encounter deck order, set-aside,
RNG state, full truth}, XOR-keyed with a fixed key + `"DO NOT READ"` preamble comment in
the file. Public `state.json` contains nothing hidden. A sha256 of hidden.blob is stored
in meta.json to detect tampering. (Threat model is honest-agent hygiene, not security.)

## 17. Testing requirements

- Unit: chaos bag distribution/determinism; skill test math incl. margins, autofail,
  elder sign; commit limits (Guts max 1); AoO triggering matrix; hunter pathing (incl.
  Barricade block, agenda 3 Parlor pull); enemy attack damage assignment + Guard Dog;
  each card implementation (≥1 test per card, key edge cases: Machete solo-engaged
  condition, Flashlight min-0 shroud, Cover Up redirect + game-end trauma, Dynamite
  self-damage, Frozen in Fear action tax, Dissonant Voices play-block, Locked Door
  most-clues targeting, Obscuring Fog discard-on-success, agenda/act flows, all four
  outcomes, XP/score computation).
- Integration: full scripted playthrough to R1 with fixed seed asserting the final
  result.json; a second script reaching R2 and one reaching no-resolution.
- Fuzz: random legal-action agent, 200 games across seeds/difficulties: no crashes, no
  invalid states (assert invariants each step: counters ≥0, zones consistent, game ends
  within 100 rounds).
- All tests: `python3 -m unittest discover -s tests` green.

## 18. Build phases (codex)

- **A — skeleton**: repo layout, model.py, rng, serialize, log, notebook, CLI plumbing
  with `new/state/actions/do/log/card/note/score` wired to a stub game that can present
  decision points. Definition of done: `new` + `state` + `actions` + `do` round-trip works
  on a stub decision.
- **B — rules kernel**: phases, basic actions, skill tests, chaos bag, enemies, encounter
  framework, damage/defeat, doom/act/agenda machinery — using placeholder simple cards.
- **C — cards**: all §10/§11 implementations + tests.
- **D — scenario + scoring**: The Gathering setup/transitions/outcomes, result.json,
  score command, integration tests, fuzzer.
- **E — docs**: playing_guide.md + scenario_reference.md (Claude writes these).

### Expansion phases (2026-07: five investigators + Return to The Gathering)

Decks are killbray's "Better Starter Decks" (arkhamdb 33937/33942–33945), vendored in
`data/decks/killbray/<investigator>.json` — 30 cards + 2 signatures + a **fixed** basic
weakness (deterministic; we do not draw a random one). Return to NotZ card data is
vendored in `data/cards/rtnotz*.json`; its setup/resolutions are the original campaign
guide's plus the exceptions on scenario card 50011 (see `data/rules/ahc26_rules_insert.pdf`).

- **V1 — investigator framework**: `new --investigator`, scenario registry, all five
  investigator abilities + elder signs, four new engine timing windows (token-reveal
  reaction, would-fail window, revelation-cancel, after-horror reaction; consumers:
  Wendy/Lucky!/Ward of Protection/Agnes), neutral skills 01090/01091/01093, basic
  weaknesses 01096/01097/01098/01101. Spec: `specs/phase_v1_investigators.md`.
- **V2–V5 — class card packages**: Daisy, Skids, Agnes, Wendy deck contents (pure card
  content; no new engine windows).
- **V6 — Return to The Gathering**: scenario module (random Attic/Cellar variants,
  double-sided location pairs, Ghouls of Umôrdhoth swap, Mysterious Gateway act).
- **V7 — rotation harness + docs + viewer + validation**: interleaved investigator
  rotation in bench.py, per-investigator strategy blurbs, fuzz matrix, demo games.

Codex: keep code plain, typed (dataclasses + type hints), no cleverness, no external deps.
Raise `EngineError` for impossible states; never let an exception corrupt a run dir.
