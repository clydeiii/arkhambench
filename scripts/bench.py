#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CSV_COLUMNS = [
    "game",
    "seed",
    "investigator",
    "status",
    "outcome",
    "resolution",
    "score",
    "xp",
    "trauma_total",
    "lita_earned",
    "victory_points",
    "rounds",
    "damage_taken",
    "horror_taken",
    "actions_taken",
    "encounter_cards_drawn",
    "enemies_defeated",
    "wall_seconds",
]


def default_seeds(games: int) -> list[int]:
    return [1000 + index for index in range(1, games + 1)]


def investigator_for_game(rotation: list[str], game: int) -> str:
    # Interleaved rotation, identical for every agent: game 1 -> rotation[0],
    # game 2 -> rotation[1], ..., wrapping. With the full five-investigator
    # rotation and 10 games, the final-20% window is the 2nd Agnes + 2nd Wendy.
    return rotation[(game - 1) % len(rotation)]


def read_seeds(path: Path, games: int) -> list[int]:
    seeds = [int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(seeds) < games:
        raise ValueError(f"seeds file has {len(seeds)} seeds, need {games}")
    return seeds[:games]


def game_dir_name(index: int, games: int) -> str:
    return f"game-{index:0{max(2, len(str(games)))}d}"


def final_window(games: int) -> tuple[int, int]:
    final_count = max(1, math.ceil(games / 5))
    first_final = games - final_count + 1
    return final_count, first_final


def notebook_line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8").splitlines())


def bench_header(label: str, k: int, n: int, notebook_lines: int, investigator: str, scenario: str) -> str:
    final_count, first_final = final_window(n)
    return (
        f"=== ArkhamBench: playthrough {k} of {n} ===\n"
        f"This game you are playing {investigator.title()} in scenario '{scenario}'. Investigator-specific\n"
        "strategy notes are in docs_agent/decks_guide.md — read your investigator's section.\n"
        f"You are agent '{label}'. Your benchmark objective is to maximize your AVERAGE SCORE over\n"
        f"the FINAL {final_count} playthroughs (games {first_final}-{n}). Earlier games are for\n"
        "learning: explore, take risks you can learn from, and invest heavily in your notebook —\n"
        f"it is the only memory that persists between games. Your notebook currently has {notebook_lines} lines.\n"
        "Your game has already been created (the current run). Play it to completion now, then\n"
        "record your lessons.\n\n"
    )


STANDALONE_MARKER = "<!-- standalone-only:"


def bench_mission(mission: str) -> str:
    # Strip the standalone-play footer (it tells agents to create their own game,
    # which derails benchmark runs — the runner already created the current run).
    mission = mission.split(STANDALONE_MARKER)[0].rstrip() + "\n"
    return mission + (
        "\n**Benchmark mode:** your game already exists as the current run. NEVER run "
        "`./ahlcg new` — play the existing game with `./ahlcg state` / `./ahlcg do <n>` "
        "until GAME OVER.\n"
    )


def build_prompt(mission: str, label: str, k: int, n: int, notebook_lines: int, investigator: str, scenario: str, note: str = "") -> str:
    extra = f"\n{note.strip()}\n" if note.strip() else ""
    return bench_header(label, k, n, notebook_lines, investigator, scenario) + extra + bench_mission(mission)


def build_new_argv(
    run_dir: Path, seed: int, difficulty: str, notebook: Path, scenario: str, investigator: str
) -> list[str]:
    return [
        "./ahlcg",
        "new",
        "--run",
        str(run_dir),
        "--seed",
        str(seed),
        "--difficulty",
        difficulty,
        "--scenario",
        scenario,
        "--investigator",
        investigator,
        "--notebook",
        str(notebook),
    ]


def build_agent_argv(agent: str, label: str, prompt: str, max_turns: int) -> list[str]:
    if agent == "codex":
        return ["codex", "exec", "-s", "workspace-write", prompt]
    allowed = f"Bash(./ahlcg:*),Read(docs_agent/**),Read(bench/{label}/notebook.md)"
    # Also hard-block creating new games: the assigned run is the only game.
    disallowed = "Bash(./ahlcg new:*),Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read(runs/**),Read(bench/**)"
    return [
        "claude",
        "-p",
        prompt,
        "--model",
        agent,
        "--allowedTools",
        allowed,
        "--disallowedTools",
        disallowed,
        "--max-turns",
        str(max_turns),
    ]


def build_continue_prompt() -> str:
    return (
        "Your game is not finished. Continue playing the CURRENT run (never run "
        "`./ahlcg new`) with `./ahlcg actions` / `./ahlcg do <n>` until GAME OVER, "
        "then record your lessons in the notebook."
    )


def game_completed(run_dir: Path) -> bool:
    return (run_dir / "result.json").exists()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_status(run_dir: Path) -> str:
    meta = run_dir / "meta.json"
    if meta.exists():
        try:
            return str(load_json(meta).get("status", "unknown"))
        except (OSError, ValueError):
            return "unknown"
    state = run_dir / "state.json"
    if state.exists():
        try:
            return str(load_json(state).get("status", "unknown"))
        except (OSError, ValueError):
            return "unknown"
    return "unknown"


def trauma_total(result: dict[str, Any]) -> int:
    if "trauma_total" in result:
        return int(result["trauma_total"])
    trauma = result.get("trauma", {})
    if isinstance(trauma, dict):
        return sum(int(value) for value in trauma.values())
    return 0


def row_from_result(game: int, seed: int, result: dict[str, Any], wall_seconds: float = 0.0, investigator: str = "roland") -> dict[str, Any]:
    return {
        "game": game,
        "seed": seed,
        "investigator": investigator,
        "status": str(result.get("status", "complete")),
        "outcome": str(result.get("outcome", "")),
        "resolution": str(result.get("resolution", "")),
        "score": int(result.get("score", 0)),
        "xp": int(result.get("xp", 0)),
        "trauma_total": trauma_total(result),
        "lita_earned": bool(result.get("lita_earned", False)),
        "victory_points": int(result.get("victory_points", 0)),
        "rounds": int(result.get("rounds", result.get("rounds_played", 0))),
        "damage_taken": int(result.get("damage_taken", 0)),
        "horror_taken": int(result.get("horror_taken", 0)),
        "actions_taken": int(result.get("actions_taken", 0)),
        "encounter_cards_drawn": int(result.get("encounter_cards_drawn", 0)),
        "enemies_defeated": int(result.get("enemies_defeated", 0)),
        "wall_seconds": round(float(wall_seconds), 3),
    }


def incomplete_row(game: int, seed: int, wall_seconds: float = 0.0, investigator: str = "roland") -> dict[str, Any]:
    row = {column: 0 for column in CSV_COLUMNS}
    row.update(
        {
            "game": game,
            "seed": seed,
            "investigator": investigator,
            "status": "incomplete",
            "outcome": "incomplete",
            "resolution": "incomplete",
            "lita_earned": False,
            "wall_seconds": round(float(wall_seconds), 3),
        }
    )
    return row


def collect_rows(label_dir: Path, games: int, seeds: list[int], *, include_incomplete: bool = True) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for game in range(1, games + 1):
        run_dir = label_dir / game_dir_name(game, games)
        result_path = run_dir / "result.json"
        if result_path.exists():
            rows.append(row_from_result(game, seeds[game - 1], load_json(result_path)))
        elif include_incomplete and run_dir.exists():
            rows.append(incomplete_row(game, seeds[game - 1]))
    return rows


def upsert_row(rows: list[dict[str, Any]], row: dict[str, Any]) -> list[dict[str, Any]]:
    kept = [existing for existing in rows if int(existing["game"]) != int(row["game"])]
    kept.append(row)
    return sorted(kept, key=lambda item: int(item["game"]))


def load_bench_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = load_json(path)
    return list(data.get("games", []))


def summary_stats(rows: list[dict[str, Any]], total_games: int) -> dict[str, float | int]:
    scores = [float(row.get("score", 0)) for row in rows]
    final_count, first_final = final_window(total_games)
    final_scores = [float(row.get("score", 0)) for row in rows if int(row["game"]) >= first_final]
    midpoint = math.ceil(total_games / 2)
    first_half = [float(row.get("score", 0)) for row in rows if int(row["game"]) <= midpoint]
    second_half = [float(row.get("score", 0)) for row in rows if int(row["game"]) > midpoint]
    return {
        "games_recorded": len(rows),
        "mean_score": mean(scores),
        "first_half_mean": mean(first_half),
        "second_half_mean": mean(second_half),
        "final_20_count": final_count,
        "final_20_first_game": first_final,
        "final_20_average": mean(final_scores),
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def write_artifacts(label_dir: Path, label: str, rows: list[dict[str, Any]], total_games: int) -> dict[str, Any]:
    label_dir.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda item: int(item["game"]))
    stats = summary_stats(rows, total_games)
    bench_data = {"label": label, "total_games": total_games, "games": rows, "summary": stats}
    atomic_write_json(label_dir / "bench.json", bench_data)
    write_csv(label_dir / "results.csv", rows)
    write_summary(label_dir / "summary.md", label, rows, stats)
    return bench_data


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})
    os.replace(tmp, path)


