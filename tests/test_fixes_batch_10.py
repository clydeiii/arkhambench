from __future__ import annotations

import unittest

from arkham import actions, encounter, enemies
from arkham.cards import player as player_cards
from arkham.effects import resolve_defeat_trauma_choice, start_damage_assignment
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_devourer_below as db
from arkham.scenarios import the_gathering as tg
from arkham.scenarios import the_midnight_masks as mm


def clear_state(state) -> None:
    state.decision_queue = []
    state.active_skill_test = None
    state.pending_damage = None
    state.investigator.hand = []
    state.investigator.deck = []
    state.investigator.discard = []
    state.investigator.play_area = []
    state.investigator.threat_area = []
    state.investigator.engaged_enemies = []
    state.investigator.resources = 10


def add_enemy(state, code: str, enemy_id: str, *, engaged: bool = True) -> str:
    location_id = state.investigator.location_id
    state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    state.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location_id)
    state.locations[location_id].enemy_ids.append(enemy_id)
    if engaged:
        state.enemies[enemy_id].engaged_with = state.investigator.id
        state.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


def add_player_card(state, code: str, zone: str, card_id: str) -> str:
    state.card_instances[card_id] = CardInstance(id=card_id, card_code=code, zone=zone, owner=state.investigator.id)
    if zone == "deck":
        state.investigator.deck.append(card_id)
    elif zone == "play":
        state.investigator.play_area.append(card_id)
        player_cards.setup_uses(state.card_instances[card_id])
    return card_id


