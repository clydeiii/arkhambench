from __future__ import annotations

import unittest

from arkham import actions, phases
from arkham.model import CardInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


def daisy_upkeep_state():  # type: ignore[no-untyped-def]
    state = build_engine_test_state(difficulty="standard", rng=ArkhamRng(25))
    state.phase = "Upkeep"
    state.investigator.id = "daisy"
    state.investigator.name = "Daisy Walker"
    state.investigator.card_code = "01002"
    state.investigator.hand = []
    state.investigator.deck = []
    state.investigator.discard = []
    state.investigator.play_area = []
    state.investigator.threat_area = []
    state.decision_queue = []
    return state


def add_card(state, code: str, zone: str, card_id: str) -> str:  # type: ignore[no-untyped-def]
    state.card_instances[card_id] = CardInstance(
        id=card_id,
        card_code=code,
        zone=zone,
        owner=state.investigator.id,
    )
    if zone == "play":
        state.investigator.play_area.append(card_id)
    elif zone == "deck":
        state.investigator.deck.append(card_id)
    return card_id


class NonPlaySlotEntryTests(unittest.TestCase):
    def test_necronomicon_overflow_interrupts_upkeep_before_resource(self) -> None:
        state = daisy_upkeep_state()
        add_card(state, "01087", "play", "flashlight")
        add_card(state, "01086", "play", "knife")
        necronomicon = add_card(state, "01009", "deck", "necronomicon")
        resources_before = state.investigator.resources
        events: list[dict] = []

        phases.run_upkeep_phase(state, events, ArkhamRng(25))

        self.assertIn(necronomicon, state.investigator.threat_area)
        self.assertEqual(state.decision_queue[0].id, "slot-overflow-discard")
        self.assertEqual(state.investigator.resources, resources_before)
        self.assertFalse(any(event["type"] == "resource_gained" for event in events))

        payload = state.decision_queue.pop(0).options[0].payload
        actions.resolve_slot_discard(state, payload, events)
        self.assertFalse(state.decision_queue)

        phases.run_upkeep_phase(state, events, ArkhamRng(25))
        self.assertEqual(state.investigator.resources, resources_before + 1)
        self.assertEqual(sum(event["type"] == "resource_gained" for event in events), 1)

        phases.run_upkeep_phase(state, events, ArkhamRng(25))
        self.assertEqual(state.investigator.resources, resources_before + 1)
        self.assertEqual(sum(event["type"] == "resource_gained" for event in events), 1)


if __name__ == "__main__":
    unittest.main()
