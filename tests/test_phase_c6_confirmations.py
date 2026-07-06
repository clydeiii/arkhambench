from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from arkham import actions, cli, fuzz
from arkham.cards import player as player_cards
from arkham.game import Game
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


def make_game(tmp: str, *, confirmations_enabled: bool = True) -> Game:
    state = build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
    state.confirmations_enabled = confirmations_enabled
    state.phase = "Investigation"
    state.status = "in_progress"
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
    state.investigator.actions_remaining = 3
    state.locations[state.investigator.location_id].clues = 0
    actions.present_action_decision(state)
    return Game(Path(tmp) / "run", state, ArkhamRng(2))


def choose_action(game: Game, action: str, **payload: str) -> list[dict]:
    decision = game.current_decision()
    assert decision is not None
    for index, option in enumerate(decision.options, start=1):
        option_payload = option.payload
        if option_payload.get("kind") != "action" or option_payload.get("action") != action:
            continue
        if all(option_payload.get(key) == value for key, value in payload.items()):
            return game.apply(index)
    raise AssertionError(f"missing action option: {action} {payload}")


def add_card(state, code: str, zone: str, card_id: str) -> str:
    state.card_instances[card_id] = CardInstance(id=card_id, card_code=code, zone=zone, owner=state.investigator.id)
    if zone == "hand":
        state.investigator.hand.append(card_id)
    elif zone == "play":
        state.investigator.play_area.append(card_id)
        player_cards.setup_uses(state.card_instances[card_id])
    return card_id


def add_enemy(state, code: str, enemy_id: str, *, exhausted: bool = False, aloof: bool = False) -> str:
    location_id = state.investigator.location_id
    state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    state.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location_id, engaged_with=state.investigator.id, exhausted=exhausted)
    state.locations[location_id].enemy_ids.append(enemy_id)
    state.investigator.engaged_enemies.append(enemy_id)
    if aloof:
        mask_id = f"{enemy_id}_mask"
        state.card_instances[mask_id] = CardInstance(id=mask_id, card_code="50043", zone="attachment")
        state.enemies[enemy_id].attachments.append(mask_id)
    return enemy_id


