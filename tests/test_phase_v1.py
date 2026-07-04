from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from arkham import actions, encounter, skill_test
from arkham.effects import resolve_agnes_horror_reaction, resolve_amnesia_keep, start_damage_assignment
from arkham.errors import EngineError
from arkham.game import Game
from arkham.log import status_line
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


class SeqRng:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = list(tokens)

    def choice(self, values):  # type: ignore[no-untyped-def]
        return self.tokens.pop(0) if self.tokens else values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def state():
    s = build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.investigator.resources = 5
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
    elif zone == "threat":
        s.investigator.threat_area.append(instance_id)
    elif zone == "deck":
        s.investigator.deck.append(instance_id)
    elif zone == "encounter_deck":
        s.encounter_deck.append(instance_id)
    return instance_id


def add_enemy(s, code: str = "01160", location: str = "study", engaged: bool = True) -> str:
    enemy_id = f"enemy_{len(s.enemies)}"
    s.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    s.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location)
    s.locations[location].enemy_ids.append(enemy_id)
    if engaged:
        s.enemies[enemy_id].engaged_with = s.investigator.id
        s.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


class PhaseV1Tests(unittest.TestCase):
    def test_new_default_roland_killbray_and_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Game.new(seed=1, difficulty="standard", deck_path=None, run_dir=Path(tmp) / "run")
            s = game.state
            self.assertEqual(s.investigator.id, "roland")
            self.assertEqual(s.investigator.card_code, "01001")
            self.assertIn("Roland Banks 01001", status_line(s))
            codes = [instance.card_code for instance in s.card_instances.values()]
            self.assertEqual(sum(1 for code in codes if code in {"01006", "01007", "01102"}), 3)
            self.assertFalse(any(s.card_instances[card_id].card_code in {"01007", "01102"} for card_id in s.investigator.hand))
            self.assertEqual(len(s.investigator.hand) + len(s.investigator.deck), 33)

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(EngineError, "01008"):
                Game.new(seed=1, difficulty="standard", deck_path=None, run_dir=Path(tmp) / "run", investigator="daisy")

    def test_wendy_cancel_returns_token_to_bag_and_is_once_per_test(self) -> None:
        s = state()
        s.investigator.id = "wendy"
        s.investigator.name = "Wendy Adams"
        s.investigator.card_code = "01005"
        discard = add_card(s, "01093", "hand")
        skill_test.start(s, [], skill="agility", difficulty=4, source="test")
        skill_test.finish_commit(s, SeqRng(["-1", "-1"]), [])
        self.assertEqual(s.decision_queue[0].id, "wendy-token-reaction")
        before = list(s.chaos_bag.tokens)
        skill_test.resolve_wendy_token_reaction(s, s.decision_queue[0].options[0].payload, [], SeqRng(["-1"]))
        self.assertEqual(s.chaos_bag.tokens, before)
        self.assertIn(discard, s.investigator.discard)
        self.assertFalse(s.decision_queue)
        self.assertEqual(s.limits["last_skill_test"]["token"], "-1")

    def test_lucky_chain_and_autofail(self) -> None:
        s = state()
        lucky = add_card(s, "01080", "hand")
        skill_test.start(s, [], skill="intellect", difficulty=4, source="test")
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertEqual(s.decision_queue[0].id, "would-fail")
        skill_test.resolve_lucky_would_fail(s, {"choice": "play", "card": lucky}, [], None)
        self.assertTrue(s.limits["last_skill_test"]["success"])

        s = state()
        first = add_card(s, "01080", "hand")
        second = add_card(s, "01080", "hand")
        skill_test.start(s, [], skill="intellect", difficulty=7, source="test")
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        skill_test.resolve_lucky_would_fail(s, {"choice": "play", "card": first}, [], None)
        self.assertEqual(s.decision_queue[0].id, "would-fail")
        skill_test.resolve_lucky_would_fail(s, {"choice": "play", "card": second}, [], None)
        self.assertTrue(s.limits["last_skill_test"]["success"])

        s = state()
        lucky = add_card(s, "01080", "hand")
        skill_test.start(s, [], skill="intellect", difficulty=1, source="test")
        skill_test.finish_commit(s, SeqRng(["autofail"]), [])
        skill_test.resolve_lucky_would_fail(s, {"choice": "play", "card": lucky}, [], None)
        self.assertFalse(s.limits["last_skill_test"]["success"])

    def test_elder_sign_per_investigator(self) -> None:
        # Roland: +1 per clue on his location
        s = state()
        s.locations[s.investigator.location_id].clues = 2
        skill_test.start(s, [], skill="intellect", difficulty=5, source="test")
        skill_test.finish_commit(s, SeqRng(["eldersign"]), [])
        self.assertTrue(s.limits["last_skill_test"]["success"])

        # Skids: +2, gain 2 resources on success
        s = state()
        s.investigator.card_code = "01003"
        skill_test.start(s, [], skill="intellect", difficulty=5, source="test")
        skill_test.finish_commit(s, SeqRng(["eldersign"]), [])
        self.assertTrue(s.limits["last_skill_test"]["success"])
        self.assertEqual(s.investigator.resources, 7)

        # Agnes: +1 per horror on her
        s = state()
        s.investigator.card_code = "01004"
        s.investigator.horror = 4
        skill_test.start(s, [], skill="intellect", difficulty=7, source="test")
        skill_test.finish_commit(s, SeqRng(["eldersign"]), [])
        self.assertTrue(s.limits["last_skill_test"]["success"])

        # Daisy: +0, draw 1 card per controlled Tome on success
        s = state()
        s.investigator.card_code = "01002"
        add_card(s, "01031", "play")
        add_card(s, "01090", "deck")
        add_card(s, "01093", "deck")
        skill_test.start(s, [], skill="intellect", difficulty=3, source="test")
        skill_test.finish_commit(s, SeqRng(["eldersign"]), [])
        self.assertTrue(s.limits["last_skill_test"]["success"])
        self.assertEqual(len(s.investigator.hand), 1)

        # Wendy: +0, but auto-success with Wendy's Amulet in play
        s = state()
        s.investigator.card_code = "01005"
        add_card(s, "01014", "play")
        skill_test.start(s, [], skill="intellect", difficulty=9, source="test")
        skill_test.finish_commit(s, SeqRng(["eldersign"]), [])
        self.assertTrue(s.limits["last_skill_test"]["success"])

    def test_ward_cancels_nonweakness_treachery(self) -> None:
        s = state()
        ward = add_card(s, "01065", "hand")
        rot = add_card(s, "01163", "encounter_deck")
        s.encounter_deck = [rot]
        encounter.draw_encounter(s, ArkhamRng(1), [])
        self.assertEqual(s.decision_queue[0].id, "revelation-cancel")
        encounter.resolve_ward_revelation(s, s.decision_queue[0].options[0].payload, [], ArkhamRng(1))
        self.assertIn(ward, s.investigator.discard)
        self.assertIn(rot, s.encounter_discard)
        self.assertIsNone(s.active_skill_test)
        self.assertEqual(s.investigator.horror, 1)

    def test_agnes_after_horror_reaction_once_per_phase(self) -> None:
        s = state()
        s.investigator.id = "agnes"
        s.investigator.name = "Agnes Baker"
        s.investigator.card_code = "01004"
        enemy = add_enemy(s)
        start_damage_assignment(s, [], source="test", damage=0, horror=1)
        self.assertEqual(s.decision_queue[0].id, "agnes-after-horror")
        resolve_agnes_horror_reaction(s, s.decision_queue.pop(0).options[0].payload, [])
        self.assertEqual(s.enemies[enemy].damage, 1)
        start_damage_assignment(s, [], source="test", damage=0, horror=1)
        self.assertFalse(s.decision_queue)

    def test_daisy_tome_action_and_skids_buy_action(self) -> None:
        s = state()
        s.investigator.id = "daisy"
        s.investigator.name = "Daisy Walker"
        s.investigator.card_code = "01002"
        s.investigator.actions_remaining = 1
        book = add_card(s, "01031", "play")
        labels = [option.label for option in actions.legal_actions(s)]
        self.assertTrue(any("Old Book" in label for label in labels))
        self.assertFalse(any(label == "Draw 1 card" for label in labels))
        actions.execute(s, {"action": "old_book", "asset": book}, [])
        self.assertTrue(s.card_instances[book].exhausted)
        self.assertEqual(s.investigator.actions_remaining, 0)

        s = state()
        s.investigator.id = "skids"
        s.investigator.name = '"Skids" O\'Toole'
        s.investigator.card_code = "01003"
        s.investigator.actions_remaining = 0
        options: list = []
        actions.add_fast_options(s, options, during_turn=True)
        skids = next(option for option in options if "Skids" in option.label)
        actions.execute(s, skids.payload, [])
        self.assertEqual(s.investigator.resources, 3)
        self.assertEqual(s.investigator.actions_remaining, 1)
        options = []
        actions.add_fast_options(s, options, during_turn=True)
        self.assertFalse(any("Skids" in option.label for option in options))

    def test_basic_weaknesses(self) -> None:
        s = state()
        keep = add_card(s, "01088", "hand")
        discard = add_card(s, "01089", "hand")
        amnesia = add_card(s, "01096", "deck")
        from arkham.effects import draw_player_card

        draw_player_card(s, [])
        resolve_amnesia_keep(s, {"keep": keep}, [])
        self.assertIn(keep, s.investigator.hand)
        self.assertIn(discard, s.investigator.discard)
        self.assertIn(amnesia, s.investigator.discard)

        paranoia = add_card(s, "01097", "deck")
        s.investigator.resources = 4
        draw_player_card(s, [])
        self.assertIn(paranoia, s.investigator.discard)
        self.assertEqual(s.investigator.resources, 0)

        haunted = add_card(s, "01098", "deck")
        draw_player_card(s, [])
        self.assertIn(haunted, s.investigator.threat_area)
        self.assertEqual(actions.player_cards.effective_base_skill(s, "intellect", "test"), 2)
        s.investigator.actions_remaining = 2
        actions.execute(s, {"action": "discard_haunted", "card": haunted}, [])
        self.assertIn(haunted, s.investigator.discard)

        mob = add_card(s, "01101", "deck")
        s.investigator.resources = 4
        draw_player_card(s, [])
        self.assertIn(mob, s.investigator.engaged_enemies)
        s.investigator.actions_remaining = 1
        actions.execute(s, {"action": "parley_mob", "enemy": mob}, [])
        self.assertIn(mob, s.investigator.discard)


if __name__ == "__main__":
    unittest.main()
