from __future__ import annotations

import unittest

from arkham import actions, enemies, phases
from arkham.cards import player as player_cards
from arkham.log import render_event
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_gathering, the_midnight_masks


def make_state():  # type: ignore[no-untyped-def]
    state = the_gathering.build_engine_test_state(difficulty="standard", rng=ArkhamRng(18))
    state.decision_queue = []
    state.investigator.hand = []
    state.investigator.play_area = []
    state.investigator.threat_area = []
    state.investigator.engaged_enemies = []
    state.enemies = {}
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
    if zone == "play_area":
        state.investigator.play_area.append(card_id)
        player_cards.setup_uses(state.card_instances[card_id])
    elif zone == "hand":
        state.investigator.hand.append(card_id)
    elif zone == "deck":
        state.investigator.deck.insert(0, card_id)
    elif zone == "discard":
        state.investigator.discard.append(card_id)
    return card_id


def rendered(state, event):  # type: ignore[no-untyped-def]
    return render_event(
        {
            "round": state.round,
            "phase": state.phase,
            "type": event["type"],
            "data": {**event.get("data", {}), "message": event.get("message", "")},
        }
    )


class FrameworkWindowTests(unittest.TestCase):
    def test_forbidden_knowledge_at_upkeep_start_then_steps_once(self) -> None:
        state = make_state()
        state.phase = "Upkeep"
        knowledge = add_card(state, "01058", "knowledge", "play_area")
        resources_before = state.investigator.resources
        deck_before = len(state.investigator.deck)
        events: list[dict] = []

        phases.advance_until_decision(state, ArkhamRng(18), events)
        self.assertEqual(state.decision_queue[0].id, "fast-window-upkeep_start")
        use = next(option.payload for option in state.decision_queue[0].options if "Forbidden Knowledge" in option.label)
        state.decision_queue = []
        actions.execute(state, use, events, ArkhamRng(18))
        phases.advance_until_decision(state, ArkhamRng(18), events)

        self.assertEqual(state.investigator.horror, 1)
        self.assertEqual(state.card_instances[knowledge].uses["secrets"], 3)
        self.assertEqual(state.investigator.resources, resources_before + 2)
        self.assertEqual(len(state.investigator.deck), deck_before - 1)
        self.assertEqual(sum(event["type"] == "ready_step" for event in events), 1)

    def test_enemy_post_window_precedes_scenario_hook(self) -> None:
        state = make_state()
        state.phase = "Enemy"
        state.agenda.stage = 3
        add_card(state, "01058", "knowledge", "play_area")
        enemy_id = "ghoul"
        state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code="01160", zone="enemy")
        state.enemies[enemy_id] = EnemyInstance(
            id=enemy_id,
            card_code="01160",
            location_id=state.investigator.location_id,
            engaged_with=state.investigator.id,
        )
        state.locations[state.investigator.location_id].enemy_ids.append(enemy_id)
        state.investigator.engaged_enemies.append(enemy_id)
        state.limits[f"fastwin:enemy_pre:{state.round}"] = True

        phases.advance_until_decision(state, ArkhamRng(18), [])

        self.assertEqual(state.decision_queue[0].id, "fast-window-enemy_post")
        self.assertEqual(state.phase, "Enemy")
        self.assertIn(enemy_id, state.investigator.engaged_enemies)

    def test_empty_boundary_windows_auto_skip(self) -> None:
        state = make_state()
        state.phase = "Enemy"
        phases.run_enemy_phase(state, [])
        self.assertFalse(state.decision_queue)
        self.assertTrue(state.limits[f"fastwin:enemy_post:{state.round}"])

        state.phase = "Upkeep"
        phases.run_upkeep_phase(state, [], ArkhamRng(18))
        self.assertFalse(state.decision_queue)
        self.assertTrue(state.limits[f"fastwin:upkeep_start:{state.round}"])