class PhaseC6ConfirmationTests(unittest.TestCase):
    def test_zero_clue_investigate_cancel_spends_nothing_and_yes_starts_test(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = make_game(tmp)
            before_actions = game.state.investigator.actions_remaining

            events = choose_action(game, "investigate")
            self.assertEqual(game.current_decision().kind, "confirmation")
            self.assertIn("Study has no clues", game.current_decision().prompt)
            self.assertFalse(any(event["type"] == "action_spent" for event in events))
            self.assertEqual(game.state.investigator.actions_remaining, before_actions)

            game.apply(2, why="no value")
            self.assertEqual(game.current_decision().id, "choose-action")
            self.assertEqual(game.state.investigator.actions_remaining, before_actions)
            self.assertIsNone(game.state.active_skill_test)

        with tempfile.TemporaryDirectory() as tmp:
            game = make_game(tmp)
            choose_action(game, "investigate")
            game.apply(1, why="checking a forced line")
            self.assertIsNotNone(game.state.active_skill_test)
            self.assertEqual(game.state.investigator.actions_remaining, 2)
            self.assertEqual(game.current_decision().id, "commit-cards")

    def test_investigate_with_clues_has_no_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = make_game(tmp)
            game.state.locations[game.state.investigator.location_id].clues = 1
            actions.present_action_decision(game.state)

            choose_action(game, "investigate")
            self.assertIsNotNone(game.state.active_skill_test)
            self.assertEqual(game.current_decision().id, "commit-cards")

    def test_flashlight_at_zero_clues_is_gated_but_burglary_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = make_game(tmp)
            flashlight = add_card(game.state, "01087", "play", "flashlight")
            burglary = add_card(game.state, "01045", "play", "burglary")
            actions.present_action_decision(game.state)

            choose_action(game, "flashlight", asset=flashlight)
            self.assertEqual(game.current_decision().kind, "confirmation")
            self.assertIn("has no clues", game.current_decision().prompt)
            game.apply(2)

            choose_action(game, "burglary", asset=burglary)
            self.assertIsNotNone(game.state.active_skill_test)
            self.assertEqual(game.current_decision().id, "commit-cards")

    def test_aoo_confirmation_cancel_and_yes_preserve_initiation_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = make_game(tmp)
            add_card(game.state, "01020", "hand", "machete")
            add_enemy(game.state, "01116", "priest")
            actions.present_action_decision(game.state)

            before = (game.state.investigator.actions_remaining, game.state.investigator.resources, game.state.investigator.damage, game.state.investigator.horror)
            choose_action(game, "play", card="machete")
            self.assertIn("This will provoke: Ghoul Priest (2 dmg/2 hor). Proceed?", game.current_decision().prompt)
            game.apply(2)
            after = (game.state.investigator.actions_remaining, game.state.investigator.resources, game.state.investigator.damage, game.state.investigator.horror)
            self.assertEqual(after, before)
            self.assertIn("machete", game.state.investigator.hand)

        with tempfile.TemporaryDirectory() as tmp:
            game = make_game(tmp)
            add_card(game.state, "01020", "hand", "machete")
            add_enemy(game.state, "01116", "priest")
            actions.present_action_decision(game.state)

            choose_action(game, "play", card="machete")
            events = game.apply(1, why="asset matters more than the hit")
            event_types = [event["type"] for event in events]
            self.assertLess(event_types.index("action_spent"), event_types.index("enemy_attack"))
            self.assertLess(event_types.index("enemy_attack"), event_types.index("card_played"))
            self.assertEqual(game.state.investigator.actions_remaining, 2)
            self.assertEqual(game.state.investigator.resources, 7)
            self.assertEqual((game.state.investigator.damage, game.state.investigator.horror), (2, 2))
            self.assertIn("machete", game.state.investigator.play_area)

    def test_aoo_exempt_exhausted_and_aloof_actions_do_not_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = make_game(tmp)
            add_enemy(game.state, "01160", "ghoul")
            actions.present_action_decision(game.state)
            choose_action(game, "fight", enemy="ghoul")
            self.assertEqual(game.current_decision().id, "commit-cards")
            self.assertIsNotNone(game.state.active_skill_test)

        for exhausted, aloof in ((True, False), (False, True)):
            with tempfile.TemporaryDirectory() as tmp:
                game = make_game(tmp)
                add_card(game.state, "01020", "hand", "machete")
                add_enemy(game.state, "01160", "ghoul", exhausted=exhausted, aloof=aloof)
                actions.present_action_decision(game.state)
                choose_action(game, "play", card="machete")
                self.assertNotEqual(game.current_decision().kind, "confirmation")
                self.assertEqual((game.state.investigator.damage, game.state.investigator.horror), (0, 0))

    def test_confirmations_can_be_disabled_and_fuzz_builds_that_way(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = make_game(tmp, confirmations_enabled=False)
            choose_action(game, "investigate")
            self.assertEqual(game.current_decision().id, "commit-cards")

        captured: list[bool] = []

        class EndedGame:
            def __init__(self) -> None:
                self.state = build_engine_test_state(difficulty="standard", rng=ArkhamRng(3))
                self.state.status = "ended"
                self.state.result = {"outcome": "test"}

        def fake_new(**kwargs):
            captured.append(bool(kwargs.get("confirmations_enabled", True)))
            return EndedGame()

        with mock.patch("arkham.fuzz.Game.new", side_effect=fake_new):
            fuzz.run_fuzz(1)
        self.assertEqual(captured, [False])

    def test_cli_no_confirmations_persists_and_confirmation_why_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["new", "--run", str(run_dir), "--no-confirmations"]), 0)
            self.assertFalse(Game.load(run_dir).state.confirmations_enabled)

        with tempfile.TemporaryDirectory() as tmp:
            game = make_game(tmp)
            choose_action(game, "investigate")
            game.apply(1, why="audit the zero-clue choice")
            log_text = (Path(tmp) / "run" / "log.md").read_text(encoding="utf-8")
            self.assertIn("confirmation", (Path(tmp) / "run" / "log.jsonl").read_text(encoding="utf-8"))
            self.assertIn("Proceed?", log_text)
            self.assertIn("audit the zero-clue choice", log_text)


if __name__ == "__main__":
    unittest.main()
