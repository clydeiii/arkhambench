from __future__ import annotations

import unittest

from arkham import encounter, phases
from arkham.model import CardInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_gathering as gathering
from arkham.scenarios import the_midnight_masks as midnight_masks


class GhoulPriestSpawnTests(unittest.TestCase):
    def test_midnight_masks_mythos_draw_engages_ghoul_priest_with_drawer(self) -> None:
        state = midnight_masks.build_state(
            difficulty="standard",
            rng=ArkhamRng(1),
            investigator_slug="roland",
            ghoul_priest_alive=True,
        )
        state.decision_queue = []
        state.phase = "Mythos"
        state.round = 2
        state.limits["mythos_doom_placed:2"] = True
        priest = next(
            card_id
            for card_id in state.encounter_deck
            if state.card_instances[card_id].card_code == "01116"
        )
        state.encounter_deck = [priest]

        phases.run_mythos_phase(state, ArkhamRng(1), [])

        self.assertEqual(state.enemies[priest].location_id, state.investigator.location_id)
        self.assertEqual(state.enemies[priest].engaged_with, state.investigator.id)
        self.assertIn(priest, state.investigator.engaged_enemies)

    def test_gathering_act_2b_still_spawns_set_aside_priest_in_hallway(self) -> None:
        state = gathering.build_gathering_state(
            difficulty="standard",
            rng=ArkhamRng(2),
            deck_path=None,
            investigator_slug="roland",
        )
        state.decision_queue = []
        gathering.advance_act(state, [])
        state.locations["hallway"].investigator_ids.remove(state.investigator.id)
        state.investigator.location_id = "parlor"
        state.locations["parlor"].investigator_ids.append(state.investigator.id)

        gathering.advance_act(state, [])

        priest = "setaside_ghoul_priest"
        self.assertEqual(state.enemies[priest].location_id, "hallway")
        self.assertIsNone(state.enemies[priest].engaged_with)
        self.assertNotIn(priest, state.investigator.engaged_enemies)

    def test_another_enemy_without_spawn_instruction_engages_drawer(self) -> None:
        state = midnight_masks.build_state(
            difficulty="standard",
            rng=ArkhamRng(3),
            investigator_slug="roland",
        )
        state.decision_queue = []
        rat = "test_swarm_of_rats"
        state.card_instances[rat] = CardInstance(
            id=rat,
            card_code="01159",
            zone="encounter_deck",
        )
        state.encounter_deck = [rat]

        encounter.draw_encounter(state, ArkhamRng(3), [])

        self.assertEqual(state.enemies[rat].location_id, state.investigator.location_id)
        self.assertEqual(state.enemies[rat].engaged_with, state.investigator.id)
        self.assertIn(rat, state.investigator.engaged_enemies)


if __name__ == "__main__":
    unittest.main()
