from __future__ import annotations

import unittest

from arkham import actions, effects, encounter, enemies, phases, skill_test
from arkham.cards import player as player_cards
from arkham.model import AgendaState, CardInstance, EnemyInstance, PendingDecision, DecisionOption
from arkham.rng import ArkhamRng
from arkham.scenarios import the_devourer_below as db
from arkham.scenarios import the_gathering as tg
from arkham.scenarios import the_midnight_masks as mm


class SeqRng:
    def __init__(self, values: list[str]) -> None:
        self.values = list(values)

    def choice(self, values):  # type: ignore[no-untyped-def]
        return self.values.pop(0) if self.values else values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def clear_state(state) -> None:  # type: ignore[no-untyped-def]
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


def add_card(state, code: str, zone: str, card_id: str) -> str:  # type: ignore[no-untyped-def]
    state.card_instances[card_id] = CardInstance(
        id=card_id,
        card_code=code,
        zone=zone,
        owner=state.investigator.id,
    )
    if zone == "hand":
        state.investigator.hand.append(card_id)
    elif zone == "deck":
        state.investigator.deck.append(card_id)
    elif zone == "play":
        state.investigator.play_area.append(card_id)
        player_cards.setup_uses(state.card_instances[card_id])
    elif zone == "threat":
        state.investigator.threat_area.append(card_id)
    elif zone == "encounter_deck":
        state.encounter_deck.append(card_id)
    return card_id


def add_enemy(state, code: str, enemy_id: str, location: str | None = None, *, engaged: bool = False) -> str:  # type: ignore[no-untyped-def]
    location = location or state.investigator.location_id
    state.card_instances[enemy_id] = CardInstance(
        id=enemy_id,
        card_code=code,
        zone="enemy",
        owner=state.investigator.id if code == "01101" else None,
    )
    state.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location)
    state.locations[location].enemy_ids.append(enemy_id)
    if engaged:
        state.enemies[enemy_id].engaged_with = state.investigator.id
        state.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


def assign_all_to_investigator(state, events, rng=None) -> None:  # type: ignore[no-untyped-def]
    while state.pending_damage:
        decision = state.decision_queue.pop(0)
        option = next(option for option in decision.options if option.payload.get("target") == "roland")
        effects.assign_damage_choice(state, option.payload, events, rng)


def move_investigator(state, location_id: str) -> None:  # type: ignore[no-untyped-def]
    old = state.investigator.location_id
    if old in state.locations and state.investigator.id in state.locations[old].investigator_ids:
        state.locations[old].investigator_ids.remove(state.investigator.id)
    state.investigator.location_id = location_id
    if state.investigator.id not in state.locations[location_id].investigator_ids:
        state.locations[location_id].investigator_ids.append(state.investigator.id)


