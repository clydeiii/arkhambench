from __future__ import annotations

import unittest

from arkham import actions, enemies, phases, skill_test
from arkham.cards import player as player_cards
from arkham.effects import assign_damage_choice
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_gathering as tg


class SeqRng:
    def choice(self, values):  # type: ignore[no-untyped-def]
        return values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def state(seed: int = 1):
    s = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(seed))
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.investigator.resources = 5
    s.investigator.damage = 0
    s.investigator.horror = 0
    s.decision_queue = []
    s.chaos_bag.tokens = ["0"]
    return s


def add_card(s, code: str, zone: str, instance_id: str) -> str:
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
    elif zone == "discard":
        s.investigator.discard.append(instance_id)
    return instance_id


def add_enemy(s, code: str, instance_id: str, *, engaged: bool = True) -> str:
    s.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="enemy")
    s.enemies[instance_id] = EnemyInstance(id=instance_id, card_code=code, location_id=s.investigator.location_id)
    s.locations[s.investigator.location_id].enemy_ids.append(instance_id)
    if engaged:
        s.enemies[instance_id].engaged_with = s.investigator.id
        s.investigator.engaged_enemies.append(instance_id)
    return instance_id


def event_count(events: list[dict], event_type: str) -> int:
    return sum(1 for event in events if event.get("type") == event_type)


class AooContinuationTests(unittest.TestCase):
    def test_no_decision_single_aoo_runs_action_effect_once(self) -> None:
        s = state()
        add_enemy(s, "01159", "rat")
        events: list[dict] = []

        actions.execute(s, {"kind": "action", "action": "resource"}, events, ArkhamRng(1))

        self.assertEqual(s.investigator.resources, 6)
        self.assertEqual(event_count(events, "resource_gained"), 1)

    def test_soak_decision_single_aoo_runs_action_effect_once(self) -> None:
        s = state()
        ally = add_card(s, "01018", "play", "beat_cop")
        add_enemy(s, "01159", "rat")
        events: list[dict] = []

        actions.execute(s, {"kind": "action", "action": "resource"}, events, ArkhamRng(1))
        self.assertEqual(event_count(events, "resource_gained"), 0)
        s.decision_queue.pop(0)
        assign_damage_choice(s, {"kind": "assign_damage", "type": "damage", "target": ally}, events, ArkhamRng(1))

        self.assertEqual(s.investigator.resources, 6)
        self.assertEqual(event_count(events, "resource_gained"), 1)

    def test_dodge_decision_single_aoo_runs_action_effect_once(self) -> None:
        s = state()
        dodge = add_card(s, "01023", "hand", "dodge")
        add_enemy(s, "01159", "rat")
        events: list[dict] = []

        actions.execute(s, {"kind": "action", "action": "resource"}, events, ArkhamRng(1))
        self.assertEqual(s.decision_queue[0].id, "enemy-attack")
        s.decision_queue.pop(0)
        enemies.cancel_pending_attack(s, events, dodge, ArkhamRng(1))

        self.assertEqual(s.investigator.resources, 5)  # +1 resource action, -1 Dodge
        self.assertEqual(event_count(events, "resource_gained"), 1)

    def test_dodge_then_second_aoo_runs_action_effect_once(self) -> None:
        s = state()
        dodge = add_card(s, "01023", "hand", "dodge")
        add_enemy(s, "01159", "rat_a")
        add_enemy(s, "01159", "rat_b")
        events: list[dict] = []

        actions.execute(s, {"kind": "action", "action": "resource"}, events, ArkhamRng(1))
        order = s.decision_queue[0].options[0].payload
        s.decision_queue = []
        actions.resolve_ordered_aoo(s, events, str(order["enemy"]), [str(eid) for eid in order["remaining"]], dict(order["action_payload"]), ArkhamRng(1))
        s.decision_queue.pop(0)
        enemies.cancel_pending_attack(s, events, dodge, ArkhamRng(1))

        self.assertEqual(s.investigator.resources, 5)
        self.assertEqual(event_count(events, "resource_gained"), 1)

    def test_defeat_reaction_defers_and_runs_action_effect_once(self) -> None:
        s = state()
        dog = add_card(s, "01021", "play", "guard_dog")
        add_enemy(s, "01159", "rat")
        s.locations[s.investigator.location_id].clues = 1
        events: list[dict] = []

        actions.execute(s, {"kind": "action", "action": "resource"}, events, ArkhamRng(1))
        s.decision_queue.pop(0)
        assign_damage_choice(s, {"kind": "assign_damage", "type": "damage", "target": dog}, events, ArkhamRng(1))
        self.assertEqual(s.decision_queue[0].id, "enemy-defeated-reactions")
        s.decision_queue.pop(0)
        enemies.resolve_enemy_defeated_reaction(s, {"kind": "enemy_defeated_reaction", "reaction": "done", "enemy": "rat"}, events)
        phases.advance_until_decision(s, ArkhamRng(1), events)

        self.assertEqual(s.investigator.resources, 6)
        self.assertEqual(event_count(events, "resource_gained"), 1)

    def test_dead_attacker_resume_runs_action_effect_once(self) -> None:
        s = state()
        events: list[dict] = []
        resume = {"kind": "action", "payload": {"kind": "action", "action": "resource", "skip_aoo": True, "cost_paid": True}}

        enemies.attack(s, events, "missing_attacker", source="attack of opportunity", resume=resume, rng=ArkhamRng(1))

        self.assertEqual(s.investigator.resources, 6)
        self.assertEqual(event_count(events, "resource_gained"), 1)

    def test_dead_attacker_in_aoo_order_is_skipped_before_resume_check(self) -> None:
        s = state()
        events: list[dict] = []
        resume = {
            "kind": "aoo_order",
            "remaining": ["missing_rat"],
            "action_payload": {"kind": "action", "action": "resource", "skip_aoo": True, "cost_paid": True},
        }

        actions.continue_aoo_order(s, events, resume, ArkhamRng(1))

        self.assertEqual(s.investigator.resources, 6)
        self.assertEqual(event_count(events, "resource_gained"), 1)