class GameEndGuardTests(unittest.TestCase):
    def test_abandoned_and_alone_defeat_stops_upkeep(self) -> None:
        state = make_state()
        state.phase = "Upkeep"
        state.investigator.card_code = "01005"
        state.investigator.name = "Wendy Adams"
        state.investigator.sanity = 7
        state.investigator.horror = 5
        state.investigator.deck = []
        state.investigator.discard = []
        discarded = add_card(state, "01088", "discarded", "discard")
        add_card(state, "01015", "abandoned", "deck")
        resources_before = state.investigator.resources
        events: list[dict] = []

        phases.run_upkeep_phase(state, events, ArkhamRng(18))

        self.assertEqual(state.status, "ended")
        self.assertIn(discarded, state.investigator.discard)
        self.assertEqual(state.card_instances[discarded].zone, "discard")
        self.assertEqual(state.investigator.resources, resources_before)
        self.assertEqual(sum(event["type"] == "game_end" for event in events), 1)


class RolandLogTests(unittest.TestCase):
    def test_defeat_reaction_has_one_specific_discovery_line(self) -> None:
        state = make_state()
        state.locations[state.investigator.location_id].clues = 1
        events: list[dict] = []

        enemies.resolve_enemy_defeated_reaction(
            state,
            {"reaction": "roland", "enemy": "defeated"},
            events,
        )

        discovery = [event for event in events if "discovered" in event.get("message", "")]
        self.assertEqual(len(discovery), 1)
        self.assertIn("after defeating an enemy", discovery[0]["message"])
        self.assertEqual(state.investigator.clues, 1)


class GatheringAgendaOrderTests(unittest.TestCase):
    def test_agenda_1_effect_finishes_before_advance(self) -> None:
        state = make_state()
        state.scenario = "the_gathering"
        state.phase = "Mythos"
        state.agenda.doom = state.agenda.threshold
        state.limits[f"mythos_encounter_drawn:{state.round}"] = True
        events: list[dict] = []
        the_gathering.check_agenda_advance(state, events, rng=ArkhamRng(18))
        self.assertEqual(state.agenda.stage, 1)

        state.decision_queue = []
        the_gathering.resolve_scenario_choice(
            state,
            {"choice": "agenda1_horror"},
            events,
            ArkhamRng(18),
        )

        effect_index = next(i for i, event in enumerate(events) if event["type"] == "damage_assigned")
        advance_index = next(i for i, event in enumerate(events) if event["type"] == "agenda_advanced")
        self.assertLess(effect_index, advance_index)
        self.assertEqual(state.agenda.stage, 2)
        self.assertEqual(state.phase, "Investigation")

    def test_agenda_2_ghoul_revelation_finishes_before_advance(self) -> None:
        state = make_state()
        state.scenario = "the_gathering"
        state.agenda.stage = 2
        state.agenda.doom = state.agenda.threshold
        state.encounter_deck = []
        state.encounter_discard = []
        state.card_instances["drawn_ghoul"] = CardInstance(
            id="drawn_ghoul",
            card_code="01160",
            zone="encounter_discard",
        )
        state.encounter_discard.append("drawn_ghoul")
        events: list[dict] = []

        the_gathering.advance_agenda_2(state, events, ArkhamRng(18))

        engage_index = next(i for i, event in enumerate(events) if event["type"] == "enemy_engaged")
        advance_index = next(i for i, event in enumerate(events) if event["type"] == "agenda_advanced")
        self.assertLess(engage_index, advance_index)
        self.assertEqual(state.agenda.stage, 3)
        self.assertEqual(state.agenda.doom, 0)


class InstanceIdLogTests(unittest.TestCase):
    def test_enemy_doom_and_attachment_render_with_instance_ids(self) -> None:
        state = make_state()
        enemy_id = "ec0006"
        state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code="50041", zone="enemy")
        state.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code="50041", location_id="study")
        mask = add_card(state, "50043", "mask", "hand")
        events: list[dict] = []

        the_midnight_masks.attach_mask_to_enemy(state, mask, enemy_id, events, ArkhamRng(18))

        attachment = next(event for event in events if event["type"] == "treachery_attached")
        doom = next(event for event in events if event["type"] == "doom_placed")
        self.assertIn("Disciple of the Devourer [ec0006]", rendered(state, attachment))
        self.assertIn("Disciple of the Devourer [ec0006]", rendered(state, doom))


if __name__ == "__main__":
    unittest.main()
