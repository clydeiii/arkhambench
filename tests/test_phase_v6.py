from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from arkham import actions, encounter, enemies, skill_test
from arkham.errors import EngineError
from arkham.game import Game
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_gathering as tg


class SeqRng:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = list(tokens)

    def choice(self, values):  # type: ignore[no-untyped-def]
        return self.tokens.pop(0) if self.tokens else values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def return_state(seed: int = 1, attic: str = "return", cellar: str = "return"):
    s = tg.build_return_state(difficulty="standard", rng=ArkhamRng(seed))
    s.decision_queue = []
    s.limits.pop("mulligan_available", None)
    s.limits["return_variant:attic"] = attic
    s.limits["return_variant:cellar"] = cellar
    s.chaos_bag.tokens = ["0"]
    return s


def move_to(s, location_id: str) -> None:
    previous = s.investigator.location_id
    if s.investigator.id in s.locations[previous].investigator_ids:
        s.locations[previous].investigator_ids.remove(s.investigator.id)
    s.investigator.location_id = location_id
    s.locations[location_id].investigator_ids.append(s.investigator.id)


def add_enemy(s, code: str, location: str, engaged: bool = True) -> str:
    enemy_id = f"enemy_{len(s.enemies)}"
    s.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    s.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location)
    s.locations[location].enemy_ids.append(enemy_id)
    if engaged:
        s.enemies[enemy_id].engaged_with = s.investigator.id
        s.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


