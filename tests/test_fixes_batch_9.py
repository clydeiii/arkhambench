from __future__ import annotations

import unittest

from arkham import actions, enemies
from arkham.cards import player as player_cards
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_devourer_below as db
from arkham.scenarios import the_gathering as tg
from arkham.scenarios import the_midnight_masks as mm


def clear_player_state(state) -> None:
    state.decision_queue = []
    state.investigator.hand = []
    state.investigator.deck = []
    state.investigator.discard = []
    state.investigator.play_area = []
    state.investigator.threat_area = []
    state.investigator.engaged_enemies = []
    state.investigator.resources = 10
    state.investigator.actions_remaining = 3
    state.turn.action_index = 0


def move_investigator_to(state, location_id: str) -> None:
    old = state.investigator.location_id
    if old in state.locations and state.investigator.id in state.locations[old].investigator_ids:
        state.locations[old].investigator_ids.remove(state.investigator.id)
    state.investigator.location_id = location_id
    if state.investigator.id not in state.locations[location_id].investigator_ids:
        state.locations[location_id].investigator_ids.append(state.investigator.id)


def add_player_card(state, code: str, zone: str = "hand", instance_id: str | None = None) -> str:
    instance_id = instance_id or f"{code}_{len(state.card_instances)}"
    state.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone=zone, owner=state.investigator.id)
    if zone == "hand":
        state.investigator.hand.append(instance_id)
    elif zone == "play":
        state.investigator.play_area.append(instance_id)
        player_cards.setup_uses(state.card_instances[instance_id])
    return instance_id


def add_enemy(state, code: str, *, enemy_id: str, engaged: bool = True) -> str:
    location_id = state.investigator.location_id
    state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    state.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location_id)
    state.locations[location_id].enemy_ids.append(enemy_id)
    if engaged:
        state.enemies[enemy_id].engaged_with = state.investigator.id
        state.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


def event_index(events: list[dict], event_type: str) -> int:
    return next(i for i, event in enumerate(events) if event["type"] == event_type)


class ActivationCostTimingTests(unittest.TestCase):
    def test_cultist_deck_clue_cost_is_paid_before_aoo(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="skids")
        clear_player_state(state)
        move_investigator_to(state, "miskatonic_university")
        state.investigator.clues = 2
        cultist = next(card_id for card_id in state.limits["cultist_deck"] if state.card_instances[card_id].card_code == "01139")
        state.limits["cultist_deck"] = [cultist]
        add_enemy(state, "01159", enemy_id="rat")
        events: list[dict] = []

        actions.execute(state, {"kind": "action", "action": "midnight_cultist_draw"}, events, ArkhamRng(1))

        self.assertEqual(state.investigator.clues, 0)
        self.assertLess(event_index(events, "clues_spent"), event_index(events, "enemy_attack"))
        self.assertLess(event_index(events, "enemy_attack"), event_index(events, "cultist_deck_draw"))

    def test_museum_horror_cost_can_defeat_before_effect_or_aoo(self) -> None:
        state = mm.build_return_state(difficulty="standard", rng=ArkhamRng(2), investigator_slug="skids")
        clear_player_state(state)
        move_investigator_to(state, "miskatonic_university")
        state.locations["miskatonic_university"].code = "50029"
        state.investigator.horror = 4
        state.investigator.clues = 0
        add_enemy(state, "01159", enemy_id="rat")
        events: list[dict] = []

        actions.execute(state, {"kind": "action", "action": "midnight_location_museum"}, events, ArkhamRng(2))

        self.assertEqual(state.status, "ended")
        self.assertEqual(state.investigator.clues, 0)
        self.assertFalse(any(event["type"] == "enemy_attack" for event in events))
        self.assertFalse(any(event["type"] == "clue_gained" for event in events))


class YithianObserverTests(unittest.TestCase):
    def test_yithian_observer_discards_before_attack_damage(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(3))
        clear_player_state(state)
        card = add_player_card(state, "01017", "hand", "physical_training")
        yithian = add_enemy(state, "01177", enemy_id="yithian")
        events: list[dict] = []

        enemies.attack(state, events, yithian, source="enemy phase", rng=ArkhamRng(3))

        self.assertNotIn(card, state.investigator.hand)
        self.assertIn(card, state.investigator.discard)
        self.assertLess(event_index(events, "card_discarded"), event_index(events, "damage_assigned"))
        damage, horror = enemies.enemy_damage_horror(state, yithian)
        self.assertEqual(state.investigator.damage, damage)
        self.assertEqual(state.investigator.horror, horror)

    def test_yithian_observer_empty_hand_deals_extra_damage_and_horror(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(4))
        clear_player_state(state)
        yithian = add_enemy(state, "01177", enemy_id="yithian")
        base_damage, base_horror = enemies.enemy_damage_horror(state, yithian)
        events: list[dict] = []

        enemies.attack(state, events, yithian, source="attack of opportunity", rng=ArkhamRng(4))

        self.assertTrue(any(event["type"] == "yithian_observer_forced" for event in events))
        self.assertEqual(state.investigator.damage, base_damage + 1)
        self.assertEqual(state.investigator.horror, base_horror + 1)


class SpawnEngagementTimingTests(unittest.TestCase):
    def test_devourer_agenda_dig_spawn_engages_before_later_resolution(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(5), investigator_slug="roland")
        clear_player_state(state)
        state.encounter_deck = ["monster"]
        state.encounter_discard = []
        state.card_instances["monster"] = CardInstance(id="monster", card_code="01160", zone="encounter_deck")
        state.agenda.doom = state.agenda.threshold
        events: list[dict] = []

        db.check_agenda_advance(state, events, rng=ArkhamRng(5))

        self.assertIn("monster", state.investigator.engaged_enemies)
        spawn_i = event_index(events, "enemy_spawned")
        engage_i = event_index(events, "enemy_engaged")
        advance_i = event_index(events, "agenda_advanced")
        self.assertEqual(engage_i, spawn_i + 1)
        self.assertLess(engage_i, advance_i)


if __name__ == "__main__":
    unittest.main()
