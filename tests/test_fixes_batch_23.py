from __future__ import annotations

import unittest

from arkham import actions, effects, enemies, skill_test
from arkham.cards import player as player_cards
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_devourer_below as db
from arkham.scenarios import the_gathering as tg


class SeqRng:
    def __init__(self, values: list[str]) -> None:
        self.values = list(values)

    def choice(self, values):  # type: ignore[no-untyped-def]
        return self.values.pop(0) if self.values else values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def clear_state(state) -> None:  # type: ignore[no-untyped-def]
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
    state.investigator.actions_remaining = 3


def add_card(state, code: str, zone: str, card_id: str) -> str:  # type: ignore[no-untyped-def]
    state.card_instances[card_id] = CardInstance(
        id=card_id,
        card_code=code,
        zone=zone,
        owner=state.investigator.id,
    )
    if zone == "hand":
        state.investigator.hand.append(card_id)
    elif zone == "play":
        state.investigator.play_area.append(card_id)
        player_cards.setup_uses(state.card_instances[card_id])
    return card_id


def add_enemy(state, code: str, enemy_id: str, *, engaged: bool = True) -> str:  # type: ignore[no-untyped-def]
    location_id = state.investigator.location_id
    state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    state.enemies[enemy_id] = EnemyInstance(
        id=enemy_id,
        card_code=code,
        location_id=location_id,
        engaged_with=state.investigator.id if engaged else None,
    )
    state.locations[location_id].enemy_ids.append(enemy_id)
    if engaged:
        state.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


def move_to_lakeside(state) -> None:  # type: ignore[no-untyped-def]
    old_location = state.investigator.location_id
    location_id = next(location for location in state.locations if location != old_location)
    if state.investigator.id in state.locations[old_location].investigator_ids:
        state.locations[old_location].investigator_ids.remove(state.investigator.id)
    state.investigator.location_id = location_id
    state.locations[location_id].investigator_ids.append(state.investigator.id)
    state.locations[location_id].code = "50034"


class FixesBatch23Tests(unittest.TestCase):
    def test_147_engaged_mask_aloof_enemy_makes_aoo(self) -> None:
        state = db.build_return_state(
            difficulty="standard",
            rng=ArkhamRng(23),
            deck_path=None,
            investigator_slug="skids",
        )
        clear_state(state)
        card = add_card(state, "01020", "hand", "machete")
        enemy = add_enemy(state, "50042", "corpse_taker")
        mask = add_card(state, "50043", "attachment", "mask")
        state.enemies[enemy].attachments.append(mask)
        events: list[dict] = []

        actions.execute(state, {"kind": "action", "action": "play", "card": card}, events, ArkhamRng(23))

        self.assertTrue(enemies.is_aloof(state, enemy))
        self.assertEqual((state.investigator.damage, state.investigator.horror), (1, 2))
        self.assertTrue(any(event["type"] == "enemy_attack" for event in events))

    def test_148_skids_elder_sign_rider_honors_extra_token(self) -> None:
        state = db.build_return_state(
            difficulty="standard",
            rng=ArkhamRng(23),
            deck_path=None,
            investigator_slug="skids",
        )
        clear_state(state)
        move_to_lakeside(state)
        resources = state.investigator.resources

        skill_test.start(
            state,
            [],
            skill="intellect",
            difficulty=1,
            source="Investigate Lakeside",
            on_success={"kind": "investigate"},
        )
        skill_test.finish_commit(state, SeqRng(["0", "eldersign"]), [])

        self.assertEqual(state.limits["last_skill_test"]["extra_tokens"], ["eldersign"])
        self.assertEqual(state.investigator.resources, resources + 2)

    def test_148_wendy_amulet_auto_success_honors_extra_token(self) -> None:
        state = db.build_return_state(
            difficulty="standard",
            rng=ArkhamRng(23),
            deck_path=None,
            investigator_slug="wendy",
        )
        clear_state(state)
        move_to_lakeside(state)
        add_card(state, "01014", "play", "amulet")

        skill_test.start(
            state,
            [],
            skill="intellect",
            difficulty=99,
            source="Investigate Lakeside",
            on_success={"kind": "investigate"},
        )
        skill_test.finish_commit(state, SeqRng(["0", "eldersign"]), [])

        result = state.limits["last_skill_test"]
        self.assertEqual(result["extra_tokens"], ["eldersign"])
        self.assertTrue(result["auto_success"])
        self.assertEqual(result["difficulty"], 0)

    def test_151_colliding_damage_assignments_queue_without_loss(self) -> None:
        state = db.build_state(
            difficulty="standard",
            rng=ArkhamRng(23),
            investigator_slug="agnes",
        )
        clear_state(state)
        ally = add_card(state, "01018", "play", "beat_cop")
        add_enemy(state, "01180", "goat", engaged=False)
        events: list[dict] = []
        skill_test.start(state, events, skill="willpower", difficulty=1, source="Shrivelling")
        state.active_skill_test["symbol_horror"] = True

        skill_test.finish_commit(state, SeqRng(["tablet"]), events)

        self.assertEqual(state.pending_damage["source"], "Tablet token")
        self.assertEqual([item["source"] for item in state.pending_damage["queue"]], ["Shrivelling"])
        state.decision_queue.pop(0)
        effects.assign_damage_choice(
            state,
            {"kind": "assign_damage", "type": "damage", "target": ally},
            events,
            SeqRng([]),
        )
        self.assertEqual(state.pending_damage["source"], "Shrivelling")
        state.decision_queue.pop(0)
        effects.assign_damage_choice(
            state,
            {"kind": "assign_damage", "type": "horror", "target": ally},
            events,
            SeqRng([]),
        )

        self.assertEqual((state.card_instances[ally].damage, state.card_instances[ally].horror), (1, 1))
        self.assertIsNone(state.pending_damage)

    def test_146_149_fog_discard_is_single_log_and_evade_logs_exhaust(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(23))
        clear_state(state)
        fog = add_card(state, "01168", "attachment", "fog")
        state.locations[state.investigator.location_id].attached_instance_ids.append(fog)
        enemy = add_enemy(state, "01160", "ghoul")
        events: list[dict] = []

        skill_test.discard_obscuring_fog_at_roland(state, events)
        enemies.evade_enemy(state, events, enemy)

        fog_logs = [
            event
            for event in events
            if "Obscuring Fog" in event.get("message", "") and "discarded" in event.get("message", "")
        ]
        self.assertEqual(len(fog_logs), 1)
        self.assertIn("enemy_disengaged", [event["type"] for event in events])
        self.assertIn("enemy_exhausted", [event["type"] for event in events])


if __name__ == "__main__":
    unittest.main()
