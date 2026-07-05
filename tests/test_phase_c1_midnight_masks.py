from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path

from arkham import chaos, effects, enemies
from arkham.game import Game
from arkham.model import CardInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_midnight_masks as mm


def codes(state, ids):
    return Counter(state.card_instances[card_id].card_code for card_id in ids)


class MidnightMasksSetupTests(unittest.TestCase):
    def test_original_setup_counts_and_campaign_inputs(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        self.assertEqual(len(state.encounter_deck), 21)
        self.assertEqual(
            codes(state, state.encounter_deck),
            Counter(
                {
                    "01135": 3,
                    "01136": 2,
                    "01169": 3,
                    "01170": 1,
                    "01171": 2,
                    "01172": 2,
                    "01173": 2,
                    "01167": 2,
                    "01168": 2,
                    "01174": 2,
                }
            ),
        )
        self.assertEqual(len(state.limits["cultist_deck"]), 5)
        self.assertEqual(state.investigator.location_id, "your_house")
        self.assertEqual(state.agenda.code, "01121a")
        self.assertEqual(state.agenda.threshold, 6)
        self.assertEqual(state.act.code, "01123")

        burned = mm.build_state(
            difficulty="standard",
            rng=ArkhamRng(1),
            investigator_slug="roland",
            house_burned=True,
            ghoul_priest_alive=True,
            lita_forced_to_find_others=True,
        )
        self.assertNotIn("your_house", burned.locations)
        self.assertEqual(burned.investigator.location_id, "rivertown")
        self.assertEqual(len(burned.encounter_deck), 22)
        self.assertEqual(codes(burned, burned.encounter_deck)["01116"], 1)
        self.assertEqual(
            burned.limits["campaign_inputs"],
            {"house_burned": True, "ghoul_priest_alive": True, "lita_forced": True},
        )

    def test_return_setup_counts_and_seeded_variants(self) -> None:
        a = mm.build_return_state(difficulty="standard", rng=ArkhamRng(7), investigator_slug="roland")
        b = mm.build_return_state(difficulty="standard", rng=ArkhamRng(7), investigator_slug="roland")
        self.assertEqual(len(a.encounter_deck), 23)
        self.assertEqual(
            codes(a, a.encounter_deck),
            Counter(
                {
                    "01135": 3,
                    "01136": 2,
                    "50041": 3,
                    "50042": 1,
                    "50043": 2,
                    "01172": 2,
                    "01173": 2,
                    "01167": 2,
                    "01168": 2,
                    "01174": 2,
                    "50031": 2,
                }
            ),
        )
        self.assertEqual(len(a.limits["cultist_deck"]), 5)
        self.assertEqual(
            {loc: a.locations[loc].code for loc in ("rivertown", "easttown", "northside", "miskatonic_university", "southside", "downtown")},
            {loc: b.locations[loc].code for loc in ("rivertown", "easttown", "northside", "miskatonic_university", "southside", "downtown")},
        )


class MidnightMasksRulesTests(unittest.TestCase):
    def test_act_draw_spends_clues_and_spawns_named_cultist(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        peter = next(card_id for card_id in state.limits["cultist_deck"] if state.card_instances[card_id].card_code == "01139")
        state.limits["cultist_deck"] = [peter]
        state.investigator.clues = 2
        events = []

        mm.draw_from_cultist_deck(state, events)

        self.assertEqual(state.investigator.clues, 0)
        self.assertEqual(state.limits["cultist_deck"], [])
        self.assertIn(peter, state.enemies)
        self.assertEqual(state.enemies[peter].location_id, "miskatonic_university")
        self.assertEqual(state.card_instances[peter].zone, "enemy")

    def test_agenda_one_flip_spawns_hunter_and_clears_all_doom(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        state.decision_queue = []
        events = []
        state.agenda.doom = 5
        acolyte = state.encounter_deck[0]
        state.card_instances[acolyte].card_code = "01169"
        mm.spawn_enemy_resolving_forced(state, events, acolyte, "rivertown", ArkhamRng(1))

        self.assertEqual(state.agenda.stage, 2)
        self.assertEqual(state.agenda.code, "01122")
        self.assertEqual(mm.total_doom(state), 0)
        hunter = "setaside_agenda_enemy"
        self.assertIn(hunter, state.enemies)
        self.assertIn(hunter, state.investigator.engaged_enemies)

    def test_masked_hunter_blocks_discover_and_spend(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        state.decision_queue = []
        events = []
        state.agenda.doom = 6
        mm.check_agenda_advance(state, events, rng=ArkhamRng(1))
        state.locations[state.investigator.location_id].clues = 1
        state.investigator.clues = 2

        self.assertEqual(effects.discover_clue(state, 1, events), 0)
        self.assertEqual(state.investigator.clues, 2)
        self.assertFalse(effects.spend_clues(state, 2, events))
        self.assertEqual(state.investigator.clues, 2)

    def test_token_modifiers_and_tablet_clue_drop(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        events = []
        acolyte = state.encounter_deck[0]
        state.card_instances[acolyte].card_code = "01169"
        mm.spawn_enemy_resolving_forced(state, events, acolyte, "rivertown", ArkhamRng(1))
        state.enemies[acolyte].doom = 3

        self.assertEqual(chaos.token_modifier(state, "skull"), (-3, False))
        self.assertEqual(chaos.token_modifier(state, "cultist"), (-2, False))
        self.assertEqual(chaos.token_modifier(state, "tablet"), (-3, False))
        state.investigator.clues = 2
        mm.apply_token_aftermath(state, events, {"token": "tablet", "success": False}, ArkhamRng(1))
        self.assertEqual(state.investigator.clues, 1)
        self.assertEqual(state.locations[state.investigator.location_id].clues, 2)

        hard = mm.build_state(difficulty="hard", rng=ArkhamRng(1), investigator_slug="roland")
        hard.agenda.doom = 2
        eid = hard.encounter_deck[0]
        hard.card_instances[eid].card_code = "01169"
        mm.spawn_enemy_resolving_forced(hard, [], eid, "rivertown", ArkhamRng(1))
        hard.enemies[eid].doom = 4
        self.assertEqual(chaos.token_modifier(hard, "skull"), (-6, False))
        self.assertEqual(chaos.token_modifier(hard, "tablet"), (-4, False))

    def test_mask_of_umordhoth_adds_health_and_aloof_or_retaliate(self) -> None:
        state = mm.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        events = []
        acolyte = state.encounter_deck[0]
        state.card_instances[acolyte].card_code = "50041"
        mm.spawn_enemy_resolving_forced(state, events, acolyte, "rivertown", ArkhamRng(1))
        mask = next(card_id for card_id in state.encounter_deck if state.card_instances[card_id].card_code == "50043")
        mm.attach_mask_to_enemy(state, mask, acolyte, events, ArkhamRng(1))

        self.assertEqual(enemies.enemy_health(state, acolyte), 3)
        self.assertTrue(enemies.is_aloof(state, acolyte))
        enemies.engage_ready_enemies_at_roland(state, events)
        self.assertNotIn(acolyte, state.investigator.engaged_enemies)

        unique = state.limits["cultist_deck"][0]
        state.card_instances[unique].card_code = "01139"
        mm.spawn_named_cultist(state, events, unique)
        mask2 = next(card_id for card_id in state.encounter_deck if card_id != mask and state.card_instances[card_id].card_code == "50043")
        mm.attach_mask_to_enemy(state, mask2, unique, events, ArkhamRng(1))
        self.assertTrue(enemies.has_retaliate(state, unique))

    def test_corpse_taker_moves_and_dumps_doom(self) -> None:
        state = mm.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        corpse = next(card_id for card_id in state.encounter_deck if state.card_instances[card_id].card_code == "50042")
        events = []
        mm.spawn_enemy_resolving_forced(state, events, corpse, "graveyard", ArkhamRng(1))
        state.enemies[corpse].doom = 2
        mm.end_enemy_phase(state, events, ArkhamRng(1))
        self.assertEqual(state.enemies[corpse].location_id, "rivertown")
        mm.end_enemy_phase(state, events, ArkhamRng(1))
        self.assertEqual(state.enemies[corpse].doom, 0)
        self.assertEqual(state.agenda.doom, 2)

    def test_result_campaign_block_and_no_insight_bonus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Game.new(
                seed=1,
                difficulty="standard",
                deck_path=None,
                run_dir=Path(tmp) / "run",
                scenario="the_midnight_masks",
                investigator="roland",
            )
            game.apply(1)
            decision = game.current_decision()
            resign = next(index for index, option in enumerate(decision.options, start=1) if option.payload.get("action") == "resign")
            game.apply(resign)
            result = game.state.result
            self.assertEqual(result["outcome"], "R1")
            self.assertEqual(result["xp"], result["victory_points"])
            self.assertEqual(result["campaign"]["scenario"], "the_midnight_masks")
            self.assertIn("The Masked Hunter", result["campaign"]["cultists_got_away"])


if __name__ == "__main__":
    unittest.main()
