# Phase D — The Gathering scenario, scoring, fuzz

Prereq: phase C. Implement `arkham/scenarios/the_gathering.py` per DESIGN §12 exactly:
setup (incl. mulligan + weakness-redraw), location graph + per-investigator clue values,
unrevealed/revealed handling, Parlor barrier, act/agenda decks with all flip effects,
agenda-3 forced effects, Ghoul Priest/Lita set-asides and entries, parley, resign, the
scenario chaos-token effects for all four difficulties, all four outcomes, XP + score per
DESIGN §13, `result.json` + `ahlcg score`.

Wire `ahlcg new` to create a real Gathering run (default difficulty standard, deck
data/decks/roland_ltp.json). Delete/retire the stub scenario from `new` (keep the phase-B
fixture for tests only).

Edge cases to get right (test each):

- Act 1 advance: enemies in Study discarded (with attachments), Study removed with clues
  lost, Roland moved to Hallway (a "move" by game effect — triggers Hallway enter effects:
  none; does NOT provoke AoO; engaged enemies move with him... they were just discarded if
  they were in the Study — enemies engaged with Roland ARE in the Study; per act text
  "Discard each enemy in the Study" → they're discarded, not moved).
- Hallway enters play already-being-entered: reveal order = locations enter unrevealed,
  Roland placed → Hallway revealed → clues (0) placed.
- Attic/Cellar forced enter effects fire on EVERY entry incl. repeat visits.
- Parlor cannot be moved into while unrevealed (option not listed); after act 2 it's
  revealed (via act effect, not entry) and Lita is there.
- Ghoul Priest spawns in Hallway on act 2→3; engages Roland if he is there (he will be,
  per act 2 objective location — but don't assume; spawn unengaged then standard
  engagement check).
- Agenda 2→3 flip: reshuffle discard into encounter deck, mill until Ghoul ENEMY
  discarded, Roland draws it (spawn engaged per normal enemy revelation, ignoring its
  printed Spawn instruction? NO — drawing an enemy resolves its revelation incl. Spawn:
  Flesh-Eater would go to Attic. Implement as a normal draw of that card).
- Agenda 3 doom-out at act 3 = defeat+trauma no-resolution path; at act ≤2 = R3, score 0.
- Resign only via revealed Parlor action. Game end → outcome + Cover Up check + trauma →
  result.json written, further CLI `do` says GAME OVER.
- Victory display: defeated Victory enemies + at game end Victory locations with 0 clues
  that are in play (Attic/Cellar; NOT the removed Study; only if revealed? RR: victory
  locations must be revealed and clueless — Attic/Cellar unrevealed at game end do NOT
  score).
- XP math per outcome per DESIGN §12 (R2 = +1 lead bonus on top of +2 insight bonus).

Fuzzer (`tests/test_fuzz.py` + `arkham/fuzz.py` runnable as `python3 -m arkham.fuzz
--games N`): uniformly-random legal choices, default 200 games across seeds ×
{easy,standard,hard,expert}: no exceptions, invariants each step (non-negative counters,
zone consistency: every card instance in exactly one zone, actions_remaining ≤ 3+effects,
game terminates ≤ 100 rounds), outcome distribution printed (expect mostly R3/defeats —
fine). Integration: scripted seeds reaching R1, R2, no-resolution (write the scripts by
playing greedily by hand via the Game API in the test).

Commit "Phase D: The Gathering + scoring + fuzz" + specs/phase_d_report.md.
