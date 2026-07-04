# Phase V1 — Investigator framework, four timing windows, neutral cards & weaknesses

Read `DESIGN.md` in full first (note the new "Expansion phases" section in §18). This
phase generalizes the engine from "Roland plays The Gathering" to "any of the five core
investigators plays a registered scenario", implements all five investigator cards
(ability + elder sign), adds four new engine timing windows with their first consumer
cards, and implements the remaining neutral skills and the four fixed basic weaknesses.

**Rules authority:** `docs_agent/rules_reference.md` (RR). Card texts below are from the
vendored JSON (`data/cards/core.json`) — read the full JSON entry for every card you
implement. If this spec conflicts with the RR or the JSON, FLAG IT in your report and
follow RR/JSON; do not guess silently.

## 1. Scenario + investigator plumbing

- `./ahlcg new` gains `--scenario the_gathering` (default) and
  `--investigator roland|daisy|skids|agnes|wendy` (default `roland`).
- Add a scenario registry in `arkham/scenarios/__init__.py`
  (`SCENARIOS: dict[str, ScenarioDef]`) so `game.py` no longer imports
  `the_gathering` by name at its 3 call sites. Phase V6 will register a second scenario.
- `--deck` still works; the **default deck** becomes
  `data/decks/killbray/<investigator>.json` for every investigator (these files exist).
  `data/decks/roland_ltp.json` remains loadable for back-compat. Existing tests that
  assert LTP deck contents must pass the explicit `--deck` path; update them.
- Killbray deck JSON: `{"investigator_code": "0100X", "slots": {code: count, ...}}` —
  33 cards = 30 deck cards + 2 signature cards + 1 **fixed** basic weakness. We use the
  listed weakness deterministically; do NOT draw a random basic weakness.
- At `new`, validate every deck slot code has a registered CardImpl; raise `EngineError`
  naming the missing codes. (Daisy/Skids/Agnes/Wendy decks will fail this check until
  phases V2–V5 land — that is correct and intended. Roland's killbray deck must pass
  after this phase.)
- Weakness handling generalizes the existing Cover Up machinery: all cards with
  `subtype_code` `basicweakness`/`weakness` are set aside during opening hand draw and
  mulligan, then shuffled into the deck (RR "Weakness" entry + existing setup logic).
- `state.json`, the markdown log header, the compact status line, and
  `arkham/export.py` run meta must all carry the investigator code + name. The model
  currently defaults `investigator_id`/`owner` to `"roland"` — make the id the chosen
  investigator's slug. Function names like `heal_roland`/`engage_ready_enemies_at_roland`
  may be renamed to `_investigator` forms or left as-is (still a solo engine); do not
  change behavior while renaming.
- `arkham/data.py` should also load `data/cards/rtnotz.json` + `rtnotz_encounter.json`
  into the card DB (used by `./ahlcg card` lookup now, scenario V6 later).

## 2. Investigator cards (all five: stats, ability, elder sign)

Stats (willpower/intellect/combat/agility, health/sanity) come from the JSON entries
01001–01005. Roland's ability + elder sign are already implemented; refactor them into
the per-investigator structure so all five follow one pattern (suggest
`arkham/cards/investigators.py`).

- **01001 Roland Banks** (existing): reaction after you defeat an enemy → discover 1 clue
  at your location, limit once per round. Elder sign: +1 per clue on your location.
- **01002 Daisy Walker**: "You may take an additional action during your turn, which can
  only be used on [[Tome]] `[action]` abilities." Implement as a 4th action usable only
  for activate-abilities on assets with the Tome trait (trait data is in the JSON
  `traits` field; Old Book of Lore 01031 is the in-scope Tome today, Necronomicon comes
  in V2). Elder sign: +0; if you succeed, draw 1 card per Tome you control.
- **01003 "Skids" O'Toole**: fast ability, during your turn, spend 2 resources → 1
  additional action this turn, limit once per turn. Present it in the existing fast
  windows (it is a fast *ability*, so it must appear in the same windows where fast
  events are offered during the investigation phase). Elder sign: +2; on success gain
  2 resources.
- **01004 Agnes Baker**: reaction, after 1+ horror is placed on Agnes → deal 1 damage to
  an enemy at your location, limit once per phase. Uses the new after-horror window (§3d).
- **01005 Wendy Adams**: reaction, when you reveal a chaos token, discard 1 card from
  hand → cancel that token, return it to the bag, reveal a new one; limit once per
  test/ability. Uses the new token-reveal window (§3a). Elder sign: +0, but if Wendy's
  Amulet (01014) is in play, you automatically succeed instead (check by card code in
  play area; the card itself arrives in V5).

The Gathering's scenario token effects and campaign log text sometimes say "Roland" —
audit `arkham/scenarios/the_gathering.py` for investigator-name assumptions
(e.g. `ghouls_at_roland_location`, resolution text, defeat trauma). Behavior is
investigator-generic; only the displayed name changes.

## 3. Four new timing windows (engine core)

These are the only engine-machinery changes in the V phases; V2–V5 are pure content.
Keep them narrow and rules-shaped. **The RR audit finding still stands: there is NO
general player window after the chaos token is revealed** — (a) and (b) are specific
triggered abilities, not boost windows.

- **(a) Token-reveal reaction** — after ST.3 reveal, if a reaction to "you reveal a
  chaos token" is available (V1: Wendy's ability, requires ≥1 card in hand and not yet
  used this test/ability), present a decision: cancel & redraw (choose the card to
  discard) or pass. On cancel: the revealed token goes back in the bag, a new token is
  revealed from the full bag (may be the same one), and the window is offered again only
  if the limit allows (it does not — once per test).
