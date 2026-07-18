from __future__ import annotations

import unittest

from arkham.effects import place_doom, start_damage_assignment
from arkham.log import render_event
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_devourer_below as devourer
from arkham.scenarios import the_gathering as gathering
from arkham.scenarios import the_midnight_masks as midnight_masks


def rendered_rule_event(state, event: dict) -> str:  # type: ignore[no-untyped-def]
    data = dict(event.get("data", {}))
    data["message"] = event.get("message", "")
    if event.get("type") == "game_end":
        data["summary"] = event.get("message", "")
    return render_event(
        {
            "round": event.get("round", state.round),
            "phase": event.get("phase", state.phase),
            "type": event["type"],
            "data": data,
        }
    )


def game_end_events(events: list[dict]) -> list[dict]:
    return [event for event in events if event["type"] == "game_end"]


class DuplicateGameEndTests(unittest.TestCase):
    def test_devourer_damage_defeat_logs_one_game_end(self) -> None:
        state = devourer.build_state(
            difficulty="standard",
            rng=ArkhamRng(1),
            deck_path=None,
            investigator_slug="roland",
        )
        state.decision_queue = []
        state.investigator.damage = state.investigator.health - 1
        events: list[dict] = []

        start_damage_assignment(
            state,
            events,
            source="test defeat",
            damage=1,
            horror=0,
            direct=True,
        )

        terminal = game_end_events(events)
        self.assertEqual(len(terminal), 1)
        rendered = [rendered_rule_event(state, event) for event in events]
        self.assertEqual(sum("GAME OVER" in line for line in rendered), 1)

    def test_devourer_r1_resolution_logs_one_game_end(self) -> None:
        state = devourer.build_state(
            difficulty="standard",
            rng=ArkhamRng(2),
            deck_path=None,
            investigator_slug="roland",
        )
        events: list[dict] = []

        devourer.finalize_result(
            state,
            events,
            outcome="R1",
            resolution="R1",
            summary="R1: the ritual was broken",
        )

        self.assertEqual(len(game_end_events(events)), 1)

    def test_gathering_damage_defeat_logs_one_game_end(self) -> None:
        state = gathering.build_gathering_state(
            difficulty="standard",
            rng=ArkhamRng(3),
            deck_path=None,
            investigator_slug="roland",
        )
        state.decision_queue = []
        state.investigator.damage = state.investigator.health - 1
        events: list[dict] = []

        start_damage_assignment(
            state,
            events,
            source="test defeat",
            damage=1,
            horror=0,
            direct=True,
        )

        self.assertEqual(len(game_end_events(events)), 1)


class DoomSourceLogTests(unittest.TestCase):
    def test_corpse_taker_forced_source_is_rendered(self) -> None:
        state = midnight_masks.build_return_state(
            difficulty="standard",
            rng=ArkhamRng(1),
            deck_path=None,
            investigator_slug="roland",
        )
        state.phase = "Mythos"
        state.round = 2
        state.decision_queue = []
        corpse = "corpse_taker"
        state.card_instances[corpse] = CardInstance(
            id=corpse,
            card_code="50042",
            zone="enemy",
        )
        state.enemies[corpse] = EnemyInstance(
            id=corpse,
            card_code="50042",
            location_id="rivertown",
        )
        state.locations["rivertown"].enemy_ids.append(corpse)
        events: list[dict] = []

        midnight_masks.end_mythos_phase(state, events, ArkhamRng(1))

        doom = next(event for event in events if event["type"] == "doom_placed")
        self.assertEqual(doom["data"]["source"], "Corpse-Taker")
        self.assertEqual(doom["message"], "Placed 1 doom on Corpse-Taker.")
        self.assertIn(
            "Placed 1 doom on Corpse-Taker (Corpse-Taker's Forced).",
            rendered_rule_event(state, doom),
        )

    def test_step_1_3_agenda_doom_wording_is_unchanged(self) -> None:
        state = gathering.build_gathering_state(
            difficulty="standard",
            rng=ArkhamRng(4),
            deck_path=None,
            investigator_slug="roland",
        )
        state.phase = "Mythos"
        state.round = 2
        events: list[dict] = []

        place_doom(state, 1, events, source="mythos")

        rendered = rendered_rule_event(state, events[0])
        self.assertIn("Placed 1 doom on the agenda.", rendered)
        self.assertNotIn("(mythos)", rendered)


class LitaEntersPlayLogTests(unittest.TestCase):
    def test_lita_log_follows_parlor_reveal_and_precedes_act_advance(self) -> None:
        state = gathering.build_gathering_state(
            difficulty="standard",
            rng=ArkhamRng(5),
            deck_path=None,
            investigator_slug="roland",
        )
        state.decision_queue = []
        state.investigator.clues = 2
        gathering.advance_act(state, [])
        state.investigator.clues = 3
        events: list[dict] = []

        gathering.advance_act(state, events)

        event_types = [event["type"] for event in events]
        reveal_index = event_types.index("location_revealed")
        lita_index = event_types.index("lita_enters_play")
        priest_index = event_types.index("enemy_spawned")
        act_index = event_types.index("act_advanced")
        self.assertLess(reveal_index, lita_index)
        self.assertLess(lita_index, priest_index)
        self.assertLess(priest_index, act_index)
        lita_event = events[lita_index]
        lita_id = lita_event["data"]["card"]
        self.assertEqual(state.card_instances[lita_id].card_code, "01117")
        self.assertIn(
            "Lita Chantler was put into play in the Parlor.",
            rendered_rule_event(state, lita_event),
        )


if __name__ == "__main__":
    unittest.main()
