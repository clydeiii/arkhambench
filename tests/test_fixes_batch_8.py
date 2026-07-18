from __future__ import annotations

import unittest

from arkham import actions, effects, enemies, phases, skill_test
from arkham.cards import player as player_cards
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_devourer_below as db
from arkham.scenarios import the_gathering as tg
from arkham.scenarios import the_midnight_masks as mm


class SeqRng:
    def __init__(self, values: list[str]) -> None:
        self.values = list(values)

    def choice(self, values):  # type: ignore[no-untyped-def]
        wanted = self.values.pop(0) if self.values else values[0]
        return wanted if wanted in values else values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def clean_state(investigator: str = "roland"):
    state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
    codes = {"roland": "01001", "daisy": "01002", "skids": "01003", "agnes": "01004", "wendy": "01005"}
    names = {"roland": "Roland Banks", "daisy": "Daisy Walker", "skids": '"Skids" O\'Toole', "agnes": "Agnes Baker", "wendy": "Wendy Adams"}
    state.investigator.id = investigator
    state.investigator.card_code = codes[investigator]
    state.investigator.name = names[investigator]
    state.investigator.hand = []
    state.investigator.deck = []
    state.investigator.discard = []
    state.investigator.play_area = []
    state.investigator.threat_area = []
    state.investigator.engaged_enemies = []
    state.investigator.resources = 10
    state.investigator.actions_remaining = 3
    state.turn.action_index = 0
    state.decision_queue = []
    state.chaos_bag.tokens = ["0"]
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
    elif zone == "discard":
        state.investigator.discard.append(instance_id)
    return instance_id


def add_enemy(state, code: str, location: str | None = None, *, engaged: bool = True, enemy_id: str | None = None) -> str:
    location = location or state.investigator.location_id
    enemy_id = enemy_id or f"enemy_{code}_{len(state.enemies)}"
    state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    state.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location)
    state.locations[location].enemy_ids.append(enemy_id)
    if engaged:
        state.enemies[enemy_id].engaged_with = state.investigator.id
        state.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


