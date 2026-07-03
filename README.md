# ArkhamBench

A rules-enforcing engine + CLI harness that lets LLM agents play *Arkham Horror: The Card
Game* (solo, "The Gathering" from Night of the Zealot) inside coding-agent harnesses, with
a persistent, compactable notebook — built to reproduce Epoch AI's EBR-Bench
continual-learning experiments with AHLCG.

- `DESIGN.md` — full architecture & rules-scope spec
- `./ahlcg` — the game CLI (see `docs_agent/playing_guide.md`)
- `docs_agent/` — documents given to playing agents (rules reference, playing guide)
- `data/` — vendored card data (arkhamdb-json-data) + decklists
- `runs/` — game run directories (gitignored)
- `tests/` — `python3 -m unittest discover -s tests`

## Quickstart

```
./ahlcg new --run runs/mygame --seed 7    # set up The Gathering (Roland, standard)
./ahlcg state                             # the board
./ahlcg do 3                              # pick option 3; prints events + next decision
./ahlcg score                             # final result once GAME OVER
python3 -m unittest discover -s tests     # engine test suite (76 tests)
python3 -m arkham.fuzz --games 100        # random-agent crash/invariant fuzz
scripts/play_demo.sh claude-sonnet-5 my-demo 7   # let an agent play a full game
```

## Demo results (2026-07-03, one game each, harness-validation runs — not a controlled comparison)

| Agent (harness) | Seed | Outcome | Score |
|---|---|---|---|
| GPT-5.5 (codex) | 23 | Defeated by agenda 3 at Act 3, Priest at 4/5 dmg | **5** (XP 6 − 1 trauma) |
| Fable 5 (claude) | 11 | **Won — R1**, Ghoul Priest slain R12 | **4** (XP 6 − 2 trauma) |
| Opus 4.8 (claude) | 31 | Defeated by horror R11 (two hunters stacked) | **2** (XP 4 − 2 trauma) |
| Sonnet 5 (claude) | 47 | Defeated by horror R4 (AoO while engaged) | **0** (XP 2 − 2 trauma) |

Caveats: different seeds; GPT-5.5 read the notebook Fable 5 wrote (shared notebook in the
first two runs — per-agent notebooks were added afterward). Full transcripts in
`runs/<name>/log.md`, agent reasoning in `logs/<name>.agent.log`, lessons in `notebooks/`.

Card data © Fantasy Flight Games, via the community project
[arkhamdb-json-data](https://github.com/Kamalisk/arkhamdb-json-data). This project is for
AI-capabilities research and commentary; it does not distribute scans of the game.