class DiscardOwnershipTests(unittest.TestCase):
    def test_threat_encounter_discards_to_encounter_and_weakness_to_player(self) -> None:
        s = state()
        dissonant = add_card(s, "01165", "threat", "dissonant")
        cover = add_card(s, "01007", "threat", "cover")

        player_cards.discard_from_threat(s, dissonant)
        player_cards.discard_from_threat(s, cover)

        self.assertIn(dissonant, s.encounter_discard)
        self.assertNotIn(dissonant, s.investigator.discard)
        self.assertIn(cover, s.investigator.discard)


class WeaknessAndSearchTests(unittest.TestCase):
    def test_research_librarian_is_optional_and_necronomicon_reveals_from_choice(self) -> None:
        s = state()
        s.investigator.card_code = "01002"
        librarian = add_card(s, "01032", "hand", "librarian")
        medical = add_card(s, "01035", "deck", "medical")
        necro = add_card(s, "01009", "deck", "necro")
        events: list[dict] = []

        actions.play_card(s, librarian, events, ArkhamRng(1))

        labels = [option.label for option in s.decision_queue[0].options]
        self.assertIn("Add Medical Texts to hand", labels)
        self.assertIn("Add The Necronomicon to hand", labels)
        self.assertIn("Decline", labels)
        self.assertIn(medical, s.investigator.deck)
        necro_payload = next(option.payload for option in s.decision_queue[0].options if option.payload.get("card") == necro)
        actions.resolve_research_librarian_choice(s, necro_payload, events, SeqRng())

        self.assertIn(necro, s.investigator.threat_area)
        self.assertEqual(s.card_instances[necro].horror, 3)
        self.assertNotIn(necro, s.investigator.hand)

    def test_scavenging_add_to_hand_resolves_weakness_revelation(self) -> None:
        s = state()
        scavenging = add_card(s, "01073", "play", "scavenging")
        necro = add_card(s, "01009", "discard", "necro")
        events: list[dict] = []

        skill_test.resolve_scavenging_reaction(
            s,
            {"kind": "scavenging_reaction", "choice": "take", "card": necro, "asset": scavenging},
            events,
        )

        self.assertIn(necro, s.investigator.threat_area)
        self.assertEqual(s.card_instances[necro].horror, 3)


class MulliganAndEndTurnTests(unittest.TestCase):
    def test_mulligan_replacements_draw_only_after_confirm(self) -> None:
        s = state()
        first = add_card(s, "01088", "hand", "cache_a")
        keep = add_card(s, "01089", "hand", "guts")
        replacement = add_card(s, "01090", "deck", "perception")
        weakness = add_card(s, "01096", "deck", "amnesia")
        s.limits["mulligan_available"] = [first, keep]
        tg.present_mulligan_decision(s)

        tg.resolve_scenario_choice(s, {"kind": "scenario", "choice": "toggle_mulligan_card", "card": first}, [], SeqRng())
        self.assertIn(first, s.investigator.hand)
        self.assertIn(replacement, s.investigator.deck)

        events: list[dict] = []
        tg.resolve_scenario_choice(s, {"kind": "scenario", "choice": "keep_hand"}, events, SeqRng())

        self.assertNotIn(first, s.investigator.hand)
        self.assertIn(keep, s.investigator.hand)
        self.assertIn(replacement, s.investigator.hand)
        self.assertIn(first, s.investigator.deck)
        self.assertIn(weakness, s.investigator.deck)

    def test_frozen_in_fear_test_fires_without_post_turn_fast_window(self) -> None:
        s = tg.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="skids")
        s.decision_queue = []
        s.investigator.actions_remaining = 0
        s.investigator.resources = 2
        frozen = "frozen"
        s.card_instances[frozen] = CardInstance(id=frozen, card_code="01164", zone="threat", owner=s.investigator.id)
        s.investigator.threat_area.append(frozen)
        events: list[dict] = []

        phases.advance_until_decision(s, ArkhamRng(1), events)

        self.assertFalse(s.decision_queue and s.decision_queue[0].id == "fast-window-inv_end")
        self.assertEqual(s.active_skill_test["source"], "Frozen in Fear")


if __name__ == "__main__":
    unittest.main()
