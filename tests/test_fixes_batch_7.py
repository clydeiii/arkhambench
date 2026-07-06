from __future__ import annotations

import unittest

from arkham import actions, campaign, effects, phases, skill_test
from arkham.cards import player as player_cards
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_devourer_below as db
from arkham.scenarios import the_gathering as tg
from arkham.scenarios import the_midnight_masks as mm


class SeqRng:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = list(tokens)

    def choice(self, values):  # type: ignore[no-untyped-def]
        return self.tokens.pop(0) if self.tokens else values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def gathering_state(investigator: str = "roland"):
    state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
    state.investigator.card_code = {"roland": "01001", "agnes": "01004"}.get(investigator, "01001")
    state.investigator.id = investigator
    state.investigator.name = "Agnes Baker" if investigator == "agnes" else "Roland Banks"
    state.decision_queue = []
    state.investigator.hand = []
    state.investigator.deck = []
    state.investigator.discard = []
    state.investigator.play_area = []
    state.investigator.threat_area = []
    state.investigator.resources = 10
    state.investigator.actions_remaining = 3
    return state


def add_card(state, code: str, zone: str = "hand", instance_id: str | None = None) -> str:
    instance_id = instance_id or f"{code}_{len(state.card_instances)}"
    state.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone=zone, owner=state.investigator.id)
    if zone == "hand":
        state.investigator.hand.append(instance_id)
    elif zone == "play":
        state.investigator.play_area.append(instance_id)
        player_cards.setup_uses(state.card_instances[instance_id])
    elif zone == "threat":
        state.investigator.threat_area.append(instance_id)
    elif zone == "deck":
        state.investigator.deck.append(instance_id)
    return instance_id


def add_enemy(state, code: str, location: str, *, engaged: bool = True, enemy_id: str | None = None) -> str:
    enemy_id = enemy_id or f"enemy_{code}_{len(state.enemies)}"
    state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    state.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location)
    state.locations[location].enemy_ids.append(enemy_id)
    if engaged:
        state.enemies[enemy_id].engaged_with = state.investigator.id
        state.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


def move_to(state, location_id: str) -> None:
    old = state.investigator.location_id
    if old in state.locations and state.investigator.id in state.locations[old].investigator_ids:
        state.locations[old].investigator_ids.remove(state.investigator.id)
    state.investigator.location_id = location_id
    if state.investigator.id not in state.locations[location_id].investigator_ids:
        state.locations[location_id].investigator_ids.append(state.investigator.id)


