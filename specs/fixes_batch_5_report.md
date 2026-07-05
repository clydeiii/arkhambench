# Fixes batch 5 report

Date: 2026-07-05

## Summary

Implemented all six requested fixes from `specs/fixes_batch_5_audit.md`.

1. AoO continuation ownership: `actions.execute` now stops unconditionally once
   `attacks_of_opportunity` starts an attack sequence. The AoO/resume chain is
   the only owner of the interrupted action effect from that point.
2. Encounter-card discard ownership: threat-area and attachment discards now route
   encounter treacheries/enemies to `encounter_discard`, while weakness cards route
   to the investigator discard.
3. Weakness enters-hand rule: search/return-to-hand paths now use a shared
   add-to-hand helper that immediately resolves weakness Revelations.
4. Research Librarian: the reaction is optional, presents one distinct Tome choice
   plus Decline, shuffles after resolution, and routes the chosen card through the
   weakness gate.
5. Mulligan: opening mulligan is now a single simultaneous set-aside declaration;
   replacements are drawn only on confirmation, then set-aside cards are shuffled
   back.
6. End-of-turn ordering: the post-final-action `inv_end` during-turn window now
   occurs before Dark Memory/Frozen in Fear end-of-turn Forced effects unless the
   turn was forcibly ended.

## AoO/resume audit

Covered resume paths:

- no-decision single attacker: action effect runs once.
- soak decision single attacker: action effect runs once after assignment.
- Dodge decision single attacker: action effect runs once after cancel/take.
- multiple attackers with Dodge on one attacker: remaining AoO queue continues and
  the action effect runs once.
- defeat reaction interposed by Guard Dog/Roland reaction: action continuation is
  deferred and runs once after the reaction window closes.
- dead attacker in an AoO queue: missing/exhausted attackers are skipped before
  card lookup/resume checks, and the interrupted action still resumes once.

## Rule conflicts

No RR/card JSON conflicts found for the implemented items. The Daisy Study
two-action/Tome-only issue from the game-02 audit is a separate confirmed issue in
that audit text, but it is not one of the six items in this batch spec and was not
changed here.

## Replay corpus

`python3 scripts/replay_corpus.py --dirs tests/fixtures/replay_corpus bench`

Result: 0 clean, 23 diverged, 0 errors.

All 23 divergences occur at step 0 due to the intentional mulligan prompt/option
structure change:

- Expected old prompt: "Choose cards to mulligan (one at a time...)"
- Actual new prompt: "Set aside any number of cards, then draw replacements
  together."

No replay reached later divergence points because the first recorded decision no
longer matches the old sequential mulligan UI.

## Verification

- `python3 -m unittest discover -s tests`: 171 tests, OK.
- `python3 -m arkham.fuzz --games 50 --scenario the_gathering --invariants-only`:
  invariants ok.
- `python3 -m arkham.fuzz --games 50 --scenario return_to_the_gathering --invariants-only`:
  invariants ok.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator daisy --invariants-only`:
  invariants ok.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator skids --invariants-only`:
  invariants ok.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator agnes --invariants-only`:
  invariants ok.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator wendy --invariants-only`:
  invariants ok.

Note: `python` and `pytest` are not available in this environment; verification
used `python3` and `unittest`.
