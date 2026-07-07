from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from arkham import actions, encounter, phases, skill_test
from arkham.cards import player as player_cards
from arkham.effects import resolve_agnes_horror_reaction
from arkham.game import Game
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_gathering
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
    s.investigator.id = "agnes"
    s.investigator.name = "Agnes Baker"
    s.investigator.card_code = "01004"
    s.investigator.willpower = 5
    s.investigator.intellect = 2
    s.investigator.combat = 2
    s.investigator.agility = 3
    s.investigator.health = 6
    s.investigator.sanity = 8
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.investigator.engaged_enemies = []
    s.investigator.resources = 10
    s.investigator.actions_remaining = 3
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
        player_cards.setup_uses(s.card_instances[instance_id])
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


class PhaseV4Tests(unittest.TestCase):
    def test_agnes_new_default_deck_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Game.new(seed=4, difficulty="standard", deck_path=None, run_dir=Path(tmp) / "run", investigator="agnes")
            self.assertEqual(game.state.investigator.id, "agnes")
            codes = [instance.card_code for instance in game.state.card_instances.values()]
            for code in {"01012", "01013", "01058", "01059", "01060", "01062", "01063", "01064", "01067", "01072", "01074", "01076"}:
                self.assertIn(code, codes)

    def test_dark_memory_end_turn_repeats_and_play_can_advance(self) -> None:
        s = state()
        memory = add_card(s, "01013")
        enemy = add_enemy(s)
        s.investigator.actions_remaining = 0
        phases.advance_until_decision(s, ArkhamRng(1), [])
        self.assertIn(memory, s.investigator.hand)
        self.assertEqual(s.investigator.horror, 2)
        self.assertEqual(s.decision_queue[0].id, "agnes-after-horror")
        resolve_agnes_horror_reaction(s, s.decision_queue.pop(0).options[0].payload, [])
        self.assertEqual(s.enemies[enemy].damage, 1)

        s.round = 2
        s.limits = {}
        phases.resolve_dark_memory_end_turn(s, [])
        self.assertEqual(s.investigator.horror, 4)

        s = state()
        memory = add_card(s, "01013")
        s.scenario = "the_gathering"
        s.agenda.code = "01105"
        s.agenda.doom = 2
        s.investigator.actions_remaining = 1
        actions.execute(s, {"kind": "action", "action": "play", "card": memory}, [], ArkhamRng(1))
        self.assertIn(memory, s.investigator.discard)
        self.assertEqual(s.decision_queue[0].id, "agenda1-back")

    def test_forbidden_knowledge_horror_resource_reaction_and_discard(self) -> None:
        s = state()
        knowledge = add_card(s, "01058", "play")
        enemy = add_enemy(s)
        events: list[dict] = []
        actions.resolve_fast_ability(s, {"ability": "forbidden_knowledge", "card": knowledge}, events)
        self.assertEqual(s.investigator.resources, 10)
        self.assertEqual(s.card_instances[knowledge].uses["secrets"], 4)
        self.assertEqual(s.investigator.horror, 1)
        resolve_agnes_horror_reaction(s, s.decision_queue.pop(0).options[0].payload, events)
        phases.advance_until_decision(s, ArkhamRng(1), events)
        self.assertEqual(s.investigator.resources, 11)
        self.assertEqual(s.card_instances[knowledge].uses["secrets"], 3)
        self.assertEqual(s.enemies[enemy].damage, 1)

        for _ in range(3):
            s.decision_queue = []
            s.card_instances[knowledge].exhausted = False
            actions.resolve_fast_ability(s, {"ability": "forbidden_knowledge", "card": knowledge}, events)
            if s.decision_queue:
                resolve_agnes_horror_reaction(s, s.decision_queue.pop(0).options[-1].payload, events)
                phases.advance_until_decision(s, ArkhamRng(1), events)
        self.assertIn(knowledge, s.investigator.discard)
        self.assertEqual(s.investigator.resources, 14)

    def test_shrivelling_uses_willpower_deals_bonus_damage_and_symbol_horror(self) -> None:
        s = state()
        shrivelling = add_card(s, "01060", "play")
        priest = add_enemy(s, "01116")
        s.investigator.actions_remaining = 1
        events = []
        actions.execute(
            s,
            {"kind": "action", "action": "asset_fight", "asset": shrivelling, "enemy": priest, "damage": 2, "skill": "willpower", "spend_use": "charges", "symbol_horror": True},
            events,
            SeqRng(["skull"]),
        )
        self.assertEqual(s.active_skill_test["skill"], "willpower")
        self.assertEqual(s.investigator.actions_remaining, 0)
        self.assertEqual(s.investigator.damage, 0)
        skill_test.finish_commit(s, SeqRng(["skull"]), events)
        self.assertEqual(s.card_instances[shrivelling].uses["charges"], 3)
        self.assertEqual(s.investigator.horror, 1)
        self.assertEqual(s.decision_queue[0].id, "agnes-after-horror")
        resolve_agnes_horror_reaction(s, s.decision_queue.pop(0).options[-1].payload, events)
        phases.advance_until_decision(s, ArkhamRng(1), events)
        self.assertEqual(s.enemies[priest].damage, 2)

    def test_baseball_bat_two_hands_and_discards_after_skull_success(self) -> None:
        s = state()
        bat = add_card(s, "01074", "play")
        knife = add_card(s, "01086")
        actions.play_card(s, knife, [])
        self.assertEqual(s.decision_queue[0].id, "slot-discard-for-play")
        self.assertTrue(any("Baseball Bat" in option.label for option in s.decision_queue[0].options))

        s = state()
        bat = add_card(s, "01074", "play")
        rat = add_enemy(s, "01159")
        s.investigator.actions_remaining = 1
        actions.execute(s, {"kind": "action", "action": "asset_fight", "asset": bat, "enemy": rat, "boost": 2, "damage": 2, "bat_discard_symbols": True}, [], SeqRng(["skull"]))
        skill_test.finish_commit(s, SeqRng(["skull"]), [])
        self.assertNotIn(rat, s.enemies)
        self.assertIn(bat, s.investigator.discard)

    def test_arcane_initiate_doom_and_spell_search(self) -> None:
        s = state()
        initiate = add_card(s, "01063")
        actions.play_card(s, initiate, [])
        self.assertEqual(s.card_instances[initiate].doom, 1)
        s.agenda.doom = 2
        the_gathering.check_agenda_advance(s, [], rng=ArkhamRng(1))
        self.assertEqual(s.decision_queue[0].id, "agenda1-back")
        the_gathering.set_agenda_2(s, [])
        self.assertEqual(s.card_instances[initiate].doom, 0)

        s = state()
        initiate = add_card(s, "01063", "play")
        shrivelling = add_card(s, "01060", "deck")
        cache = add_card(s, "01088", "deck")
        memory = add_card(s, "01013", "deck")
        actions.resolve_fast_ability(s, {"ability": "arcane_initiate", "card": initiate}, [])
        labels = [option.label for option in s.decision_queue[0].options]
        self.assertTrue(any("Shrivelling" in label for label in labels))
        self.assertTrue(any("Dark Memory" in label for label in labels))
        choice = next(option.payload for option in s.decision_queue[0].options if option.payload.get("card") == shrivelling)
        actions.resolve_arcane_initiate_choice(s, choice, [], SeqRng([]))
        self.assertIn(shrivelling, s.investigator.hand)
        self.assertIn(cache, s.investigator.deck)
        self.assertIn(memory, s.investigator.deck)

    def test_drawn_to_the_flame_resolves_encounter_then_discovers_clues(self) -> None:
        s = state()
        drawn = add_card(s, "01064")
        ward = add_card(s, "01065")
        remains = add_card(s, "01163", "encounter_deck")
        actions.execute(s, {"kind": "action", "action": "play", "card": drawn}, [], ArkhamRng(1))
        self.assertEqual(s.decision_queue[0].id, "revelation-cancel")
        encounter.resolve_ward_revelation(s, s.decision_queue.pop(0).options[0].payload, [], ArkhamRng(1))
        encounter.resolve_after_encounter_draw(s, [])
        self.assertIn(remains, s.encounter_discard)
        self.assertIn(ward, s.investigator.discard)
        self.assertEqual(s.investigator.clues, 2)

    def test_stray_cat_auto_evades_non_elite_only(self) -> None:
        s = state()
        cat = add_card(s, "01076", "play")
        minion = add_enemy(s, "01160", engaged=False)
        actions.resolve_fast_ability(s, {"ability": "stray_cat", "card": cat, "enemy": minion}, [])
        self.assertTrue(s.enemies[minion].exhausted)
        self.assertIsNone(s.enemies[minion].engaged_with)
        self.assertIn(cat, s.investigator.discard)

        s = state()
        cat = add_card(s, "01076", "play")
        add_enemy(s, "01116", engaged=False)
        options: list = []
        actions.add_fast_options(s, options, during_turn=True)
        self.assertFalse(any("Stray Cat" in option.label for option in options))

    def test_heirloom_draws_on_spell_play_not_commit_and_fearless_heals(self) -> None:
        s = state()
        heirloom = add_card(s, "01012", "play")
        shrivelling = add_card(s, "01060")
        draw = add_card(s, "01093", "deck")
        actions.play_card(s, shrivelling, [])
        self.assertEqual(s.decision_queue[0].id, "heirloom-reaction")
        actions.resolve_heirloom_reaction(s, s.decision_queue.pop(0).options[0].payload, [], SeqRng([]))
        self.assertIn(draw, s.investigator.hand)
        self.assertIn(heirloom, s.investigator.play_area)

        s = state()
        add_card(s, "01012", "play")
        shrivelling = add_card(s, "01060")
        skill_test.start(s, [], skill="combat", difficulty=1, source="commit test")
        skill_test.commit_card(s, {"card": shrivelling}, [])
        self.assertEqual(s.decision_queue[0].id, "commit-cards")

        s = state()
        s.investigator.horror = 2
        fearless = add_card(s, "01067")
        skill_test.start(s, [], skill="willpower", difficulty=1, source="Fearless test")
        skill_test.commit_card(s, {"card": fearless}, [])
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertEqual(s.investigator.horror, 1)


if __name__ == "__main__":
    unittest.main()
