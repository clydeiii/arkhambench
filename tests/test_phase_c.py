from __future__ import annotations

import unittest

from arkham import actions, encounter, enemies, phases, skill_test
from arkham.cards.registry import REGISTRY
from arkham.effects import discover_clue, draw_player_card, end_game, resolve_cover_up_choice, start_damage_assignment
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


PHASE_C_CODES = {
    "01001", "01006", "01007", "01102", "01016", "01017", "01018", "01019",
    "01020", "01021", "01022", "01023", "01024", "01025", "01030", "01031",
    "01032", "01033", "01034", "01035", "01036", "01037", "01038", "01039",
    "01086", "01087", "01088", "01089", "01092", "01116", "01117", "01118",
    "01119", "01159", "01160", "01161", "01162", "01163", "01164", "01165",
    "01166", "01167", "01168", "01174",
}


def state(seed: int = 1):
    s = build_engine_test_state(difficulty="standard", rng=ArkhamRng(seed))
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.investigator.resources = 10
    s.chaos_bag.tokens = ["0"]
    s.decision_queue = []
    return s


def add_card(s, code: str, zone: str = "hand", instance_id: str | None = None) -> str:
    instance_id = instance_id or f"{code}_{len(s.card_instances)}"
    s.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone=zone)
    if zone == "hand":
        s.investigator.hand.append(instance_id)
    elif zone == "play":
        s.investigator.play_area.append(instance_id)
        from arkham.cards.player import setup_uses

        setup_uses(s.card_instances[instance_id])
    elif zone == "threat":
        s.investigator.threat_area.append(instance_id)
    elif zone == "deck":
        s.investigator.deck.append(instance_id)
    elif zone == "encounter_deck":
        s.encounter_deck.append(instance_id)
    return instance_id


def add_enemy(s, code: str, location: str = "study", engaged: bool = True, instance_id: str | None = None) -> str:
    instance_id = instance_id or f"enemy_{code}_{len(s.enemies)}"
    s.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="enemy")
    s.enemies[instance_id] = EnemyInstance(id=instance_id, card_code=code, location_id=location)
    s.locations[location].enemy_ids.append(instance_id)
    if engaged:
        s.enemies[instance_id].engaged_with = "roland"
        s.investigator.engaged_enemies.append(instance_id)
    return instance_id


def resolve_current_test(s, events=None):
    events = events if events is not None else []
    skill_test.finish_commit(s, ArkhamRng(1), events)
    if s.decision_queue and s.decision_queue[0].id == "post-reveal-boosts":
        s.decision_queue = []
        skill_test.resolve(s, events)
    return events


class PhaseCRegistryTests(unittest.TestCase):
    def test_every_phase_c_card_registered(self) -> None:
        missing = sorted(PHASE_C_CODES - set(REGISTRY))
        self.assertEqual(missing, [])


