from __future__ import annotations

import unittest

from arkham import actions, effects, encounter, enemies, phases, skill_test
from arkham.cards import player as player_cards
from arkham.chaos import token_modifier
from arkham.model import CardInstance, EnemyInstance
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


def clear_state(state) -> None:
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


def add_card(state, code: str, zone: str = "hand", card_id: str | None = None) -> str:
    card_id = card_id or f"{code}_{len(state.card_instances)}"
    state.card_instances[card_id] = CardInstance(id=card_id, card_code=code, zone=zone, owner=state.investigator.id)
    if zone == "hand":
        state.investigator.hand.append(card_id)
    elif zone == "deck":
        state.investigator.deck.append(card_id)
    elif zone == "play":
        state.investigator.play_area.append(card_id)
        player_cards.setup_uses(state.card_instances[card_id])
    elif zone == "encounter_drawn":
        pass
    return card_id


def add_enemy(state, code: str, enemy_id: str, *, location: str | None = None, engaged: bool = True) -> str:
    location = location or state.investigator.location_id
    state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    state.enemies[enemy_id] = EnemyInstance(id=enemy_id, card_code=code, location_id=location)
    state.locations[location].enemy_ids.append(enemy_id)
    if engaged:
        state.enemies[enemy_id].engaged_with = state.investigator.id
        state.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


