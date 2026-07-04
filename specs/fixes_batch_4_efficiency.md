# Batch 4 — token-free engine debugging: replay corpus + semantic fuzzer invariants

Read DESIGN.md and specs/bug_adjudications.md first — the invariants below are
generalizations of the 8 defects agents found on 2026-07-04. Engine/tooling only; do
not touch viewer/ or docs_agent/.

## 1. Replay corpus differential check — `scripts/replay_corpus.py`

We have deterministic replay (arkham/export.py replays a run's recorded choices and
verifies each decision prompt matches). Build a corpus runner:

- `python3 scripts/replay_corpus.py [--dirs bench runs]` finds every completed run
  (has result.json + log.jsonl) under the given dirs (default: bench/*/game-*),
  replays each against the CURRENT engine, and reports per-run: CLEAN,
  DIVERGED (step N, what differed), or ERROR.
- Divergences are EXPECTED when a rules fix changes behavior — the tool's job is to
  make every behavioral change visible and attributable, not to fail hard. Exit 0
  with a summary table; `--strict` exits 1 on any divergence (CI use).
- Snapshot the divergence details to a file the caller names (--out), so a fix's
  behavioral footprint can be recorded in the commit message.
- Keep it stdlib-only and fast (no subprocesses per step).

Note: runs recorded before today's fixes WILL diverge at the fixed decision points —
that is signal, not failure. The valuable property is: replaying the corpus after an
"innocent refactor" should show ZERO divergences.

## 2. Semantic invariants in the fuzzer (arkham/fuzz.py)

At every decision point (not just game end), assert — crash loudly with seed +
decision context on violation:

a. **Unique option labels** — no two options in one decision render identical text
   (caught: duplicate "Advance act" entries).
b. **No self-moves** — no option whose payload is a move (action move, elusive,
   survival-instinct move, act-forced moves excluded) targets the investigator's
   current location (caught: Elusive move-to-self).
c. **Label math matches engine math** — for options whose label contains
   "test <Skill>(<N>) vs <M>": when chosen, the started test's base must equal N and
   difficulty M (caught: Machete label vs pre-boost base). Implement by parsing the
   label at choice time in the fuzzer, not by changing the engine.
d. **Charged actions leave a trace** — after any events list containing action_spent,
   the same step must contain at least one subsequent non-action_spent event OR a
   decision must be pending OR actions must have been refunded (caught: dropped move
   continuation). Keep the check heuristic and loose enough to avoid false positives
   (e.g. "Pass" is fine — it logs turn_passed).
e. **Action accounting** — actions_remaining never negative; per-round actions spent
   never exceed entitled actions (3 + Daisy tome + Leo + Skids buys, i.e. track
   grants via events rather than hardcoding; a simple upper bound of 6 is fine).
f. **Doom/clue sanity** — doom and clue counts never negative anywhere; victory
   display only ever grows during a game.

Run the full matrix as the definition of done: fuzz 50 the_gathering roland + 50
return roland + 25 × each other investigator on return, all with invariants active.
Also add `--invariants-only` docs note in the module docstring.

## 3. Wire both into the test suite lightly

- One unittest that runs a 5-game fuzz with invariants (fast smoke).
- One unittest that replays two committed fixture runs (add tiny fixture run dirs
  under tests/fixtures/ by playing ~10 scripted decisions in a temp game and saving
  it — keep them small) and asserts CLEAN.

Write specs/fixes_batch_4_report.md. Do not git commit.
