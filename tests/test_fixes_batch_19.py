from __future__ import annotations

import unittest

from arkham import actions, encounter, enemies, skill_test
from arkham.cards import player as player_cards
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


def make_state():  # type: ignore[no-untyped-def]
    state = build_engine_test_state(difficulty="standard", rng=ArkhamRng(19))
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
    state.enemies = {}
    state.chaos_bag.tokens = ["0"]
    for location in state.locations.values():
        location.enemy_ids = []
    return state


def add_card(state, code: str, card_id: str, zone: str) -> str:  # type: ignore[no-untyped-def]
    state.card_instances[card_id] = CardInstance(
        id=card_id,
        card_code=code,
        zone=zone,
        owner=state.investigator.id,
    )
    if zone == "hand":
        state.investigator.hand.append(card_id)
    elif zone == "discard":
        state.investigator.discard.append(card_id)
    elif zone == "play":
        state.investigator.play_area.append(card_id)
        player_cards.setup_uses(state.card_instances[card_id])
    elif zone == "threat":
        state.investigator.threat_area.append(card_id)
    return card_id


def add_enemy(state, enemy_id: str = "ghoul") -> str:  # type: ignore[no-untyped-def]
    location_id = state.investigator.location_id
    state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code="01160", zone="enemy")
    state.enemies[enemy_id] = EnemyInstance(
        id=enemy_id,
        card_code="01160",
        location_id=location_id,
    )
    state.locations[location_id].enemy_ids.append(enemy_id)
    return enemy_id


def resolve_failing_test(state):  # type: ignore[no-untyped-def]
    events: list[dict] = []
    skill_test.start(
        state,
        events,
        skill="combat",
        difficulty=state.investigator.combat + 1,
        source="Dissonant Voices regression",
    )
    skill_test.finish_commit(state, ArkhamRng(19), events)
    return events


class DissonantSpecialWindowTests(unittest.TestCase):
    def test_lucky_in_hand_is_not_offered_and_test_fails_normally(self) -> None:
        state = make_state()
        lucky = add_card(state, "01080", "lucky", "hand")
        lucky_2 = add_card(state, "01084", "lucky2", "hand")
        add_card(state, "01165", "dissonant", "threat")

        resolve_failing_test(state)

        self.assertFalse(any(decision.id == "would-fail" for decision in state.decision_queue))
        self.assertFalse(state.limits["last_skill_test"]["success"])
        self.assertIsNone(state.active_skill_test)
        self.assertIn(lucky, state.investigator.hand)
        self.assertIn(lucky_2, state.investigator.hand)

    def test_lucky_on_amulet_discard_top_is_not_offered(self) -> None:
        state = make_state()
        add_card(state, "01014", "amulet", "play")
        lucky = add_card(state, "01080", "discard-lucky", "discard")
        add_card(state, "01165", "dissonant", "threat")

        resolve_failing_test(state)

        self.assertFalse(any(decision.id == "would-fail" for decision in state.decision_queue))
        self.assertFalse(state.limits["last_skill_test"]["success"])
        self.assertIn(lucky, state.investigator.discard)

    def test_ward_cancel_is_not_offered(self) -> None:
        state = make_state()
        add_card(state, "01065", "ward", "hand")
        add_card(state, "01165", "dissonant", "threat")
        treachery = add_card(state, "01163", "remains", "encounter_drawn")

        self.assertFalse(encounter.present_revelation_cancel(state, treachery))
        self.assertFalse(any(decision.id == "revelation-cancel" for decision in state.decision_queue))

    def test_other_special_event_windows_are_also_blocked(self) -> None:
        state = make_state()
        add_card(state, "01165", "dissonant", "threat")
        add_card(state, "01056", "sure-gamble", "hand")
        add_card(state, "01079", "look", "hand")
        add_card(state, "01023", "dodge", "hand")
        add_card(state, "01022", "evidence", "hand")
        add_card(state, "01083", "close-call", "hand")
        enemy_id = add_enemy(state)
        state.locations[state.investigator.location_id].clues = 1

        skill_test.start(state, [], skill="combat", difficulty=5, source="Sure Gamble audit")
        state.decision_queue = []
        state.active_skill_test["modifier"] = -1
        skill_test.present_token_reveal_reaction(state, ArkhamRng(19), [])
        self.assertFalse(state.decision_queue)
        self.assertEqual(skill_test.legal_look_what_i_found_cards(state), [])
        self.assertIsNone(enemies.legal_dodge_card(state))

        enemies.present_enemy_defeat_reactions(state, [], enemy_id)
        evidence_labels = [option.label for decision in state.decision_queue for option in decision.options]
        self.assertFalse(any("Evidence!" in label for label in evidence_labels))

        state.decision_queue = []
        actions.queue_close_call_reaction(state, enemy_id)
        self.assertFalse(state.decision_queue)

    def test_without_dissonant_all_special_event_offers_remain(self) -> None:
        state = make_state()
        lucky = add_card(state, "01080", "lucky", "hand")
        lucky_2 = add_card(state, "01084", "lucky2", "hand")
        add_card(state, "01014", "amulet", "play")
        discard_lucky = add_card(state, "01080", "discard-lucky", "discard")
        look = add_card(state, "01079", "look", "hand")
        sure_gamble = add_card(state, "01056", "sure-gamble", "hand")
        dodge = add_card(state, "01023", "dodge", "hand")
        add_card(state, "01022", "evidence", "hand")
        add_card(state, "01083", "close-call", "hand")
        add_card(state, "01065", "ward", "hand")
        treachery = add_card(state, "01163", "remains", "encounter_drawn")
        enemy_id = add_enemy(state)
        state.locations[state.investigator.location_id].clues = 1

        self.assertEqual(skill_test.legal_lucky_cards(state), [lucky, lucky_2, discard_lucky])
        self.assertEqual(skill_test.legal_look_what_i_found_cards(state), [look])
        self.assertEqual(enemies.legal_dodge_card(state), dodge)
        self.assertTrue(encounter.present_revelation_cancel(state, treachery))

        state.decision_queue = []
        skill_test.start(state, [], skill="combat", difficulty=5, source="Sure Gamble audit")
        state.decision_queue = []
        state.active_skill_test["modifier"] = -1
        skill_test.present_token_reveal_reaction(state, ArkhamRng(19), [])
        sure_options = [option.payload.get("card") for option in state.decision_queue[0].options]
        self.assertIn(sure_gamble, sure_options)

        state.decision_queue = []
        enemies.present_enemy_defeat_reactions(state, [], enemy_id)
        evidence_labels = [option.label for option in state.decision_queue[0].options]
        self.assertTrue(any("Evidence!" in label for label in evidence_labels))

        state.decision_queue = []
        actions.queue_close_call_reaction(state, enemy_id)
        self.assertEqual(state.decision_queue[0].id, "close-call-reaction")


if __name__ == "__main__":
    unittest.main()
