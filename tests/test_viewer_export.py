from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from arkham.export import export_run, rebuild_index
from arkham.game import Game


ROOT = Path(__file__).resolve().parent.parent


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def play_decisions(run_dir: Path, count: int = 3) -> list[dict]:
    game = Game.new(seed=31, difficulty="standard", deck_path=None, run_dir=run_dir)
    for _ in range(count):
        decision = game.current_decision()
        if decision is None:
            break
        game.apply(1)
    return [entry for entry in read_jsonl(run_dir / "log.jsonl") if entry["type"] == "decision_made"]


def codes_in_steps(steps: list[dict]) -> set[str]:
    codes: set[str] = set()
    for step in steps:
        state = step["state"]
        investigator = state.get("investigator") or {}
        if investigator.get("card_code"):
            codes.add(investigator["card_code"])
        for instance in (state.get("card_instances") or {}).values():
            codes.add(instance["card_code"])
        for enemy in (state.get("enemies") or {}).values():
            codes.add(enemy["card_code"])
        for location in (state.get("locations") or {}).values():
            codes.add(location["code"])
        if state.get("agenda"):
            codes.add(state["agenda"]["code"])
        if state.get("act"):
            codes.add(state["act"]["code"])
    return codes


class TimelineCaptureTests(unittest.TestCase):
    def test_new_and_apply_write_timeline_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            decisions = play_decisions(run_dir, count=2)
            lines = read_jsonl(run_dir / "timeline.jsonl")

            self.assertEqual(len(lines), len(decisions) + 1)
            self.assertEqual(lines[0]["i"], 0)
            self.assertIsNone(lines[0]["chose"])
            self.assertIn("state", lines[0])
            self.assertIsNotNone(lines[0]["pending"])
            self.assertEqual(lines[1]["chose"]["label"], decisions[0]["data"]["label"])
            self.assertIn("events", lines[1])


class ExporterTests(unittest.TestCase):
    def test_replay_export_steps_choices_index_and_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            decisions = play_decisions(run_dir, count=3)
            (run_dir / "timeline.jsonl").unlink()

            out_dir = root / "viewer" / "data"
            out_path = export_run(run_dir, out_dir, name="scripted")
            payload = json.loads(out_path.read_text(encoding="utf-8"))

            self.assertFalse((run_dir / "timeline.jsonl").exists())
            self.assertTrue(payload["meta"]["complete"])
            self.assertIsNone(payload["meta"]["divergence_step"])
            self.assertEqual(len(payload["steps"]), len(decisions) + 1)
            for step, decision in zip(payload["steps"], decisions):
                self.assertEqual(step["decision"]["chosen"], decision["data"]["option"])
                self.assertEqual(step["decision"]["chosen_label"], decision["data"]["label"])
            self.assertTrue(codes_in_steps(payload["steps"]).issubset(set(payload["cards"])))

            index = rebuild_index(out_dir)
            self.assertEqual(index[0]["name"], "scripted")
            self.assertEqual(index[0]["file"], "scripted.json")
            self.assertEqual(index[0]["steps"], len(payload["steps"]))

    def test_replay_divergence_exports_partial_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            play_decisions(run_dir, count=2)
            (run_dir / "timeline.jsonl").unlink()

            entries = read_jsonl(run_dir / "log.jsonl")
            for entry in entries:
                if entry["type"] == "decision_presented":
                    entry["data"]["prompt"] = "doctored prompt"
                    break
            (run_dir / "log.jsonl").write_text(
                "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries),
                encoding="utf-8",
            )

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                out_path = export_run(run_dir, root / "viewer" / "data", name="diverged")
            payload = json.loads(out_path.read_text(encoding="utf-8"))

            self.assertFalse(payload["meta"]["complete"])
            self.assertEqual(payload["meta"]["divergence_step"], 0)
            self.assertIn("WARNING: replay diverged", stderr.getvalue())
            self.assertGreaterEqual(len(payload["steps"]), 1)


class ViewerDataSchemaTests(unittest.TestCase):
    def test_existing_viewer_data_exports_have_required_step_schema(self) -> None:
        data_dir = ROOT / "viewer" / "data"
        exports = sorted(path for path in data_dir.glob("*.json") if path.name != "index.json")
        if not exports:
            self.skipTest("no viewer/data exports present")

        for path in exports:
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("meta", payload, path.name)
            self.assertIn("cards", payload, path.name)
            self.assertIn("steps", payload, path.name)
            self.assertTrue(payload["steps"], path.name)
            for step in payload["steps"]:
                self.assertIn("i", step)
                self.assertIn("round", step)
                self.assertIn("phase", step)
                self.assertIn("status", step)
                self.assertIn("events", step)
                self.assertIn("decision", step)
                self.assertIn("state", step)
                decision = step["decision"]
                if decision is not None:
                    self.assertIn("prompt", decision)
                    self.assertIn("options", decision)
                    self.assertIn("chosen", decision)
                    self.assertIn("chosen_label", decision)


if __name__ == "__main__":
    unittest.main()
