# Benchmark harness + compact status line

## 1. Compact status line (log legibility)

Add `status_line(state) -> str` (arkham/log.py or a small render helper), one line, fixed
field order, abbreviated:

```
[R4·Investigation a2/3 | Hallway | clu2 res4 | dmg3/9 hor1/5 | h4 d21 x9 | Act2 Agd2 doom5/7]
```

Fields: round·phase, actions left/total (only during investigation; omit `aN/3` in other
phases), Roland's location name, clues, resources, damage/health, horror/sanity, hand
count (h), deck count (d), player discard count (x), act stage, agenda stage,
doom total-in-play/threshold.

Emit it:
- in `log.md`: as its own line immediately before every `decision_presented` transcript
  line (so a reader always has current state next to each decision), and
- in the CLI: printed directly above the decision whenever `do` / `actions` / `new`
  prints a decision point.

Keep `log.jsonl` unchanged except adding a `"status"` field to decision_presented events.
Update the determinism test expectations if needed. Show the same line at GAME OVER with
final values.

## 2. Benchmark runner — `scripts/bench.py` (python3 stdlib, executable)

This is ArkhamBench proper: N sequential playthroughs by one agent, persistent per-label
notebook, EBR-Bench-style scoring (average of the final 20% of games).

```
python3 scripts/bench.py --agent <claude-model-id|codex> --label fable5-b1 \
    [--games 10] [--difficulty standard] [--seeds-file FILE] [--max-continues 2] \
    [--max-turns 500] [--dry-run]
```

Behavior:
- Layout: `bench/<label>/game-01..NN/` (run dirs), `bench/<label>/notebook.md`
  (via `ahlcg new --notebook`), `bench/<label>/logs/game-NN.agent.log`,
  `bench/<label>/bench.json`, `results.csv`, `summary.md`.
- Seeds: default seed for game i = 1000+i (identical across labels/agents for fairness);
  `--seeds-file` = one int per line overrides.
- Per game loop:
  1. If `game-NN/result.json` exists → skip (resumability).
  2. `./ahlcg new --run bench/<label>/game-NN --seed S --difficulty D --notebook bench/<label>/notebook.md`
  3. Invoke the agent (subprocess, stream output to the agent log):
     - claude models: `claude -p "<prompt>" --model <id> --allowedTools "Bash(./ahlcg:*),Read(docs_agent/**),Read(bench/<label>/notebook.md)" --disallowedTools "Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read(runs/**),Read(bench/**)" --max-turns <max-turns>`
     - codex: `codex exec -s workspace-write "<prompt>"`
  4. Prompt = docs_agent/mission.md content + a bench header (see §3) telling the agent
     it is playing game k of N and that its objective is the average score of the final
     20% of games.
  5. After the session: if no result.json and the game is still in progress, re-invoke
     with a short "Your game is not finished. Continue the current run to completion."
     prompt, up to --max-continues times. Still unfinished → record status="incomplete",
     score 0 (log loudly).
  6. Append the game's row to bench.json + results.csv immediately (crash-safe).
- results.csv columns: game, seed, status, outcome, resolution, score, xp, trauma_total,
  lita_earned, victory_points, rounds, damage_taken, horror_taken, actions_taken,
  encounter_cards_drawn, enemies_defeated, wall_seconds.
- summary.md: per-game table, aggregate stats, learning signal: mean score of first half
  vs second half, and **final-20% average** (ceil(N/5) last games) labeled as the
  headline benchmark number.
- `--dry-run`: print planned seeds/commands without invoking anything.
- Safety: refuse to start if another bench appears active (lock file bench/<label>/.lock
  with pid; remove on exit). Agents share CWD/.current_run, so the runner must be the
  only game in town; document this.

## 3. Bench mission header (prepended to mission.md content per game)

```
=== ArkhamBench: playthrough {k} of {n} ===
You are agent '{label}'. Your benchmark objective is to maximize your AVERAGE SCORE over
the FINAL {final_count} playthroughs (games {first_final}-{n}). Earlier games are for
learning: explore, take risks you can learn from, and invest heavily in your notebook —
it is the only memory that persists between games. Your notebook currently has {notebook_lines} lines.
Your game has already been created (the current run). Play it to completion now, then
record your lessons.
```

## 4. Tests

- Unit-test status_line rendering against a constructed GameState (exact string).
- Unit-test bench summarization: build fake bench/<label> dirs with result.json fixtures,
  run the summary/CSV code (import bench.py as a module — keep logic in functions),
  assert final-20% math (N=10 → last 2), incomplete-game handling, resumability skip.
- Do NOT invoke real agents in tests; cover the command construction with a --dry-run
  style unit test asserting the exact argv for both claude and codex agents.
- `python3 -m unittest discover -s tests` green; `python3 -m arkham.fuzz --games 50` clean.
- Write specs/harness_report.md. No git commit (sandbox).
```
