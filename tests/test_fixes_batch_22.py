from __future__ import annotations

import unittest
from pathlib import Path

from arkham import data as card_data
from arkham import encounter, skill_test
from arkham.cards import player as player_cards
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_devourer_below as db
from arkham.scenarios import the_gathering as tg
from arkham.scenarios import the_midnight_masks as mm


ROOT = Path(__file__).resolve().parents[1]


class SeqRng:
    def __init__(self, values: list[str]) -> None:
        self.values = list(values)

    def choice(self, values):  # type: ignore[no-untyped-def]
        return self.values.pop(0) if self.values else values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def add_player_card(state, code: str, card_id: str, zone: str) -> str:  # type: ignore[no-untyped-def]
    state.card_instances[card_id] = CardInstance(
        id=card_id,
        card_code=code,
        zone=zone,
        owner=state.investigator.id,
    )
    if zone == "play":
        state.investigator.play_area.append(card_id)
        player_cards.setup_uses(state.card_instances[card_id])
    elif zone == "deck":
        state.investigator.deck.append(card_id)
    return card_id


class RevealAddsPlacedCluesTests(unittest.TestCase):
    def test_disciple_clue_on_unrevealed_woods_survives_reveal_once(self) -> None:
        state = db.build_state(
            difficulty="standard",
            rng=ArkhamRng(22),
            deck_path=None,
            investigator_slug="roland",
        )
        state.decision_queue = []
        woods_id = next(location_id for location_id in state.locations if location_id != "main_path")
        printed = int(card_data.get_card(state.locations[woods_id].code).get("clues") or 0)
        disciple = "disciple"
        state.card_instances[disciple] = CardInstance(id=disciple, card_code="50041", zone="enemy")
        state.enemies[disciple] = EnemyInstance(
            id=disciple,
            card_code="50041",
            location_id=woods_id,
        )
        state.locations[woods_id].enemy_ids.append(disciple)
        state.investigator.clues = 1

        db.resolve_scenario_choice(
            state,
            {"choice": "disciple_clue", "enemy": disciple},
            [],
            ArkhamRng(22),
        )
        self.assertEqual(state.locations[woods_id].clues, 1)

        db.reveal_location(state, [], woods_id)
        self.assertEqual(state.locations[woods_id].clues, 1 + printed)

        db.reveal_location(state, [], woods_id)
        self.assertEqual(state.locations[woods_id].clues, 1 + printed)

    def test_normal_devourer_reveal_uses_printed_clue_value(self) -> None:
        state = db.build_state(
            difficulty="standard",
            rng=ArkhamRng(23),
            deck_path=None,
            investigator_slug="roland",
        )
        woods_id = next(location_id for location_id in state.locations if location_id != "main_path")
        printed = int(card_data.get_card(state.locations[woods_id].code).get("clues") or 0)

        db.reveal_location(state, [], woods_id)

        self.assertEqual(state.locations[woods_id].clues, printed)

    def test_gathering_reveal_adds_printed_clues_only_once(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(22))
        state.locations["attic"].revealed = False
        state.locations["attic"].shroud = None
        state.locations["attic"].clues = 1

        tg.reveal_location(state, [], "attic")
        self.assertEqual(state.locations["attic"].clues, 3)

        tg.reveal_location(state, [], "attic")
        self.assertEqual(state.locations["attic"].clues, 3)

    def test_midnight_masks_reveal_adds_printed_clues_only_once(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(22), investigator_slug="roland")
        location = state.locations["southside"]
        printed = int(card_data.get_card(location.code).get("clues") or 0)
        location.clues = 2

        mm.reveal_location(state, [], "southside")
        self.assertEqual(location.clues, 2 + printed)

        mm.reveal_location(state, [], "southside")
        self.assertEqual(location.clues, 2 + printed)


