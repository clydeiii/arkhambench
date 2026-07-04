from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from arkham import actions
from arkham.effects import advance_act, end_game
from arkham.game import Game
from arkham.model import ActState, CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import agenda_3_doom_out, build_gathering_state, finalize_result


def gathering(seed: int = 1):
    state = build_gathering_state(difficulty="standard", rng=ArkhamRng(seed))
    state.decision_queue = []
    return state


def add_enemy(state, code: str, location: str, engaged: bool = True, instance_id: str = "enemy1") -> str:
    state.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="enemy")
    state.enemies[instance_id] = EnemyInstance(id=instance_id, card_code=code, location_id=location)
    state.locations[location].enemy_ids.append(instance_id)
    if engaged:
        state.enemies[instance_id].engaged_with = "roland"
        state.investigator.engaged_enemies.append(instance_id)
    return instance_id


class PhaseDScenarioTests(unittest.TestCase):
    def test_act1_discards_study_enemies_removes_study_and_reveals_hallway(self) -> None:
        state = gathering()
        enemy = add_enemy(state, "01160", "study")
        state.investigator.clues = 2
        advance_act(state, [])
        self.assertNotIn("study", state.locations)
        self.assertIn("study", state.removed_from_game)
        self.assertEqual(state.investigator.location_id, "hallway")
        self.assertTrue(state.locations["hallway"].revealed)
        self.assertIn(enemy, state.encounter_discard)
        self.assertNotIn(enemy, state.investigator.engaged_enemies)

    def test_parlor_blocked_until_act2_and_lita_priest_enter(self) -> None:
        state = gathering()
        state.investigator.clues = 2
        advance_act(state, [])
        labels = [option.label for option in actions.legal_actions(state)]
        self.assertFalse(any("Parlor" in label for label in labels))
        state.investigator.clues = 3
        advance_act(state, [])
        self.assertTrue(state.locations["parlor"].revealed)
        self.assertTrue(any(state.card_instances[card].card_code == "01117" for card in state.locations["parlor"].attached_instance_ids))
        self.assertTrue(any(state.card_instances[enemy].card_code == "01116" for enemy in state.locations["hallway"].enemy_ids))

    def test_attic_and_cellar_forced_effects_fire_on_each_entry(self) -> None:
        state = gathering()
        state.investigator.clues = 2
        advance_act(state, [])
        actions.move(state, "attic", [])
        self.assertEqual(state.investigator.horror, 1)
        actions.move(state, "hallway", [])
        actions.move(state, "attic", [])
        self.assertEqual(state.investigator.horror, 2)

    def test_result_json_score_for_no_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            game = Game.new(seed=3, difficulty="standard", deck_path=None, run_dir=run_dir)
            game.apply(1)
            state = game.state
            state.decision_queue = []
            state.locations["attic"] = state.locations.get("attic") or __import__("arkham.model", fromlist=["Location"]).Location(id="attic", code="01113", name="Attic", revealed=True, shroud=1, clues=0, connections=["hallway"])
            end_game(state, [], "Roland resigned")
            game.save()
            result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["outcome"], "no_resolution")
            self.assertEqual(result["xp"], result["victory_points"] + 2)
            self.assertGreaterEqual(result["score"], 0)

    def test_r1_and_r2_xp_math(self) -> None:
        state = gathering()
        state.locations["attic"] = __import__("arkham.model", fromlist=["Location"]).Location(id="attic", code="01113", name="Attic", revealed=True, shroud=1, clues=0, connections=["hallway"])
        state.trauma["mental"] = 1
        finalize_result(state, [], outcome="R1", resolution="R1", summary="burn")
        # R1: xp = victory(1) + 2 insight; score = xp - trauma.
        self.assertEqual(state.result["xp"], 3)
        self.assertTrue(state.result["lita_earned"])
        self.assertEqual(state.result["score"], 2)

        state = gathering()
        state.locations["attic"] = __import__("arkham.model", fromlist=["Location"]).Location(id="attic", code="01113", name="Attic", revealed=True, shroud=1, clues=0, connections=["hallway"])
        finalize_result(state, [], outcome="R2", resolution="R2", summary="stand")
        # R2: xp = victory(1) + 2 insight + 1 lead bonus; NO Lita, no Lita bonus.
        self.assertEqual(state.result["xp"], 4)
        self.assertFalse(state.result["lita_earned"])
        self.assertEqual(state.result["score"], 4)

    def test_r3_scores_zero(self) -> None:
        state = gathering()
        state.act.stage = 2
        agenda_3_doom_out(state, [])
        self.assertEqual(state.result["outcome"], "R3")
        self.assertEqual(state.result["xp"], 0)
        self.assertEqual(state.result["score"], 0)


if __name__ == "__main__":
    unittest.main()
