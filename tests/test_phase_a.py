from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from arkham.game import Game
from arkham.model import (
    ActState,
    AgendaState,
    CardInstance,
    ChaosBag,
    DecisionOption,
    GameState,
    Investigator,
    Location,
    PendingDecision,
    TurnState,
)
from arkham.notebook import add_note, compact, show
from arkham.serialize import atomic_write_json, decode_hidden


ROOT = Path(__file__).resolve().parent.parent


class ModelTests(unittest.TestCase):
    def test_game_state_round_trips(self) -> None:
        state = GameState(
            schema_version=1,
            scenario="stub",
            difficulty="standard",
            status="in_progress",
            round=2,
            phase="Investigation",
            turn=TurnState(investigator_id="roland", action_index=1),
            investigator=Investigator(
                id="roland",
                name="Roland Banks",
                card_code="01001",
                location_id="study",
                willpower=3,
                intellect=3,
                combat=4,
                agility=2,
                health=9,
                sanity=5,
                resources=5,
                clues=1,
                actions_remaining=2,
                hand=["c1"],
                deck=["c2", "c3"],
                discard=["c4"],
            ),
            card_instances={
                "c1": CardInstance(id="c1", card_code="01016", zone="hand"),
                "c2": CardInstance(id="c2", card_code="01020", zone="player_deck"),
            },
            locations={
                "study": Location(
                    id="study",
                    code="01111",
                    name="Study",
                    revealed=True,
                    shroud=2,
                    clues=2,
                    connections=["hallway"],
                    investigator_ids=["roland"],
                )
            },
            agenda=AgendaState(
                code="01105",
                name="What's Going On?!",
                stage=1,
                doom=1,
                threshold=3,
            ),
            act=ActState(code="01108", name="Trapped", stage=1, clues_required=2),
            chaos_bag=ChaosBag(tokens=["0", "-1", "autofail"]),
            victory_display=["v1"],
            decision_queue=[
                PendingDecision(
                    id="d1",
                    prompt="choose",
                    options=[DecisionOption(label="A", payload={"choice": "a"})],
                )
            ],
            encounter_discard=["e1"],
            removed_from_game=["r1"],
        )

        self.assertEqual(GameState.from_dict(state.to_dict()), state)


class PersistenceTests(unittest.TestCase):
    def test_hidden_public_split_excludes_deck_order_from_state_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            game = Game.new(seed=11, difficulty="standard", deck_path=None, run_dir=run_dir)
            public_bytes = (run_dir / "state.json").read_bytes()
            hidden = decode_hidden((run_dir / "hidden.blob").read_text(encoding="utf-8"))

            deck_ids = game.state.investigator.deck
            self.assertTrue(deck_ids)
            self.assertNotIn(deck_ids[0].encode("utf-8"), public_bytes)
            self.assertNotIn(b'"deck":', public_bytes)
            self.assertIn(deck_ids[0], hidden["state"]["investigator"]["deck"])

    def test_atomic_write_keeps_existing_json_on_replace_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text('{"ok": true}\n', encoding="utf-8")
            with mock.patch("arkham.serialize.os.replace", side_effect=RuntimeError("crash")):
                with self.assertRaises(RuntimeError):
                    atomic_write_json(path, {"ok": False})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"ok": True})


class NotebookTests(unittest.TestCase):
    def test_add_show_compact_and_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = Path(tmp) / "notebook.md"
            add_note(notebook, "remember this", run_name="run-a", round_number=3)
            body = show(notebook)
            self.assertIn("Run run-a · Round 3", body)
            self.assertIn("remember this", body)

            archive = compact(notebook, "short memory")
            self.assertEqual(show(notebook), "short memory\n")
            self.assertTrue(archive.exists())
            self.assertIn("remember this", archive.read_text(encoding="utf-8"))


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        full_env = os.environ.copy()
        full_env["PYTHONPATH"] = str(ROOT)
        if env:
            full_env.update(env)
        return subprocess.run(
            [sys.executable, "-m", "arkham", *args],
            cwd=cwd,
            env=full_env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_phase_b_round_trip_new_actions_do_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            run_dir = cwd / "runs" / "stub"

            new = self.run_cli("new", "--seed", "7", "--run", str(run_dir), cwd=cwd)
            self.assertEqual(new.returncode, 0, new.stderr)
            self.assertIn("Choose opening hand mulligan", new.stdout)

            actions = self.run_cli("actions", "--run", str(run_dir), cwd=cwd)
            self.assertEqual(actions.returncode, 0, actions.stderr)
            self.assertIn("Keep opening hand", actions.stdout)

            do = self.run_cli("do", "1", "--run", str(run_dir), cwd=cwd)
            self.assertEqual(do.returncode, 0, do.stderr)
            self.assertIn("Decision made", do.stdout)
            self.assertIn("Choose an action", do.stdout)

            do = self.run_cli("do", "1", "--run", str(run_dir), cwd=cwd)
            self.assertEqual(do.returncode, 0, do.stderr)
            self.assertIn("Commit", do.stdout)

            log = self.run_cli("log", "--run", str(run_dir), "--tail", "10", cwd=cwd)
            self.assertEqual(log.returncode, 0, log.stderr)
            self.assertIn("Started intellect test", log.stdout)

    def test_card_lookup_by_code_and_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            by_code = self.run_cli("card", "01001", cwd=cwd)
            self.assertEqual(by_code.returncode, 0, by_code.stderr)
            self.assertIn("Roland Banks", by_code.stdout)
            self.assertIn("willpower", by_code.stdout)

            by_name = self.run_cli("card", "ghoul priest", cwd=cwd)
            self.assertEqual(by_name.returncode, 0, by_name.stderr)
            self.assertIn("Ghoul Priest", by_name.stdout)
            self.assertIn("fight", by_name.stdout)


if __name__ == "__main__":
    unittest.main()
