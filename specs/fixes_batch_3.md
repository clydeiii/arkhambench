# Fixes batch 3 — findings from Clyde's review of the sonnet5-return-preview games

Read DESIGN.md first. Rules authority: docs_agent/rules_reference.md + vendored JSON;
flag conflicts in specs/fixes_batch_3_report.md and follow RR/JSON. Engine code only —
do NOT touch viewer/, docs_agent/, or README.md (being edited in parallel).

## 1. Roland's reaction fires for every investigator (CRITICAL rules bug)

`arkham/enemies.py present_enemy_defeat_reactions` offers "Use Roland Banks reaction"
with no investigator check — Daisy/Skids/Agnes/Wendy all got free clues on kills and
the demo agents exploited it. Gate the option on
`state.investigator.card_code == "01001"`. Evidence! (01022) is fine to offer anyone
who somehow has it (it is a card, not an identity), but its log message hardcodes
"Roland played Evidence!" — use the investigator's name. Add a regression test: a
Daisy game state defeating an enemy at a cluey location must NOT present the Roland
reaction (and the fuzzer already covers no-crash).

## 2. Hardcoded "Roland" in log/event strings

Grep `arkham/` for log messages containing "Roland" — clue_discovered, damage_assigned,
investigator_moved, card_played, encounter_drawn ("Roland drew encounter card"),
turn/parley/resign messages, agenda1_discard, heal messages, etc. Every user-facing
message must use `state.investigator.name`. Function NAMES like `heal_roland` may stay
(rename only if trivial); it is the emitted text that matters. Test: run a Daisy game
via the harness helpers, assert no event message contains "Roland".

## 3. Skill-test result messages must show the math

Current: `Rotting Remains: success by 2.` Wanted (all data already exists in
compute_result):

    Rotting Remains: success by 2 — willpower 3 + committed 2 + boosts 1 + token -1 = 5 vs 3.

For autofail: `... — autofail (skill value 0) vs 3.` Include Wendy redraws implicitly
(the final token is what shows). Also include the elder-sign modifier like any token.
Update the existing `skill_test_result` log_event message; keep the structured fields
unchanged (viewer parses them).

## 4. Random discards must name the card

`agenda1_discard` says "discarded 1 random card for Agenda 1" — name the card (the V6
forced-discard messages already do this; match their style). Sweep for any other
rng.choice discard that does not name the card.

## 5. "Spent 1 action on asset_fight" — humanize action_spent messages

The action_spent event prints internal action ids (asset_fight, old_book,
blinding_light, study_draw, ...). Build a describe_action(state, action, payload)
helper used by the log call so messages read like:
- `Spent 1 action: Fight with Machete (target: Swarm of Rats)`
- `Spent 1 action: Investigate Guest Hall`
- `Spent 2 actions: Study (Aberrant Gateway) — draw 3 cards`
- `Spent 1 action: Play Old Book of Lore`
`spend_action` currently gets only the action string — thread the payload through from
`execute` (it is available at the call site).

## 6. Locked Door tie-break is the player's choice

`encounter.locked_door_target` picks deterministically by sort. RR: when instructions
reference "the location with the most X" and there is a tie, the investigator chooses.
When >1 revealed location ties for most clues (including the all-zero case), present a
decision listing the tied locations; auto-attach only when a single location leads.
Keep save/load-safe decision plumbing like other encounter decisions. Test both paths.

## 7. Scoring v3 (Clyde's ruling from the campaign guide)

Lita is earned in every outcome except R2 without needing to enter play, so the +3
score bonus is redundant. New formula, both scenarios:

    Score = max(0, XP − total trauma);  R3 (agenda-out at act ≤ 2) = 0.

- Remove the +3 Lita term (delete/stop using LITA_SCORE_VALUE); keep `lita_earned`
  exactly as computed today (R1 and no_resolution yes; R2/R3 no) — it stays a reported
  dimension in result.json.
- Hospital Debts penalty logic keeps working against the new formula.
- Update every test asserting old scores.

## 8. Show Daisy's restricted action in the prompt/status

"4 actions left" hides that one is Tome-only. When
`state.investigator.card_code == "01002"` and the Tome action is still unused this
round, render action counts as e.g. `4 actions left (1 Tome-only)` in the
choose-action prompt and the compact status line. (The gating itself is correct —
verified from game data — this is display only.)

## 9. `./ahlcg do <n> --why "reason"` — agent motivation logging

Add an optional `--why` string to the `do` subcommand. When present, log an
`agent_reason` event (message = the reason verbatim, max ~300 chars) BEFORE the
option's effects so it lands in the same step's event list, and include it in
timeline.jsonl like any event. No engine behavior change. Test: do with --why shows in
log.jsonl and log.md.

## 10. `./ahlcg bug "description"` — in-band engine bug reports

New subcommand appending a timestamped entry (round, phase, description) to
`<run>/bug_reports.md` and logging a `bug_report` event. No effect on game state.
Test: file created, entry appended, game unaffected.

## Definition of done

Full suite green, fuzz 50 the_gathering + 50 return_to_the_gathering clean, plus fuzz
25 per non-Roland investigator on return. Write specs/fixes_batch_3_report.md with
anything flagged. Do not git commit.
