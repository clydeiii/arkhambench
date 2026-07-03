"""Regression: fast-ability windows at phase boundaries (fixes_batch_2 §1).

Case from runs/gpt55-demo-1: Beat Cop's fast ping must be usable after the last
action of the turn resolves, before the enemy phase.
"""
from __future__ import annotations

import unittest

from arkham import phases
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


class FastWindowTest(unittest.TestCase):
    def _state_with_beat_cop_and_enemy(self):
        state = build_engine_test_state(difficulty="standard", rng=ArkhamRng(9))
        inv = state.investigator
        inv.actions_remaining = 0
        # Put Beat Cop into play.
        state.card_instances["bc1"] = CardInstance(id="bc1", card_code="01018", zone="play_area")
        inv.play_area.append("bc1")
        # Put an exhausted enemy at Roland's location (exhausted so the enemy
        # phase itself is quiet; the window should still offer the ping).
        enemy_id = "fw_enemy"
        state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code="01160", zone="enemy")
        state.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code="01160", location_id=inv.location_id, exhausted=True)
        state.locations[inv.location_id].enemy_ids.append(enemy_id)
        return state, enemy_id

    def test_end_of_turn_window_offers_beat_cop(self) -> None:
        state, _ = self._state_with_beat_cop_and_enemy()
        events: list[dict] = []
        phases.advance_until_decision(state, ArkhamRng(9), events)
        self.assertTrue(state.decision_queue)
        decision = state.decision_queue[0]
        self.assertEqual(decision.kind, "fast_window")
        labels = [option.label for option in decision.options]
        self.assertTrue(any("Beat Cop" in label for label in labels), labels)
        self.assertEqual(decision.options[-1].payload["kind"], "fast_window_pass")

    def test_pass_closes_window_for_the_round(self) -> None:
        state, _ = self._state_with_beat_cop_and_enemy()
        events: list[dict] = []
        phases.advance_until_decision(state, ArkhamRng(9), events)
        decision = state.decision_queue[0]
        key = decision.options[-1].payload["key"]
        state.limits[str(key)] = True
        state.decision_queue = []
        phases.advance_until_decision(state, ArkhamRng(9), events)
        # The inv_end window must not re-present; a window at a LATER boundary
        # (e.g. enemy_pre) is fine and expected while Beat Cop remains legal.
        if state.decision_queue:
            self.assertNotEqual(state.decision_queue[0].id, "fast-window-inv_end")


if __name__ == "__main__":
    unittest.main()
