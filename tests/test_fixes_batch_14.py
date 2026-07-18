from __future__ import annotations

import json
import unittest

from arkham import actions, campaign, effects, phases, skill_test, upgrade
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_gathering
from tests.test_phase_c2_campaign import CampaignTempCase


def clean_state():  # type: ignore[no-untyped-def]
    state = the_gathering.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
    state.investigator.hand = []
    state.investigator.deck = []
    state.investigator.discard = []
    state.investigator.play_area = []
    state.investigator.threat_area = []
    state.investigator.engaged_enemies = []
    state.investigator.resources = 10
    state.investigator.actions_remaining = 0
    state.decision_queue = []
    state.encounter_deck = []
    state.encounter_discard = []
    return state


def add_card(state, code: str, zone: str, card_id: str) -> str:  # type: ignore[no-untyped-def]
    state.card_instances[card_id] = CardInstance(
        id=card_id, card_code=code, zone=zone, owner=state.investigator.id
    )
    if zone == "hand":
        state.investigator.hand.append(card_id)
    elif zone == "deck":
        state.investigator.deck.append(card_id)
    elif zone == "play":
        state.investigator.play_area.append(card_id)
    return card_id


def add_engaged_enemy(state) -> str:  # type: ignore[no-untyped-def]
    enemy_id = "enemy"
    location_id = state.investigator.location_id
    state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code="01159", zone="enemy")
    state.enemies[enemy_id] = EnemyInstance(
        id=enemy_id,
        card_code="01159",
        location_id=location_id,
        engaged_with=state.investigator.id,
    )
    state.locations[location_id].enemy_ids.append(enemy_id)
    state.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


class LitaSlotTests(unittest.TestCase):
    def test_playing_second_ally_discards_lita_before_it_enters_play(self) -> None:
        state = clean_state()
        lita = add_card(state, "01117", "play", "lita")
        initiate = add_card(state, "01063", "hand", "initiate")

        actions.play_card(state, initiate, [])

        self.assertEqual(state.decision_queue[0].id, "slot-discard-for-play")
        self.assertEqual([option.payload["discard"] for option in state.decision_queue[0].options], [lita])
        self.assertNotIn(initiate, state.investigator.play_area)
        payload = state.decision_queue.pop(0).options[0].payload
        actions.resolve_slot_discard(state, payload, [])
        self.assertNotIn(lita, state.investigator.play_area)
        self.assertIn(initiate, state.investigator.play_area)

    def test_playing_lita_discard_other_ally_first(self) -> None:
        state = clean_state()
        initiate = add_card(state, "01063", "play", "initiate")
        lita = add_card(state, "01117", "hand", "lita")

        actions.play_card(state, lita, [])

        self.assertEqual(state.decision_queue[0].id, "slot-discard-for-play")
        self.assertEqual([option.payload["discard"] for option in state.decision_queue[0].options], [initiate])
        payload = state.decision_queue.pop(0).options[0].payload
        actions.resolve_slot_discard(state, payload, [])
        self.assertNotIn(initiate, state.investigator.play_area)
        self.assertIn(lita, state.investigator.play_area)

    def test_gaining_control_of_story_lita_enforces_ally_capacity(self) -> None:
        state = clean_state()
        initiate = add_card(state, "01063", "play", "initiate")
        lita = "story_lita"
        state.card_instances[lita] = CardInstance(id=lita, card_code="01117", zone="story")
        state.locations[state.investigator.location_id].attached_instance_ids.append(lita)

        skill_test.apply_callback(
            state,
            [],
            {"kind": "lita_parley", "lita": lita},
            success=True,
            margin=0,
        )

        self.assertIn(lita, state.investigator.play_area)
        self.assertEqual(state.decision_queue[0].id, "slot-overflow-discard")
        payload = next(
            option.payload
            for option in state.decision_queue[0].options
            if option.payload["discard"] == initiate
        )
        state.decision_queue = []
        actions.resolve_slot_discard(state, payload, [])
        self.assertNotIn(initiate, state.investigator.play_area)
        self.assertIn(lita, state.investigator.play_area)

    def test_book_of_shadows_arcane_slot_bonus_is_unchanged(self) -> None:
        state = clean_state()
        book = add_card(state, "01070", "play", "book")
        arcane = [
            add_card(state, "01060", "play", "spell_1"),
            add_card(state, "01061", "play", "spell_2"),
            add_card(state, "01060", "play", "spell_3"),
        ]

        self.assertTrue(actions.slot_fits(state, "Arcane", arcane))
        self.assertIn(book, state.investigator.play_area)
        self.assertFalse(actions.slot_fits(state, "Arcane", arcane + ["spell_4"]))


