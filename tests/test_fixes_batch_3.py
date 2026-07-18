from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from arkham import cli, encounter, enemies, skill_test
from arkham.game import Game
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


class SeqRng:
    def __init__(self, values: list[str]) -> None:
        self.values = list(values)

    def choice(self, values):  # type: ignore[no-untyped-def]
        return self.values.pop(0) if self.values else values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def state():
    s = build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.decision_queue = []
    s.chaos_bag.tokens = ["0"]
    return s


def add_card(s, code: str, zone: str = "hand", instance_id: str | None = None) -> str:
    instance_id = instance_id or f"{code}_{len(s.card_instances)}"
    s.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone=zone, owner=s.investigator.id)
    if zone == "hand":
        s.investigator.hand.append(instance_id)
    elif zone == "encounter_deck":
        s.encounter_deck.append(instance_id)
    return instance_id


def add_enemy(s, code: str = "01159", location: str = "study") -> str:
    enemy_id = f"enemy_{len(s.enemies)}"
    s.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    s.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location, engaged_with=s.investigator.id)
    s.locations[location].enemy_ids.append(enemy_id)
    s.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


def messages(run_dir: Path) -> list[str]:
    rows = [json.loads(line) for line in (run_dir / "log.jsonl").read_text(encoding="utf-8").splitlines() if line]
    return [str(row.get("data", {}).get("message", "")) for row in rows]


class FixesBatch3Tests(unittest.TestCase):
    def test_daisy_enemy_defeat_does_not_offer_roland_reaction(self) -> None:
        s = state()
        s.investigator.id = "daisy"
        s.investigator.name = "Daisy Walker"
        s.investigator.card_code = "01002"
        s.locations["study"].clues = 2
        enemy = add_enemy(s)

        enemies.damage_enemy(s, [], enemy, 1)

        self.assertFalse(
            any(option.payload.get("reaction") == "roland" for decision in s.decision_queue for option in decision.options)
        )

    def test_daisy_log_messages_do_not_name_roland(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            game = Game.new(seed=1, difficulty="standard", deck_path=None, run_dir=run_dir, investigator="daisy")
            game.apply(1)

            self.assertFalse(any("Roland" in message for message in messages(run_dir)))

    def test_skill_test_result_message_shows_math_and_autofail(self) -> None:
        s = state()
        guts = add_card(s, "01089", "hand")
        events: list[dict] = []
        skill_test.start(s, events, skill="willpower", difficulty=3, source="Rotting Remains")
        skill_test.commit_card(s, {"card": guts}, events)
        s.active_skill_test["boosts"].append({"amount": 1})
        skill_test.finish_commit(s, SeqRng(["-1"]), events)
        result = next(event["message"] for event in events if event["type"] == "skill_test_result")
        self.assertIn("willpower 3 + committed 2 + boosts 1 + token -1 = 5 vs 3", result)

        s = state()
        events = []
        skill_test.start(s, events, skill="willpower", difficulty=3, source="Rotting Remains")
        skill_test.finish_commit(s, SeqRng(["autofail"]), events)
        result = next(event["message"] for event in events if event["type"] == "skill_test_result")
        self.assertIn("autofail (skill value 0) vs 3", result)

    def test_locked_door_tie_is_player_choice_and_unique_target_auto_attaches(self) -> None:
        s = state()
        for location in s.locations.values():
            location.clues = 0
            location.revealed = location.id == "study"
        door = add_card(s, "01174", "encounter_deck")
        encounter.resolve_revelation(s, ArkhamRng(1), [], door)
        self.assertEqual(s.decision_queue[0].id, "locked-door-target")
        labels = [option.label for option in s.decision_queue[0].options]
        self.assertEqual(len(labels), 4)
        for location_name in ("Study", "Hallway", "Attic", "Cellar"):
            self.assertTrue(any(location_name in label for label in labels))

        encounter.resolve_locked_door_target(s, s.decision_queue.pop(0).options[0].payload, [])
        self.assertTrue(any(door in location.attached_instance_ids for location in s.locations.values()))

        s = state()
        s.locations["study"].clues = 1
        s.locations["attic"].clues = 3
        s.locations["cellar"].clues = 2
        door = add_card(s, "01174", "encounter_deck")
        encounter.resolve_revelation(s, ArkhamRng(1), [], door)
        self.assertFalse(s.decision_queue)
        self.assertIn(door, s.locations["attic"].attached_instance_ids)

    def test_do_why_logs_reason_and_bug_report_is_in_band(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            Game.new(seed=2, difficulty="standard", deck_path=None, run_dir=run_dir)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["do", "1", "--run", str(run_dir), "--why", "keep tempo"]), 0)

            log_text = (run_dir / "log.jsonl").read_text(encoding="utf-8")
            md_text = (run_dir / "log.md").read_text(encoding="utf-8")
            self.assertIn("agent_reason", log_text)
            self.assertIn("keep tempo", log_text)
            self.assertIn("keep tempo", md_text)
            timeline = (run_dir / "timeline.jsonl").read_text(encoding="utf-8")
            self.assertIn("agent_reason", timeline)

            before = Game.load(run_dir).state.to_dict()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["bug", "bad action label", "--run", str(run_dir)]), 0)
            after = Game.load(run_dir).state.to_dict()
            self.assertEqual(after, before)
            self.assertIn("bad action label", (run_dir / "bug_reports.md").read_text(encoding="utf-8"))
            self.assertIn("bug_report", (run_dir / "log.jsonl").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