class PhaseV6Tests(unittest.TestCase):
    def test_setup_layout_counts_and_variant_determinism(self) -> None:
        s = tg.build_return_state(difficulty="standard", rng=ArkhamRng(9))
        self.assertEqual(set(s.locations), {"study", "guest_hall", "bedroom", "bathroom"})
        self.assertTrue(s.locations["study"].revealed)
        self.assertEqual(s.locations["study"].code, "50013")
        self.assertEqual(s.act.name, "Mysterious Gateway")
        self.assertEqual(s.act.clues_required, 3)
        deck_codes = [s.card_instances[cid].card_code for cid in s.encounter_deck]
        self.assertEqual(len(deck_codes), 32)
        for gone in ("01160", "01161", "01162"):
            self.assertNotIn(gone, deck_codes)
        self.assertEqual(deck_codes.count("50038"), 3)
        self.assertEqual(deck_codes.count("50024"), 2)

        pairs = set()
        for seed in range(1, 25):
            a = tg.build_return_state(difficulty="standard", rng=ArkhamRng(seed))
            b = tg.build_return_state(difficulty="standard", rng=ArkhamRng(seed))
            variant = (a.limits["return_variant:attic"], a.limits["return_variant:cellar"])
            self.assertEqual(variant, (b.limits["return_variant:attic"], b.limits["return_variant:cellar"]))
            pairs.add(variant)
        self.assertTrue({v[0] for v in pairs} == {"original", "return"})
        self.assertTrue({v[1] for v in pairs} == {"original", "return"})

    def test_act1_gating_and_breaking_the_wall(self) -> None:
        s = return_state()
        s.investigator.clues = 3
        opts = [o.payload.get("action") for o in actions.legal_actions(s)]
        self.assertNotIn("advance_act", opts)

        tg.reveal_location(s, [], "guest_hall")
        move_to(s, "guest_hall")
        opts = [o.payload.get("action") for o in actions.legal_actions(s)]
        self.assertIn("advance_act", opts)
        self.assertNotIn("draw", opts)
        with self.assertRaises(EngineError):
            actions.execute(s, {"kind": "action", "action": "draw"}, [], ArkhamRng(2))

        actions.execute(s, {"kind": "action", "action": "advance_act"}, [], ArkhamRng(2))
        self.assertEqual(s.investigator.clues, 0)
        self.assertEqual(s.investigator.location_id, "hallway")
        hallway = s.locations["hallway"]
        self.assertTrue(hallway.revealed)
        self.assertEqual(hallway.name, "Hallway")
        self.assertLessEqual({"guest_hall", "attic", "cellar", "parlor"}, set(hallway.connections))
        self.assertIn("hallway", s.locations["guest_hall"].connections)
        for loc in ("attic", "cellar", "parlor"):
            self.assertIn(loc, s.locations)
            self.assertFalse(s.locations[loc].revealed)
        self.assertEqual(s.act.stage, 2)
        self.assertEqual(s.act.name, "The Barrier")
        self.assertEqual(s.active_skill_test["source"], "Breaking the Wall")
        hand_before = len(s.investigator.hand)
        skill_test.finish_commit(s, SeqRng(["0"]), [])  # Roland wp 3 vs 4 -> fail by 1
        self.assertEqual(len(s.investigator.hand), hand_before - 1)

    def test_reveal_cascade_far_above_and_field_of_graves(self) -> None:
        s = return_state()
        s.investigator.clues = 3
        tg.reveal_location(s, [], "guest_hall")
        move_to(s, "guest_hall")
        actions.execute(s, {"kind": "action", "action": "advance_act"}, [], ArkhamRng(2))
        skill_test.finish_commit(s, SeqRng(["+1"]), [])

        tg.reveal_location(s, [], "attic")
        self.assertIn("field_of_graves", s.locations)
        far_above = s.locations["field_of_graves"]
        self.assertFalse(far_above.revealed)
        self.assertEqual(far_above.name, "Far Above Your House")
        self.assertIn("field_of_graves", s.locations["attic"].connections)
        self.assertIn("attic", far_above.connections)

        hand_before = len(s.investigator.hand)
        tg.reveal_location(s, [], "field_of_graves")
        self.assertEqual(far_above.name, "Field of Graves")
        self.assertEqual(s.active_skill_test["source"], "Field of Graves")
        skill_test.finish_commit(s, SeqRng(["-3"]), [])  # wp 3 - 3 = 0 vs 4 -> fail by 4
        self.assertEqual(len(s.investigator.hand), max(0, hand_before - 4))

        far_above.clues = 0
        tg.add_victory_locations(s)
        self.assertIn("field_of_graves", s.victory_display)
        self.assertEqual(tg.calculate_victory_points(s), 1)

    def test_original_variants_keep_core_behavior(self) -> None:
        s = return_state(attic="original", cellar="original")
        s.investigator.clues = 3
        tg.reveal_location(s, [], "guest_hall")
        move_to(s, "guest_hall")
        actions.execute(s, {"kind": "action", "action": "advance_act"}, [], ArkhamRng(2))
        skill_test.finish_commit(s, SeqRng(["+1"]), [])
        self.assertEqual(s.locations["attic"].code, "01113")
        tg.reveal_location(s, [], "attic")
        self.assertNotIn("field_of_graves", s.locations)
        tg.after_enter_location(s, [], "attic")  # original Attic: 1 horror on enter
        self.assertTrue(s.pending_damage or s.investigator.horror >= 1)

    def test_ghoul_pits_rats_search(self) -> None:
        s = return_state()
        s.locations["cellar"] = type(s.locations["study"])(
            id="cellar", code="50020", name="Cellar", revealed=True, shroud=2, clues=1, connections=["ghoul_pits"]
        )
        tg.put_return_location_into_play(s, [], "ghoul_pits")
        rats = [cid for cid in s.encounter_deck if s.card_instances[cid].card_code == "01159"]
        self.assertGreaterEqual(len(rats), 2)
        move_to(s, "cellar")
        tg.ghoul_pits_draw_rats(s, [], ArkhamRng(3), 2)
        spawned = [e for e in s.enemies.values() if e.card_code == "01159"]
        self.assertEqual(len(spawned), 2)

    def test_study_gateway_draw_and_spawn_fallback(self) -> None:
        s = return_state()
        hand_before = len(s.investigator.hand)
        opts = [o.payload.get("action") for o in actions.legal_actions(s)]
        self.assertIn("study_draw", opts)
        actions.execute(s, {"kind": "action", "action": "study_draw"}, [], ArkhamRng(2))
        self.assertEqual(len(s.investigator.hand), hand_before + 3)
        self.assertEqual(s.investigator.actions_remaining, 1)

        # Flesh-Eater spawns at the Attic even though it is not in play yet:
        # the Study's gateway pulls the location into play.
        flesh_eater = next(cid for cid in s.encounter_deck if s.card_instances[cid].card_code == "01118")
        s.encounter_deck.remove(flesh_eater)
        encounter.resolve_revelation(s, ArkhamRng(2), [], flesh_eater)
        self.assertIn("attic", s.locations)
        self.assertFalse(s.locations["attic"].revealed)
        self.assertEqual(s.enemies[flesh_eater].location_id, "attic")

    def test_zealots_seal_both_branches(self) -> None:
        s = return_state()
        seal = next(cid for cid in s.encounter_deck if s.card_instances[cid].card_code == "50024")
        s.investigator.hand = s.investigator.hand[:3]
        encounter.resolve_revelation(s, ArkhamRng(2), [], seal)
        # solo with no soak assets: the 1 damage / 1 horror applies directly
        self.assertEqual(s.investigator.damage, 1)
        self.assertEqual(s.investigator.horror, 1)

        s2 = return_state(seed=2)
        while len(s2.investigator.hand) < 4:
            s2.investigator.hand.append(s2.investigator.deck.pop(0))
        seal2 = next(cid for cid in s2.encounter_deck if s2.card_instances[cid].card_code == "50024")
        encounter.resolve_revelation(s2, ArkhamRng(2), [], seal2)
        self.assertEqual(s2.active_skill_test["source"], "The Zealot's Seal")
        hand_before = len(s2.investigator.hand)
        skill_test.finish_commit(s2, SeqRng(["-3"]), [])  # wp 3 - 3 = 0 vs 2 -> fail
        self.assertEqual(len(s2.investigator.hand), hand_before - 2)

    def test_chill_from_below_discard_and_damage_shortfall(self) -> None:
        s = return_state()
        chill = next(cid for cid in s.encounter_deck if s.card_instances[cid].card_code == "50040")
        s.investigator.hand = s.investigator.hand[:1]
        encounter.resolve_revelation(s, ArkhamRng(2), [], chill)
        self.assertEqual(s.active_skill_test["source"], "Chill from Below")
        skill_test.finish_commit(s, SeqRng(["-3"]), [])  # value 0 vs 3 -> fail by 3
        self.assertEqual(len(s.investigator.hand), 0)
        self.assertEqual(s.investigator.damage, 2)  # 2 damage shortfall after 1 discard

    def test_grave_eater_and_acolyte(self) -> None:
        s = return_state()
        eater = add_enemy(s, "50038", "study")
        hand_before = len(s.investigator.hand)
        enemies.after_attack(s, [], eater, {}, source="enemy phase", rng=ArkhamRng(4))
        self.assertEqual(len(s.investigator.hand), hand_before - 1)

        acolyte = add_enemy(s, "50039", "study")
        s.investigator.hand = []
        opts = actions.legal_actions(s)
        evade_targets = [o.payload.get("enemy") for o in opts if o.payload.get("action") == "evade"]
        self.assertNotIn(acolyte, evade_targets)
        with self.assertRaises(EngineError):
            actions.execute(s, {"kind": "action", "action": "evade", "enemy": acolyte}, [], ArkhamRng(2))
        s.investigator.hand.append(s.investigator.deck.pop(0))
        s.card_instances[s.investigator.hand[0]].zone = "hand"
        evade_targets = [
            o.payload.get("enemy") for o in actions.legal_actions(s) if o.payload.get("action") == "evade"
        ]
        self.assertIn(acolyte, evade_targets)

    def test_bathroom_and_bedroom_forced(self) -> None:
        s = return_state()
        tg.reveal_location(s, [], "guest_hall")
        tg.reveal_location(s, [], "bathroom")
        move_to(s, "bathroom")
        s.investigator.actions_remaining = 3
        tg.apply_token_aftermath(
            s, [], {"token": "skull", "success": True, "callback_kind": "investigate", "source": "Investigate Bathroom"}, ArkhamRng(2)
        )
        self.assertEqual(s.investigator.actions_remaining, 0)

        tg.reveal_location(s, [], "bedroom")
        move_to(s, "bedroom")
        hand_before = len(s.investigator.hand)
        tg.apply_token_aftermath(
            s, [], {"token": "-1", "success": False, "callback_kind": "investigate", "source": "Investigate Bedroom"}, ArkhamRng(2)
        )
        self.assertEqual(len(s.investigator.hand), hand_before - 1)
        # non-investigate tests at the bedroom do not trigger the forced discard
        hand_before = len(s.investigator.hand)
        tg.apply_token_aftermath(
            s, [], {"token": "-1", "success": False, "callback_kind": "horror_per_fail", "source": "Rotting Remains"}, ArkhamRng(2)
        )
        self.assertEqual(len(s.investigator.hand), hand_before)

    def test_new_game_smoke_and_scoring_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Game.new(
                seed=3,
                difficulty="standard",
                deck_path=None,
                run_dir=Path(tmp) / "run",
                scenario="return_to_the_gathering",
                investigator="wendy",
            )
            self.assertEqual(game.state.scenario, "return_to_the_gathering")
            self.assertEqual(game.state.investigator.id, "wendy")
            game.apply(1)  # keep opening hand
            self.assertEqual(game.state.status, "in_progress")

        s = return_state()
        tg.finalize_result(s, [], outcome="R1", resolution="R1", summary="R1")
        self.assertEqual(s.result["resolution"], "R1")
        self.assertTrue(s.result["lita_earned"])
        self.assertEqual(s.result["score"], max(0, s.result["xp"] - sum(s.trauma.values())))


