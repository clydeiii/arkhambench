from __future__ import annotations

import unittest

from arkham import actions, encounter
from arkham.model import CardInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


def make_state():  # type: ignore[no-untyped-def]
    state = build_engine_test_state(difficulty="standard", rng=ArkhamRng(17))
    state.decision_queue = []
    for location in state.locations.values():
        location.clues = 0
        location.revealed = location.id == "study"
    return state


def add_locked_door(state, instance_id: str = "door") -> str:  # type: ignore[no-untyped-def]
    state.card_instances[instance_id] = CardInstance(id=instance_id, card_code="01174", zone="encounter_drawn")
    return instance_id


class LockedDoorInPlayPoolTests(unittest.TestCase):
    def test_all_in_play_locations_tie_even_when_unrevealed(self) -> None:
        state = make_state()
        door = add_locked_door(state)

        encounter.resolve_revelation(state, ArkhamRng(17), [], door)

        decision = state.decision_queue[0]
        self.assertEqual(decision.id, "locked-door-target")
        self.assertEqual(
            {option.payload["location"] for option in decision.options},
            {"study", "hallway", "attic", "cellar"},
        )

    def test_revealed_location_with_clue_is_unique_max(self) -> None:
        state = make_state()
        state.locations["study"].clues = 1
        door = add_locked_door(state)

        encounter.resolve_revelation(state, ArkhamRng(17), [], door)

        self.assertFalse(state.decision_queue)
        self.assertIn(door, state.locations["study"].attached_instance_ids)

    def test_door_chosen_on_unrevealed_location_blocks_after_reveal(self) -> None:
        state = make_state()
        door = add_locked_door(state)
        encounter.resolve_revelation(state, ArkhamRng(17), [], door)
        choice = next(
            option.payload
            for option in state.decision_queue[0].options
            if option.payload["location"] == "attic"
        )
        state.decision_queue = []

        encounter.resolve_locked_door_target(state, choice, [])
        state.locations["attic"].revealed = True

        self.assertIn(door, state.locations["attic"].attached_instance_ids)
        self.assertTrue(actions.location_locked(state, "attic"))


if __name__ == "__main__":
    unittest.main()
