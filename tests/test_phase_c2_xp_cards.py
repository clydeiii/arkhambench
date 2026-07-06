from __future__ import annotations

import unittest

from arkham import actions, enemies, skill_test
from arkham.cards import player as player_cards
from arkham.effects import assign_damage_choice, start_damage_assignment
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


def state(seed: int = 1):
    s = build_engine_test_state(difficulty="standard", rng=ArkhamRng(seed))
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.investigator.resources = 10
    s.investigator.actions_remaining = 3
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
        player_cards.setup_uses(s.card_instances[instance_id])
    elif zone == "deck":
        s.investigator.deck.append(instance_id)
    elif zone == "discard":
        s.investigator.discard.append(instance_id)
    elif zone == "encounter_deck":
        s.encounter_deck.append(instance_id)
    return instance_id


def add_enemy(s, code: str, location: str = "study", engaged: bool = True, instance_id: str | None = None) -> str:
    instance_id = instance_id or f"enemy_{code}_{len(s.enemies)}"
    s.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="enemy")
    s.enemies[instance_id] = EnemyInstance(id=instance_id, card_code=code, location_id=location)
    s.locations[location].enemy_ids.append(instance_id)
    if engaged:
        s.enemies[instance_id].engaged_with = s.investigator.id
        s.investigator.engaged_enemies.append(instance_id)
    return instance_id


def finish_test(s, rng: ArkhamRng | None = None):
    events: list[dict] = []
    skill_test.finish_commit(s, rng or ArkhamRng(1), events)
    if s.decision_queue and s.decision_queue[0].id == "post-reveal-boosts":
        s.decision_queue = []
        skill_test.resolve(s, events, rng)
    return events