class PostFinalActionWindowIntegrationTests(unittest.TestCase):
    def test_phase_loop_offers_ready_arcane_initiate_after_final_action(self) -> None:
        state = clean_state()
        add_card(state, "01063", "play", "initiate")
        add_card(state, "01060", "deck", "spell")

        phases.advance_until_decision(state, ArkhamRng(1), [])

        self.assertEqual(state.decision_queue[0].id, "fast-window-inv_end")
        self.assertTrue(any("Arcane Initiate" in option.label for option in state.decision_queue[0].options))

    def test_pass_precedes_dark_memory_and_does_not_reopen_inv_end(self) -> None:
        state = clean_state()
        state.investigator.card_code = "01003"
        state.investigator.name = '"Skids" O\'Toole'
        add_card(state, "01013", "hand", "memory")
        add_card(state, "01059", "play", "rosary")
        add_engaged_enemy(state)
        events: list[dict] = []

        phases.advance_until_decision(state, ArkhamRng(1), events)
        self.assertEqual(state.decision_queue[0].id, "fast-window-inv_end")
        pass_payload = state.decision_queue[0].options[-1].payload
        state.limits[str(pass_payload["key"])] = True
        state.decision_queue = []

        phases.advance_until_decision(state, ArkhamRng(1), events)
        self.assertEqual(state.decision_queue[0].id, "assign-damage")
        self.assertTrue(any(event["type"] == "dark_memory_revealed" for event in events))
        for _ in range(2):
            payload = state.decision_queue.pop(0).options[0].payload
            effects.assign_damage_choice(
                state, payload, events, ArkhamRng(1)
            )
        phases.advance_until_decision(state, ArkhamRng(1), events)

        self.assertEqual(state.phase, "Enemy")
        self.assertNotEqual(state.decision_queue[0].id, "fast-window-inv_end")
        self.assertEqual(
            sum(event["type"] == "dark_memory_revealed" for event in events), 1
        )

    def test_forced_turn_end_skips_window_and_fires_forced_effect(self) -> None:
        state = clean_state()
        add_card(state, "01063", "play", "initiate")
        add_card(state, "01060", "deck", "spell")
        add_card(state, "01013", "hand", "memory")
        state.limits[f"turn_forcibly_ended:{state.round}"] = True
        events: list[dict] = []

        phases.advance_until_decision(state, ArkhamRng(1), events)

        self.assertEqual(state.decision_queue[0].id, "assign-damage")
        self.assertTrue(any(event["type"] == "dark_memory_revealed" for event in events))
        self.assertFalse(any(decision.id == "fast-window-inv_end" for decision in state.decision_queue))

    def test_no_legal_fast_options_auto_skips_to_forced_effect(self) -> None:
        state = clean_state()
        add_card(state, "01013", "hand", "memory")
        add_card(state, "01059", "play", "rosary")

        phases.advance_until_decision(state, ArkhamRng(1), [])

        self.assertEqual(state.decision_queue[0].id, "assign-damage")
        self.assertTrue(state.limits[f"fastwin:inv_end:{state.round}"])


class PurchaseLedgerTests(CampaignTempCase):
    def test_two_buys_persist_through_upgrade_done_and_campaign_record(self) -> None:
        campaign_dir = self.campaign_dir("purchase-ledger")
        campaign.create_campaign(
            campaign_dir, investigator="roland", difficulty="standard", seed=14
        )
        first_run, _ = campaign.start_next_scenario(campaign_dir)
        self.write_result(first_run, xp=10)
        state = campaign.record_current_run(campaign_dir, run_arg=str(first_run))

        upgrade.buy_card(state, "50002", replace="01024")
        upgrade.buy_card(state, "01091", remove="01019")
        expected = [
            {"window": 2, "code": "50002", "replaced": "01024", "removed": None, "price": 2},
            {"window": 2, "code": "01091", "replaced": None, "removed": "01019", "price": 1},
        ]
        self.assertEqual(state["purchases"], expected)

        campaign.save_campaign(campaign_dir, state)
        done = campaign.finish_upgrade(campaign_dir)
        self.assertEqual(done["purchases"], expected)

        second_run, _ = campaign.start_next_scenario(campaign_dir)
        self.write_result(second_run, scenario="return_to_the_midnight_masks")
        recorded = campaign.record_current_run(campaign_dir, run_arg=str(second_run))
        self.assertEqual(recorded["purchases"], expected)

        campaign.finish_upgrade(campaign_dir)
        third_run, _ = campaign.start_next_scenario(campaign_dir)
        self.write_result(third_run, scenario="return_to_the_devourer_below")
        completed = campaign.record_current_run(campaign_dir, run_arg=str(third_run))
        self.assertEqual(completed["purchases"], expected)
        summary = json.loads(
            (campaign_dir / "campaign_summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(summary["purchases"], expected)


if __name__ == "__main__":
    unittest.main()
