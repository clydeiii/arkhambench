from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from arkham.log import status_line
from arkham.model import ActState, AgendaState, CardInstance, ChaosBag, GameState, Investigator, Location, TurnState
from scripts import bench


class StatusLineTests(unittest.TestCase):
    def test_status_line_exact_rendering(self) -> None:
        state = GameState(
            schema_version=1,
            scenario="the_gathering",
            difficulty="standard",
            status="in_progress",
            round=4,
            phase="Investigation",
            turn=TurnState(investigator_id="roland", action_index=1),
            investigator=Investigator(
                id="roland",
                name="Roland Banks",
                card_code="01001",
                location_id="hallway",
                willpower=3,
                intellect=3,
                combat=4,
                agility=2,
                health=9,
                sanity=5,
                damage=3,
                horror=1,
                resources=4,
                clues=2,
                actions_remaining=2,
                hand=["h1", "h2", "h3", "h4"],
                deck=[f"d{i}" for i in range(21)],
                discard=[f"x{i}" for i in range(9)],
            ),
            card_instances={"doom_card": CardInstance(id="doom_card", card_code="x", zone="play", doom=1)},
            locations={"hallway": Location(id="hallway", code="01112", name="Hallway", revealed=True)},
            agenda=AgendaState(code="01106", name="The Barrier", stage=2, doom=4, threshold=7),
            act=ActState(code="01109", name="The Barrier", stage=2, clues_required=3),
            chaos_bag=ChaosBag(tokens=["0"]),
        )

        self.assertEqual(
            status_line(state),
            "[R4·Investigation a2/3 | Roland Banks 01001 | Hallway | clu2 res4 | dmg3/9 hor1/5 | h4 d21 x9 | Act2 Agd2 doom5/7]",
        )


class BenchSummaryTests(unittest.TestCase):
    def write_result(self, run_dir: Path, score: int, *, outcome: str = "R1") -> None:
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "outcome": outcome,
            "resolution": outcome,
            "score": score,
            "xp": score + 1,
            "trauma": {"physical": 1, "mental": 0},
            "lita_earned": True,
            "victory_points": 2,
            "rounds_played": 5,
            "damage_taken": 2,
            "horror_taken": 1,
            "actions_taken": 12,
            "encounter_cards_drawn": 4,
            "enemies_defeated": 3,
        }
        (run_dir / "result.json").write_text(json.dumps(payload), encoding="utf-8")

    def test_summary_csv_final_window_incomplete_and_resumability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            label_dir = Path(tmp) / "bench" / "fable5-b1"
            seeds = bench.default_seeds(10)
            for game in range(1, 11):
                run_dir = label_dir / bench.game_dir_name(game, 10)
                if game == 9:
                    run_dir.mkdir(parents=True, exist_ok=True)
                    continue
                self.write_result(run_dir, game)

            rows = bench.collect_rows(label_dir, 10, seeds)
            data = bench.write_artifacts(label_dir, "fable5-b1", rows, 10)

            self.assertTrue(bench.game_completed(label_dir / "game-01"))
            self.assertEqual(data["summary"]["final_20_count"], 2)
            self.assertEqual(data["summary"]["final_20_first_game"], 9)
            self.assertEqual(data["summary"]["final_20_average"], 5.0)
            self.assertEqual([row for row in rows if row["game"] == 9][0]["status"], "incomplete")

            with (label_dir / "results.csv").open("r", encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
            self.assertEqual(csv_rows[8]["status"], "incomplete")
            self.assertEqual(csv_rows[9]["score"], "10")


class BenchCommandTests(unittest.TestCase):
    def test_claude_and_codex_argv(self) -> None:
        prompt = "PROMPT"
        self.assertEqual(
            bench.build_agent_argv("claude-3-5-sonnet", "fable5-b1", prompt, 500),
            [
                "claude",
                "-p",
                "PROMPT",
                "--model",
                "claude-3-5-sonnet",
                "--allowedTools",
                "Bash(./ahlcg:*),Read(docs_agent/**),Read(bench/fable5-b1/notebook.md)",
                "--disallowedTools",
                "Bash(./ahlcg new:*),Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Read(runs/**),Read(bench/**)",
                "--max-turns",
                "500",
            ],
        )
        self.assertEqual(
            bench.build_agent_argv("codex", "fable5-b1", prompt, 500),
            ["codex", "exec", "-s", "workspace-write", "PROMPT"],
        )


if __name__ == "__main__":
    unittest.main()
