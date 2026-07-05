from __future__ import annotations

import unittest

from arkham import actions, encounter, enemies
from arkham.cards import player as player_cards
from arkham.model import CardInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_midnight_masks as mm


def move_to(state, location_id: str, code: str | None = None) -> None:
    old = state.investigator.location_id
    if old in state.locations and state.investigator.id in state.locations[old].investigator_ids:
        state.locations[old].investigator_ids.remove(state.investigator.id)
    state.investigator.location_id = location_id
    if state.investigator.id not in state.locations[location_id].investigator_ids:
        state.locations[location_id].investigator_ids.append(state.investigator.id)
    if code is not None:
        state.locations[location_id].code = code
    state.locations[location_id].revealed = True
    state.locations[location_id].name = mm.location_revealed_name(state.locations[location_id].code)


def add_player_card(state, code: str, zone: str) -> str:
    card_id = f"test_{code}_{len(state.card_instances)}"
    state.card_instances[card_id] = CardInstance(id=card_id, card_code=code, zone=zone)
    if zone == "hand":
        state.investigator.hand.append(card_id)
    elif zone == "deck":
        state.investigator.deck.insert(0, card_id)
    elif zone == "play":
        state.investigator.play_area.append(card_id)
        player_cards.setup_uses(state.card_instances[card_id])
    return card_id


def add_enemy(state, code: str, location_id: str, *, engaged: bool = False) -> str:
    enemy_id = f"enemy_{code}_{len(state.card_instances)}"
    state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="encounter_drawn")
    enemies.spawn_enemy(state, [], instance_id=enemy_id, location_id=location_id, engaged=engaged)
    return enemy_id


class MidnightMasksLocationAbilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        self.state.decision_queue = []
        self.state.investigator.actions_remaining = 10
        self.events: list[dict] = []

    def option_actions(self) -> set[str]:
        return {str(option.payload.get("action")) for option in actions.legal_actions(self.state)}

    def test_your_house_draws_and_gains_once_per_turn(self) -> None:
        deck_count = len(self.state.investigator.deck)
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_your_house"}, self.events, ArkhamRng(2))
        self.assertEqual(len(self.state.investigator.deck), deck_count - 1)
        self.assertEqual(self.state.investigator.resources, 6)
        self.assertNotIn("midnight_location_your_house", self.option_actions())
        self.state.round += 1
        self.assertIn("midnight_location_your_house", self.option_actions())

    def test_historical_society_draws_three_once_per_game(self) -> None:
        move_to(self.state, "southside", "01126")
        deck_count = len(self.state.investigator.deck)
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_historical_society"}, self.events, ArkhamRng(3))
        self.assertEqual(len(self.state.investigator.deck), deck_count - 3)
        self.assertNotIn("midnight_location_historical_society", self.option_actions())

    def test_mas_boarding_house_searches_ally_and_consumes_on_miss(self) -> None:
        move_to(self.state, "southside", "01127")
        ally = add_player_card(self.state, "01032", "deck")
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_mas"}, self.events, ArkhamRng(4))
        mm.resolve_scenario_choice(self.state, self.state.decision_queue[0].options[0].payload, self.events, ArkhamRng(4))
        self.assertIn(ally, self.state.investigator.hand)
        self.assertNotIn("midnight_location_mas", self.option_actions())

        missed = mm.build_state(difficulty="standard", rng=ArkhamRng(5), investigator_slug="roland")
        missed.decision_queue = []
        missed.investigator.actions_remaining = 3
        move_to(missed, "southside", "01127")
        missed.investigator.deck = []
        actions.execute(missed, {"kind": "action", "action": "midnight_location_mas"}, [], ArkhamRng(5))
        self.assertTrue(missed.limits.get("midnight_location_limit:southside"))

    def test_st_marys_hospital_heals_damage_once_per_game(self) -> None:
        move_to(self.state, "st_marys_hospital", "01128")
        self.state.investigator.damage = 4
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_hospital"}, self.events, ArkhamRng(6))
        self.assertEqual(self.state.investigator.damage, 1)
        self.state.investigator.damage = 4
        self.assertNotIn("midnight_location_hospital", self.option_actions())

    def test_miskatonic_university_searches_top_six_repeatably(self) -> None:
        move_to(self.state, "miskatonic_university", "01129")
        tome = add_player_card(self.state, "01031", "deck")
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_university"}, self.events, ArkhamRng(7))
        mm.resolve_scenario_choice(self.state, self.state.decision_queue[0].options[0].payload, self.events, ArkhamRng(7))
        self.assertIn(tome, self.state.investigator.hand)
        self.assertIn("midnight_location_university", self.option_actions())

    def test_first_bank_gains_resources_once_per_game(self) -> None:
        move_to(self.state, "downtown", "01130")
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_bank"}, self.events, ArkhamRng(8))
        self.assertEqual(self.state.investigator.resources, 8)
        self.assertNotIn("midnight_location_bank", self.option_actions())

    def test_arkham_asylum_heals_horror_once_per_game(self) -> None:
        move_to(self.state, "downtown", "01131")
        self.state.investigator.horror = 4
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_asylum"}, self.events, ArkhamRng(9))
        self.assertEqual(self.state.investigator.horror, 1)
        self.state.investigator.horror = 4
        self.assertNotIn("midnight_location_asylum", self.option_actions())

    def test_easttown_discounts_ally_assets(self) -> None:
        move_to(self.state, "easttown", "01132")
        librarian = add_player_card(self.state, "01032", "hand")
        self.state.investigator.resources = 0
        play = next(option for option in actions.legal_actions(self.state) if option.payload.get("action") == "play" and option.payload.get("card") == librarian)
        self.assertIn("(0 res)", play.label)
        actions.execute(self.state, play.payload, self.events, ArkhamRng(10))
        self.assertIn(librarian, self.state.investigator.play_area)
        self.assertEqual(self.state.investigator.resources, 0)

    def test_northside_spends_resources_and_gains_clues_once_per_game(self) -> None:
        move_to(self.state, "northside", "01134")
        self.state.investigator.resources = 5
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_northside"}, self.events, ArkhamRng(11))
        self.assertEqual(self.state.investigator.resources, 0)
        self.assertEqual(self.state.investigator.clues, 2)
        self.assertNotIn("midnight_location_northside", self.option_actions())

    def test_police_station_adds_ammo_or_supplies_once_per_game(self) -> None:
        self.state.scenario = mm.RETURN_SCENARIO
        move_to(self.state, "easttown", "50027")
        gun = add_player_card(self.state, "01016", "play")
        payload = next(option.payload for option in actions.legal_actions(self.state) if option.payload.get("action") == "midnight_location_police")
        actions.execute(self.state, payload, self.events, ArkhamRng(12))
        self.assertEqual(self.state.card_instances[gun].uses["ammo"], 6)
        self.assertNotIn("midnight_location_police", self.option_actions())

    def test_train_station_moves_to_any_arkham_location_once_per_game(self) -> None:
        self.state.scenario = mm.RETURN_SCENARIO
        move_to(self.state, "northside", "50028")
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_train"}, self.events, ArkhamRng(13))
        payload = next(option.payload for option in self.state.decision_queue[0].options if option.payload.get("location") == "graveyard")
        mm.resolve_scenario_choice(self.state, payload, self.events, ArkhamRng(13))
        self.assertEqual(self.state.investigator.location_id, "graveyard")
        self.assertNotIn("midnight_location_train", self.option_actions())

    def test_museum_takes_horror_and_gains_clue_once_per_game(self) -> None:
        self.state.scenario = mm.RETURN_SCENARIO
        move_to(self.state, "miskatonic_university", "50029")
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_museum"}, self.events, ArkhamRng(14))
        self.assertEqual(self.state.investigator.horror, 2)
        self.assertEqual(self.state.investigator.clues, 1)
        self.assertNotIn("midnight_location_museum", self.option_actions())

    def test_warehouse_discards_willpower_card_to_remove_cultist_doom_once_per_game(self) -> None:
        self.state.scenario = mm.RETURN_SCENARIO
        move_to(self.state, "rivertown", "50030")
        card = add_player_card(self.state, "01031", "hand")
        cultist = add_enemy(self.state, "01169", "rivertown", engaged=True)
        self.state.enemies[cultist].doom = 2
        actions.execute(self.state, {"kind": "action", "action": "midnight_location_warehouse"}, self.events, ArkhamRng(15))
        mm.resolve_scenario_choice(self.state, self.state.decision_queue[0].options[0].payload, self.events, ArkhamRng(15))
        self.assertNotIn(card, self.state.investigator.hand)
        self.assertEqual(self.state.enemies[cultist].doom, 1)
        self.assertNotIn("midnight_location_warehouse", self.option_actions())