class FixesBatch11Tests(unittest.TestCase):
    def test_60_forbidden_knowledge_pays_horror_before_resource_effect(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(state)
        state.investigator.id = "agnes"
        state.investigator.name = "Agnes Baker"
        state.investigator.card_code = "01004"
        knowledge = add_card(state, "01058", "play", "knowledge")
        ghoul = add_enemy(state, "01160", "ghoul")
        events: list[dict] = []

        actions.resolve_fast_ability(state, {"ability": "forbidden_knowledge", "card": knowledge}, events)

        self.assertEqual(state.investigator.horror, 1)
        self.assertEqual(state.investigator.resources, 10)
        self.assertEqual(state.card_instances[knowledge].uses["secrets"], 4)
        self.assertEqual(state.decision_queue[0].id, "agnes-after-horror")
        effects.resolve_agnes_horror_reaction(state, state.decision_queue.pop(0).options[0].payload, events)
        phases.advance_until_decision(state, ArkhamRng(1), events)
        self.assertEqual(state.investigator.resources, 11)
        self.assertEqual(state.card_instances[knowledge].uses["secrets"], 3)
        self.assertEqual(state.enemies[ghoul].damage, 1)

        boosted = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(boosted)
        training = add_card(boosted, "01017", "play", "training")
        events = []
        skill_test.start(boosted, events, skill="willpower", difficulty=4, source="Physical Training ordering")
        skill_test.apply_skill_boost(boosted, {"card_code": "01017", "skill": "willpower"}, events)
        self.assertEqual(boosted.investigator.resources, 9)
        skill_test.finish_commit(boosted, SeqRng(["0"]), events)
        event_types = [event["type"] for event in events]
        self.assertLess(event_types.index("skill_boost"), event_types.index("skill_test_result"))

    def test_61_searches_only_decline_when_no_eligible_card_found(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(state)
        initiate = add_card(state, "01063", "play", "initiate")
        shrivelling = add_card(state, "01060", "deck", "shrivelling")
        add_card(state, "01088", "deck", "cache")

        actions.resolve_fast_ability(state, {"ability": "arcane_initiate", "card": initiate}, [])
        labels = [option.label for option in state.decision_queue[0].options]
        self.assertIn("Draw Shrivelling", labels)
        self.assertNotIn("Draw no Spell", labels)

        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(state)
        initiate = add_card(state, "01063", "play", "initiate")
        add_card(state, "01088", "deck", "cache")
        actions.resolve_fast_ability(state, {"ability": "arcane_initiate", "card": initiate}, [])
        self.assertEqual([option.label for option in state.decision_queue[0].options], ["Draw no Spell"])

        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(state)
        librarian = add_card(state, "01032", "hand", "librarian")
        add_card(state, "01035", "deck", "medical")
        actions.play_card(state, librarian, [], ArkhamRng(1))
        self.assertNotIn("Decline", [option.label for option in state.decision_queue[0].options])

    def test_62_return_act_back_test_resolves_before_next_act_is_current(self) -> None:
        state = tg.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        state.investigator.location_id = "guest_hall"
        state.locations["study"].investigator_ids = []
        state.locations["guest_hall"].investigator_ids = [state.investigator.id]
        state.investigator.clues = 3
        events: list[dict] = []

        actions.execute(state, {"kind": "action", "action": "advance_act"}, events, SeqRng(["0"]))

        self.assertEqual(state.act.name, "Mysterious Gateway")
        self.assertEqual(state.active_skill_test["source"], "Breaking the Wall")
        skill_test.finish_commit(state, SeqRng(["0"]), events)
        self.assertEqual(state.act.name, "The Barrier")

    def test_64_after_fail_investigation_reactions_work_with_substituted_skills(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        state.locations["main_path"].code = "01153"
        state.locations["main_path"].shroud = 3
        state.locations["main_path"].clues = 2
        state.investigator.agility = 2
        add_card(state, "01079", "hand", "look")
        actions.execute(state, {"kind": "action", "action": "investigate"}, [], SeqRng(["0"]))
        skill_test.finish_commit(state, SeqRng(["0"]), [])
        labels = [option.label for option in state.decision_queue[0].options]
        self.assertTrue(any("Look what I found" in label for label in labels))

    def test_65_fast_asset_play_enforces_hand_slots(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(state)
        add_card(state, "01030", "play", "glass1")
        add_card(state, "01040", "play", "glass2")
        blade = add_card(state, "01044", "hand", "blade")
        actions.resolve_fast_ability(state, {"ability": "play_fast_asset", "card": blade}, [])
        self.assertEqual(state.decision_queue[0].id, "slot-discard-for-play")
        self.assertEqual(state.investigator.resources, 9)
        self.assertNotIn(blade, state.investigator.play_area)

    def test_66_unengaged_aloof_enemy_must_be_engaged_before_fight(self) -> None:
        state = mm.build_return_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        acolyte = add_enemy(state, "01169", "acolyte", engaged=False)
        mask = add_card(state, "50043", "encounter_drawn", "mask")
        state.card_instances[mask].zone = "attachment"
        state.enemies[acolyte].attachments.append(mask)
        labels = [option.label for option in actions.legal_actions(state)]
        self.assertFalse(any(label.startswith("Fight Acolyte") for label in labels))
        self.assertTrue(any(label.startswith("Engage Acolyte") for label in labels))
        enemies.engage_enemy(state, [], acolyte)
        self.assertTrue(any(option.label.startswith("Fight Acolyte") for option in actions.legal_actions(state)))

    def test_67_umordhoths_hunger_kills_after_discarding_last_card(self) -> None:
        state = db.build_return_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland")
        clear_state(state)
        last = add_card(state, "01089", "hand", "last")
        hunger = add_card(state, "50037", "encounter_drawn", "hunger")
        db.encounter_revelation(state, SeqRng([last]), [], hunger)
        self.assertEqual(state.status, "ended")
        self.assertIn(last, state.investigator.discard)
        self.assertEqual(state.result["summary"], "Umordhoth's Hunger killed the investigator")

    def test_68_committed_success_effects_resolve_before_twisting_paths_move(self) -> None:
        state = db.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        state.investigator.location_id = "twisting_paths"
        state.locations["main_path"].investigator_ids = []
        state.locations["twisting_paths"].investigator_ids = [state.investigator.id]
        state.locations["twisting_paths"].revealed = True
        perception = add_card(state, "01090", "hand", "perception")
        add_card(state, "01088", "deck", "drawn")
        events: list[dict] = []
        actions.execute(state, {"kind": "action", "action": "move", "location": "main_path"}, events, SeqRng(["+1"]))
        skill_test.commit_card(state, {"card": perception}, events)
        skill_test.finish_commit(state, SeqRng(["+1"]), events)
        event_types = [event["type"] for event in events]
        self.assertLess(event_types.index("card_drawn"), event_types.index("investigator_moved"))

    def test_69_shrivelling_symbol_horror_resolves_at_reveal_before_attack_result(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(state)
        state.investigator.id = "agnes"
        state.investigator.name = "Agnes Baker"
        state.investigator.card_code = "01004"
        state.investigator.willpower = 5
        shrivelling = add_card(state, "01060", "play", "shrivelling")
        ghoul = add_enemy(state, "01160", "ghoul")
        events: list[dict] = []
        actions.execute(state, {"kind": "action", "action": "asset_fight", "asset": shrivelling, "enemy": ghoul, "damage": 2, "skill": "willpower", "spend_use": "charges", "symbol_horror": True}, events, SeqRng(["skull"]))
        skill_test.finish_commit(state, SeqRng(["skull"]), events)
        self.assertEqual(state.decision_queue[0].id, "agnes-after-horror")
        self.assertEqual(state.enemies[ghoul].damage, 0)
        self.assertFalse(any(event["type"] == "skill_test_result" for event in events))

    def test_70_devourer_reuses_got_away_cultist_parley_and_forced_routes(self) -> None:
        names = ["Herman Collins", "Peter Warren", "Victoria Devereux", "Jeremiah Pierce", "Alma Hill", "Ruth Turner", "Billy Cooper"]
        state = db.build_return_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland", cultists_got_away=names)
        clear_state(state)
        state.investigator.clues = 3
        state.investigator.hand = [add_card(state, "01089", "hand", f"card{i}") for i in range(4)]
        db.put_ritual_site_into_play(state, [])
        db.spawn_got_away_cultists(state, [])
        labels = [option.label for option in actions.legal_actions(state)]
        for expected in ["Herman Collins", "Peter Warren", "Victoria Devereux", "Jeremiah Pierce", "Alma Hill"]:
            self.assertTrue(any(expected in label for label in labels), expected)
        ruth = next(enemy_id for enemy_id, enemy in state.enemies.items() if enemy.card_code == "01141")
        enemies.evade_enemy(state, [], ruth)
        self.assertIn(ruth, state.victory_display)
        billy = next(enemy_id for enemy_id, enemy in state.enemies.items() if enemy.card_code == "50045")
        monster = add_enemy(state, "01160", "monster")
        enemies.defeat_enemy(state, [], monster)
        self.assertIn(billy, state.victory_display)

    def test_71_wendy_amulet_elder_sign_prints_auto_success_vs_zero(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
        clear_state(state)
        state.investigator.card_code = "01005"
        state.investigator.name = "Wendy Adams"
        add_card(state, "01014", "play", "amulet")
        events: list[dict] = []
        skill_test.start(state, events, skill="agility", difficulty=4, source="Wendy test")
        skill_test.finish_commit(state, SeqRng(["eldersign"]), events)
        result = next(event["message"] for event in events if event["type"] == "skill_test_result")
        self.assertIn("vs 0", result)

    def test_56_on_defeat_clue_reaction_logs_only_actual_discovery(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        state.locations[state.investigator.location_id].clues = 2
        hunter = add_enemy(state, "01121b", "hunter")
        rat = add_enemy(state, "01159", "rat")
        events: list[dict] = []
        enemies.resolve_enemy_defeated_reaction(state, {"reaction": "roland", "enemy": rat}, events)
        self.assertIn(hunter, state.investigator.engaged_enemies)
        self.assertEqual([event["type"] for event in events], ["clue_discovery_blocked"])

    def test_74_midnight_masks_standard_skull_uses_highest_cultist_doom(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        peter = add_enemy(state, "01139", "peter")
        wizard = add_enemy(state, "01170", "wizard", engaged=False)
        state.enemies[peter].doom = 2
        state.enemies[wizard].doom = 1
        self.assertEqual(token_modifier(state, "skull"), (-2, False))

    def test_75_on_wings_success_does_nothing(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(1), investigator_slug="roland")
        clear_state(state)
        state.investigator.location_id = "southside"
        state.locations["southside"].investigator_ids = [state.investigator.id]
        ghoul = add_enemy(state, "01160", "ghoul", location="southside")
        events: list[dict] = []
        mm.on_wings_aftermath(state, events, failed=False)
        self.assertEqual(state.investigator.location_id, "southside")
        self.assertIn(ghoul, state.investigator.engaged_enemies)
        self.assertEqual(events, [])

    def test_76_enemy_phase_attacks_only_engaged_same_named_instance_and_logs_id(self) -> None:
        state = db.build_return_state(difficulty="standard", rng=ArkhamRng(1), deck_path=None, investigator_slug="roland")
        clear_state(state)
        engaged = add_enemy(state, "50038", "eater_engaged", location="main_path", engaged=True)
        unengaged = add_enemy(state, "50038", "eater_unengaged", location="main_path", engaged=False)
        state.phase = "Enemy"
        events: list[dict] = []
        phases.run_enemy_phase(state, events, ArkhamRng(1))
        attacks = [event for event in events if event["type"] == "enemy_attack"]
        self.assertEqual(len(attacks), 1)
        self.assertEqual(attacks[0]["data"]["enemy"], engaged)
        self.assertIn("[eater_engaged]", attacks[0]["message"])
        self.assertNotIn(unengaged, state.limits.get(f"enemy_phase_attacked:{state.round}", []))

        state = db.build_return_state(difficulty="standard", rng=ArkhamRng(2), deck_path=None, investigator_slug="roland")
        clear_state(state)
        engaged = add_enemy(state, "50038", "aoo_engaged", location="main_path", engaged=True)
        add_enemy(state, "50038", "aoo_unengaged", location="main_path", engaged=False)
        self.assertEqual(actions.aoo_attackers(state, "draw"), [engaged])


if __name__ == "__main__":
    unittest.main()
