# Phase A — Engine skeleton, CLI, notebook

Read `DESIGN.md` in full first. Implement sections §2, §3, §4 (rendering can be basic but
complete), §14 (notebook), §15 (logging), §16 (hidden state) as the skeleton described in
§18 Phase A. Do NOT implement game rules yet — build the frame the rules will run in.

## Deliverables

1. `ahlcg` executable wrapper + `arkham/` package with the module files from §2 (empty
   shells where phase B will fill in, real implementations for: model dataclasses, rng,
   serialize, log, notebook, cli, data.py loader, game.py facade).
2. `model.py`: dataclasses for GameState and all entities per DESIGN §2/§4. GameState must
   round-trip: `GameState.from_dict(gs.to_dict()) == gs`. Include: investigator (stats,
   damage/horror, resources, clues, actions_remaining, hand/deck/discard as card-instance
   id lists), card instances (instance id, card code, zone, exhausted, uses, damage,
   horror, clues, doom, attachments), locations (code, revealed, shroud, clues,
   connections, attached instance ids), enemies-in-play, agenda/act state, chaos bag,
   victory display, round/phase/turn bookkeeping, decision-point queue (a serializable
   pending-decision structure: id, prompt, options with labels + opaque payloads).
3. `game.py`: `Game.new(seed, difficulty, deck_path, run_dir)`, `Game.load(run_dir)`,
   `Game.save()` (atomic; public state.json + hidden.blob split per §16),
   `Game.current_decision()`, `Game.apply(option_index)` — for phase A, wire a STUB
   scenario: a trivial decision loop ("stub decision: option A/B/end") proving the
   round-trip, persistence, logging, and decision plumbing work end to end.
4. `cli.py`: all §3 commands (`new/state/actions/do/log/card/note/score`) with run-dir
   resolution (`--run` flag > `AHLCG_RUN` env > `./.current_run` file). `card` searches
   the vendored JSON DB by code or case-insensitive name fragment and prints full
   text/stats (both player and encounter DBs). `score` prints "game in progress" stub.
5. `notebook.py` per §14 including history archiving on compact, and run/round context
   injection on `note add`.
6. `log.py`: JSONL events + markdown transcript appender per §15.
7. `tests/` covering: state round-trip serialization; hidden/public split (no deck order
   in state.json bytes); notebook add/show/compact + archive; CLI round trip on the stub
   game (new → actions → do → log) via subprocess; card lookup; atomic save (simulate
   crash: temp file never leaves corrupt state.json).

## Rules of engagement

- Python ≥3.10 stdlib only. Type hints + dataclasses. No third-party deps.
- Keep every module small and boring. Interfaces exactly as DESIGN §2 names them.
- `python3 -m unittest discover -s tests` must pass.
- When done: `git add -A && git commit -m "Phase A: engine skeleton, CLI, notebook"`.
- Write a short `specs/phase_a_report.md`: what you built, any deviations from DESIGN.md
  and why, open questions for the rules kernel.
