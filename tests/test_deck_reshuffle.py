"""RR: drawing from an empty player deck shuffles the discard back in and the
investigator takes 1 horror after the draw (was a no-op before fix)."""
from __future__ import annotations

import unittest

from arkham.effects import draw_player_card
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


class DeckReshuffleTest(unittest.TestCase):
    def test_empty_deck_reshuffles_discard_and_costs_horror(self) -> None:
        state = build_engine_test_state(difficulty="standard", rng=ArkhamRng(4))
        inv = state.investigator
        # Empty the deck into the discard pile.
        inv.discard.extend(inv.deck)
        for card_id in inv.deck:
            state.card_instances[card_id].zone = "discard"
        inv.deck = []
        discard_before = len(inv.discard)
        self.assertGreater(discard_before, 0)

        events: list[dict] = []
        drawn = draw_player_card(state, events, ArkhamRng(4))

        self.assertIsNotNone(drawn)
        self.assertEqual(len(inv.discard), 0)
        self.assertEqual(len(inv.deck), discard_before - 1)
        # 1 horror owed: either assigned directly or pending assignment (soak choice).
        owed = inv.horror + (state.pending_damage or {}).get("remaining_horror", 0)
        self.assertEqual(owed, 1)

    def test_empty_deck_and_discard_draws_nothing(self) -> None:
        state = build_engine_test_state(difficulty="standard", rng=ArkhamRng(4))
        inv = state.investigator
        for card_id in inv.deck:
            state.card_instances[card_id].zone = "removed"
        inv.deck = []
        inv.discard = []
        events: list[dict] = []
        self.assertIsNone(draw_player_card(state, events, ArkhamRng(4)))
        self.assertEqual(inv.horror, 0)


if __name__ == "__main__":
    unittest.main()