class PhaseCPlayerCardTests(unittest.TestCase):
    def test_roland_reaction_discovers_after_enemy_defeat_once_per_round(self) -> None:
        s = state()
        s.locations["study"].clues = 2
        enemy = add_enemy(s, "01159")
        events = []
        enemies.damage_enemy(s, events, enemy, 1)
        enemies.resolve_enemy_defeated_reaction(s, {"reaction": "roland"}, events)
        self.assertEqual(s.investigator.clues, 1)
        self.assertTrue(s.limits["roland_reaction:1"])

    def test_rolands_38_special_uses_location_clue_bonus_and_ammo(self) -> None:
        s = state()
        gun = add_card(s, "01006", "play")
        enemy = add_enemy(s, "01159")
        s.locations["study"].clues = 1
        events = []
        actions.execute(s, {"action": "asset_fight", "asset": gun, "enemy": enemy, "boost": 3, "damage": 2}, events)
        self.assertEqual(s.card_instances[gun].uses["ammo"], 3)
        self.assertEqual(s.active_skill_test["base"], 7)

    def test_cover_up_optionally_redirects_discovery_and_adds_game_end_trauma(self) -> None:
        s = state()
        cover = add_card(s, "01007", "threat")
        s.card_instances[cover].clues = 2
        s.locations["study"].clues = 3
        events = []
        discover_clue(s, 3, events)
        self.assertEqual(s.decision_queue[0].kind, "cover_up")
        resolve_cover_up_choice(s, s.decision_queue[0].options[0].payload, events)
        self.assertEqual(s.investigator.clues, 0)
        self.assertNotIn(cover, s.investigator.threat_area)
        discover_clue(s, 1, events)
        self.assertEqual(s.investigator.clues, 1)
        cover2 = add_card(s, "01007", "threat")
        s.card_instances[cover2].clues = 1
        end_game(s, events, "test end")
        self.assertEqual(s.trauma["mental"], 1)

    def test_silver_twilight_acolyte_draw_spawns_engaged_and_attack_adds_doom(self) -> None:
        s = state()
        acolyte = add_card(s, "01102", "deck")
        events = []
        draw_player_card(s, events)
        self.assertIn(acolyte, s.investigator.engaged_enemies)
        enemies.attack(s, events, acolyte, source="enemy phase")
        self.assertEqual(s.agenda.doom, 1)

    def test_45_automatic_spends_ammo_for_plus_damage_attack(self) -> None:
        s = state()
        gun = add_card(s, "01016", "play")
        rat = add_enemy(s, "01159")
        events = []
        actions.execute(s, {"action": "asset_fight", "asset": gun, "enemy": rat, "boost": 1, "damage": 2}, events)
        resolve_current_test(s, events)
        self.assertNotIn(rat, s.enemies)
        self.assertEqual(s.card_instances[gun].uses["ammo"], 3)

    def test_physical_training_boosts_only_before_reveal(self) -> None:
        s = state()
        add_card(s, "01017", "play")
        events = []
        skill_test.start(s, events, skill="willpower", difficulty=6, source="test")
        self.assertTrue(any(o.payload.get("kind") == "skill_boost" for o in s.decision_queue[0].options))
        skill_test.apply_skill_boost(s, {"card_code": "01017", "skill": "willpower"}, events)
        s.decision_queue = []
        skill_test.finish_commit(s, ArkhamRng(1), events)
        self.assertFalse(s.decision_queue)
        before = s.investigator.resources
        skill_test.apply_skill_boost(s, {"card_code": "01017", "skill": "willpower"}, events)
        self.assertEqual(s.investigator.resources, before)

    def test_beat_cop_static_and_discard_damage(self) -> None:
        s = state()
        cop = add_card(s, "01018", "play")
        rat = add_enemy(s, "01159")
        self.assertEqual(actions.player_cards.effective_base_skill(s, "combat", "Fight"), 5)
        actions.resolve_fast_ability(s, {"ability": "beat_cop", "card": cop, "enemy": rat}, [])
        self.assertNotIn(cop, s.investigator.play_area)
        self.assertNotIn(rat, s.enemies)

    def test_first_aid_heals_and_discards_when_empty(self) -> None:
        s = state()
        first_aid = add_card(s, "01019", "play")
        s.investigator.damage = 3
        events = []
        for _ in range(3):
            actions.first_aid(s, {"asset": first_aid, "heal": "damage"}, events)
        self.assertEqual(s.investigator.damage, 0)
        self.assertIn(first_aid, s.investigator.discard)

    def test_machete_extra_damage_only_when_enemy_is_sole_engaged_enemy(self) -> None:
        s = state()
        machete = add_card(s, "01020", "play")
        rat = add_enemy(s, "01159")
        options = []
        actions.add_asset_action_options(s, options)
        self.assertTrue(any(o.payload.get("enemy") == rat and o.payload.get("damage") == 2 for o in options))
        add_enemy(s, "01159", instance_id="rat2")
        options = []
        actions.add_asset_action_options(s, options)
        self.assertTrue(any(o.payload.get("enemy") == rat and o.payload.get("damage") == 1 for o in options))
        self.assertIn(machete, s.investigator.play_area)

    def test_guard_dog_damages_attacking_enemy_when_soaking_damage(self) -> None:
        s = state()
        dog = add_card(s, "01021", "play")
        ghoul = add_enemy(s, "01160")
        events = []
        start_damage_assignment(s, events, source="Ghoul", damage=1, horror=0, resume={"kind": "after_attack", "enemy": ghoul})
        from arkham.effects import assign_damage_choice

        assign_damage_choice(s, {"type": "damage", "target": dog}, events)
        self.assertEqual(s.enemies[ghoul].damage, 1)

    def test_evidence_discovers_after_enemy_defeat(self) -> None:
        s = state()
        ev = add_card(s, "01022", "hand")
        s.locations["study"].clues = 1
        enemy = add_enemy(s, "01159")
        events = []
        enemies.damage_enemy(s, events, enemy, 1)
        enemies.resolve_enemy_defeated_reaction(s, {"reaction": "evidence", "card": ev}, events)
        self.assertEqual(s.investigator.clues, 1)
        self.assertIn(ev, s.investigator.discard)

    def test_dodge_cancels_enemy_attack(self) -> None:
        s = state()
        dodge = add_card(s, "01023", "hand")
        enemy = add_enemy(s, "01160")
        events = []
        enemies.attack(s, events, enemy, source="enemy phase")
        enemies.cancel_pending_attack(s, events, dodge)
        self.assertEqual(s.investigator.damage, 0)
        self.assertIn(dodge, s.investigator.discard)

    def test_dynamite_blast_damages_enemies_and_roland_at_chosen_location(self) -> None:
        s = state()
        dyn = add_card(s, "01024", "hand")
        rat = add_enemy(s, "01159")
        events = []
        actions.dynamite_blast(s, {"card": dyn, "location": "study"}, events)
        self.assertNotIn(rat, s.enemies)
        self.assertEqual(s.investigator.damage, 3)

    def test_vicious_blow_adds_attack_damage_on_success(self) -> None:
        s = state()
        blow = add_card(s, "01025", "hand")
        ghoul = add_enemy(s, "01160")
        events = []
        skill_test.start(s, events, skill="combat", difficulty=0, source="Fight Ghoul", on_success={"kind": "fight", "enemy": ghoul, "damage": 1})
        skill_test.commit_card(s, {"card": blow}, events)
        resolve_current_test(s, events)
        self.assertNotIn(ghoul, s.enemies)

    def test_magnifying_glass_static_only_while_investigating(self) -> None:
        s = state()
        add_card(s, "01030", "play")
        self.assertEqual(actions.player_cards.effective_base_skill(s, "intellect", "Investigate Study"), 4)
        self.assertEqual(actions.player_cards.effective_base_skill(s, "intellect", "Medical Texts"), 3)

    def test_old_book_of_lore_searches_top_three_and_draws_choice(self) -> None:
        s = state()
        book = add_card(s, "01031", "play")
        card = add_card(s, "01088", "deck")
        add_card(s, "01086", "deck")
        add_card(s, "01087", "deck")
        actions.old_book_of_lore(s, {"asset": book}, [])
        self.assertEqual(len(s.decision_queue[0].options), 3)
        actions.resolve_old_book_choice(s, s.decision_queue[0].options[0].payload, [], ArkhamRng(1))
        self.assertIn(card, s.investigator.hand)
        self.assertTrue(s.card_instances[book].exhausted)

    def test_research_librarian_finds_tome_asset(self) -> None:
        s = state()
        tome = add_card(s, "01031", "deck")
        librarian = add_card(s, "01032", "hand")
        actions.play_card(s, librarian, [])
        self.assertEqual(s.decision_queue[0].id, "research-librarian-search")
        actions.resolve_research_librarian_choice(s, s.decision_queue[0].options[0].payload, [], ArkhamRng(1))
        self.assertIn(tome, s.investigator.hand)

    def test_dr_milan_static_and_successful_investigate_resource(self) -> None:
        s = state()
        add_card(s, "01033", "play")
        s.investigator.resources = 0
        s.locations["study"].clues = 1
        events = []
        skill_test.start(s, events, skill="intellect", difficulty=0, source="Investigate Study", on_success={"kind": "investigate"})
        resolve_current_test(s, events)
        self.assertEqual(s.decision_queue[0].id, "milan-reaction")
        skill_test.resolve_milan_reaction(s, s.decision_queue.pop(0).options[0].payload, events)
        self.assertEqual(s.investigator.resources, 1)
        self.assertEqual(actions.player_cards.effective_base_skill(s, "intellect", "Other"), 4)

    def test_hyperawareness_boosts_intellect_and_agility(self) -> None:
        s = state()
        add_card(s, "01034", "play")
        skill_test.start(s, [], skill="agility", difficulty=5, source="Evade")
        self.assertTrue(any("Hyperawareness" in o.label for o in s.decision_queue[0].options))

    def test_medical_texts_success_heals_failure_deals_damage(self) -> None:
        s = state()
        s.investigator.damage = 1
        events = []
        skill_test.start(s, events, skill="intellect", difficulty=0, source="Medical Texts", on_success={"kind": "medical_texts"}, on_failure={"kind": "medical_texts"})
        resolve_current_test(s, events)
        self.assertEqual(s.investigator.damage, 0)
        s.chaos_bag.tokens = ["-4"]
        skill_test.start(s, events, skill="intellect", difficulty=9, source="Medical Texts", on_success={"kind": "medical_texts"}, on_failure={"kind": "medical_texts"})
        resolve_current_test(s, events)
        self.assertEqual(s.investigator.damage, 1)

    def test_mind_over_matter_substitutes_intellect_until_round_end(self) -> None:
        s = state()
        mom = add_card(s, "01036", "hand")
        actions.resolve_fast_ability(s, {"ability": "mind_over_matter", "card": mom}, [])
        self.assertEqual(actions.player_cards.effective_base_skill(s, "combat", "Fight"), 3)

    def test_working_a_hunch_discovers_clue_fast(self) -> None:
        s = state()
        hunch = add_card(s, "01037", "hand")
        s.locations["study"].clues = 1
        actions.resolve_fast_ability(s, {"ability": "working_hunch", "card": hunch}, [])
        self.assertEqual(s.investigator.clues, 1)

    def test_barricade_attaches_blocks_hunter_and_discards_on_leave(self) -> None:
        s = state()
        barrier = add_card(s, "01038", "hand")
        actions.play_card(s, barrier, [])
        rat = add_enemy(s, "01159", location="hallway", engaged=False)
        self.assertTrue(enemies.move_blocked(s, rat, "study"))
        actions.move(s, "hallway", [])
        self.assertIn(barrier, s.investigator.discard)

    def test_deduction_discovers_an_additional_clue(self) -> None:
        s = state()
        deduction = add_card(s, "01039", "hand")
        s.locations["study"].clues = 2
        events = []
        skill_test.start(s, events, skill="intellect", difficulty=0, source="Investigate Study", on_success={"kind": "investigate"})
        skill_test.commit_card(s, {"card": deduction}, events)
        resolve_current_test(s, events)
        self.assertEqual(s.investigator.clues, 2)

    def test_knife_throw_discards_for_extra_damage(self) -> None:
        s = state()
        knife = add_card(s, "01086", "play")
        ghoul = add_enemy(s, "01160")
        actions.asset_fight(s, {"asset": knife, "enemy": ghoul, "boost": 2, "damage": 2, "discard_asset": True}, [])
        self.assertIn(knife, s.investigator.discard)

    def test_flashlight_reduces_shroud_to_min_zero_and_stays_empty(self) -> None:
        s = state()
        flashlight = add_card(s, "01087", "play")
        s.locations["study"].shroud = 1
        events = []
        for _ in range(3):
            actions.flashlight_investigate(s, {"asset": flashlight}, events)
            self.assertEqual(s.active_skill_test["difficulty"], 0)
            s.active_skill_test = None
        self.assertEqual(s.card_instances[flashlight].uses["supplies"], 0)
        self.assertIn(flashlight, s.investigator.play_area)

    def test_emergency_cache_gains_three_resources(self) -> None:
        s = state()
        cache = add_card(s, "01088", "hand")
        s.investigator.resources = 0
        actions.play_card(s, cache, [])
        self.assertEqual(s.investigator.resources, 3)

    def test_guts_max_one_and_draws_on_success(self) -> None:
        s = state()
        g1 = add_card(s, "01089", "hand")
        g2 = add_card(s, "01089", "hand")
        draw = add_card(s, "01088", "deck")
        events = []
        skill_test.start(s, events, skill="willpower", difficulty=0, source="test")
        skill_test.commit_card(s, {"card": g1}, events)
        self.assertFalse(any(o.payload.get("card") == g2 for o in s.decision_queue[0].options))
        resolve_current_test(s, events)
        self.assertIn(draw, s.investigator.hand)

    def test_manual_dexterity_max_one_and_draws_on_success(self) -> None:
        s = state()
        m1 = add_card(s, "01092", "hand")
        m2 = add_card(s, "01092", "hand")
        draw = add_card(s, "01088", "deck")
        events = []
        skill_test.start(s, events, skill="agility", difficulty=0, source="test")
        skill_test.commit_card(s, {"card": m1}, events)
        self.assertFalse(any(o.payload.get("card") == m2 for o in s.decision_queue[0].options))
        resolve_current_test(s, events)
        self.assertIn(draw, s.investigator.hand)


