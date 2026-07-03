"""Regression: hand-size discard must not re-trigger upkeep draw/resource.

Found by the Fable 5 demo agent (runs/fable5-demo-1): each discard-to-size choice
re-entered run_upkeep_phase, drawing a card and gaining a resource per iteration,
allowing the whole deck to be cycled during a single upkeep.
"""
from __future__ import annotations

import unittest

from arkham import phases
from arkham.model import GameState


def _upkeep_state() -> GameState:
    from arkham.rng import ArkhamRng
    from arkham.scenarios.the_gathering import build_engine_test_state

    state = build_engine_test_state(difficulty="standard", rng=ArkhamRng(5))
    state.phase = "Upkeep"
    state.investigator.actions_remaining = 0
    return state


class UpkeepIdempotencyTest(unittest.TestCase):
    def test_discard_to_size_does_not_redraw(self) -> None:
        state = _upkeep_state()
        # Force an oversized hand: move everything from deck to hand.
        inv = state.investigator
        # Leave 1 card in deck; hand of 9 + upkeep draw = 10 (> 8 triggers discard).
        while len(inv.deck) > 1 and len(inv.hand) < 9:
            card = inv.deck.pop(0)
            inv.hand.append(card)
            state.card_instances[card].zone = "hand"
        deck_before = len(inv.deck)
        resources_before = inv.resources

        events: list[dict] = []
        phases.run_upkeep_phase(state, events)  # draws 1, presents discard decision
        hand_after_first = len(inv.hand)
        self.assertTrue(state.decision_queue, "expected discard-to-size decision")

        # Simulate resolving one discard, then the phase loop re-entering upkeep.
        payload = state.decision_queue[0].options[0].payload
        state.decision_queue = []
        phases.discard_to_size(state, payload, events)
        phases.run_upkeep_phase(state, events)

        self.assertEqual(len(inv.deck), deck_before - 1, "second upkeep entry must not draw again")
        self.assertEqual(inv.resources, resources_before + 1, "second upkeep entry must not gain resource again")
        self.assertEqual(len(inv.hand), hand_after_first - 1)


if __name__ == "__main__":
    unittest.main()