class FixesBatch12Tests(unittest.TestCase):
    def test_86_alma_draws_resolve_in_order_and_victory_waits(self) -> None:
        state = mm.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        state.agenda.threshold = 99
        state.investigator.clues = 0
        state.encounter_deck = []
        state.encounter_discard = []
        alma = add_enemy(state, "50046", "alma", engaged=True)
        add_card(state, "50031", "encounter_deck", "horrors")
        add_card(state, "01135", "encounter_deck", "shadow")
        fog = add_card(state, "01168", "encounter_deck", "fog")
        events: list[dict] = []

        mm.parley_cultist(state, alma, events, SeqRng([]))
        self.assertEqual(state.agenda.doom, 1)
        self.assertEqual(state.decision_queue[0].id, "hunting-shadow")
        self.assertNotIn(alma, state.victory_display)
        shadow_choice = state.decision_queue.pop(0).options[-1].payload
        mm.resolve_scenario_choice(state, shadow_choice, events, SeqRng([]))
        assign_all_to_investigator(state, events, SeqRng([]))
        ward = add_card(state, "01065", "hand", "ward")
        phases.advance_until_decision(state, SeqRng([]), events)
        self.assertEqual(state.investigator.damage, 2)
        self.assertEqual(state.decision_queue[0].id, "revelation-cancel")
        self.assertNotIn(alma, state.victory_display)
        ward_choice = state.decision_queue.pop(0).options[-1].payload
        encounter.resolve_ward_revelation(state, ward_choice, events, SeqRng([]))
        phases.advance_until_decision(state, SeqRng([]), events)
        self.assertIn(fog, state.locations[state.investigator.location_id].attached_instance_ids)
        self.assertIn(alma, state.victory_display)
        self.assertIn(ward, state.investigator.hand)

    def test_86_alma_waits_for_third_draw_skill_test(self) -> None:
        state = mm.build_return_state(difficulty="standard", rng=ArkhamRng(2), investigator_slug="roland")
        clear_state(state)
        state.encounter_deck = []
        state.encounter_discard = []
        state.encounter_deck = []
        state.encounter_discard = []
        alma = add_enemy(state, "50046", "alma", engaged=True)
        add_card(state, "01168", "encounter_deck", "fog1")
        add_card(state, "01168", "encounter_deck", "fog2")
        add_card(state, "01167", "encounter_deck", "chill")
        mm.parley_cultist(state, alma, [], SeqRng([]))
        self.assertIsNotNone(state.active_skill_test)
        self.assertNotIn(alma, state.victory_display)
        skill_test.finish_commit(state, SeqRng(["+1"]), [])
        phases.advance_until_decision(state, SeqRng([]), [])
        self.assertIn(alma, state.victory_display)

    def test_87_move_engages_before_graveyard_test(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        current = state.investigator.location_id
        state.locations[current].connections = ["graveyard"]
        state.locations["graveyard"].connections = [current]
        herman = add_enemy(state, "01138", "herman", "graveyard")
        events: list[dict] = []
        actions.move(state, "graveyard", events, ArkhamRng(1))
        types = [event["type"] for event in events]
        self.assertIn(herman, state.investigator.engaged_enemies)
        self.assertLess(types.index("enemy_engaged"), types.index("skill_test_started"))

    def test_89_fallback_mask_has_no_mask_doom_but_in_play_attach_does(self) -> None:
        state = mm.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        state.encounter_deck = []
        state.encounter_discard = []
        state.locations = {state.investigator.location_id: state.locations[state.investigator.location_id]}
        mask = add_card(state, "50043", "encounter_drawn", "mask")
        acolyte = add_card(state, "01169", "encounter_deck", "acolyte")
        mm.mask_of_umordhoth(state, [], SeqRng([]), mask)
        self.assertEqual(state.enemies[acolyte].doom, 1)
        self.assertIn(mask, state.enemies[acolyte].attachments)

        mask2 = add_card(state, "50043", "encounter_drawn", "mask2")
        other = add_enemy(state, "01169", "other")
        mm.attach_mask_to_enemy(state, mask2, other, [], ArkhamRng(1))
        self.assertEqual(state.enemies[other].doom, 1)

    def test_91_cultist_token_ties_choose_and_unique_target_is_automatic(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        one = add_enemy(state, "01169", "one")
        two = add_enemy(state, "01170", "two")
        mm.apply_token_aftermath(state, [], {"token": "cultist", "success": True}, ArkhamRng(1))
        self.assertEqual(state.decision_queue[0].id, "chaos-cultist-target")
        choice = state.decision_queue.pop(0).options[1].payload
        mm.resolve_scenario_choice(state, choice, [], ArkhamRng(1))
        self.assertEqual(state.enemies[two].doom, 1)

        state.decision_queue = []
        state.enemies.pop(two)
        state.locations[state.investigator.location_id].enemy_ids.remove(two)
        mm.apply_token_aftermath(state, [], {"token": "cultist", "success": True}, ArkhamRng(1))
        self.assertEqual(state.enemies[one].doom, 1)
        self.assertFalse(state.decision_queue)

        devourer = db.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(devourer)
        add_enemy(devourer, "01169", "a")
        add_enemy(devourer, "01170", "b")
        devourer.active_skill_test = {"token": "cultist", "extra_tokens": []}
        db.apply_token_reveal_effects(devourer, [], devourer.active_skill_test, ArkhamRng(1))
        self.assertEqual(devourer.decision_queue[0].kind, "token_reveal_reaction")
        self.assertEqual(sum(enemy.doom for enemy in devourer.enemies.values()), 0)

    def test_92_act_back_spawn_resolves_disciple_forced(self) -> None:
        for clues in (0, 1):
            state = db.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
            clear_state(state)
            db.put_ritual_site_into_play(state, [])
            state.agenda.stage = 2
            state.investigator.clues = clues
            state.encounter_deck = []
            disciple = add_card(state, "50041", "encounter_deck", f"disciple{clues}")
            db.spawn_enemy_from_top_until(state, [], rng=ArkhamRng(1), location_id="ritual_site", monster_only=False, doom=0)
            self.assertEqual(state.enemies[disciple].doom, 1)
            self.assertEqual(state.investigator.clues, 0)
            if clues:
                self.assertEqual(state.locations["ritual_site"].clues, 3)

    def test_93_disciple_forced_precedes_fallback_mask_attach(self) -> None:
        state = db.build_return_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland")
        clear_state(state)
        state.agenda.stage = 1
        state.encounter_deck = []
        state.encounter_discard = []
        mask = add_card(state, "50043", "encounter_drawn", "mask")
        disciple = add_card(state, "50041", "encounter_deck", "disciple")
        mm.mask_of_umordhoth(state, [], SeqRng([]), mask)
        self.assertEqual(state.decision_queue[0].id, "enemy-spawn-location")
        spawn_choice = state.decision_queue.pop(0).options[0].payload
        db.resolve_scenario_choice(state, spawn_choice, [], ArkhamRng(1))
        self.assertEqual(state.decision_queue[0].id, "disciple-forced")
        self.assertNotIn(mask, state.enemies[disciple].attachments)
        disciple_choice = state.decision_queue.pop(0).options[0].payload
        db.resolve_scenario_choice(state, disciple_choice, [], ArkhamRng(1))
        self.assertIn(mask, state.enemies[disciple].attachments)
        self.assertEqual(state.enemies[disciple].doom, 1)

    def test_94_corpse_taker_transfer_waits_for_mythos_advance_check(self) -> None:
        for builder, target, module in ((mm.build_return_state, "rivertown", mm), (db.build_return_state, "main_path", db)):
            kwargs = {"difficulty": "standard", "rng": ArkhamRng(1), "investigator_slug": "roland"}
            if module is db:
                kwargs["deck_path"] = None
            state = builder(**kwargs)
            clear_state(state)
            state.agenda = AgendaState(code="agenda", name="Agenda 1", stage=1, threshold=3, doom=2)
            corpse = add_enemy(state, "50042", "corpse", target)
            state.enemies[corpse].doom = 1
            module.end_enemy_phase(state, [], ArkhamRng(1))
            self.assertEqual(state.agenda.stage, 1)
            self.assertEqual(state.agenda.doom, 3)
            effects.check_agenda_advance(state, [], rng=ArkhamRng(1))
            self.assertNotEqual(state.agenda.stage, 1)

    def test_95_end_mythos_forced_fires_once_after_fast_window(self) -> None:
        state = mm.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        state.phase = "Mythos"
        state.round = 2
        state.limits["mythos_doom_placed:2"] = True
        state.limits["mythos_encounter_drawn:2"] = True
        corpse = add_enemy(state, "50042", "corpse", "rivertown")
        debt = add_card(state, "01011", "threat", "debt")
        events: list[dict] = []
        phases.advance_until_decision(state, ArkhamRng(1), events)
        self.assertEqual(state.enemies[corpse].doom, 0)
        use = next(option.payload for option in state.decision_queue.pop(0).options if option.payload.get("ability") == "hospital_debts")
        actions.execute(state, use, events, ArkhamRng(1))
        phases.advance_until_decision(state, ArkhamRng(1), events)
        passed = state.decision_queue.pop(0).options[-1].payload
        state.limits[passed["key"]] = True
        phases.advance_until_decision(state, ArkhamRng(1), events)
        self.assertEqual(state.card_instances[debt].uses["resources"], 1)
        self.assertEqual(state.enemies[corpse].doom, 1)
        mm.end_mythos_phase(state, events, ArkhamRng(1))
        self.assertEqual(state.enemies[corpse].doom, 1)

    def test_96_agenda3_waits_for_amnesia_revelation(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        state.agenda = AgendaState(code="01144", name="The Ritual Begins", stage=2, threshold=5)
        add_card(state, "01089", "hand", "keep1")
        add_card(state, "01090", "hand", "keep2")
        skill_test.apply_callback(
            state,
            [],
            {"kind": "devourer_agenda2"},
            success=False,
            margin=1,
            rng=SeqRng(["01096"]),
        )
        self.assertEqual(state.agenda.stage, 2)
        self.assertEqual(state.decision_queue[0].id, "amnesia-keep")
        choice = state.decision_queue.pop(0).options[0].payload
        effects.resolve_amnesia_keep(state, choice, [])
        phases.advance_until_decision(state, ArkhamRng(1), [])
        self.assertEqual(state.agenda.stage, 3)

    def test_97_agenda_back_spawn_doom_is_logged(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        state.encounter_deck = []
        ghoul = add_card(state, "01160", "encounter_deck", "ghoul")
        events: list[dict] = []
        db.spawn_enemy_from_top_until(state, events, rng=ArkhamRng(1), location_id="main_path", monster_only=True, doom=1)
        self.assertEqual(state.enemies[ghoul].doom, 1)
        doom_event = next(event for event in events if event["type"] == "doom_placed")
        self.assertEqual(doom_event["data"]["source"], "Death to the Intruders")

    def test_98_milan_reaction_accept_pass_and_blanking(self) -> None:
        for choice, expected in (("gain", 1), ("pass", 0)):
            state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
            clear_state(state)
            add_card(state, "01033", "play", "milan")
            state.investigator.resources = 0
            state.locations[state.investigator.location_id].clues = 1
            skill_test.start(state, [], skill="intellect", difficulty=0, source="Investigate", on_success={"kind": "investigate"})
            skill_test.finish_commit(state, SeqRng(["0"]), [])
            self.assertEqual(state.decision_queue[0].id, "milan-reaction")
            payload = next(option.payload for option in state.decision_queue.pop(0).options if option.payload["choice"] == choice)
            skill_test.resolve_milan_reaction(state, payload, [])
            self.assertEqual(state.investigator.resources, expected)

        blanked = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(blanked)
        add_card(blanked, "01033", "play", "milan")
        add_enemy(blanked, "01103", "priest")
        blanked.locations[blanked.investigator.location_id].clues = 1
        skill_test.start(blanked, [], skill="intellect", difficulty=0, source="Investigate", on_success={"kind": "investigate"})
        skill_test.finish_commit(blanked, SeqRng(["0"]), [])
        self.assertFalse(any(decision.id == "milan-reaction" for decision in blanked.decision_queue))

    def test_99_elusive_from_twisting_paths_tests_and_failed_move_only_is_canceled(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="wendy")
        clear_state(state)
        move_investigator(state, "twisting_paths")
        state.locations["twisting_paths"].revealed = True
        elusive = add_card(state, "01050", "hand", "elusive")
        foe = add_enemy(state, "01160", "foe", engaged=True)
        events: list[dict] = []
        actions.resolve_fast_ability(
            state,
            {"ability": "elusive", "card": elusive, "location": "main_path"},
            events,
        )
        self.assertEqual(state.active_skill_test["source"], "Twisting Paths")
        self.assertNotIn(foe, state.investigator.engaged_enemies)
        skill_test.finish_commit(state, SeqRng(["-4"]), events)
        self.assertEqual(state.investigator.location_id, "twisting_paths")
        self.assertIn(elusive, state.investigator.discard)
        self.assertEqual(state.investigator.resources, 8)

    def test_100_great_willow_only_surges_revelation_owned_tests(self) -> None:
        state = db.build_return_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland")
        clear_state(state)
        state.encounter_deck = []
        state.encounter_discard = []
        willow = next(location_id for location_id in state.locations if location_id != "main_path")
        state.locations[willow].code = "50033"
        move_investigator(state, willow)
        rotting = add_card(state, "01163", "encounter_drawn", "rotting")
        add_card(state, "01168", "encounter_deck", "next")
        events: list[dict] = []
        encounter.resolve_revelation(state, SeqRng(["0"]), events, rotting)
        skill_test.finish_commit(state, SeqRng(["0"]), events)
        self.assertTrue(any(event["type"] == "surge" for event in events))
        self.assertNotIn("next", state.encounter_deck)

        frozen = db.build_return_state(difficulty="standard", rng=ArkhamRng(2), deck_path=None, investigator_slug="roland")
        clear_state(frozen)
        frozen.encounter_deck = []
        frozen.encounter_discard = []
        willow = next(location_id for location_id in frozen.locations if location_id != "main_path")
        frozen.locations[willow].code = "50033"
        move_investigator(frozen, willow)
        add_card(frozen, "01168", "encounter_deck", "still_there")
        events = []
        skill_test.start(frozen, events, skill="willpower", difficulty=3, source="Frozen in Fear", on_success={"kind": "discard_threat_on_success", "card_code": "01164"})
        skill_test.finish_commit(frozen, SeqRng(["0"]), events)
        self.assertFalse(any(event["type"] == "surge" for event in events))
        self.assertIn("still_there", frozen.encounter_deck)

    def test_101_heal_logs_actual_amount(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(state)
        state.investigator.damage = 1
        state.investigator.horror = 1
        events: list[dict] = []
        effects.heal_roland(state, events, damage=3, horror=3)
        self.assertEqual([event["data"]["amount"] for event in events], [1, 1])
        self.assertTrue(all("healed 1" in event["message"] for event in events))

    def test_102_location_extra_tokens_follow_wendy_window_and_are_once_per_test(self) -> None:
        state = db.build_return_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="wendy")
        clear_state(state)
        lake = next(location_id for location_id in state.locations if location_id != "main_path")
        state.locations[lake].code = "50034"
        move_investigator(state, lake)
        add_card(state, "01089", "hand", "discard")
        events: list[dict] = []
        skill_test.start(state, events, skill="intellect", difficulty=2, source="Investigate Lakeside", on_success={"kind": "investigate"})
        skill_test.finish_commit(state, SeqRng(["-1", "autofail"]), events)
        self.assertEqual(state.decision_queue[0].id, "wendy-token-reaction")
        self.assertEqual(len([event for event in events if event["type"] == "chaos_token"]), 1)
        redraw = next(option.payload for option in state.decision_queue.pop(0).options if option.payload.get("choice") == "redraw")
        skill_test.resolve_wendy_token_reaction(state, redraw, events, SeqRng(["0", "-2"]))
        self.assertTrue(state.active_skill_test is None or state.limits["last_skill_test"]["extra_tokens"] == ["-2"])
        self.assertEqual(len([event for event in events if event["data"].get("extra")]), 1)

        state = db.build_return_state(difficulty="standard", rng=ArkhamRng(2), deck_path=None, investigator_slug="wendy")
        clear_state(state)
        lake = next(location_id for location_id in state.locations if location_id != "main_path")
        state.locations[lake].code = "50034"
        move_investigator(state, lake)
        add_card(state, "01089", "hand", "discard")
        events = []
        skill_test.start(state, events, skill="intellect", difficulty=2, source="Investigate Lakeside", on_success={"kind": "investigate"})
        skill_test.finish_commit(state, SeqRng(["0"]), events)
        first_pass = state.decision_queue.pop(0).options[-1].payload
        skill_test.resolve_wendy_token_reaction(state, first_pass, events, SeqRng(["-1"]))
        redraw = next(option.payload for option in state.decision_queue.pop(0).options if option.payload.get("choice") == "redraw")
        skill_test.resolve_wendy_token_reaction(state, redraw, events, SeqRng(["+1", "-4"]))
        self.assertEqual(len([event for event in events if event["data"].get("extra")]), 1)

    def test_103_museum_damage_resume_spends_one_action(self) -> None:
        state = mm.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        museum = "miskatonic_university"
        state.locations[museum].code = "50029"
        move_investigator(state, museum)
        events: list[dict] = []
        actions.execute(state, {"kind": "action", "action": "midnight_location_museum"}, events, ArkhamRng(1))
        assign_all_to_investigator(state, events, ArkhamRng(1))
        self.assertEqual(state.investigator.actions_remaining, 2)
        self.assertEqual(state.investigator.horror, 2)
        self.assertEqual(state.investigator.clues, 1)

    def test_104_screeching_byakhee_conditional_stats_respect_mind_wipe(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(state)
        byakhee = add_enemy(state, "01175", "byakhee", engaged=True)
        state.investigator.horror = state.investigator.sanity - 4
        self.assertEqual((enemies.enemy_fight_value(state, byakhee), enemies.enemy_evade_value(state, byakhee)), (4, 4))
        state.investigator.horror = state.investigator.sanity - 5
        self.assertEqual((enemies.enemy_fight_value(state, byakhee), enemies.enemy_evade_value(state, byakhee)), (3, 3))
        state.investigator.horror = state.investigator.sanity - 4
        state.limits[f"mind_wipe:{state.phase}:{byakhee}"] = True
        self.assertEqual((enemies.enemy_fight_value(state, byakhee), enemies.enemy_evade_value(state, byakhee)), (3, 3))

    def test_105_player_weakness_enemy_goes_to_owner_discard_and_cannot_reshuffle(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        mob = add_enemy(state, "01101", "mob", engaged=True)
        enemies.defeat_enemy(state, [], mob)
        self.assertIn(mob, state.investigator.discard)
        self.assertNotIn(mob, state.encounter_discard)
        normal = add_card(state, "01168", "encounter_discard", "normal")
        state.encounter_discard.append(normal)
        encounter.reshuffle(state, ArkhamRng(1), [])
        self.assertNotIn(mob, state.encounter_deck)

    def test_86_revelation_presenters_append_behind_existing_decisions(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        sentinel = PendingDecision("sentinel", "scenario", "First", [DecisionOption("Pass", {"kind": "scenario", "choice": "noop"})])
        state.decision_queue = [sentinel]
        ward = add_card(state, "01065", "hand", "ward")
        treachery = add_card(state, "01168", "encounter_drawn", "treachery")
        self.assertTrue(encounter.present_revelation_cancel(state, treachery))
        self.assertEqual([decision.id for decision in state.decision_queue], ["sentinel", "revelation-cancel"])
        state.decision_queue = [sentinel]
        mm.hunting_shadow(state, [], treachery)
        self.assertEqual([decision.id for decision in state.decision_queue], ["sentinel", "hunting-shadow"])
        self.assertIn(ward, state.investigator.hand)


if __name__ == "__main__":
    unittest.main()
