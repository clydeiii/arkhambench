# Fixes batch 6 report

Date: 2026-07-05

## Summary

Implemented the three confirmed fixes from `specs/fixes_batch_6_audit2.md`.

1. Play-action resource costs are now paid during initiation before attacks of
   opportunity. The interrupted action payload carries `resource_cost_paid` /
   `resource_cost` through AoO resume, slot-discard continuations, and the effect
   phase so costs are not charged twice. If the play is no longer legal when the
   interrupted action resumes, the prepaid resource cost is refunded. The same
   initiation-cost plumbing covers the AoO-provoking special event play actions
   Dynamite Blast and Sneak Attack.
2. Leo De Luca only removes an action when discarded during the investigation
   phase if no action has been taken this turn (`turn.action_index == 0`). Once the
   first qualifying action has consumed Leo's unrestricted additional action,
   discarding Leo does not reduce `actions_remaining`.
3. Damage/horror assignment now records all per-token choices in
   `pending_damage["assigned"]` and applies them simultaneously after the last
   token is assigned. Soak legality is computed from existing tokens plus pending
   assignments, assets are discarded only after the full batch is applied, and
   investigator defeat / Agnes after-horror reactions occur after simultaneous
   application. The pending allocation shape is JSON-safe and survives save/load
   mid-assignment.

## Replay corpus

Command:

`python3 scripts/replay_corpus.py --dirs bench runs --out /tmp/arkham_replay_batch6.json`

Result: 2 clean, 22 diverged, 0 errors.

- `bench/haiku45-audit2/game-01`: CLEAN.
- `bench/haiku45-audit2/game-03`: CLEAN.
- `bench/haiku45-audit2/game-02`: diverges at step 21 because the current engine
  correctly shows Wendy with 2 actions left after Leo is discarded, while the
  recorded pre-fix run showed 1 action left. This is the expected batch-6 Leo
  action-clawback fix.
- The other 21 divergences are step-0 mulligan prompt mismatches from the earlier
  batch-5 simultaneous mulligan UI change, not from this batch.

## Verification

- `python3 -m py_compile arkham/actions.py arkham/effects.py arkham/cards/player.py tests/test_fixes_batch_6.py`: OK.
- `python3 -m unittest discover -s tests`: 177 tests, OK.
- `python3 -m arkham.fuzz --games 50 --scenario the_gathering --investigator roland --invariants-only`: invariants ok.
- `python3 -m arkham.fuzz --games 50 --scenario return_to_the_gathering --investigator roland --invariants-only`: invariants ok.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator daisy --invariants-only`: invariants ok.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator skids --invariants-only`: invariants ok.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator agnes --invariants-only`: invariants ok.
- `python3 -m arkham.fuzz --games 25 --scenario return_to_the_gathering --investigator wendy --invariants-only`: invariants ok.

Note: `pytest` is not installed in this environment, so verification used
`unittest`.
