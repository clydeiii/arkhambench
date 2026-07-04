from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from arkham import actions, phases, skill_test
from arkham.cards import player as player_cards
from arkham.effects import assign_damage_choice, resolve_player_weakness_draw, start_damage_assignment
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
    s.investigator.id = "wendy"
    s.investigator.name = "Wendy Adams"
    s.investigator.card_code = "01005"
    s.investigator.willpower = 4
    s.investigator.intellect = 3
    s.investigator.combat = 1
    s.investigator.agility = 4
    s.investigator.health = 7
    s.investigator.sanity = 7
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.investigator.engaged_enemies = []
    s.investigator.resources = 10
    s.investigator.actions_remaining = 3
    for location in s.locations.values():
        location.investigator_ids = ["wendy" if investigator_id == "roland" else investigator_id for investigator_id in location.investigator_ids]
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
    elif zone == "discard":
        s.investigator.discard.append(instance_id)
    elif zone == "deck":
        s.investigator.deck.append(instance_id)
    return instance_id


def add_enemy(s, code: str = "01160", location: str = "study", engaged: bool = True, exhausted: bool = False) -> str:
    enemy_id = f"enemy_{len(s.enemies)}"
    s.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    s.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location, exhausted=exhausted)
    s.locations[location].enemy_ids.append(enemy_id)
    if engaged:
        s.enemies[enemy_id].engaged_with = s.investigator.id
        s.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


