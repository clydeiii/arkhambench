from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from arkham import actions, phases, skill_test
from arkham.cards import player as player_cards
from arkham.game import Game
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state, finalize_result


class SeqRng:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = list(tokens)

    def choice(self, values):  # type: ignore[no-untyped-def]
        return self.tokens.pop(0) if self.tokens else values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def state():
    s = build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
    s.investigator.id = "skids"
    s.investigator.name = '"Skids" O\'Toole'
    s.investigator.card_code = "01003"
    s.investigator.willpower = 2
    s.investigator.intellect = 3
    s.investigator.combat = 3
    s.investigator.agility = 4
    s.investigator.health = 8
    s.investigator.sanity = 6
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
    elif zone == "threat":
        s.investigator.threat_area.append(instance_id)
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


class PhaseV3Tests(unittest.TestCase):
    def test_skids_new_default_deck_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Game.new(seed=3, difficulty="standard", deck_path=None, run_dir=Path(tmp) / "run", investigator="skids")
            self.assertEqual(game.state.investigator.id, "skids")
            codes = [instance.card_code for instance in game.state.card_instances.values()]
            for code in {"01010", "01011", "01044", "01045", "01047", "01049", "01050", "01052", "01053"}:
                self.assertIn(code, codes)

    def test_on_the_lam_suppresses_non_elite_attacks_and_expires(self) -> None:
        s = state()
        card = add_card(s, "01010")
        minion = add_enemy(s, "01160")
        actions.execute(s, {"kind": "action", "action": "fast_ability", "ability": "on_the_lam", "card": card}, [])
        actions.execute(s, {"kind": "action", "action": "resource"}, [], SeqRng(["0"]))
        self.assertEqual(s.investigator.damage, 0)
        self.assertFalse(s.enemies[minion].exhausted)

        s.phase = "Enemy"
        phases.run_enemy_phase(s, [], SeqRng(["0"]))
        self.assertEqual(s.investigator.damage, 0)
        self.assertFalse(s.enemies[minion].exhausted)

        priest = add_enemy(s, "01116")
        phases.run_enemy_phase(s, [], SeqRng(["0"]))
        self.assertEqual(s.investigator.damage, 2)
        self.assertEqual(s.investigator.horror, 2)
        self.assertTrue(s.enemies[priest].exhausted)

        s.phase = "Upkeep"
        s.enemies[priest].exhausted = True
        phases.advance_until_decision(s, ArkhamRng(1), [])
        self.assertFalse(any(str(key).startswith("on_the_lam:") for key in s.limits))

    def test_hospital_debts_banking_limit_and_xp_penalty(self) -> None:
        s = state()
        debt = add_card(s, "01011", "threat")
        for _ in range(3):
            actions.resolve_fast_ability(s, {"ability": "hospital_debts", "card": debt}, [])
        self.assertEqual(s.card_instances[debt].uses["resources"], 2)
        self.assertEqual(s.investigator.resources, 8)

        finalize_result(s, [], outcome="R3", resolution="R3", summary="killed")
        self.assertEqual(s.result["xp"], 0)
        self.assertEqual(s.result["hospital_debts_xp_penalty"], 2)

        s = state()
        debt = add_card(s, "01011", "threat")
        s.card_instances[debt].uses["resources"] = 6
        finalize_result(s, [], outcome="R2", resolution="R2", summary="stand")
        self.assertEqual(s.result["hospital_debts_xp_penalty"], 0)

    def test_burglary_replaces_clues_exhausts_and_provokes_aoo(self) -> None:
        s = state()
        s.investigator.resources = 0
        burglary = add_card(s, "01045", "play")
        add_enemy(s, "01160")
        clues = s.locations[s.investigator.location_id].clues
        actions.execute(s, {"kind": "action", "action": "burglary", "asset": burglary}, [], SeqRng(["0"]))
        self.assertEqual(s.investigator.damage, 1)
        self.assertEqual(s.investigator.horror, 1)
        self.assertTrue(s.card_instances[burglary].exhausted)
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertEqual(s.investigator.resources, 3)
        self.assertEqual(s.locations[s.investigator.location_id].clues, clues)
        self.assertEqual(s.investigator.clues, 0)

    def test_switchblade_fast_play_and_succeed_by_damage(self) -> None:
        s = state()
        blade = add_card(s, "01044")
        actions.execute(s, {"kind": "action", "action": "fast_ability", "ability": "play_fast_asset", "card": blade}, [])
        self.assertEqual(s.investigator.actions_remaining, 3)
        self.assertEqual(s.investigator.resources, 9)
        self.assertIn(blade, s.investigator.play_area)

        rat = add_enemy(s, "01159")
        actions.execute(s, {"kind": "action", "action": "asset_fight", "asset": blade, "enemy": rat, "boost": 0, "damage": 1, "succeed_by": 2, "bonus_damage": 1}, [])
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertNotIn(rat, s.enemies)

    def test_elusive_disengages_and_moves_to_revealed_empty_location(self) -> None:
        s = state()
        card = add_card(s, "01050")
        first = add_enemy(s, "01160")
        second = add_enemy(s, "01159")
        events: list = []
        actions.execute(s, {"kind": "action", "action": "fast_ability", "ability": "elusive", "card": card, "location": "hallway"}, events)
        played = [e for e in events if e.get("type") == "event_played"]
        self.assertTrue(played and s.investigator.name in played[0]["message"])
        self.assertEqual(s.investigator.location_id, "hallway")
        self.assertEqual(s.investigator.damage, 0)
        self.assertFalse(s.investigator.engaged_enemies)
        self.assertIsNone(s.enemies[first].engaged_with)
        self.assertIsNone(s.enemies[second].engaged_with)
        self.assertFalse(s.enemies[first].exhausted)
        self.assertFalse(s.enemies[second].exhausted)

    def test_sneak_attack_targets_exhausted_enemy_and_provokes_aoo(self) -> None:
        s = state()
        card = add_card(s, "01052")
        exhausted = add_enemy(s, "01159", engaged=False, exhausted=True)
        ready = add_enemy(s, "01160")
        labels = [option.label for option in actions.legal_actions(s)]
        self.assertTrue(any("Sneak Attack" in label and "Swarm of Rats" in label for label in labels))
        self.assertFalse(any("Sneak Attack" in label and "Ghoul Minion" in label for label in labels))
        actions.execute(s, {"kind": "action", "action": "sneak_attack", "card": card, "enemy": exhausted}, [], SeqRng(["0"]))
        self.assertEqual(s.investigator.damage, 1)
        self.assertEqual(s.investigator.horror, 1)
        self.assertIn(ready, s.enemies)
        self.assertNotIn(exhausted, s.enemies)

    def test_opportunist_returns_only_on_succeed_by_three(self) -> None:
        s = state()
        opp = add_card(s, "01053")
        skill_test.start(s, [], skill="intellect", difficulty=1, source="test")
        skill_test.commit_card(s, {"card": opp}, [])
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertIn(opp, s.investigator.hand)

        s = state()
        opp = add_card(s, "01053")
        skill_test.start(s, [], skill="intellect", difficulty=2, source="test")
        skill_test.commit_card(s, {"card": opp}, [])
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertIn(opp, s.investigator.discard)

    def test_derringer_ammo_label_and_succeed_by_damage(self) -> None:
        s = state()
        derringer = add_card(s, "01047", "play")
        s.card_instances[derringer].uses["ammo"] = 1
        ghoul = add_enemy(s, "01160")
        labels = [option.label for option in actions.legal_actions(s)]
        self.assertTrue(any(".41 Derringer" in label and "Combat(5)" in label for label in labels))
        actions.execute(s, {"kind": "action", "action": "asset_fight", "asset": derringer, "enemy": ghoul, "boost": 2, "damage": 1, "succeed_by": 2, "bonus_damage": 1}, [])
        self.assertEqual(s.card_instances[derringer].uses["ammo"], 0)
        skill_test.finish_commit(s, SeqRng(["0"]), [])
        self.assertNotIn(ghoul, s.enemies)
        labels = [option.label for option in actions.legal_actions(s)]
        self.assertFalse(any(".41 Derringer" in label for label in labels))