class MidnightMasksHookTests(unittest.TestCase):
    def test_ghoul_priest_draw_redirects_to_your_house_when_present(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(20), investigator_slug="roland", ghoul_priest_alive=True)
        state.decision_queue = []
        priest = next(card_id for card_id in state.encounter_deck if state.card_instances[card_id].card_code == "01116")
        state.encounter_deck = [priest]
        encounter.draw_encounter(state, ArkhamRng(20), [])
        self.assertEqual(state.enemies[priest].location_id, "your_house")
        self.assertNotIn(priest, state.investigator.engaged_enemies)

    def test_ghoul_priest_default_spawns_engaged_when_house_burned(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(21), investigator_slug="roland", house_burned=True, ghoul_priest_alive=True)
        state.decision_queue = []
        priest = next(card_id for card_id in state.encounter_deck if state.card_instances[card_id].card_code == "01116")
        state.encounter_deck = [priest]
        encounter.draw_encounter(state, ArkhamRng(21), [])
        self.assertEqual(state.enemies[priest].location_id, state.investigator.location_id)
        self.assertIn(priest, state.investigator.engaged_enemies)

    def test_cunning_distraction_evades_ruth_forced_but_only_exhausts_others(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(22), investigator_slug="roland")
        state.decision_queue = []
        state.investigator.actions_remaining = 3
        state.investigator.resources = 5
        cunning = add_player_card(state, "01078", "hand")
        ruth = add_enemy(state, "01141", state.investigator.location_id, engaged=True)
        other = add_enemy(state, "01169", state.investigator.location_id, engaged=True)
        actions.execute(state, {"kind": "action", "action": "cunning_distraction", "card": cunning}, [], ArkhamRng(22))
        self.assertIn(ruth, state.victory_display)
        self.assertNotIn(ruth, state.enemies)
        self.assertIn(other, state.enemies)
        self.assertTrue(state.enemies[other].exhausted)
        self.assertIsNone(state.enemies[other].engaged_with)

    def test_peter_warren_spawn_at_investigator_location_engages_immediately(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(23), investigator_slug="roland")
        state.decision_queue = []
        move_to(state, "miskatonic_university", "01129")
        peter = next(card_id for card_id in state.limits["cultist_deck"] if state.card_instances[card_id].card_code == "01139")
        state.limits["cultist_deck"] = [peter]
        state.investigator.clues = 2
        mm.draw_from_cultist_deck(state, [])
        self.assertIn(peter, state.investigator.engaged_enemies)


if __name__ == "__main__":
    unittest.main()
