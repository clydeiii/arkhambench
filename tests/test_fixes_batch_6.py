from __future__ import annotations

import unittest

from arkham import actions
from arkham.cards import player as player_cards
from arkham.effects import assign_damage_choice, start_damage_assignment
from arkham.model import CardInstance, EnemyInstance, GameState
from arkham.rng import ArkhamRng
from arkham.scenarios import the_gathering as tg


def state(seed: int = 1):
    s = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(seed))
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.investigator.engaged_enemies = []
    s.investigator.resources = 10
    s.investigator.damage = 0
    s.investigator.horror = 0
    s.investigator.actions_remaining = 3
    s.turn.action_index = 0
    s.decision_queue = []
    s.chaos_bag.tokens = ["0"]
    return s


def add_card(s, code: str, zone: str = "hand", instance_id: str | None = None) -> str:
    instance_id = instance_id or f"{code}_{len(s.card_instances)}"
    s.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone=zone, owner=s.investigator.id)
    if zone == "hand":
        s.investigator.hand.append(instance_id)
    elif zone == "play":
        s.investigator.play_area.append(instance_id)
        player_cards.setup_uses(s.card_instances[instance_id])
    elif zone == "discard":
        s.investigator.discard.append(instance_id)
    return instance_id


def add_enemy(s, code: str = "01159", instance_id: str = "enemy") -> str:
    s.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="enemy")
    s.enemies[instance_id] = EnemyInstance(id=instance_id, card_code=code, location_id=s.investigator.location_id, engaged_with=s.investigator.id)
    s.locations[s.investigator.location_id].enemy_ids.append(instance_id)
    s.investigator.engaged_enemies.append(instance_id)
    return instance_id


class PlayCostTimingTests(unittest.TestCase):
    def test_play_resource_cost_is_paid_before_aoo_and_not_double_charged(self) -> None:
        s = state()
        dark_memory = add_card(s, "01013")
        beat_cop = add_card(s, "01018", "play", "beat_cop")
        add_enemy(s, "01159", "rat")
        events: list[dict] = []

        actions.execute(s, {"kind": "action", "action": "play", "card": dark_memory}, events, ArkhamRng(1))

        self.assertEqual(s.investigator.resources, 8)
        self.assertIsNotNone(s.pending_damage)
        self.assertIn(dark_memory, s.investigator.hand)

        s.decision_queue.pop(0)
        assign_damage_choice(s, {"kind": "assign_damage", "type": "damage", "target": beat_cop}, events, ArkhamRng(1))

        self.assertEqual(s.investigator.resources, 8)
        self.assertIn(dark_memory, s.investigator.discard)
        self.assertTrue(any(event["type"] == "doom_placed" for event in events))


class LeoDeLucaActionTests(unittest.TestCase):
    def test_leo_discard_only_claws_back_unspent_bonus_action(self) -> None:
        s = state()
        leo = add_card(s, "01048", "play", "leo")
        s.investigator.actions_remaining = 4
        s.turn.action_index = 0

        player_cards.discard_from_play(s, leo)

        self.assertEqual(s.investigator.actions_remaining, 3)

    def test_leo_discard_does_not_claw_back_after_action_taken(self) -> None:
        s = state()
        leo = add_card(s, "01048", "play", "leo")
        s.investigator.actions_remaining = 2
        s.turn.action_index = 2

        player_cards.discard_from_play(s, leo)

        self.assertEqual(s.investigator.actions_remaining, 2)


class SimultaneousDamageAssignmentTests(unittest.TestCase):
    def test_damage_and_horror_from_one_source_can_both_be_assigned_to_leo(self) -> None:
        s = state()
        s.investigator.id = "wendy"
        s.investigator.name = "Wendy Adams"
        s.investigator.card_code = "01005"
        leo = add_card(s, "01048", "play", "leo")
        s.card_instances[leo].damage = 1
        s.card_instances[leo].horror = 1
        s.investigator.actions_remaining = 2
        s.turn.action_index = 1
        events: list[dict] = []

        start_damage_assignment(s, events, source="Grave-Eater", damage=1, horror=1)
        s.decision_queue.pop(0)
        assign_damage_choice(s, {"kind": "assign_damage", "type": "damage", "target": leo}, events)

        self.assertIn(leo, s.investigator.play_area)
        self.assertEqual(s.card_instances[leo].damage, 1)
        self.assertTrue(any(option.payload.get("target") == leo and option.payload.get("type") == "horror" for option in s.decision_queue[0].options))

        s.decision_queue.pop(0)
        assign_damage_choice(s, {"kind": "assign_damage", "type": "horror", "target": leo}, events)

        self.assertIn(leo, s.investigator.discard)
        self.assertEqual(s.card_instances[leo].damage, 2)
        self.assertEqual(s.card_instances[leo].horror, 2)
        self.assertEqual(s.investigator.actions_remaining, 2)
        self.assertEqual(s.investigator.damage, 0)
        self.assertEqual(s.investigator.horror, 0)

    def test_pending_damage_allocation_survives_save_load(self) -> None:
        s = state()
        leo = add_card(s, "01048", "play", "leo")
        s.card_instances[leo].damage = 1
        s.card_instances[leo].horror = 1
        events: list[dict] = []

        start_damage_assignment(s, events, source="Grave-Eater", damage=1, horror=1)
        s.decision_queue.pop(0)
        assign_damage_choice(s, {"kind": "assign_damage", "type": "damage", "target": leo}, events)
        loaded = GameState.from_dict(s.to_dict())

        loaded.decision_queue.pop(0)
        assign_damage_choice(loaded, {"kind": "assign_damage", "type": "horror", "target": leo}, events)

        self.assertIn(leo, loaded.investigator.discard)
        self.assertIsNone(loaded.pending_damage)


if __name__ == "__main__":
    unittest.main()