class PhaseC2XpCardBehaviorTests(unittest.TestCase):
    def test_shotgun_damage_caps_at_card_json_max_five(self) -> None:
        s = state()
        shotgun = add_card(s, "01029", "play")
        priest = add_enemy(s, "01116")
        mask = add_card(s, "50043", "discard", instance_id="mask")
        s.enemies[priest].attachments.append(mask)
        s.investigator.combat = 6
        s.chaos_bag.tokens = ["+1"]

        events: list[dict] = []
        actions.asset_fight(s, {"asset": shotgun, "enemy": priest, "boost": 3, "damage": 1, "shotgun": True}, events)
        finish_test(s, ArkhamRng(1))

        self.assertEqual(s.card_instances[shotgun].uses["ammo"], 1)
        self.assertIn(priest, s.enemies)
        self.assertEqual(s.enemies[priest].damage, 5)

    def test_sure_gamble_flips_negative_modifier_sign(self) -> None:
        s = state()
        gamble = add_card(s, "01056", "hand")
        s.chaos_bag.tokens = ["-2"]
        skill_test.start(s, [], skill="combat", difficulty=5, source="test")
        finish_test(s, ArkhamRng(1))
        self.assertEqual(s.decision_queue[0].id, "wendy-token-reaction")

        skill_test.resolve_sure_gamble_reaction(
            s,
            {"kind": "sure_gamble_reaction", "choice": "play", "card": gamble},
            [],
            ArkhamRng(1),
        )
        self.assertEqual(s.limits["last_skill_test"]["modifier"], 2)
        self.assertTrue(s.limits["last_skill_test"]["success"])
        self.assertIn(gamble, s.investigator.discard)

    def test_will_to_survive_prevents_chaos_token_reveal_this_turn(self) -> None:
        s = state()
        will = add_card(s, "01085", "hand")
        s.chaos_bag.tokens = ["autofail"]
        actions.resolve_fast_ability(s, {"ability": "will_to_survive", "card": will}, [])
        skill_test.start(s, [], skill="combat", difficulty=4, source="tokenless")
        events = finish_test(s, ArkhamRng(1))

        self.assertTrue(any(event["type"] == "chaos_token_skipped" for event in events))
        self.assertIsNone(s.limits["last_skill_test"]["token"])
        self.assertTrue(s.limits["last_skill_test"]["success"])

    def test_aquinnah_redirects_attack_damage_to_another_enemy(self) -> None:
        s = state()
        aquinnah = add_card(s, "01082", "play")
        attacker = add_enemy(s, "01160", instance_id="attacker")
        target = add_enemy(s, "01159", engaged=False, instance_id="target")

        enemies.attack(s, [], attacker, source="test")
        self.assertEqual(s.decision_queue[0].id, "enemy-attack")
        enemies.resolve_aquinnah_attack(s, [], aquinnah, target, ArkhamRng(1))

        self.assertTrue(s.card_instances[aquinnah].exhausted)
        self.assertEqual(s.card_instances[aquinnah].horror, 1)
        self.assertNotIn(target, s.enemies)
        self.assertEqual(s.investigator.damage, 0)
        self.assertIsNotNone(s.pending_damage)
        self.assertEqual(s.pending_damage["remaining_horror"], 1)

    def test_disc_of_itzamna_discards_non_elite_enemy_on_spawn(self) -> None:
        s = state()
        disc = add_card(s, "01041", "play")
        enemy = add_card(s, "01160", "encounter_deck", instance_id="spawned")

        spawned = enemies.spawn_enemy(s, [], instance_id=enemy)
        self.assertIsNone(spawned)
        self.assertNotIn(enemy, s.enemies)
        self.assertIn(enemy, s.encounter_discard)
        self.assertIn(disc, s.investigator.discard)

    def test_grotesque_statue_reveals_two_and_resolves_chosen_token(self) -> None:
        s = state()
        statue = add_card(s, "01071", "play")
        s.chaos_bag.tokens = ["-3", "+1"]
        skill_test.start(s, [], skill="combat", difficulty=5, source="statue")
        finish_test(s, ArkhamRng(1))
        self.assertEqual(s.decision_queue[0].id, "grotesque-reaction")

        skill_test.resolve_grotesque_reaction(
            s,
            {"kind": "grotesque_reaction", "choice": "use", "card": statue},
            [],
            ArkhamRng(4),
        )
        self.assertEqual(s.card_instances[statue].uses["charges"], 3)
        self.assertEqual(s.decision_queue[0].id, "grotesque-choice")
        chosen = next(option.payload for option in s.decision_queue[0].options if option.payload["token"] == "+1")
        skill_test.resolve_grotesque_choice(s, chosen, [], ArkhamRng(1))

        self.assertEqual(s.limits["last_skill_test"]["token"], "+1")
        self.assertTrue(s.limits["last_skill_test"]["success"])

    def test_police_badge_static_willpower_and_discard_for_two_actions(self) -> None:
        s = state()
        badge = add_card(s, "01027", "play")
        s.investigator.actions_remaining = 1
        self.assertEqual(player_cards.effective_base_skill(s, "willpower", "test"), 4)

        actions.resolve_fast_ability(s, {"ability": "police_badge", "card": badge}, [])
        self.assertEqual(s.investigator.actions_remaining, 3)
        self.assertIn(badge, s.investigator.discard)

    def test_close_call_shuffles_evaded_enemy_back_into_encounter_deck(self) -> None:
        s = state()
        close = add_card(s, "01083", "hand")
        enemy = add_enemy(s, "01160")
        enemies.evade_enemy(s, [], enemy)
        actions.queue_close_call_reaction(s, enemy)

        self.assertEqual(s.decision_queue[0].id, "close-call-reaction")
        actions.resolve_close_call_reaction(
            s,
            {"kind": "close_call_reaction", "choice": "play", "card": close, "enemy": enemy},
            [],
            ArkhamRng(1),
        )
        self.assertNotIn(enemy, s.enemies)
        self.assertIn(enemy, s.encounter_deck)
        self.assertIn(close, s.investigator.discard)
        self.assertEqual(s.investigator.resources, 8)

    def test_bulletproof_vest_and_elder_sign_amulet_soak_damage_and_horror(self) -> None:
        s = state()
        vest = add_card(s, "01094", "play")
        amulet = add_card(s, "01095", "play")

        start_damage_assignment(s, [], source="test", damage=1, horror=1)
        assign_damage_choice(s, {"kind": "assign_damage", "type": "damage", "target": vest}, [])
        assign_damage_choice(s, {"kind": "assign_damage", "type": "horror", "target": amulet}, [])

        self.assertEqual(s.investigator.damage, 0)
        self.assertEqual(s.investigator.horror, 0)
        self.assertEqual(s.card_instances[vest].damage, 1)
        self.assertEqual(s.card_instances[amulet].horror, 1)

    def test_cryptic_research_draws_three_cards(self) -> None:
        s = state()
        cryptic = add_card(s, "01043", "hand")
        drawn = [add_card(s, code, "deck") for code in ("01016", "01017", "01018")]

        actions.resolve_fast_ability(s, {"ability": "cryptic_research", "card": cryptic}, [])
        for card_id in drawn:
            self.assertIn(card_id, s.investigator.hand)
        self.assertIn(cryptic, s.investigator.discard)

    def test_beat_cop_2_exhausts_takes_damage_and_damages_enemy(self) -> None:
        s = state()
        cop = add_card(s, "01028", "play")
        ghoul = add_enemy(s, "01160")
        self.assertEqual(player_cards.effective_base_skill(s, "combat", "Fight"), 5)

        actions.resolve_fast_ability(s, {"ability": "beat_cop_2", "card": cop, "enemy": ghoul}, [])
        self.assertTrue(s.card_instances[cop].exhausted)
        self.assertEqual(s.card_instances[cop].damage, 1)
        self.assertEqual(s.enemies[ghoul].damage, 1)

    def test_lucky_2_adds_two_and_draws_a_card(self) -> None:
        s = state()
        lucky = add_card(s, "01084", "hand")
        draw = add_card(s, "01016", "deck")
        skill_test.start(s, [], skill="combat", difficulty=6, source="lucky")
        finish_test(s, ArkhamRng(1))
        self.assertEqual(s.decision_queue[0].id, "would-fail")

        skill_test.resolve_lucky_would_fail(
            s,
            {"kind": "lucky_would_fail", "choice": "play", "card": lucky},
            [],
            ArkhamRng(1),
        )
        self.assertTrue(s.limits["last_skill_test"]["success"])
        self.assertIn(draw, s.investigator.hand)
        self.assertIn(lucky, s.investigator.discard)

    def test_leo_de_luca_1_costs_five_and_grants_extra_action(self) -> None:
        s = state()
        leo = add_card(s, "01054", "hand")
        s.investigator.resources = 5
        s.investigator.actions_remaining = 2

        actions.play_card(s, leo, [])
        self.assertEqual(s.investigator.resources, 0)
        self.assertEqual(s.investigator.actions_remaining, 3)
        self.assertIn(leo, s.investigator.play_area)

    def test_dynamite_blast_2_can_skip_attacks_of_opportunity(self) -> None:
        s = state()
        blast = add_card(s, "50002", "hand")
        guard = add_enemy(s, "01160", instance_id="guard")
        target = add_enemy(s, "01160", location="hallway", engaged=False, instance_id="target")
        s.investigator.resources = 4

        actions.execute(s, {"action": "dynamite", "card": blast, "location": "hallway", "skip_aoo": True}, [], ArkhamRng(1))
        self.assertNotIn(target, s.enemies)
        self.assertIn(guard, s.enemies)
        self.assertFalse(any(decision.id == "enemy-attack" for decision in s.decision_queue))
        self.assertEqual(s.investigator.damage, 0)

    def test_mind_wipe_level_1_blanks_and_level_3_reduces_attack_values(self) -> None:
        s = state()
        enemy = add_enemy(s, "01160")
        wipe1 = add_card(s, "01068", "hand")
        actions.resolve_fast_ability(s, {"ability": "mind_wipe", "card": wipe1, "enemy": enemy}, [])
        self.assertTrue(enemies.mind_wiped(s, enemy))
        self.assertEqual(enemies.enemy_damage_horror(s, enemy), (1, 1))

        s = state()
        enemy = add_enemy(s, "01160")
        wipe3 = add_card(s, "50008", "hand")
        actions.resolve_fast_ability(s, {"ability": "mind_wipe", "card": wipe3, "enemy": enemy}, [])
        self.assertTrue(enemies.mind_wiped(s, enemy))
        self.assertEqual(enemies.enemy_damage_horror(s, enemy), (0, 0))

    def test_encyclopedia_book_of_shadows_and_cat_burglar_actions(self) -> None:
        s = state()
        encyclopedia = add_card(s, "01042", "play")
        actions.encyclopedia_action(s, {"asset": encyclopedia, "skill": "intellect"}, [])
        self.assertTrue(s.card_instances[encyclopedia].exhausted)
        self.assertEqual(player_cards.effective_base_skill(s, "intellect", "test"), 5)

        s = state()
        book = add_card(s, "01070", "play")
        spell = add_card(s, "01060", "play")
        before = s.card_instances[spell].uses["charges"]
        actions.book_of_shadows_action(s, {"asset": book, "spell": spell}, [])
        self.assertEqual(s.card_instances[spell].uses["charges"], before + 1)
        self.assertTrue(s.card_instances[book].exhausted)

        s = state()
        burglar = add_card(s, "01055", "play")
        enemy = add_enemy(s, "01160")
        self.assertEqual(player_cards.effective_base_skill(s, "agility", "test"), 3)
        actions.cat_burglar_action(s, {"asset": burglar, "location": "hallway"}, [])
        self.assertEqual(s.investigator.location_id, "hallway")
        self.assertIsNone(s.enemies[enemy].engaged_with)
        self.assertTrue(s.card_instances[burglar].exhausted)

    def test_hot_streak_both_levels_gain_ten_after_their_printed_costs(self) -> None:
        for code, starting_resources in (("50006", 5), ("01057", 3)):
            s = state()
            hot_streak = add_card(s, code, "hand")
            s.investigator.resources = starting_resources
            actions.play_card(s, hot_streak, [])
            self.assertEqual(s.investigator.resources, 10)
            self.assertIn(hot_streak, s.investigator.discard)

    def test_extra_ammunition_adds_three_ammo_to_firearm(self) -> None:
        s = state()
        extra = add_card(s, "01026", "hand")
        gun = add_card(s, "01016", "play")
        before = s.card_instances[gun].uses["ammo"]

        actions.extra_ammunition(s, {"card": extra, "asset": gun}, [])
        self.assertEqual(s.card_instances[gun].uses["ammo"], before + 3)
        self.assertIn(extra, s.investigator.discard)
        self.assertEqual(s.investigator.resources, 8)

    def test_upgraded_talents_provide_their_boost_options(self) -> None:
        cases = [
            ("50001", "willpower"),
            ("50003", "intellect"),
            ("50005", "combat"),
            ("50007", "willpower"),
            ("50009", "agility"),
        ]
        for code, skill in cases:
            with self.subTest(code=code, skill=skill):
                s = state()
                add_card(s, code, "play")
                skill_test.start(s, [], skill=skill, difficulty=10, source="talent")
                options = player_cards.boost_options(s)
                self.assertTrue(any(option.payload.get("card_code") == code for option in options))
                before = s.investigator.resources
                self.assertTrue(player_cards.apply_boost(s, code, skill))
                self.assertEqual(s.investigator.resources, before - 1)

    def test_magnifying_glass_1_blinding_light_2_and_rabbits_foot_3(self) -> None:
        s = state()
        add_card(s, "01040", "play")
        self.assertEqual(player_cards.effective_base_skill(s, "intellect", "Investigate Study"), 4)

        s = state()
        blinding = add_card(s, "01069", "hand")
        ghoul = add_enemy(s, "01160")
        actions.blinding_light(s, {"card": blinding, "enemy": ghoul}, [])
        finish_test(s, ArkhamRng(1))
        self.assertNotIn(ghoul, s.enemies)
        self.assertIn(blinding, s.investigator.discard)

        s = state()
        foot = add_card(s, "50010", "play")
        top = [add_card(s, code, "deck") for code in ("01016", "01017", "01018")]
        skill_test.start(s, [], skill="combat", difficulty=7, source="rabbit")
        finish_test(s, ArkhamRng(1))
        self.assertEqual(s.decision_queue[0].id, "after-fail-reactions")
        skill_test.resolve_after_fail_reaction(
            s,
            {"kind": "after_fail_reaction", "reaction": "rabbit3", "card": foot, "count": 3},
            [],
            ArkhamRng(1),
        )
        self.assertTrue(s.card_instances[foot].exhausted)
        self.assertEqual(s.decision_queue[-1].id, "rabbits-foot-3-choice")
        skill_test.resolve_rabbits_foot_3(
            s,
            {"kind": "rabbits_foot_3", "card": top[1], "candidates": top},
            [],
            ArkhamRng(1),
        )
        self.assertIn(top[1], s.investigator.hand)


if __name__ == "__main__":
    unittest.main()
