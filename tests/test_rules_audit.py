from __future__ import annotations

import unittest

from arkham import actions, phases
from arkham.effects import place_doom
from arkham.game import Game
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_gathering
from arkham.scenarios.the_gathering import build_engine_test_state


def state(seed: int = 1):
    s = build_engine_test_state(difficulty="standard", rng=ArkhamRng(seed))
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.investigator.resources = 10
    s.chaos_bag.tokens = ["0"]
    s.decision_queue = []
    return s


def add_card(s, code: str, zone: str, instance_id: str) -> str:
    s.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone=zone)
    if zone == "hand":
        s.investigator.hand.append(instance_id)
    elif zone == "play":
        s.investigator.play_area.append(instance_id)
        from arkham.cards.player import setup_uses

        setup_uses(s.card_instances[instance_id])
    elif zone == "deck":
        s.investigator.deck.append(instance_id)
    return instance_id


def add_enemy(s, code: str, instance_id: str, *, engaged: bool = True, exhausted: bool = False, location: str = "study") -> str:
    s.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="enemy")
    s.enemies[instance_id] = EnemyInstance(id=instance_id, card_code=code, location_id=location, exhausted=exhausted)
    s.locations[location].enemy_ids.append(instance_id)
    if engaged:
        s.enemies[instance_id].engaged_with = "roland"
        s.investigator.engaged_enemies.append(instance_id)
    return instance_id


class RulesAuditRegressionTests(unittest.TestCase):
    def test_enemy_phase_attack_exhausts_but_aoo_and_retaliate_do_not(self) -> None:
        s = state()
        enemy = add_enemy(s, "01159", "rat")
        events = []

        from arkham.enemies import attack

        attack(s, events, enemy, source="enemy phase", rng=ArkhamRng(1))
        self.assertTrue(s.enemies[enemy].exhausted)

        s = state()
        enemy = add_enemy(s, "01159", "rat")
        attack(s, [], enemy, source="attack of opportunity", rng=ArkhamRng(1))
        self.assertFalse(s.enemies[enemy].exhausted)

        s = state()
        priest = add_enemy(s, "01116", "priest")
        attack(s, [], priest, source="retaliate", rng=ArkhamRng(1))
        self.assertFalse(s.enemies[priest].exhausted)

    def test_enemy_phase_and_aoo_attack_order_are_player_choices(self) -> None:
        s = state()
        add_enemy(s, "01159", "rat_a")
        add_enemy(s, "01159", "rat_b")
        s.phase = "Enemy"

        phases.run_enemy_phase(s, [], ArkhamRng(1))
        self.assertEqual(s.decision_queue[0].id, "enemy-attack-order")

        s = state()
        add_enemy(s, "01159", "rat_a")
        add_enemy(s, "01159", "rat_b")
        actions.execute(s, {"action": "draw"}, [], ArkhamRng(1))
        self.assertEqual(s.decision_queue[0].id, "aoo-attack-order")

    def test_doom_placement_requires_permission_to_advance_and_advance_clears_all_doom(self) -> None:
        s = state()
        s.agenda.doom = 2
        acolyte = add_enemy(s, "01160", "acolyte")
        s.enemies[acolyte].doom = 1

        place_doom(s, 1, [], source="Silver Twilight Acolyte", can_advance=False)
        self.assertEqual(s.agenda.stage, 1)

        the_gathering.check_agenda_advance(s, [])
        self.assertEqual(s.decision_queue[0].id, "agenda1-back")
        self.assertEqual(s.agenda.doom, 3)  # visible until the flip resolves
        the_gathering.set_agenda_2(s, [])
        self.assertEqual(s.agenda.doom, 0)
        self.assertEqual(s.enemies[acolyte].doom, 0)

    def test_upkeep_ready_engages_exhausted_enemy_at_rolands_location(self) -> None:
        s = state()
        enemy = add_enemy(s, "01159", "rat", engaged=False, exhausted=True)
        s.phase = "Upkeep"

        phases.run_upkeep_phase(s, [], ArkhamRng(1))

        self.assertFalse(s.enemies[enemy].exhausted)
        self.assertIn(enemy, s.investigator.engaged_enemies)

    def test_slots_unique_and_old_book_weakness_draw(self) -> None:
        s = state()
        add_card(s, "01020", "play", "machete")
        add_card(s, "01087", "play", "flashlight")
        add_card(s, "01031", "hand", "book")

        actions.play_card(s, "book", [])
        self.assertEqual(s.decision_queue[0].id, "slot-discard-for-play")
        payload = s.decision_queue[0].options[0].payload
        s.decision_queue = []
        actions.resolve_slot_discard(s, payload, [])
        self.assertIn("book", s.investigator.play_area)

        add_card(s, "01033", "play", "milan_a")
        add_card(s, "01033", "hand", "milan_b")
        self.assertFalse(actions.can_enter_play_unique(s, "01033"))
        actions.play_card(s, "milan_b", [])
        self.assertIn("milan_b", s.investigator.hand)

        s = state()
        book = add_card(s, "01031", "play", "book")
        cover = add_card(s, "01007", "deck", "cover")
        add_card(s, "01088", "deck", "cache")
        actions.old_book_of_lore(s, {"asset": book}, [])
        actions.resolve_old_book_choice(s, {"card": cover, "candidates": [cover, "cache"]}, [], ArkhamRng(1))
        self.assertIn(cover, s.investigator.threat_area)
        self.assertNotIn(cover, s.investigator.hand)

    def test_hard_cultist_token_recurses_until_non_cultist(self) -> None:
        class TokenRng:
            def __init__(self) -> None:
                self.tokens = ["cultist", "cultist", "0"]

            def choice(self, values):
                return self.tokens.pop(0)

        s = state()
        s.scenario = "the_gathering"
        s.difficulty = "hard"
        s.chaos_bag.tokens = ["cultist", "0"]
        events = []

        from arkham import skill_test

        skill_test.start(s, events, skill="willpower", difficulty=5, source="hard token")
        s.decision_queue = []
        skill_test.finish_commit(s, TokenRng(), events)  # type: ignore[arg-type]

        self.assertEqual(s.limits["last_skill_test"]["token"], "cultist")
        self.assertEqual(s.limits["last_skill_test"]["extra_tokens"], ["cultist", "0"])
        self.assertEqual(s.investigator.horror, 2)


if __name__ == "__main__":
    unittest.main()
