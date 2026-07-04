from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from arkham import actions, skill_test
from arkham.cli import render_state
from arkham.effects import RuleEventList, check_agenda_advance, log_event, place_doom
from arkham.errors import EngineError
from arkham.game import Game
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_gathering
from arkham.scenarios.the_gathering import build_engine_test_state, build_gathering_state


def engine_state(seed: int = 1):
    state = build_engine_test_state(difficulty="standard", rng=ArkhamRng(seed))
    state.investigator.hand = []
    state.investigator.deck = []
    state.investigator.discard = []
    state.investigator.play_area = []
    state.investigator.threat_area = []
    state.investigator.resources = 10
    state.chaos_bag.tokens = ["0"]
    return state


def gathering_state(seed: int = 1):
    state = build_gathering_state(difficulty="standard", rng=ArkhamRng(seed))
    state.decision_queue = []
    return state


def add_card(state, code: str, zone: str, instance_id: str) -> str:
    state.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone=zone)
    if zone == "hand":
        state.investigator.hand.append(instance_id)
    elif zone == "play":
        state.investigator.play_area.append(instance_id)
    elif zone == "threat":
        state.investigator.threat_area.append(instance_id)
    elif zone == "encounter_deck":
        state.encounter_deck.append(instance_id)
    return instance_id


def add_enemy(state, code: str, instance_id: str, *, engaged: bool = True, location: str = "study") -> str:
    state.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="enemy")
    state.enemies[instance_id] = EnemyInstance(id=instance_id, card_code=code, location_id=location)
    state.locations[location].enemy_ids.append(instance_id)
    if engaged:
        state.enemies[instance_id].engaged_with = "roland"
        state.investigator.engaged_enemies.append(instance_id)
    return instance_id


class ReverseRng:
    def shuffle(self, values):
        values.reverse()