if __name__ == "__main__":
    unittest.main()


class ElusiveDestinationTests(unittest.TestCase):
    def test_elusive_never_offers_current_location_or_no_op_play(self) -> None:
        from arkham import actions
        from arkham.scenarios import the_gathering as tg
        from arkham.rng import ArkhamRng

        s = tg.build_return_state(difficulty="standard", rng=ArkhamRng(5))
        s.decision_queue = []
        s.limits.pop("mulligan_available", None)
        s.investigator.card_code = "01003"
        s.investigator.hand = []
        s.investigator.resources = 5
        elusive = "elusive_test"
        from arkham.model import CardInstance

        s.card_instances[elusive] = CardInstance(id=elusive, card_code="01050", zone="hand", owner=s.investigator.id)
        s.investigator.hand.append(elusive)

        # Study is the only revealed location and Skids stands on it with no
        # enemies engaged: Elusive has no legal effect and must not be offered.
        labels = [o.label for o in actions.legal_actions(s) if "Elusive" in o.label]
        self.assertEqual(labels, [])
        self.assertNotIn("study", actions.elusive_destinations(s))

        # With another revealed, enemy-free location it is offered — but never
        # to the current location.
        tg.reveal_location(s, [], "guest_hall")
        labels = [o.label for o in actions.legal_actions(s) if "Elusive" in o.label]
        self.assertEqual(labels, ["Play Elusive and move to Guest Hall"])