def write_summary(path: Path, label: str, rows: list[dict[str, Any]], stats: dict[str, float | int]) -> None:
    lines = [
        f"# ArkhamBench summary: {label}",
        "",
        f"Headline benchmark number: final-20% average = {stats['final_20_average']:.2f}",
        f"Final window: last {stats['final_20_count']} game(s), starting at game {stats['final_20_first_game']}.",
        "",
        "## Per-game results",
        "",
        "| Game | Seed | Investigator | Status | Outcome | Resolution | Score | XP | Trauma | Rounds |",
        "| ---: | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['game']} | {row['seed']} | {row.get('investigator', '')} | {row['status']} | {row['outcome']} | "
            f"{row['resolution']} | {row['score']} | {row['xp']} | {row['trauma_total']} | {row['rounds']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate stats",
            "",
            f"- Games recorded: {stats['games_recorded']}",
            f"- Mean score: {stats['mean_score']:.2f}",
            f"- First-half mean score: {stats['first_half_mean']:.2f}",
            f"- Second-half mean score: {stats['second_half_mean']:.2f}",
            f"- Final-20% average: {stats['final_20_average']:.2f}",
            "",
            "## Per-investigator",
            "",
        ]
    )
    by_investigator: dict[str, list[float]] = {}
    for row in rows:
        by_investigator.setdefault(str(row.get("investigator", "?")), []).append(float(row.get("score", 0)))
    for slug in sorted(by_investigator):
        scores = by_investigator[slug]
        lines.append(f"- {slug}: mean {mean(scores):.2f} over {len(scores)} game(s)")
    lines.extend(
        [
            "",
            "## Safety note",
            "",
            "ArkhamBench uses a per-label lock file because agents share CWD/.current_run; "
            "the runner must be the only active game process for this label.",
        ]
    )
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