class FixesBatch8Tests(unittest.TestCase):
    def test_34_no_post_turn_fast_window_after_final_action(self) -> None:
        state = clean_state("skids")
        add_card(state, "01036", "hand", "mom")
        state.investigator.actions_remaining = 2
        actions.execute(state, {"kind": "action", "action": "pass"}, [])
        events: list[dict] = []
        phases.advance_until_decision(state, ArkhamRng(1), events)
        self.assertFalse(state.decision_queue and state.decision_queue[0].id == "fast-window-inv_end")

    def test_35_enemy_doom_waits_for_agenda_check(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        state.decision_queue = []
        acolyte = add_enemy(state, "01169", state.investigator.location_id, engaged=False)
        state.agenda.doom = state.agenda.threshold - 1
        mm.place_doom_on_enemy(state, acolyte, 1, [], source="Acolyte", rng=ArkhamRng(1))
        self.assertEqual(state.agenda.stage, 1)
        self.assertEqual(state.enemies[acolyte].doom, 1)
        effects.check_agenda_advance(state, [], rng=ArkhamRng(1))
        self.assertEqual(state.agenda.stage, 2)

    def test_36_hunting_nightgaunt_doubles_negative_evade_tokens(self) -> None:
        state = clean_state("wendy")
        nightgaunt = add_enemy(state, "01172")
        state.chaos_bag.tokens = ["-1"]
        events: list[dict] = []
        actions.execute(state, {"kind": "action", "action": "evade", "enemy": nightgaunt}, events, SeqRng(["-1"]))
        skill_test.finish_commit(state, SeqRng(["-1"]), events)  # type: ignore[arg-type]
        self.assertEqual(state.limits["last_skill_test"]["modifier"], -2)

    def test_37_young_deep_one_forced_horror_on_engage(self) -> None:
        state = clean_state()
        young = add_enemy(state, "01181", engaged=False)
        events: list[dict] = []
        enemies.engage_enemy(state, events, young)
        self.assertEqual(state.investigator.horror, 1)

    def test_38_weaknesses_are_excluded_from_optional_discard_costs(self) -> None:
        state = clean_state("wendy")
        add_card(state, "01096", "hand", "amnesia")
        add_card(state, "01081", "hand", "manual")
        skill_test.start(state, [], skill="agility", difficulty=1, source="Wendy check")
        state.active_skill_test["token"] = "-1"
        state.active_skill_test["modifier"] = -1
        skill_test.present_token_reveal_reaction(state, ArkhamRng(1), [])
        labels = [option.label for option in state.decision_queue[0].options]
        self.assertFalse(any("Amnesia" in label for label in labels))

        masked = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        masked.decision_queue = []
        masked.investigator.hand = []
        for code in ["01096", "01017", "01089", "01090", "01091"]:
            add_card(masked, code, "hand", code)
        herman = add_enemy(masked, "01138", masked.investigator.location_id, engaged=False, enemy_id="herman")
        mm.present_herman_discard_choice(masked, herman)
        self.assertFalse(any("Amnesia" in option.label for option in masked.decision_queue[0].options))

    def test_39_tokens_clear_when_cards_leave_play(self) -> None:
        state = clean_state()
        initiate = add_card(state, "01063", "play", "initiate")
        state.card_instances[initiate].doom = 1
        player_cards.discard_from_play(state, initiate)
        self.assertEqual(state.card_instances[initiate].doom, 0)

        enemy = add_enemy(state, "01169", engaged=True, enemy_id="acolyte")
        state.enemies[enemy].doom = 2
        enemies.defeat_enemy(state, [], enemy)
        self.assertNotIn(enemy, state.enemies)
        self.assertEqual(tg.total_doom(state), state.agenda.doom)

    def test_40_moving_engaged_enemy_away_disengages_it(self) -> None:
        state = clean_state()
        state.locations["attic"].revealed = True
        enemy = add_enemy(state, "50042", state.investigator.location_id, engaged=True)
        enemies.move_enemy_to(state, [], enemy, "attic")
        self.assertIsNone(state.enemies[enemy].engaged_with)
        self.assertNotIn(enemy, state.investigator.engaged_enemies)

    def test_41_madness_weakness_to_hand_resolves_revelation(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland")
        state.decision_queue = []
        db.gain_madness_weakness(state, [], SeqRng(["01099"]), to_hand=True)  # type: ignore[arg-type]
        psychosis = next(card_id for card_id, inst in state.card_instances.items() if inst.card_code == "01099")
        self.assertIn(psychosis, state.investigator.threat_area)
        self.assertNotIn(psychosis, state.investigator.hand)

    def test_42_played_card_is_limbo_during_aoo_and_fizzle_keeps_paid_cost(self) -> None:
        state = clean_state()
        machete = add_card(state, "01020", "hand", "machete")
        manual = add_card(state, "01089", "hand", "manual")
        add_enemy(state, "50038", engaged=True, enemy_id="grave")
        state.investigator.resources = 5
        actions.execute(state, {"kind": "action", "action": "play", "card": machete}, [], SeqRng([manual]))  # type: ignore[list-item,arg-type]
        self.assertEqual(state.investigator.resources, 2)
        self.assertIn(machete, state.investigator.play_area)
        self.assertIn(manual, state.investigator.discard)

        fizzle = clean_state()
        add_card(fizzle, "01020", "discard", "lost")
        fizzle.investigator.resources = 2
        actions.play_card(fizzle, "lost", [], cost_paid=True, paid_cost=3)
        self.assertEqual(fizzle.investigator.resources, 2)

    def test_44_leo_de_luca_grants_action_each_turn_for_either_copy(self) -> None:
        state = clean_state()
        add_card(state, "01054", "play", "leo1")
        self.assertEqual(phases.starting_actions(state), 4)
        state.investigator.actions_remaining = 2
        state.turn.action_index = 2
        player_cards.discard_from_play(state, "leo1")
        self.assertEqual(state.investigator.actions_remaining, 2)

    def test_43_skill_modifiers_recompute_at_st5(self) -> None:
        state = clean_state()
        lita = add_card(state, "01117", "play", "lita")
        skill_test.start(state, [], skill="combat", difficulty=5, source="Fight test")
        self.assertEqual(state.active_skill_test["base"], 5)
        state.decision_queue = []
        state.active_skill_test["token"] = "0"
        state.active_skill_test["modifier"] = 0
        player_cards.discard_from_play(state, lita)
        skill_test.resolve(state, [], ArkhamRng(1))
        self.assertEqual(state.limits["last_skill_test"]["base"], 4)

    def test_45_logging_batch(self) -> None:
        got = list(db.NAMED_CULTIST_BY_NAME)[:1]
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland", cultists_got_away=got)
        events: list[dict] = []
        db.resolve_scenario_choice(state, {"choice": "keep_hand"}, events, ArkhamRng(1))
        self.assertTrue(any(event["type"] == "setup_effect" and "got away" in event["message"] for event in events))
        self.assertTrue(any(event["type"] == "setup_effect" and "elderthing" in event["message"] for event in events))

        masked = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        masked.decision_queue = []
        masked.agenda.stage = 2
        masked.investigator.clues = 1
        disciple = add_enemy(masked, "50041", masked.investigator.location_id, engaged=False)
        events = []
        mm.disciple_after_spawn(masked, events, disciple, ArkhamRng(1))
        self.assertTrue(any(event["type"] == "clue_placed" for event in events))

        museum = None
        for seed in range(1, 100):
            candidate = mm.build_return_state(difficulty="standard", rng=ArkhamRng(seed), investigator_slug="roland")
            if any(loc.code == "50029" for loc in candidate.locations.values()):
                museum = candidate
                break
        self.assertIsNotNone(museum)
        museum.decision_queue = []
        museum.investigator.location_id = next(loc_id for loc_id, loc in museum.locations.items() if loc.code == "50029")
        events = []
        mm.execute_location_action(museum, {"action": "midnight_location_museum"}, events, ArkhamRng(1))
        self.assertTrue(any(event["type"] == "clues_gained" and "from the token pool" in event["message"] for event in events))

        flame = clean_state()
        flame.locations[flame.investigator.location_id].clues = 1
        flame.limits["after_encounter_draw"] = {"kind": "drawn_to_the_flame"}
        events = []
        from arkham import encounter

        encounter.resolve_after_encounter_draw(flame, events)
        self.assertTrue(any(event["type"] == "drawn_to_the_flame" and event["data"].get("amount") == 1 for event in events))


if __name__ == "__main__":
    unittest.main()