class PhaseV5Tests(unittest.TestCase):
    def test_wendy_new_default_deck_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Game.new(seed=5, difficulty="standard", deck_path=None, run_dir=Path(tmp) / "run", investigator="wendy")
            self.assertEqual(game.state.investigator.id, "wendy")
            codes = [instance.card_code for instance in game.state.card_instances.values()]
            for code in {"01014", "01015", "01046", "01048", "01051", "01073", "01075", "01077", "01078", "01079", "01081"}:
                self.assertIn(code, codes)

    def test_amulet_plays_only_top_discard_event_and_bottoms_played_events(self) -> None:
        s = state()
        add_card(s, "01014", "play")
        backstab = add_card(s, "01051", "discard")
        cache = add_card(s, "01088", "discard")
        labels = [option.label for option in actions.legal_actions(s)]
        self.assertTrue(any("Emergency Cache from discard" in label for label in labels))
        self.assertFalse(any("Backstab from discard" in label for label in labels))

        actions.execute(s, {"kind": "action", "action": "play", "card": cache}, [], SeqRng(["0"]))
        self.assertIn(cache, s.investigator.deck)
        self.assertNotIn(cache, s.investigator.discard)
        self.assertIn(backstab, s.investigator.discard)

        lucky = add_card(s, "01080", "hand")
        player_cards.discard_from_hand(s, lucky)
        self.assertIn(lucky, s.investigator.discard)

    def test_abandoned_and_alone_direct_horror_and_removed_discard(self) -> None:
        s = state()
        leo = add_card(s, "01048", "play")
        item = add_card(s, "01075", "discard")
        event = add_card(s, "01080", "discard")
        weakness = add_card(s, "01015", "hand")
        resolve_player_weakness_draw(s, [], weakness)
        self.assertEqual(s.investigator.horror, 2)
        self.assertEqual(s.card_instances[leo].horror, 0)
        self.assertIn(item, s.removed_from_game)
        self.assertIn(event, s.removed_from_game)
        self.assertNotIn(item, s.investigator.discard)
        self.assertEqual(s.investigator.discard, [weakness])

    def test_backstab_uses_agility_deals_three_and_is_aoo_exempt(self) -> None:
        s = state()
        backstab = add_card(s, "01051")
        ghoul = add_enemy(s, "01160")
        add_enemy(s, "01159")
        actions.execute(s, {"kind": "action", "action": "backstab", "card": backstab, "enemy": ghoul}, [], SeqRng(["0"]))
        self.assertEqual(s.investigator.damage, 0)
        self.assertEqual(s.investigator.horror, 0)
        self.assertEqual(s.active_skill_test["skill"], "agility")
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertNotIn(ghoul, s.enemies)
        self.assertIn(backstab, s.investigator.discard)

    def test_look_what_i_found_and_rabbits_foot_share_after_fail_window(self) -> None:
        s = state()
        add_card(s, "01075", "play")
        look = add_card(s, "01079")
        draw = add_card(s, "01092", "deck")
        s.locations[s.investigator.location_id].clues = 1
        skill_test.start(s, [], skill="intellect", difficulty=4, source="Investigate Study", on_failure={"kind": "investigate"})
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertEqual(s.decision_queue[0].id, "wendy-token-reaction")
        skill_test.resolve_wendy_token_reaction(s, s.decision_queue.pop(0).options[-1].payload, [], SeqRng(["0"]))
        labels = [option.label for option in s.decision_queue[0].options]
        self.assertTrue(any("Rabbit" in label for label in labels))
        self.assertTrue(any("Look what I found" in label for label in labels))

        rabbit_payload = next(option.payload for option in s.decision_queue.pop(0).options if option.payload.get("reaction") == "rabbit")
        skill_test.resolve_after_fail_reaction(s, rabbit_payload, [], SeqRng(["0"]))
        self.assertIn(draw, s.investigator.hand)
        look_payload = next(option.payload for option in s.decision_queue.pop(0).options if option.payload.get("reaction") == "look")
        skill_test.resolve_after_fail_reaction(s, look_payload, [], SeqRng(["0"]))
        self.assertEqual(s.investigator.clues, 1)
        self.assertEqual(s.locations[s.investigator.location_id].clues, 0)
        self.assertIn(look, s.investigator.discard)

    def test_survival_instinct_disengages_others_and_moves_optionally(self) -> None:
        s = state()
        survival = add_card(s, "01081")
        target = add_enemy(s, "01160")
        other = add_enemy(s, "01159")
        skill_test.start(s, [], skill="agility", difficulty=1, source="Evade Ghoul Minion", on_success={"kind": "evade", "enemy": target})
        skill_test.commit_card(s, {"card": survival}, [])
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertEqual(s.decision_queue[0].id, "survival-instinct")
        payload = next(option.payload for option in s.decision_queue.pop(0).options if option.payload.get("disengage") and option.payload.get("location") == "hallway")
        skill_test.resolve_survival_instinct(s, payload, [])
        self.assertTrue(s.enemies[target].exhausted)
        self.assertIsNone(s.enemies[other].engaged_with)
        self.assertFalse(s.enemies[other].exhausted)
        self.assertEqual(s.investigator.location_id, "hallway")

    def test_leo_de_luca_grants_fourth_action_and_soaks(self) -> None:
        s = state()
        leo = add_card(s, "01048")
        actions.execute(s, {"kind": "action", "action": "play", "card": leo}, [], SeqRng(["0"]))
        self.assertEqual(s.investigator.actions_remaining, 3)
        self.assertEqual(phases.starting_actions(s), 4)
        start_damage_assignment(s, [], source="test", damage=0, horror=2)
        assign_damage_choice(s, {"type": "horror", "target": leo}, [])
        assign_damage_choice(s, {"type": "horror", "target": leo}, [])
        self.assertIn(leo, s.investigator.discard)

    def test_pickpocketing_fires_on_evade_and_cunning_not_elusive(self) -> None:
        s = state()
        pick = add_card(s, "01046", "play")
        draw = add_card(s, "01092", "deck")
        enemy = add_enemy(s, "01160")
        skill_test.start(s, [], skill="agility", difficulty=1, source="Evade Ghoul Minion", on_success={"kind": "evade", "enemy": enemy})
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertEqual(s.decision_queue[0].id, "pickpocketing-reaction")
        actions.resolve_pickpocketing_reaction(s, s.decision_queue.pop(0).options[0].payload, [], SeqRng(["0"]))
        self.assertIn(draw, s.investigator.hand)

        s.card_instances[pick].exhausted = False
        cunning = add_card(s, "01078")
        add_enemy(s, "01159", engaged=False)
        actions.execute(s, {"kind": "action", "action": "cunning_distraction", "card": cunning}, [], SeqRng(["0"]))
        self.assertEqual(s.decision_queue[0].id, "pickpocketing-reaction")

        s = state()
        add_card(s, "01046", "play")
        elusive = add_card(s, "01050")
        add_enemy(s, "01160")
        actions.resolve_fast_ability(s, {"ability": "elusive", "card": elusive, "location": "hallway"}, [])
        self.assertFalse(s.decision_queue)


if __name__ == "__main__":
    unittest.main()