if __name__ == "__main__":
    unittest.main()


class PostActionWindowTests(unittest.TestCase):
    def _guest_hall_state(self, investigator_code: str):
        s = return_state(seed=3)
        s.investigator.card_code = investigator_code
        s.investigator.clues = 3
        s.investigator.actions_remaining = 0
        s.investigator.resources = 5
        tg.reveal_location(s, [], "guest_hall")
        move_to(s, "guest_hall")
        return s

    def test_objective_offered_in_post_last_action_window(self) -> None:
        from arkham import phases

        s = self._guest_hall_state("01004")
        queued = phases.present_fast_window(s, "inv_end", during_turn=True)
        self.assertTrue(queued)
        labels = [o.label for o in s.decision_queue[0].options]
        self.assertTrue(any(l.startswith("Advance act") for l in labels), labels)

    def test_skids_can_buy_action_after_last_action(self) -> None:
        from arkham import phases

        s = self._guest_hall_state("01003")
        s.investigator.clues = 0
        queued = phases.present_fast_window(s, "inv_end", during_turn=True)
        self.assertTrue(queued)
        labels = [o.label for o in s.decision_queue[0].options]
        self.assertTrue(any("Skids" in l for l in labels), labels)

    def test_forced_turn_end_closes_during_turn_window(self) -> None:
        from arkham import phases

        s = self._guest_hall_state("01003")
        s.limits[f"turn_forcibly_ended:{s.round}"] = True
        queued = phases.present_fast_window(s, "inv_end", during_turn=False)
        if queued:
            labels = [o.label for o in s.decision_queue[0].options]
            self.assertFalse(any("Skids" in l or l.startswith("Advance act") for l in labels), labels)
