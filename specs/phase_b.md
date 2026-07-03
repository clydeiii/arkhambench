# Phase B — Rules kernel

Prereq: phase A merged. Read DESIGN.md §5–§9 and this file. Build the full rules engine
using SIMPLE PLACEHOLDER cards where card behavior is needed (real cards come in phase C);
the placeholder scenario from phase A grows into a real "engine test scenario" fixture
(tests/fixtures) with 2–3 locations, a 10-card vanilla deck, a small encounter deck of
vanilla enemies + direct-damage treacheries, 2 agendas, 2 acts. The Gathering itself is
phase D.

## Build order

1. **Phase/round loop** (`phases.py`): mythos (skip round 1) → investigation → enemy →
   upkeep, with the window/decision mechanics from DESIGN §5. The engine advances until a
   decision is required (decision queue from phase A), persists, returns.
2. **Basic actions** (`actions.py`): generation of the legal-action list each time the
   investigator has actions remaining (DESIGN §5 list, incl. play/activate hooks, act
   clue-spend option, pass/end-turn), execution, attacks of opportunity per DESIGN
   (Move/Investigate/Draw/Resource/Play/other-Activate provoke; Fight/Evade/Parley/Resign
   don't; fast plays never), action costs incl. additional-cost effects hook (Frozen in
   Fear needs it in phase C: first move/fight/evade each round +1 action).
3. **Skill tests** (`skill_test.py`): the ST.1–ST.8 machine per DESIGN §5, as a
   sub-state-machine that can suspend for decisions (commit window, post-reveal window,
   target choices). Committed icons: use card JSON fields skill_willpower/intellect/
   combat/agility/wild. Enforce per-card commit limits hook. Margins recorded. Chaos bag
   (`chaos.py`): seeded draw-with-replacement; token effects delegated to scenario hook;
   autofail/eldersign semantics.
4. **Enemies** (`enemies.py`): spawn (incl. spawn-location-not-in-play → discard),
   engage/disengage, exhaust/ready, hunter movement (BFS shortest path; ties broken
   deterministically by location code order; blocked-move hook for Barricade), enemy
   attacks with damage/horror assignment decisions (allies as soak per DESIGN §5),
   retaliate hook, victory display on defeat.
5. **Encounter framework** (`encounter.py`): draw → revelation for treachery (test /
   effect / attach / threat-area) and enemy (spawn); encounter discard; reshuffle on
   empty.
6. **Doom/agenda/act** machinery incl. advance-on-threshold check after ANY doom change,
   agenda/act flip effects as scenario hooks, act advance via clue spend.
7. **Damage/horror/defeat**: assignment decision points, asset destruction, investigator
   defeat → game end path; resign path; trauma bookkeeping fields.
8. **Triggers** (`triggers.py`): window enumeration (only surface when options exist),
   reaction/forced dispatch, once-per-round limits, "for this test/round/turn" expiry.

## Decision-point protocol (uniform, agent-facing)

Every decision the kernel emits must carry: `kind` (choose_action, commit_cards,
choose_target, assign_damage, choose_option, use_reaction, mulligan, ...), a human prompt
with full context per DESIGN §3, and options with stable labels. `do <n>` semantics from
phase A unchanged. Multi-select decisions (mulligan, commit) are modeled as repeated
single choices with a "Done" option — keep the CLI dead simple.

## Tests

Unit tests per DESIGN §17 for everything above using the fixture scenario: AoO matrix,
engaged-move-together, hunter BFS + tiebreak, reshuffle, doom-advance mid-mythos vs via
placement, upkeep order (ready → draw → resource → hand size), ties-succeed, autofail
ignores modifiers, commit icons + wild, margins, ally soak + destruction, defeat paths,
determinism: same seed + same action script ⇒ byte-identical log.jsonl (minus
timestamps — put timestamps only in meta.json, not in log events; transcripts may have
round/seq numbers).

Same rules of engagement as phase A. Commit when green:
"Phase B: rules kernel". Write specs/phase_b_report.md (deviations, open questions,
anything phase C/D must know about your hook signatures).