class PhaseCEncounterCardTests(unittest.TestCase):
    def test_ghoul_priest_retaliates_hunts_and_enters_victory_display(self) -> None:
        s = state()
        priest = add_enemy(s, "01116")
        self.assertTrue(enemies.has_retaliate(s, priest))
        enemies.damage_enemy(s, [], priest, 5)
        self.assertIn(priest, s.victory_display)

    def test_lita_parley_control_static_and_monster_damage(self) -> None:
        s = state()
        lita = add_card(s, "01117", "story")
        s.locations["study"].attached_instance_ids.append(lita)
        events = []
        skill_test.start(s, events, skill="intellect", difficulty=0, source="Parley", on_success={"kind": "lita_parley", "lita": lita})
        resolve_current_test(s, events)
        self.assertIn(lita, s.investigator.play_area)
        start_damage_assignment(s, events, source="test", damage=0, horror=1)
        horror_option = next(option for option in s.decision_queue[0].options if option.payload["target"] == lita)
        from arkham.effects import assign_damage_choice

        assign_damage_choice(s, horror_option.payload, events)
        self.assertEqual(s.card_instances[lita].horror, 1)
        self.assertEqual(actions.player_cards.effective_base_skill(s, "combat", "Fight"), 5)
        ghoul = add_enemy(s, "01160")
        skill_test.start(s, events, skill="combat", difficulty=0, source="Fight", on_success={"kind": "fight", "enemy": ghoul, "damage": 1})
        resolve_current_test(s, events)
        self.assertNotIn(ghoul, s.enemies)

    def test_flesh_eater_spawns_at_attic(self) -> None:
        s = state()
        card = add_card(s, "01118", "encounter_deck")
        encounter.resolve_revelation(s, ArkhamRng(1), [], card)
        self.assertIn(card, s.locations["attic"].enemy_ids)

    def test_icy_ghoul_spawns_at_cellar(self) -> None:
        s = state()
        card = add_card(s, "01119", "encounter_deck")
        encounter.resolve_revelation(s, ArkhamRng(1), [], card)
        self.assertIn(card, s.locations["cellar"].enemy_ids)

    def test_swarm_of_rats_is_hunter(self) -> None:
        s = state()
        rat = add_enemy(s, "01159", engaged=False)
        self.assertTrue(enemies.is_hunter(s, rat))

    def test_ghoul_minion_spawns_engaged_by_default(self) -> None:
        s = state()
        card = add_card(s, "01160", "encounter_deck")
        encounter.resolve_revelation(s, ArkhamRng(1), [], card)
        self.assertIn(card, s.investigator.engaged_enemies)

    def test_ravenous_ghoul_spawns_engaged_by_default(self) -> None:
        s = state()
        card = add_card(s, "01161", "encounter_deck")
        encounter.resolve_revelation(s, ArkhamRng(1), [], card)
        self.assertIn(card, s.investigator.engaged_enemies)

    def test_grasping_hands_deals_damage_per_point_failed(self) -> None:
        s = state()
        card = add_card(s, "01162", "encounter_deck")
        s.chaos_bag.tokens = ["-4"]
        encounter.resolve_revelation(s, ArkhamRng(1), [], card)
        resolve_current_test(s)
        self.assertEqual(s.investigator.damage, 3)

    def test_rotting_remains_deals_horror_per_point_failed(self) -> None:
        s = state()
        card = add_card(s, "01163", "encounter_deck")
        s.chaos_bag.tokens = ["-4"]
        encounter.resolve_revelation(s, ArkhamRng(1), [], card)
        resolve_current_test(s)
        self.assertEqual(s.investigator.horror, 3)

    def test_frozen_in_fear_taxes_first_fight_and_discards_on_end_turn_success(self) -> None:
        s = state()
        frozen = add_card(s, "01164", "threat")
        events = []
        actions.spend_action(s, events, "fight")
        self.assertEqual(s.investigator.actions_remaining, 1)
        actions.spend_action(s, events, "move")
        self.assertEqual(s.investigator.actions_remaining, 0)
        s.investigator.actions_remaining = 0
        self.assertTrue(phases.start_frozen_end_turn_test(s, events))
        resolve_current_test(s, events)
        self.assertIn(frozen, s.encounter_discard)

    def test_dissonant_voices_blocks_asset_event_play_and_discards_end_round(self) -> None:
        s = state()
        dissonant = add_card(s, "01165", "threat")
        flashlight = add_card(s, "01087", "hand")
        self.assertTrue(actions.dissonant_blocks(s, "01087"))
        actions.play_card(s, flashlight, [])
        self.assertIn(flashlight, s.investigator.hand)
        phases.discard_dissonant_voices(s, [])
        self.assertIn(dissonant, s.encounter_discard)

    def test_ancient_evils_places_doom_and_checks_advance(self) -> None:
        s = state()
        s.agenda.doom = 2
        card = add_card(s, "01166", "encounter_deck")
        encounter.resolve_revelation(s, ArkhamRng(1), [], card)
        self.assertEqual(s.agenda.stage, 2)

    def test_crypt_chill_discards_controlled_asset_or_deals_damage_if_none(self) -> None:
        s = state()
        asset = add_card(s, "01087", "play")
        card = add_card(s, "01167", "encounter_deck")
        s.chaos_bag.tokens = ["-4"]
        encounter.resolve_revelation(s, ArkhamRng(1), [], card)
        resolve_current_test(s)
        from arkham.effects import discard_asset_choice

        discard_asset_choice(s, {"card": asset}, [])
        self.assertIn(asset, s.investigator.discard)
        s2 = state()
        card2 = add_card(s2, "01167", "encounter_deck")
        s2.chaos_bag.tokens = ["-4"]
        encounter.resolve_revelation(s2, ArkhamRng(1), [], card2)
        resolve_current_test(s2)
        self.assertEqual(s2.investigator.damage, 2)

    def test_obscuring_fog_attaches_adds_shroud_and_discards_after_success(self) -> None:
        s = state()
        fog = add_card(s, "01168", "encounter_deck")
        encounter.resolve_revelation(s, ArkhamRng(1), [], fog)
        self.assertEqual(actions.modified_shroud(s, "study"), 4)
        s.locations["study"].clues = 1
        skill_test.start(s, [], skill="intellect", difficulty=0, source="Investigate Study", on_success={"kind": "investigate"})
        resolve_current_test(s)
        self.assertIn(fog, s.encounter_discard)

    def test_locked_door_targets_most_clues_blocks_investigation_and_breaks(self) -> None:
        s = state()
        s.locations["study"].clues = 1
        s.locations["attic"].clues = 3
        door = add_card(s, "01174", "encounter_deck")
        encounter.resolve_revelation(s, ArkhamRng(1), [], door)
        self.assertIn(door, s.locations["attic"].attached_instance_ids)
        s.investigator.location_id = "attic"
        self.assertTrue(actions.location_locked(s, "attic"))
        skill_test.start(s, [], skill="combat", difficulty=0, source="Locked Door", on_success={"kind": "locked_door", "door": door})
        resolve_current_test(s)
        self.assertIn(door, s.encounter_discard)


if __name__ == "__main__":
    unittest.main()