class FixesBatch10Tests(unittest.TestCase):
    def test_49_on_wings_assigns_damage_horror_before_then_movement(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        add_enemy(state, "01160", "ghoul")
        events: list[dict] = []

        mm.on_wings_aftermath(state, events, failed=True)

        event_types = [event["type"] for event in events]
        self.assertLess(event_types.index("damage_assigned"), event_types.index("enemy_disengaged"))
        self.assertLess(event_types.index("damage_assigned"), event_types.index("investigator_moved"))
        self.assertEqual((state.investigator.damage, state.investigator.horror), (1, 1))

    def test_50_card_driven_investigations_use_scenario_skill_hook(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(2), investigator_slug="roland")
        clear_state(state)
        location = state.locations[state.investigator.location_id]
        location.code = "01153"
        location.revealed = True
        location.shroud = 3
        flashlight = add_player_card(state, "01087", "play", "flashlight")

        actions.flashlight_investigate(state, {"asset": flashlight}, [])
        self.assertEqual(state.active_skill_test["skill"], "agility")

        state.active_skill_test = None
        location.code = "01154"
        burglary = add_player_card(state, "01045", "play", "burglary")
        actions.burglary_action(state, {"asset": burglary}, [])
        self.assertEqual(state.active_skill_test["skill"], "combat")

    def test_51_searches_offer_choice_for_multiple_distinct_names(self) -> None:
        gathering = tg.build_engine_test_state(difficulty="hard", rng=ArkhamRng(3))
        clear_state(gathering)
        gathering.encounter_deck = ["minion", "ravenous"]
        gathering.card_instances["minion"] = CardInstance(id="minion", card_code="01160", zone="encounter_deck")
        gathering.card_instances["ravenous"] = CardInstance(id="ravenous", card_code="01161", zone="encounter_deck")
        tg.search_and_draw_ghoul(gathering, [], ArkhamRng(3))
        self.assertEqual(gathering.decision_queue[0].id, "gathering-ghoul-search")
        self.assertEqual(len(gathering.decision_queue[0].options), 2)

        devourer = db.build_state(difficulty="hard", rng=ArkhamRng(4), investigator_slug="roland")
        clear_state(devourer)
        devourer.encounter_deck = ["yithian", "goat"]
        devourer.card_instances["yithian"] = CardInstance(id="yithian", card_code="01177", zone="encounter_deck")
        devourer.card_instances["goat"] = CardInstance(id="goat", card_code="01180", zone="encounter_deck")
        db.draw_monster_from_deck_or_discard(devourer, [], ArkhamRng(4))
        self.assertEqual(devourer.decision_queue[0].id, "devourer-monster-search")
        self.assertEqual(len(devourer.decision_queue[0].options), 2)

        masked = mm.build_state(difficulty="standard", rng=ArkhamRng(5), investigator_slug="roland")
        clear_state(masked)
        masked.encounter_deck = ["acolyte", "wizard"]
        masked.card_instances["acolyte"] = CardInstance(id="acolyte", card_code="01169", zone="encounter_deck")
        masked.card_instances["wizard"] = CardInstance(id="wizard", card_code="01170", zone="encounter_deck")
        chanting = "chanting"
        masked.card_instances[chanting] = CardInstance(id=chanting, card_code="01171", zone="encounter_drawn")
        mm.mysterious_chanting(masked, [], ArkhamRng(5), chanting)
        self.assertEqual(masked.decision_queue[0].id, "cultist-search")
        self.assertEqual(len(masked.decision_queue[0].options), 2)

    def test_52_offer_of_power_and_reachable_encounter_cards_are_not_placeholder(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(6), investigator_slug="roland")
        clear_state(state)
        state.agenda.threshold = 99
        add_player_card(state, "01089", "deck", "manual")
        add_player_card(state, "01090", "deck", "guts")
        offer = "offer"
        state.card_instances[offer] = CardInstance(id=offer, card_code="01178", zone="encounter_drawn")
        encounter.resolve_revelation(state, ArkhamRng(6), [], offer)
        offer_payload = state.decision_queue.pop(0).options[0].payload
        db.resolve_scenario_choice(state, offer_payload, [], ArkhamRng(6))
        self.assertEqual(len(state.investigator.hand), 2)
        self.assertEqual(state.agenda.doom, 2)

        scenario_codes = {
            "the_gathering": set(tg.ENCOUNTER_COUNTS) | {"01116"},
            "return_to_the_gathering": set(tg.RETURN_ENCOUNTER_COUNTS) | {"01116"},
            "the_midnight_masks": set(mm.ENCOUNTER_COUNTS) | set(mm.CORE_CULTISTS) | {"01116", "01121b"},
            "return_to_the_midnight_masks": set(mm.RETURN_ENCOUNTER_COUNTS) | set(mm.CORE_CULTISTS) | set(mm.RETURN_CULTISTS) | {"01116", "50026b"},
            "the_devourer_below": set(db.CORE_ENCOUNTER_COUNTS) | {code for counts in db.AGENT_SETS.values() for code in counts} | set(mm.CORE_CULTISTS) | {"01116", "01121b", "50026b"},
            "return_to_the_devourer_below": set(db.CORE_ENCOUNTER_COUNTS) | set(db.RETURN_COUNTS) | {code for counts in db.AGENT_SETS.values() for code in counts} | set(mm.CORE_CULTISTS) | set(mm.RETURN_CULTISTS) | {"01116", "01121b", "50026b"},
        }
        builders = {
            "the_gathering": tg.build_gathering_state,
            "return_to_the_gathering": tg.build_return_state,
            "the_midnight_masks": mm.build_state,
            "return_to_the_midnight_masks": mm.build_return_state,
            "the_devourer_below": db.build_state,
            "return_to_the_devourer_below": lambda **kwargs: db.build_return_state(deck_path=None, **kwargs),
        }
        for scenario, codes in scenario_codes.items():
            for code in sorted(codes):
                with self.subTest(scenario=scenario, code=code):
                    candidate = builders[scenario](difficulty="standard", rng=ArkhamRng(7), investigator_slug="roland")
                    clear_state(candidate)
                    candidate_id = "sweep"
                    candidate.card_instances[candidate_id] = CardInstance(id=candidate_id, card_code=code, zone="encounter_drawn")
                    events: list[dict] = []
                    encounter.resolve_revelation(candidate, ArkhamRng(7), events, candidate_id)
                    self.assertFalse(any("placeholder effect" in event["message"] for event in events))

    def test_53_duplicate_engaged_enemy_instances_each_attack_for_aoo(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(8))
        clear_state(state)
        state.investigator.deck = []
        add_player_card(state, "01089", "deck", "manual")
        add_enemy(state, "50038", "grave1")
        add_enemy(state, "50038", "grave2")
        events: list[dict] = []
        actions.attacks_of_opportunity(state, events, "draw", {"kind": "action", "action": "draw"}, ArkhamRng(8))

        first = state.decision_queue.pop(0).options[0].payload
        actions.resolve_ordered_aoo(state, events, first["enemy"], first["remaining"], first["action_payload"], ArkhamRng(8))
        attacks = [event for event in events if event["type"] == "enemy_attack"]
        self.assertEqual(len(attacks), 2)
        self.assertEqual({event["data"]["enemy"] for event in attacks}, {"grave1", "grave2"})

    def test_54_simultaneous_damage_horror_defeat_records_one_chosen_trauma(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(9))
        clear_state(state)
        state.investigator.damage = state.investigator.health - 1
        state.investigator.horror = state.investigator.sanity - 1

        start_damage_assignment(state, [], source="test", damage=1, horror=1, direct=True)

        self.assertEqual(state.decision_queue[0].id, "defeat-trauma-choice")
        self.assertEqual(state.trauma, {})
        resolve_defeat_trauma_choice(state, state.decision_queue[0].options[1].payload, [])
        self.assertEqual(state.trauma, {"mental": 1})
        self.assertEqual(state.status, "ended")


if __name__ == "__main__":
    unittest.main()
