from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from arkham import actions, encounter, enemies, phases, skill_test
from arkham.effects import place_doom, start_damage_assignment
from arkham.game import Game
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


ROOT = Path(__file__).resolve().parent.parent


def state(seed: int = 1):
    return build_engine_test_state(difficulty="standard", rng=ArkhamRng(seed))


class PhaseBRulesTests(unittest.TestCase):
    def add_enemy(self, s, code: str = "01180", location: str = "study", engaged: bool = True) -> str:
        instance_id = "enemy1"
        s.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="enemy")
        s.enemies[instance_id] = EnemyInstance(id=instance_id, card_code=code, location_id=location)
        s.locations[location].enemy_ids.append(instance_id)
        if engaged:
            s.enemies[instance_id].engaged_with = "roland"
            s.investigator.engaged_enemies.append(instance_id)
        return instance_id

    def test_attacks_of_opportunity_matrix_and_move_together(self) -> None:
        s = state()
        enemy_id = self.add_enemy(s)
        events = []

        actions.execute(s, {"action": "move", "location": "hallway"}, events)
        self.assertEqual(s.investigator.damage, 1)
        self.assertEqual(s.investigator.location_id, "hallway")
        self.assertEqual(s.enemies[enemy_id].location_id, "hallway")
        self.assertIn(enemy_id, s.investigator.engaged_enemies)

        s.investigator.actions_remaining = 3
        before = s.investigator.damage
        actions.execute(s, {"action": "fight", "enemy": enemy_id}, events)
        self.assertEqual(s.investigator.damage, before)
        self.assertIsNotNone(s.active_skill_test)

    def test_hunter_bfs_tiebreak_and_barricade_block(self) -> None:
        s = state()
        s.locations["study"].connections = ["attic", "cellar"]
        s.locations["attic"].connections = ["study", "hallway"]
        s.locations["cellar"].connections = ["study", "hallway"]
        s.locations["hallway"].connections = ["attic", "cellar"]
        enemy_id = self.add_enemy(s, code="01180", location="study", engaged=False)
        s.investigator.location_id = "hallway"

        self.assertEqual(enemies.next_step_toward(s, "study", "hallway", enemy_id), "attic")

        barrier = "barrier1"
        s.card_instances[barrier] = CardInstance(id=barrier, card_code="phaseb_barricade", zone="attachment")
        s.locations["attic"].attached_instance_ids.append(barrier)
        self.assertEqual(enemies.next_step_toward(s, "study", "hallway", enemy_id), "cellar")

    def test_encounter_reshuffle_and_doom_advance(self) -> None:
        s = state()
        rng = ArkhamRng(3)
        s.encounter_deck = []
        s.encounter_discard = ["ec0001", "ec0002"]
        events = []

        encounter.draw_encounter(s, rng, events)
        self.assertEqual(len(s.encounter_deck), 1)
        self.assertTrue(any(event["type"] == "encounter_reshuffled" for event in events))

        s.agenda.doom = 2
        place_doom(s, 1, events, source="test")
        self.assertEqual(s.agenda.stage, 2)
        self.assertEqual(s.agenda.doom, 0)

    def test_upkeep_order_ready_draw_resource_hand_size(self) -> None:
        s = state()
        s.phase = "Upkeep"
        s.card_instances[s.investigator.hand[0]].exhausted = True
        s.investigator.resources = 0
        s.investigator.hand.extend(s.investigator.deck)
        s.investigator.deck = []
        events = []

        phases.run_upkeep_phase(s, events)
        self.assertFalse(any(card.exhausted for card in s.card_instances.values()))
        self.assertEqual(s.investigator.resources, 1)
        self.assertEqual(s.decision_queue[0].kind, "choose_option")

    def test_skill_tests_ties_autofail_icons_wild_and_margins(self) -> None:
        s = state()
        rng = ArkhamRng(4)
        s.chaos_bag.tokens = ["0"]
        events = []
        skill_test.start(s, events, skill="intellect", difficulty=3, source="tie")
        skill_test.finish_commit(s, rng, events)
        self.assertTrue(s.limits["last_skill_test"]["success"])
        self.assertEqual(s.limits["last_skill_test"]["margin"], 0)

        s = state()
        s.chaos_bag.tokens = ["autofail"]
        events = []
        skill_test.start(s, events, skill="intellect", difficulty=0, source="autofail")
        skill_test.finish_commit(s, rng, events)
        self.assertFalse(s.limits["last_skill_test"]["success"])

        s = state()
        wild = "wild1"
        s.card_instances[wild] = CardInstance(id=wild, card_code="01093", zone="hand")
        s.investigator.hand = [wild]
        s.chaos_bag.tokens = ["0"]
        events = []
        skill_test.start(s, events, skill="combat", difficulty=6, source="wild")
        skill_test.commit_card(s, {"card": wild}, events)
        skill_test.finish_commit(s, rng, events)
        self.assertTrue(s.limits["last_skill_test"]["success"])
        self.assertEqual(s.limits["last_skill_test"]["committed_icons"], 2)

    def test_ally_soak_destruction_and_defeat(self) -> None:
        s = state()
        ally = "ally1"
        s.card_instances[ally] = CardInstance(id=ally, card_code="01018", zone="play")
        s.investigator.play_area.append(ally)
        events = []

        start_damage_assignment(s, events, source="test", damage=2, horror=0)
        self.assertEqual(s.decision_queue[0].kind, "assign_damage")
        for _ in range(2):
            option = next(option for option in s.decision_queue[0].options if option.payload["target"] == ally)
            from arkham.effects import assign_damage_choice

            s.decision_queue = []
            assign_damage_choice(s, option.payload, events)
        self.assertIn(ally, s.investigator.discard)

        start_damage_assignment(s, events, source="defeat", damage=9, horror=0, direct=True)
        self.assertEqual(s.status, "ended")
        self.assertEqual(s.trauma["physical"], 1)


class PhaseBDeterminismTests(unittest.TestCase):
    def run_script(self, run_dir: Path) -> list[str]:
        run_dir.parent.mkdir(parents=True, exist_ok=True)
        script = [
            ("new", "--seed", "99", "--run", str(run_dir)),
            ("do", "4", "--run", str(run_dir)),
            ("do", "10", "--run", str(run_dir)),
        ]
        for args in script:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT)
            result = subprocess.run(
                [sys.executable, "-m", "arkham", *args],
                cwd=run_dir.parent,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        return (run_dir / "log.jsonl").read_text(encoding="utf-8").splitlines()

    def test_same_seed_and_actions_byte_identical_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = self.run_script(Path(tmp) / "a")
            second = self.run_script(Path(tmp) / "b")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