class FixBatch1Tests(unittest.TestCase):
    def test_finish_mythos_after_agenda_choice_does_not_redraw_encounter(self) -> None:
        state = gathering_state()
        state.round = 3
        state.phase = "Mythos"
        state.limits["mythos_encounter_drawn:3"] = True
        before = list(state.encounter_deck)
        events = []

        the_gathering.finish_mythos_after_agenda_choice(state, events, ArkhamRng(9))

        self.assertEqual(state.encounter_deck, before)
        self.assertFalse(any(event["type"] == "encounter_drawn" for event in events))
        self.assertEqual(state.phase, "Investigation")

    def test_agenda_2_uses_supplied_rng_for_ghoul_search(self) -> None:
        state = gathering_state()
        state.agenda.stage = 2
        state.encounter_deck = []
        state.encounter_discard = []
        add_card(state, "01159", "encounter_deck", "rat")
        add_card(state, "01166", "encounter_deck", "evils")
        add_card(state, "01160", "encounter_deck", "minion")
        events = []

        the_gathering.advance_agenda_2(state, events, ReverseRng())  # type: ignore[arg-type]

        self.assertEqual(state.agenda.stage, 3)
        self.assertIn("minion", state.enemies)
        self.assertNotIn("rat", state.enemies)

    def test_aoo_exemption_is_by_action_type_and_engage_provokes(self) -> None:
        state = engine_state()
        first = add_enemy(state, "01159", "rat_a")
        second = add_enemy(state, "01159", "rat_b")
        events = []

        actions.execute(state, {"action": "fight", "enemy": first}, events)
        self.assertEqual(state.investigator.damage, 0)
        self.assertEqual([event["data"]["enemy"] for event in events if event["type"] == "enemy_attack"], [])
        self.assertIsNotNone(state.active_skill_test)

        state = engine_state()
        add_enemy(state, "01159", "rat_a")
        add_enemy(state, "01159", "rat_b")
        add_enemy(state, "01159", "rat_c", engaged=False)
        events = []
        actions.execute(state, {"action": "engage", "enemy": "rat_c"}, events)
        self.assertEqual(state.investigator.actions_remaining, 2)
        self.assertEqual(state.decision_queue[0].id, "aoo-attack-order")
        action_payload = dict(state.decision_queue[0].options[0].payload["action_payload"])
        state.decision_queue = []
        actions.resolve_ordered_aoo(state, events, "rat_b", ["rat_a"], action_payload, ArkhamRng(1))
        if state.decision_queue:
            payload = state.decision_queue[0].options[0].payload
            state.decision_queue = []
            actions.resolve_ordered_aoo(state, events, str(payload["enemy"]), list(payload["remaining"]), dict(payload["action_payload"]), ArkhamRng(1))
        self.assertEqual(state.investigator.damage, 2)
        self.assertIn("rat_c", state.investigator.engaged_enemies)
        self.assertEqual([event["data"]["enemy"] for event in events if event["type"] == "enemy_attack"], ["rat_b", "rat_a"])

    def test_aoo_happens_after_action_cost_before_effect(self) -> None:
        state = engine_state()
        add_enemy(state, "01159", "rat")
        events = []

        actions.execute(state, {"action": "draw"}, events, ArkhamRng(1))

        spent = next(i for i, event in enumerate(events) if event["type"] == "action_spent")
        attack = next(i for i, event in enumerate(events) if event["type"] == "enemy_attack")
        drawn = next(i for i, event in enumerate(events) if event["type"] == "deck_empty" or event["type"] == "card_drawn")
        self.assertLess(spent, attack)
        self.assertLess(attack, drawn)

    def test_frozen_in_fear_makes_unaffordable_actions_illegal_and_guarded(self) -> None:
        state = engine_state()
        add_card(state, "01164", "threat", "frozen")
        state.investigator.actions_remaining = 1

        labels = [option.label for option in actions.legal_actions(state)]

        self.assertFalse(any(label.startswith("Move ") for label in labels))
        with self.assertRaises(EngineError):
            actions.spend_action(state, [], "move")

    def test_agenda_advancement_discards_agenda_doom_but_keeps_other_doom_counting(self) -> None:
        state = gathering_state()
        state.agenda.doom = 2
        acolyte = add_enemy(state, "01160", "acolyte")
        state.enemies[acolyte].doom = 1

        the_gathering.check_agenda_advance(state, [])

        # Doom stays visible (3/3) while the flip choice is pending...
        self.assertEqual(state.agenda.doom, 2)
        self.assertEqual(state.decision_queue[0].id, "agenda1-back")
        # ...and ALL doom in play clears when the flip resolves.
        the_gathering.set_agenda_2(state, [])
        self.assertEqual(state.agenda.doom, 0)
        self.assertEqual(state.enemies[acolyte].doom, 0)

        fixture = engine_state()
        fixture.agenda.doom = 2
        place_doom(fixture, 2, [], source="test", can_advance=True)
        self.assertEqual(fixture.agenda.stage, 2)
        self.assertEqual(fixture.agenda.doom, 0)

    def test_rule_events_keep_emit_time_round_and_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = engine_state()
            game = Game(Path(tmp), state, ArkhamRng(1))
            game._initialize_files(seed=1, difficulty="standard", deck_path=None)
            events = RuleEventList(state)
            log_event(events, "before", "before phase change")
            state.phase = "Enemy"
            log_event(events, "after", "after phase change")

            game._append_rule_events(events)
            rows = [json.loads(line) for line in (Path(tmp) / "log.jsonl").read_text(encoding="utf-8").splitlines()]

        self.assertEqual(rows[0]["phase"], "Investigation")
        self.assertEqual(rows[1]["phase"], "Enemy")

    def test_autofail_failure_margin_is_zero_and_label_is_clear(self) -> None:
        state = engine_state()
        state.chaos_bag.tokens = ["autofail"]
        events = []

        skill_test.start(state, events, skill="intellect", difficulty=0, source="Frozen in Fear")
        skill_test.finish_commit(state, ArkhamRng(1), events)

        self.assertEqual(state.limits["last_skill_test"]["margin"], 0)
        self.assertEqual(state.limits["last_skill_test"]["value"], 0)
        self.assertTrue(any("failure (autofail) by 0" in event["message"] for event in events))

    def test_state_rendering_uses_card_names_and_enemy_ally_status(self) -> None:
        state = engine_state()
        magnifier = add_card(state, "01030", "play", "pc0014")
        beat_cop = add_card(state, "01018", "play", "ally1")
        state.card_instances[beat_cop].damage = 1
        state.card_instances[beat_cop].horror = 1
        add_card(state, "01164", "threat", "frozen")
        door = add_card(state, "01174", "attachment", "door1")
        state.locations["study"].attached_instance_ids.append(door)
        priest = add_enemy(state, "01116", "priest")
        state.enemies[priest].damage = 1
        state.enemies[priest].exhausted = True

        rendered = render_state(state)

        self.assertIn("Magnifying Glass (pc0014)", rendered)
        self.assertIn("Frozen in Fear (frozen)", rendered)
        self.assertIn("Locked Door (door1)", rendered)
        self.assertIn("Ghoul Priest [1/5 dmg, exhausted, engaged]", rendered)
        self.assertIn("Beat Cop (ally1) [1/2 dmg, 1/2 horror]", rendered)
        self.assertIn(magnifier, state.investigator.play_area)


if __name__ == "__main__":
    unittest.main()