class BenchLock:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self) -> "BenchLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            text = self.path.read_text(encoding="utf-8").strip()
            pid = int(text) if text.isdigit() else None
            if pid is None or pid_active(pid):
                raise RuntimeError(f"bench appears active: {self.path}")
            self.path.unlink()
        self.path.write_text(str(os.getpid()), encoding="utf-8")
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        try:
            if self.path.read_text(encoding="utf-8").strip() == str(os.getpid()):
                self.path.unlink()
        except OSError:
            pass


def pid_active(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def run_streamed(argv: list[str], log_path: Path | None = None) -> int:
    if log_path is None:
        return subprocess.run(argv, cwd=ROOT, check=False).returncode
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"$ {shlex.join(argv)}\n")
        handle.flush()
        process = subprocess.Popen(
            argv,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            handle.write(line)
            handle.flush()
            print(line, end="")
        return process.wait()


def run_bench(args: argparse.Namespace) -> int:
    games = int(args.games)
    seeds = read_seeds(Path(args.seeds_file), games) if args.seeds_file else default_seeds(games)
    rotation = [slug.strip() for slug in str(args.investigators).split(",") if slug.strip()]
    if not rotation:
        raise ValueError("--investigators must name at least one investigator")
    label_dir = ROOT / "bench" / args.label
    notebook = label_dir / "notebook.md"
    mission = (ROOT / "docs_agent" / "mission.md").read_text(encoding="utf-8")

    if args.dry_run:
        print(f"label: {args.label}")
        print(f"seeds: {', '.join(str(seed) for seed in seeds)}")
        for game, seed in enumerate(seeds, start=1):
            investigator = investigator_for_game(rotation, game)
            run_dir = label_dir / game_dir_name(game, games)
            prompt = build_prompt(mission, args.label, game, games, notebook_line_count(notebook), investigator, args.scenario, args.prompt_note)
            print(shlex.join(build_new_argv(run_dir, seed, args.difficulty, notebook, args.scenario, investigator)))
            print(shlex.join(build_agent_argv(args.agent, args.label, prompt, args.max_turns)))
        return 0

    with BenchLock(label_dir / ".lock"):
        label_dir.mkdir(parents=True, exist_ok=True)
        (label_dir / "logs").mkdir(parents=True, exist_ok=True)
        notebook.parent.mkdir(parents=True, exist_ok=True)
        notebook.touch(exist_ok=True)
        rows = load_bench_rows(label_dir / "bench.json")
        for game, seed in enumerate(seeds, start=1):
            investigator = investigator_for_game(rotation, game)
            run_dir = label_dir / game_dir_name(game, games)
            log_path = label_dir / "logs" / f"game-{game:0{max(2, len(str(games)))}d}.agent.log"
            if game_completed(run_dir):
                print(f"skip game {game}: existing result.json")
                row = row_from_result(game, seed, load_json(run_dir / "result.json"), investigator=investigator)
                rows = upsert_row(rows, row)
                write_artifacts(label_dir, args.label, rows, games)
                continue

            start = time.monotonic()
            if (run_dir / "state.json").exists() and run_status(run_dir) == "in_progress":
                # Crash/outage resume: the game exists mid-play — never re-new
                # (that would wipe the run); hand it straight back to the agent.
                print(f"resume game {game}: in progress, skipping new")
                (ROOT / ".current_run").write_text(str(run_dir) + "\n", encoding="utf-8")
            else:
                new_rc = run_streamed(build_new_argv(run_dir, seed, args.difficulty, notebook, args.scenario, investigator))
                if new_rc != 0:
                    raise RuntimeError(f"new failed for game {game} with exit {new_rc}")

            prompt = build_prompt(mission, args.label, game, games, notebook_line_count(notebook), investigator, args.scenario, args.prompt_note)
            rc = run_streamed(build_agent_argv(args.agent, args.label, prompt, args.max_turns), log_path)
            if rc != 0:
                print(f"warning: agent exited {rc} for game {game}", file=sys.stderr)

            continues = 0
            while not game_completed(run_dir) and run_status(run_dir) == "in_progress" and continues < args.max_continues:
                continues += 1
                rc = run_streamed(
                    build_agent_argv(args.agent, args.label, build_continue_prompt(), args.max_turns),
                    log_path,
                )
                if rc != 0:
                    print(f"warning: continue {continues} exited {rc} for game {game}", file=sys.stderr)

            elapsed = time.monotonic() - start
            if game_completed(run_dir):
                row = row_from_result(game, seed, load_json(run_dir / "result.json"), elapsed, investigator=investigator)
            else:
                print(f"warning: game {game} incomplete after {continues} continue(s); score=0", file=sys.stderr)
                row = incomplete_row(game, seed, elapsed, investigator=investigator)
            rows = upsert_row(rows, row)
            write_artifacts(label_dir, args.label, rows, games)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ArkhamBench playthroughs.")
    parser.add_argument("--agent", required=True, help="claude model id or codex")
    parser.add_argument("--label", required=True)
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--difficulty", choices=("easy", "standard", "hard", "expert"), default="standard")
    parser.add_argument("--scenario", choices=("the_gathering", "return_to_the_gathering"), default="return_to_the_gathering")
    parser.add_argument("--prompt-note", default="", help="extra text inserted into every game prompt")
    parser.add_argument(
        "--investigators",
        default="roland,daisy,skids,agnes,wendy",
        help="comma-separated rotation, cycled per game index (identical for all agents)",
    )
    parser.add_argument("--seeds-file")
    parser.add_argument("--max-continues", type=int, default=2)
    parser.add_argument("--max-turns", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run_bench(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
