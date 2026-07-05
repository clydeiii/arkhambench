# ArkhamBench

A rules-enforcing engine + CLI harness that lets LLM agents play *Arkham Horror: The Card
Game* solo — "The Gathering" and "Return to The Gathering" (Night of the Zealot, Part I)
with any of the five core-set investigators — inside coding-agent harnesses, with a
persistent, compactable notebook. Built to reproduce Epoch AI's EBR-Bench
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
./ahlcg new --run runs/mygame2 --scenario return_to_the_gathering --investigator agnes
./ahlcg state                             # the board
./ahlcg do 3                              # pick option 3; prints events + next decision
./ahlcg score                             # final result once GAME OVER
python3 -m unittest discover -s tests     # engine test suite (144 tests)
python3 -m arkham.fuzz --games 100 --scenario return_to_the_gathering --investigator wendy
scripts/play_demo.sh claude-sonnet-5 my-demo 7   # let an agent play a full game
python3 scripts/bench.py --agent claude-sonnet-5 --label mybench --games 10
# ^ benchmark: Return to The Gathering, investigators rotate roland,daisy,skids,
#   agnes,wendy per game (same order+seeds for every agent), per-label notebook
```

Decks are killbray's ["Better Starter Decks"](https://arkhamdb.com/decklist/view/33937/better-starter-decks-roland-banks-1.0)
(30 cards + 2 signatures + a fixed basic weakness, revised-core pool), vendored in
`data/decks/killbray/`.

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
- **Lita Chantler earned?** — per the campaign guide she joins the campaign in every
  outcome except R2 (she never needs to enter play), so she is tracked as a campaign
  dimension rather than scored.
- **Resolution reached**, victory points, rounds, damage/horror per round, tests
  passed/failed, etc.

**Score = max(0, XP − trauma)**; killed by the agenda while still trapped (R3) scores 0.
(An earlier formula added +3 for Lita; dropped once the campaign guide confirmed she is
earned in all outcomes but R2 regardless of play.)

## Benchmark results — main run (2026-07-05)

**Setup:** four agents, ten games each, *Return to The Gathering* on Standard,
identical seeds (1001–1010) and an identical interleaved investigator rotation
(Roland, Daisy, Skids, Agnes, Wendy — twice through). Each agent has a persistent
per-agent notebook as its only cross-game memory, starting empty. The headline metric
is the **final-20% average** (games 9–10), per EBR-Bench methodology. All 40 games ran
on a single frozen engine version, and every game is step-through browsable in the
[live viewer](https://clydeiii.github.io/arkhambench/).

![Score per game](results/scores_by_game.svg)

| Agent (harness) | Scores by game | Mean | **Final-20%** | Wins |
|---|---|---:|---:|---|
| Fable 5 (claude) | 2 3 6 7 2 3 2 3 **9** 4 | 4.10 | **6.50** | R1 g3, R2 g9 |
| Sonnet 5 (claude) | 3 2 0 0 2 0 1 0 **8** 3 | 1.90 | **5.50** | R2 g9 |
| Opus 4.8 (claude) | 5 1 6 3 4 4 2 3 4 3 | 3.50 | **3.50** | R1 g3 |
| GPT-5.5 (codex) | 9 4 4 0 1 3 2 … *(lane in progress)* | — | — | R2 g1 |

### Do models actually get better across ten games?

Mostly **no** — at this scale, per-game variance dominates any learning signal. We
measure the trend three ways, because the naive way is confounded: with the
interleaved rotation, game index is correlated with *which investigator* is being
played (game 4 is always Agnes), so a raw score-vs-game trend partly measures roster
difficulty, not learning.

1. **OLS slope** of score vs game index (descriptive trend).
2. **Spearman rank correlation** (robust to the score's outliers).
3. **Paired second-visit delta** — for each investigator, second play minus first
   play (five matched pairs per agent). This is the cleanest learning measure: same
   investigator and deck, richer notebook, different seed.

| Agent | Slope /game | Spearman ρ | Paired Δ (2nd − 1st visit) |
|---|---:|---:|---:|
| Fable 5 | +0.19 | +0.29 | **+0.20** (R +1, D −1, S −3, A +2, W +2) |
| Sonnet 5 | +0.26 | +0.18 | **+1.00** (R −3, D −1, S 0, A +8, W +1) |
| Opus 4.8 | −0.09 | −0.24 | **−0.60** (R −1, D +1, S −3, A +1, W −1) |
| GPT-5.5 | *(pending)* | *(pending)* | *(pending)* |

![Second-visit deltas](results/second_visit_deltas.svg)

Honest reading of n=10 runs:

- **No agent shows consistent improvement.** Fable's positive slope is real but
  small; Opus is flat-to-declining; Sonnet's +1.00 paired delta is carried entirely
  by one game (its Agnes going 0 → 8) — remove that pair and its delta is −0.75.
- **The wins cluster where the metric looks.** Three of the four victories landed in
  games the rotation made Agnes/late games — and two of them in the scored window.
  Notebooks demonstrably *transport specific plans* (both Claude window-wins executed
  a Priest-kill-then-R2 line their notebooks had described), which is different from
  raising average play quality. Models learn **recipes**, not **skill** — at least
  in ten games.
- **Cold-start capability ≠ learning.** GPT-5.5's opening game (a 9-point R2 win
  with an empty notebook) is the single best game of the benchmark so far — followed
  by regression toward the field. High game-1 skill and positive learning curves are
  independent axes, and this benchmark separates them.
- **Shared seeds make capability gaps legible.** On seed 1003 (Skids), Fable and
  Opus independently found the same R1 kill line (both scored 6 in 16 rounds);
  Sonnet scored 0 on identical draws.
- **Caveats:** 10 games is underpowered for slopes on a 0–9 score with this variance;
  the 2-game scored window is sensitive to single conversions (it's why Sonnet's
  headline beats Opus's despite a 1.6-point worse mean). The 30-game version of this
  run is the obvious next step.

### The second benchmark: can models playtest?

While building this we found the bounty structure turns the benchmark self-healing:
agents are told verified engine-bug reports (via `./ahlcg bug`) are worth more than
score, making every adversary an auditor. Across two live hunts and two
transcript-audit passes (cheap model plays, strong model audits the log), agents
filed 24+ adjudicated reports; **21 confirmed engine defects were found and fixed**
before this benchmark ran — including an engine-wide double-execution bug that unit
tests, 200-game fuzzing, and human review all missed. Game skill and playtest skill
turn out to be distinct: the best bug-finder (Fable 5, 6 confirmed finds) and the
best cold-start player (GPT-5.5) are different models. Full verdicts:
[`specs/bug_adjudications.md`](specs/bug_adjudications.md).

## Demo results (2026-07-03, one game each, harness-validation runs — not a controlled comparison)

Scores under the current `max(0, XP − trauma)` formula (the runs were played under
earlier formulas, and a defeat-trauma double-count inflated opus48/sonnet5 trauma by 1):

| Agent (harness) | Seed | Outcome | XP | Trauma | Lita | Score |
|---|---|---|---|---|---|---|
| GPT-5.5 (codex) | 23 | Defeated by agenda 3 at Act 3, Priest at 4/5 dmg | 6 | 1 | yes | **5** |
| Fable 5 (claude) | 11 | **Won — R1**, Ghoul Priest slain R12 | 6 | 2 | yes | **4** |
| Opus 4.8 (claude) | 31 | Defeated by horror R11 (two hunters stacked) | 4 | 1 | yes | **3** |
| Sonnet 5 (claude) | 47 | Defeated by horror R4 (AoO while engaged) | 2 | 1 | yes | **1** |

(The Gathering's no-resolution outcome is canonically forgiving — you escape with Lita
and your victory display — so defeat is punished mainly through trauma and lost tempo.
The score spread between careful and careless play comes from VP banked and trauma.)

Caveats: different seeds; GPT-5.5 read the notebook Fable 5 wrote (shared notebook in the
first two runs — per-agent notebooks were added afterward). Full transcripts in
`runs/<name>/log.md`, agent reasoning in `logs/<name>.agent.log`, lessons in `notebooks/`.

Card data © Fantasy Flight Games, via the community project
[arkhamdb-json-data](https://github.com/Kamalisk/arkhamdb-json-data). This project is for
AI-capabilities research and commentary; it does not distribute scans of the game.
