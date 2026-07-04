from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from arkham import actions, skill_test
from arkham.effects import draw_player_card
from arkham.errors import EngineError
from arkham.game import Game
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
    s.investigator.id = "daisy"
    s.investigator.name = "Daisy Walker"
    s.investigator.card_code = "01002"
    s.investigator.willpower = 3
    s.investigator.intellect = 5
    s.investigator.combat = 2
    s.investigator.agility = 2
    s.investigator.health = 5
    s.investigator.sanity = 9
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.investigator.engaged_enemies = []
    s.investigator.resources = 10
    s.investigator.actions_remaining = 4
    s.decision_queue = []
    s.encounter_deck = []
    s.encounter_discard = []
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


class PhaseV2Tests(unittest.TestCase):
    def test_daisy_new_default_deck_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Game.new(seed=2, difficulty="standard", deck_path=None, run_dir=Path(tmp) / "run", investigator="daisy")
            self.assertEqual(game.state.investigator.id, "daisy")
            codes = [instance.card_code for instance in game.state.card_instances.values()]
            self.assertIn("01008", codes)
            self.assertIn("01009", codes)
            self.assertIn("01061", codes)
            self.assertIn("01066", codes)

    def test_unimplemented_deck_codes_still_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            deck_path = Path(tmp) / "deck.json"
            # 01026 Extra Ammunition (XP) is outside every killbray deck, so this
            # stays a valid unimplemented-code probe as phases V3-V5 land.
            deck_path.write_text(json.dumps({"investigator_code": "01001", "slots": {"01088": 2, "01026": 1}}))
            with self.assertRaisesRegex(EngineError, "01026"):
                Game.new(seed=1, difficulty="standard", deck_path=deck_path, run_dir=Path(tmp) / "run")

    def test_tote_slots_tomes_and_regular_hand_assets(self) -> None:
        s = state()
        add_card(s, "01008", "play", "tote")
        add_card(s, "01031", "play", "book")
        add_card(s, "01035", "play", "texts")
        add_card(s, "01087", "play", "flashlight")
        add_card(s, "01086", "play", "knife")
        third_regular = add_card(s, "01016", "hand", "auto")
        actions.play_card(s, third_regular, [])
        self.assertEqual(s.decision_queue[0].id, "slot-discard-for-play")
        labels = [option.label for option in s.decision_queue[0].options]
        self.assertTrue(any("Flashlight" in label for label in labels))
        self.assertTrue(any("Knife" in label for label in labels))
        self.assertFalse(any("Old Book" in label for label in labels))
        actions.resolve_slot_discard(s, s.decision_queue.pop(0).options[0].payload, [])
        self.assertIn(third_regular, s.investigator.play_area)

        from arkham.effects import discard_asset_choice

        discard_asset_choice(s, {"card": "tote"}, [])
        self.assertEqual(s.decision_queue[0].id, "slot-overflow-discard")

    def test_necronomicon_revelation_elder_sign_and_discard(self) -> None:
        s = state()
        necro = add_card(s, "01009", "deck", "necro")
        draw_player_card(s, [])
        self.assertIn(necro, s.investigator.threat_area)
        self.assertEqual(s.card_instances[necro].horror, 3)

        skill_test.start(s, [], skill="intellect", difficulty=1, source="test")
        skill_test.finish_commit(s, SeqRng(["eldersign"]), [])
        self.assertFalse(s.limits["last_skill_test"]["success"])
        self.assertTrue(s.limits["last_skill_test"]["modifier"] == 0)

        enemy = add_enemy(s, "01159")
        s.investigator.actions_remaining = 3
        for _ in range(3):
            actions.execute(s, {"action": "necronomicon", "asset": necro}, [], SeqRng(["0"]))
            while s.decision_queue and s.decision_queue[0].id == "assign-damage":
                s.decision_queue.pop(0)
        self.assertIn(necro, s.investigator.discard)
        self.assertEqual(s.investigator.horror, 3)
        self.assertEqual(s.investigator.damage, 3)
        self.assertLessEqual(s.investigator.actions_remaining, 0)
        self.assertIn(enemy, s.investigator.engaged_enemies)

    def test_scrying_encounter_reorders_and_enforces_costs(self) -> None:
        s = state()
        scrying = add_card(s, "01061", "play", "scrying")
        s.card_instances[scrying].uses["charges"] = 3
        evils = add_card(s, "01166", "encounter_deck", "evils")
        rot = add_card(s, "01163", "encounter_deck", "rot")
        hands = add_card(s, "01162", "encounter_deck", "hands")
        actions.execute(s, {"action": "scrying", "asset": scrying, "target": "encounter"}, [])
        self.assertEqual(s.decision_queue[0].id, "scrying-order")
        self.assertEqual(len(s.decision_queue[0].options), 6)
        self.assertIn("Ancient Evils", s.decision_queue[0].prompt)
        payload = next(option.payload for option in s.decision_queue[0].options if option.payload["order"] == [hands, rot, evils])
        actions.resolve_scrying_order(s, payload, [])
        self.assertEqual(s.encounter_deck[:3], [hands, rot, evils])
        self.assertTrue(s.card_instances[scrying].exhausted)
        self.assertEqual(s.card_instances[scrying].uses["charges"], 2)

    def test_blinding_light_uses_willpower_damages_and_loses_action(self) -> None:
        s = state()
        card = add_card(s, "01066", "hand", "blind")
        enemy = add_enemy(s, "01159")
        s.investigator.willpower = 4
        s.investigator.actions_remaining = 2
        actions.execute(s, {"action": "blinding_light", "card": card, "enemy": enemy}, [])
        self.assertEqual(s.active_skill_test["skill"], "willpower")
        self.assertEqual(s.investigator.actions_remaining, 1)
        skill_test.finish_commit(s, SeqRng(["skull"]), [])
        self.assertNotIn(enemy, s.investigator.engaged_enemies)
        self.assertNotIn(enemy, s.enemies)
        self.assertEqual(s.investigator.actions_remaining, 0)
        self.assertIn(card, s.investigator.discard)

    def test_daisy_tome_action_works_on_necronomicon(self) -> None:
        s = state()
        necro = add_card(s, "01009", "threat", "necro")
        s.card_instances[necro].horror = 1
        s.investigator.actions_remaining = 1
        labels = [option.label for option in actions.legal_actions(s)]
        self.assertTrue(any("Necronomicon" in label for label in labels))
        self.assertFalse(any(label == "Draw 1 card" for label in labels))


if __name__ == "__main__":
    unittest.main()
