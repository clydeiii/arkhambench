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

## Watching a game

```
scripts/view.sh bench/sonnet5-mini
open http://localhost:8765/viewer/
```

`scripts/view.sh` exports any passed bench or run directories that are not already in
`viewer/data/`, rebuilds the viewer index, caches card images, and serves the static UI
from the repo root. The viewer steps through every decision of a run: location map with
card art, player board, event ticker, the decision presented with the agent's choice
highlighted, and double-sided card modals.

**Live viewer:** https://clydeiii.github.io/arkhambench/ — redeploy with
`scripts/deploy_pages.sh` after exporting new runs.

## Scoring

Reported per run in `result.json`, alongside the raw dimensions (track them all —
composite score is for the benchmark's single number, the dimensions are for analysis):

- **XP** — per the campaign guide: victory display total + resolution bonuses
  (+2 insight in most outcomes; +1 extra for the lead in R2; 0 if killed by agenda-out
  at act ≤ 2).
- **Trauma** — defeat trauma (physical/mental by cause), resolution trauma (R1's burned
  house), Cover Up's game-end trauma.
- **Lita Chantler earned?** — she joins the campaign deck in some outcomes (R1,
  no-resolution) but not others (R2, R3).
- **Resolution reached**, victory points, rounds, damage/horror per round, tests
  passed/failed, etc.

**Score = max(0, XP − trauma + 3·Lita)** — the +3 approximates Lita's campaign equity
(she is arguably the strongest card in the Core Set era), so the R1-vs-R2 choice prices
in the real prize the way an experienced player would, instead of rewarding trauma-dodging.

## Demo results (2026-07-03, one game each, harness-validation runs — not a controlled comparison)

Scores recomputed under the current formula (the runs were played under an earlier
`XP − trauma` formula, and a defeat-trauma double-count inflated opus48/sonnet5 trauma by 1):

| Agent (harness) | Seed | Outcome | XP | Trauma | Lita | Score |
|---|---|---|---|---|---|---|
| GPT-5.5 (codex) | 23 | Defeated by agenda 3 at Act 3, Priest at 4/5 dmg | 6 | 1 | yes | **8** |
| Fable 5 (claude) | 11 | **Won — R1**, Ghoul Priest slain R12 | 6 | 2 | yes | **7** |
| Opus 4.8 (claude) | 31 | Defeated by horror R11 (two hunters stacked) | 4 | 1 | yes | **6** |
| Sonnet 5 (claude) | 47 | Defeated by horror R4 (AoO while engaged) | 2 | 1 | yes | **4** |

(The Gathering's no-resolution outcome is canonically forgiving — you escape with Lita
and your victory display — so defeat is punished mainly through trauma and lost tempo.
The score spread between careful and careless play comes from VP banked and trauma.)

Caveats: different seeds; GPT-5.5 read the notebook Fable 5 wrote (shared notebook in the
first two runs — per-agent notebooks were added afterward). Full transcripts in
`runs/<name>/log.md`, agent reasoning in `logs/<name>.agent.log`, lessons in `notebooks/`.

Card data © Fantasy Flight Games, via the community project
[arkhamdb-json-data](https://github.com/Kamalisk/arkhamdb-json-data). This project is for
AI-capabilities research and commentary; it does not distribute scans of the game.