class SourcedLogDedupTests(unittest.TestCase):
    def test_daisy_elder_sign_draw_has_only_sourced_log(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(22))
        state.decision_queue = []
        state.investigator.card_code = "01002"
        state.investigator.name = "Daisy Walker"
        state.investigator.play_area = []
        state.investigator.hand = []
        state.investigator.deck = []
        add_player_card(state, "01031", "tome-one", "play")
        add_player_card(state, "01035", "tome-two", "play")
        drawn = [
            add_player_card(state, "01089", "draw-one", "deck"),
            add_player_card(state, "01093", "draw-two", "deck"),
        ]
        events: list[dict] = []

        skill_test.start(state, events, skill="intellect", difficulty=1, source="Daisy elder sign log")
        skill_test.finish_commit(state, SeqRng(["eldersign"]), events)

        sourced = [event for event in events if event["type"] == "elder_sign"]
        self.assertEqual(len(sourced), 1)
        self.assertEqual(sourced[0]["data"]["amount"], 2)
        self.assertFalse(any(event["type"] == "card_drawn" for event in events))
        self.assertTrue(set(drawn) <= set(state.investigator.hand))

    def test_drawn_to_the_flame_discovery_has_only_sourced_log_and_actual_amount(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(22))
        state.decision_queue = []
        location = state.locations[state.investigator.location_id]
        location.clues = 1
        state.investigator.clues = 0
        state.limits["after_encounter_draw"] = {"kind": "drawn_to_the_flame"}
        events: list[dict] = []

        encounter.resolve_after_encounter_draw(state, events)

        discovery = [
            event
            for event in events
            if event["type"] in {"drawn_to_the_flame", "clue_discovered"}
        ]
        self.assertEqual(len(discovery), 1)
        self.assertEqual(discovery[0]["type"], "drawn_to_the_flame")
        self.assertEqual(discovery[0]["data"]["amount"], 1)
        self.assertEqual(state.investigator.clues, 1)
        self.assertEqual(location.clues, 0)


class CentralLocationAndOnWingsTests(unittest.TestCase):
    def test_all_printed_central_location_faces_have_the_trait(self) -> None:
        codes = {
            "01126",
            "01127",
            "01130",
            "01131",
            "01132",
            "01134",
            "50027",
            "50028",
        }

        for code in sorted(codes):
            with self.subTest(code=code):
                traits = {
                    trait.strip()
                    for trait in str(card_data.get_card(code).get("traits", "")).split(".")
                    if trait.strip()
                }
                self.assertIn("Central", traits)

    def test_on_wings_offers_every_legal_central_destination(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(22), investigator_slug="roland")
        state.decision_queue = []
        expected = mm.central_destinations(state)
        self.assertGreater(len(expected), 1)

        mm.on_wings_disengage_and_move(state, [])

        self.assertEqual(state.investigator.location_id, "your_house")
        self.assertEqual(state.decision_queue[0].id, "on-wings-destination")
        offered = [option.payload["location"] for option in state.decision_queue[0].options]
        self.assertEqual(offered, expected)
        self.assertNotIn(state.investigator.location_id, offered)

    def test_on_wings_still_auto_moves_with_one_central_destination(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(22), investigator_slug="roland")
        state.decision_queue = []
        for location_id in mm.central_destinations(state):
            if location_id != "rivertown":
                del state.locations[location_id]
        events: list[dict] = []

        mm.on_wings_disengage_and_move(state, events)

        self.assertEqual(state.investigator.location_id, "rivertown")
        self.assertFalse(state.decision_queue)
        self.assertEqual(sum(event["type"] == "investigator_moved" for event in events), 1)


class MidnightMasksDefeatDocumentationTests(unittest.TestCase):
    def test_no_resolution_defeat_points_to_resolution_one(self) -> None:
        text = (ROOT / "docs_agent" / "scenario_reference.md").read_text(encoding="utf-8")
        midnight_masks = text.split("## The Midnight Masks", 1)[1].split("\n## ", 1)[0]

        self.assertIn("each investigator resigned or was defeated", midnight_masks)
        self.assertIn("Resolution 1", midnight_masks)
        self.assertIn("usual trauma", midnight_masks)


if __name__ == "__main__":
    unittest.main()