class FixesBatch7Tests(unittest.TestCase):
    def test_campaign_log_devourer_block_does_not_clobber_midnight_fields(self) -> None:
        state = {
            "log": {
                "cultists_interrogated": [],
                "cultists_got_away": ["Herman Collins"],
                "past_midnight": True,
                "ghoul_priest_alive": True,
            },
            "chaos_bag_additions": [],
            "deck": {},
        }
        campaign.apply_campaign_log(
            state,
            {"scenario": "the_devourer_below", "campaign": {"scenario": "the_devourer_below", "ritual_broken": True, "elderthing_added": True}},
        )
        self.assertEqual(state["log"]["cultists_got_away"], ["Herman Collins"])
        self.assertTrue(state["log"]["past_midnight"])
        self.assertTrue(state["log"]["ritual_broken"])

    def test_deduction_logs_only_actual_additional_clues_and_hunter_block(self) -> None:
        state = gathering_state()
        state.locations[state.investigator.location_id].clues = 0
        deduction = add_card(state, "01039")
        events: list[dict] = []
        skill_test.start(state, events, skill="intellect", difficulty=1, source="Investigate Study", on_success={"kind": "investigate"})
        skill_test.commit_card(state, {"card": deduction}, events)
        skill_test.finish_commit(state, SeqRng(["+1"]), events)  # type: ignore[arg-type]
        self.assertFalse(any(event["type"] == "deduction" for event in events))

        masked = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        masked.decision_queue = []
        masked.locations[masked.investigator.location_id].clues = 2
        hunter = add_enemy(masked, "01121b", masked.investigator.location_id, engaged=True, enemy_id="hunter")
        masked.investigator.hand = []
        deduction = add_card(masked, "01039")
        events = []
        skill_test.start(masked, events, skill="intellect", difficulty=1, source="Investigate Your House", on_success={"kind": "investigate"})
        skill_test.commit_card(masked, {"card": deduction}, events)
        skill_test.finish_commit(masked, SeqRng(["+1"]), events)  # type: ignore[arg-type]
        self.assertIn(hunter, masked.investigator.engaged_enemies)
        self.assertEqual([event["type"] for event in events if event["type"] in {"clue_discovery_blocked", "deduction"}], ["clue_discovery_blocked"])

    def test_two_magnifying_glasses_stack_in_options_and_resolution(self) -> None:
        state = gathering_state()
        add_card(state, "01030", "play", "glass1")
        add_card(state, "01040", "play", "glass2")
        label = next(option.label for option in actions.legal_actions(state) if option.payload.get("action") == "investigate")
        self.assertIn("Intellect(5)", label)
        events: list[dict] = []
        actions.execute(state, {"kind": "action", "action": "investigate"}, events, SeqRng(["0"]))
        self.assertEqual(state.active_skill_test["base"], 5)
        skill_test.finish_commit(state, SeqRng(["0"]), events)  # type: ignore[arg-type]
        self.assertEqual(state.limits["last_skill_test"]["base"], 5)

    def test_unconditional_symbol_effects_happen_before_test_result_and_cultist_doom_on_success_or_fail(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland")
        state.decision_queue = []
        ghoul = add_enemy(state, "50038", "main_path", engaged=True, enemy_id="ghoul")
        state.investigator.combat = 6
        events: list[dict] = []
        actions.execute(state, {"kind": "action", "action": "fight", "enemy": ghoul}, events, SeqRng(["tablet"]))
        skill_test.finish_commit(state, SeqRng(["tablet"]), events)  # type: ignore[arg-type]
        event_types = [event["type"] for event in events]
        self.assertLess(event_types.index("damage_assigned"), event_types.index("skill_test_result"))
        self.assertLess(event_types.index("damage_assigned"), event_types.index("enemy_damaged"))

        for token in ["+1", "-4"]:
            masked = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
            masked.decision_queue = []
            cultist = add_enemy(masked, "01169", masked.investigator.location_id, engaged=True)
            skill_test.start(masked, [], skill="willpower", difficulty=3, source="Cultist timing")
            masked.active_skill_test["token"] = "cultist"
            masked.active_skill_test["modifier"] = 1 if token == "+1" else -4
            skill_test.resolve(masked, [], ArkhamRng(1))
            self.assertEqual(masked.enemies[cultist].doom, 1)

    def test_wrath_damage_path_loops_for_full_margin_and_mixed_choices(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland")
        state.decision_queue = []
        db.present_wrath_choices(state, 3)
        for _ in range(3):
            state.decision_queue = []
            db.resolve_scenario_choice(state, {"choice": "wrath_damage"}, [], ArkhamRng(1))
        self.assertEqual((state.investigator.damage, state.investigator.horror), (3, 3))
        self.assertFalse(state.decision_queue)

        mixed = db.build_state(difficulty="standard", rng=ArkhamRng(2), deck_path=None, investigator_slug="roland")
        mixed.decision_queue = []
        card = mixed.investigator.hand[0]
        db.present_wrath_choices(mixed, 2)
        mixed.decision_queue = []
        db.resolve_scenario_choice(mixed, {"choice": "wrath_discard", "card": card}, [], ArkhamRng(1))
        mixed.decision_queue = []
        db.resolve_scenario_choice(mixed, {"choice": "wrath_damage"}, [], ArkhamRng(1))
        self.assertIn(card, mixed.investigator.discard)
        self.assertEqual((mixed.investigator.damage, mixed.investigator.horror), (1, 1))
        self.assertFalse(mixed.decision_queue)

    def test_devourer_tablet_and_treachery_horror_both_apply(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland")
        state.decision_queue = []
        add_enemy(state, "50038", "main_path", engaged=True, enemy_id="monster")
        skill_test.start(state, [], skill="willpower", difficulty=6, source="Rotting Remains", on_failure={"kind": "horror_per_fail", "source": "Rotting Remains"})
        skill_test.finish_commit(state, SeqRng(["tablet"]), [])  # type: ignore[arg-type]
        self.assertEqual(state.investigator.damage, 1)
        self.assertGreaterEqual(state.investigator.horror, 1)

    def test_on_wings_skips_noop_move_but_still_disengages(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland", house_burned=True)
        state.decision_queue = []
        nightgaunt = add_enemy(state, "01172", "rivertown", engaged=True)
        acolyte = add_enemy(state, "01169", "rivertown", engaged=True)
        events: list[dict] = []
        mm.on_wings_aftermath(state, events, failed=False)
        self.assertIn(nightgaunt, state.investigator.engaged_enemies)
        self.assertNotIn(acolyte, state.investigator.engaged_enemies)
        self.assertFalse(any(event["type"] == "investigator_moved" for event in events))

    def test_agnes_reaction_during_aoo_preserves_move_resume_and_decline_path(self) -> None:
        for use_reaction in [True, False]:
            state = tg.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="agnes")
            state.decision_queue = []
            state.investigator.hand = []
            state.investigator.deck = []
            state.investigator.discard = []
            state.investigator.play_area = []
            state.investigator.threat_area = []
            state.investigator.resources = 10
            state.investigator.actions_remaining = 3
            state.locations["study"].connections = ["guest_hall"]
            state.locations["guest_hall"].connections = ["study"]
            ghoul = add_enemy(state, "01160", "study", engaged=True)
            events: list[dict] = []
            actions.execute(state, {"kind": "action", "action": "move", "location": "guest_hall"}, events, ArkhamRng(1))
            self.assertEqual(state.decision_queue[0].id, "agnes-after-horror")
            payload = state.decision_queue.pop(0).options[0 if use_reaction else -1].payload
            effects.resolve_agnes_horror_reaction(state, payload, events)
            phases.advance_until_decision(state, ArkhamRng(1), events)
            self.assertEqual(state.investigator.location_id, "guest_hall")
            if use_reaction:
                self.assertEqual(state.enemies[ghoul].damage, 1)

    def test_devourer_wizard_doom_uses_devourer_agenda_not_midnight_masks(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland")
        state.decision_queue = []
        wizard = add_enemy(state, "01170", "main_path", engaged=False, enemy_id="wizard")
        state.agenda.doom = 3
        events: list[dict] = []
        db.end_mythos_phase(state, events, ArkhamRng(1))
        self.assertEqual(state.agenda.name, "The Arkham Woods")
        self.assertNotIn("setaside_agenda_enemy", state.enemies)
        self.assertNotEqual(state.result and state.result.get("summary"), "R2: the clock struck midnight")
        self.assertEqual(state.enemies[wizard].doom, 1)
        effects.check_agenda_advance(state, events, rng=ArkhamRng(1))
        self.assertEqual(state.agenda.name, "The Ritual Begins")

    def test_agenda_dispatch_canary_keeps_each_scenario_in_its_family(self) -> None:
        cases = [
            ("the_midnight_masks", mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland"), "Time Is Running Short"),
            ("return_to_the_midnight_masks", mm.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland"), "Time Is Running Short"),
            ("the_devourer_below", db.build_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland"), "The Ritual Begins"),
            ("return_to_the_devourer_below", db.build_return_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland"), "The Ritual Begins"),
        ]
        for scenario, state, expected_agenda in cases:
            state.decision_queue = []
            state.agenda.doom = state.agenda.threshold
            effects.check_agenda_advance(state, [], rng=ArkhamRng(2))
            self.assertEqual(state.scenario, scenario)
            self.assertEqual(state.agenda.name, expected_agenda)
            self.assertFalse(state.result and "clock struck midnight" in str(state.result.get("summary", "")) and "devourer" in scenario)

        for scenario, builder in [
            ("the_gathering", tg.build_gathering_state),
            ("return_to_the_gathering", tg.build_return_state),
        ]:
            state = builder(difficulty="standard", rng=ArkhamRng(1))
            state.decision_queue = []
            state.agenda.doom = state.agenda.threshold
            effects.check_agenda_advance(state, [], rng=ArkhamRng(2))
            self.assertEqual(state.scenario, scenario)
            self.assertTrue(state.decision_queue and state.decision_queue[0].id == "agenda1-back")
            self.assertNotIn("setaside_agenda_enemy", state.enemies)


if __name__ == "__main__":
    unittest.main()