- **(b) Would-fail window** — at ST.6, if the test would fail and the investigator has a
  playable "when you would fail" card, present it. First consumer, implement now:
  **01080 Lucky!** (survivor event, cost 1, fast): "Play when you would fail a skill
  test. Get +2 to your skill value for the duration of that test." Recompute
  success/failure after the boost; if it still fails and another Lucky! is playable,
  offer again. Playing Lucky! against an autofail token still fails (skill value is 0
  and the test "would fail" regardless — Lucky! adds to skill value, autofail sets the
  TOTAL to 0 per the audited rule; offering it would waste the card, but RAW it is
  legal — allow it and let the recomputation still fail). FLAG in your report if you
  believe the RR contradicts this.
- **(c) Revelation-cancel window** — when the investigator draws a treachery (encounter
  draw AND weakness treachery draw), before resolving its Revelation, offer playable
  "when you draw a treachery" fast plays. First consumer, implement now: **01065 Ward of
  Protection** (mystic event, cost 1, fast): "Play when you draw a treachery card. Cancel
  that card's revelation effect. Take 1 horror." The treachery is still considered drawn
  and goes to discard; only its revelation effect is canceled. Peril is out of scope
  (no core Gathering treachery has it).
- **(d) After-horror reaction** — after horror is placed on the investigator (from any
  source, after the assignment resolves), offer available reactions. V1 consumer: Agnes.
  If multiple horror are placed at once, the trigger fires once. Respect once-per-phase
  limit via the existing `state.limits` pattern.

All four windows must be decision-point idempotent (safe across save/load), appear in
timeline.jsonl like other decisions, and never fire when no consumer is available (no
noise decisions for Roland).

## 4. Neutral skills & basic weaknesses

- **01090 Perception** (skill, 2× intellect icons): "Max 1 committed per skill test. If
  this test is successful, draw 1 card." Same pattern as implemented Deduction/Overpower
  analogs — note the max-1-committed rule.
- **01091 Overpower** (skill, 2× combat): max 1 per test; on success draw 1. (Check
  whether already implemented as 01091 — the implemented list has 01089 Guts and 01092
  Manual Dexterity; Overpower may be new.)
- **01093 Unexpected Courage** (skill, 2× wild): max 1 committed per skill test, no text.
- **01096 Amnesia** (basic weakness treachery): "Revelation — Choose and discard all but
  1 card from your hand." Present the keep-1 choice as a decision.
- **01097 Paranoia** (basic weakness treachery): "Revelation — Discard all your resources."
- **01098 Haunted** (basic weakness treachery): "Revelation — Add Haunted to your threat
  area." While in threat area: -1 to each skill. "`[action]` `[action]`: Discard
  Haunted." (a 2-action activate ability; no AoO exemption — it is an activate, so it
  DOES provoke attacks of opportunity).
- **01101 Mob Enforcer** (basic weakness enemy, fight 4 / health 3 / evade 3, 1 damage /
  0 horror): Prey — bearer only. Hunter. "`[action]` Spend 4 resources: Parley. Discard
  Mob Enforcer." Weakness ENEMY draw: per RR, when drawn it spawns engaged with the
  drawing investigator (follow the RR "Weakness"/"Enemy" entries; the existing
  Silver Twilight Acolyte 01102 implementation is the model). Parley is AoO-exempt
  (action-type rule already in the engine).

## 5. Tests (add to `tests/`)

1. Per-investigator `new` smoke test: correct stats, deck size 33 handled as 30+2+1,
   signatures present, weakness set-aside during mulligan (Daisy/Skids/Agnes/Wendy will
   fail deck validation until V2–V5 — test the validation error message itself for one
   of them).
2. Roland + killbray deck: full game playable by random agent (fuzz N=25 with
   `--investigator roland` default deck) with zero invariant violations.
3. Wendy cancel: deterministic test that the canceled token returns to the bag before
   the redraw (bag count unchanged), the redraw can repeat the same token, limit once
   per test, hand decreases by 1.
4. Lucky! chain: fail by 1 → Lucky! → pass; fail by 3 → Lucky! → still fail → second
   Lucky! offered; autofail + Lucky! still fails.
5. Ward of Protection cancels Rotting Remains' revelation (no test made, no
   damage/horror from the card), Ward's own 1 horror applied, treachery discarded.
6. Agnes reaction: fires after horror assignment, damages a chosen enemy at her
   location, once per phase, not offered with no enemy present.
7. Daisy Tome action: 4th action only usable on Old Book of Lore's activate; normal
   actions still capped at 3.
8. Skids buy-action: once per turn, costs 2, works mid-turn from fast window.
9. Elder sign per investigator (force-reveal via seeded bag or test hook): Roland
   clues-based, Skids +2/+2 resources, Agnes +1/horror, Daisy draw-per-Tome, Wendy +0.
10. Weaknesses: Amnesia keep-1 decision, Paranoia resources to 0, Haunted persistent -1
    skills + 2-action discard + AoO provoked, Mob Enforcer spawns engaged on draw +
    parley discard.
11. Full existing suite stays green (`python3 -m unittest discover -s tests`) and
    `python3 -m arkham.fuzz --games 50` clean.

## Rules of engagement

- Python ≥3.10 stdlib only, dataclasses + type hints, no cleverness.
- Do not change scoring, resolutions, logging formats, or replay/export semantics beyond
  adding the investigator field.
- Determinism: all randomness through the game RNG; save/load safe at every decision.
- Write `specs/phase_v1_report.md` when done: what you built, what you flagged, test
  count before/after.
