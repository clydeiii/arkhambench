from __future__ import annotations

import unittest

from arkham import actions, enemies, skill_test
from arkham.cards import player as player_cards
from arkham.effects import assign_damage_choice, start_damage_assignment
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios.the_gathering import build_engine_test_state


class SeqRng:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = list(tokens)

    def choice(self, values):  # type: ignore[no-untyped-def]
        return self.tokens.pop(0) if self.tokens else values[0]

    def shuffle(self, values):  # type: ignore[no-untyped-def]
        return None


def state():
    s = build_engine_test_state(difficulty="standard", rng=ArkhamRng(1))
    s.investigator.id = "skids"
    s.investigator.name = '"Skids" O\'Toole'
    s.investigator.card_code = "01003"
    s.investigator.willpower = 2
    s.investigator.intellect = 3
    s.investigator.combat = 3
    s.investigator.agility = 4
    s.investigator.health = 8
    s.investigator.sanity = 6
    s.investigator.hand = []
    s.investigator.deck = []
    s.investigator.discard = []
    s.investigator.play_area = []
    s.investigator.threat_area = []
    s.investigator.engaged_enemies = []
    s.investigator.resources = 10
    s.investigator.actions_remaining = 3
    s.decision_queue = []
    s.encounter_deck = []
    s.encounter_discard = []
    s.chaos_bag.tokens = ["0", "-2", "+1", "autofail"]
    return s


def add_card(s, code: str, zone: str = "hand", instance_id: str | None = None) -> str:
    instance_id = instance_id or f"{code}_{len(s.card_instances)}"
    s.card_instances[instance_id] = CardInstance(
        id=instance_id,
        card_code=code,
        zone=zone,
        owner=s.investigator.id,
    )
    if zone == "hand":
        s.investigator.hand.append(instance_id)
    elif zone == "play":
        s.investigator.play_area.append(instance_id)
        player_cards.setup_uses(s.card_instances[instance_id])
    elif zone == "deck":
        s.investigator.deck.append(instance_id)
    elif zone == "discard":
        s.investigator.discard.append(instance_id)
    return instance_id


def add_enemy(
    s,
    code: str = "01160",
    *,
    location: str = "study",
    engaged: bool = True,
    exhausted: bool = False,
    instance_id: str | None = None,
) -> str:
    enemy_id = instance_id or f"enemy_{len(s.enemies)}"
    s.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="enemy")
    s.enemies[enemy_id] = EnemyInstance(
        id=enemy_id,
        card_code=code,
        location_id=location,
        exhausted=exhausted,
    )
    s.locations[location].enemy_ids.append(enemy_id)
    if engaged:
        s.enemies[enemy_id].engaged_with = s.investigator.id
        s.investigator.engaged_enemies.append(enemy_id)
    return enemy_id


def finish_test(s, rng) -> list[dict]:  # type: ignore[no-untyped-def]
    events: list[dict] = []
    skill_test.finish_commit(s, rng, events)
    return events


class XpCardProbeTests(unittest.TestCase):
    def test_close_call_fires_after_evade_and_shuffles_the_enemy(self) -> None:
        s = state()
        close_call = add_card(s, "01083")
        ghoul = add_enemy(s)

        actions.execute(s, {"kind": "action", "action": "evade", "enemy": ghoul}, [], SeqRng(["0"]))
        finish_test(s, SeqRng(["0"]))
        self.assertTrue(s.enemies[ghoul].exhausted)
        self.assertEqual(s.decision_queue[0].id, "close-call-reaction")

        actions.resolve_close_call_reaction(
            s,
            {"kind": "close_call_reaction", "choice": "play", "card": close_call, "enemy": ghoul},
            [],
            SeqRng([]),
        )
        self.assertNotIn(ghoul, s.enemies)
        self.assertIn(ghoul, s.encounter_deck)
        self.assertIn(close_call, s.investigator.discard)
        self.assertEqual(s.investigator.resources, 8)

    def test_sure_gamble_flips_the_revealed_negative_modifier(self) -> None:
        s = state()
        gamble = add_card(s, "01056")
        skill_test.start(s, [], skill="intellect", difficulty=4, source="probe")
        finish_test(s, SeqRng(["-2"]))
        self.assertEqual(s.active_skill_test["modifier"], -2)
        self.assertEqual(s.decision_queue[0].id, "wendy-token-reaction")

        skill_test.resolve_sure_gamble_reaction(
            s,
            {"kind": "sure_gamble_reaction", "choice": "play", "card": gamble},
            [],
            SeqRng([]),
        )
        result = s.limits["last_skill_test"]
        self.assertEqual(result["modifier"], 2)
        self.assertEqual(result["value"], 5)
        self.assertTrue(result["success"])
        self.assertIn(gamble, s.investigator.discard)

    def test_will_to_survive_covers_committed_tests_then_expires_at_end_of_turn(self) -> None:
        s = state()
        will = add_card(s, "01085")
        committed = add_card(s, "01091")  # Overpower: 2 combat icons.
        actions.resolve_fast_ability(s, {"ability": "will_to_survive", "card": will}, [])

        skill_test.start(s, [], skill="combat", difficulty=5, source="during turn")
        skill_test.commit_card(s, {"card": committed}, [])
        events = finish_test(s, SeqRng(["autofail"]))
        result = s.limits["last_skill_test"]
        self.assertTrue(result["success"])
        self.assertEqual(result["committed_icons"], 2)
        self.assertIsNone(result["token"])
        self.assertTrue(any(event["type"] == "chaos_token_skipped" for event in events))

        actions.execute(s, {"kind": "action", "action": "pass"}, [])
        from arkham import phases
        phases.advance_until_decision(s, ArkhamRng(1), [])  # real end-of-turn transition
        s.phase = "Enemy"
        skill_test.start(s, [], skill="willpower", difficulty=2, source="after turn")
        finish_test(s, SeqRng(["autofail"]))
        self.assertEqual(s.limits["last_skill_test"]["token"], "autofail")
        self.assertFalse(s.limits["last_skill_test"]["success"])

    def test_aquinnah_redirects_damage_but_not_horror_with_two_enemies(self) -> None:
        s = state()
        aquinnah = add_card(s, "01082", "play")
        attacker = add_enemy(s, "01116", instance_id="attacker")
        target = add_enemy(s, "01160", engaged=False, instance_id="target")

        enemies.attack(s, [], attacker, source="probe", rng=SeqRng([]))
        self.assertEqual(s.decision_queue[0].id, "enemy-attack")
        enemies.resolve_aquinnah_attack(s, [], aquinnah, target, SeqRng([]))

        self.assertNotIn(target, s.enemies)  # Ghoul Minion took the Priest's 2 damage.
        self.assertEqual(s.investigator.damage, 0)
        self.assertEqual(s.pending_damage["remaining_horror"], 2)
        self.assertTrue(s.card_instances[aquinnah].exhausted)
        self.assertEqual(s.card_instances[aquinnah].horror, 1)

        assign_damage_choice(s, {"type": "horror", "target": "roland"}, [])
        assign_damage_choice(s, {"type": "horror", "target": "roland"}, [])
        self.assertEqual(s.investigator.horror, 2)

    def assert_four_point_soak_before_defeat(
        self,
        code: str,
        point_type: str,
        investigator_attr: str,
        starting_value: int,
    ) -> None:
        s = state()
        soak = add_card(s, code, "play")
        setattr(s.investigator, investigator_attr, starting_value)
        start_damage_assignment(
            s,
            [],
            source="probe",
            damage=4 if point_type == "damage" else 0,
            horror=4 if point_type == "horror" else 0,
        )
        for _ in range(4):
            assign_damage_choice(s, {"type": point_type, "target": soak}, [])

        self.assertEqual(getattr(s.investigator, investigator_attr), starting_value)
        self.assertEqual(s.status, "in_progress")
        self.assertIn(soak, s.investigator.discard)
        self.assertNotIn(soak, s.investigator.play_area)

    def test_bulletproof_vest_takes_four_damage_before_defeat_recomputes(self) -> None:
        self.assert_four_point_soak_before_defeat("01094", "damage", "damage", 7)

    def test_elder_sign_amulet_takes_four_horror_before_defeat_recomputes(self) -> None:
        self.assert_four_point_soak_before_defeat("01095", "horror", "horror", 5)

    def test_grotesque_statue_draws_two_and_resolves_only_the_choice(self) -> None:
        s = state()
        statue = add_card(s, "01071", "play")
        skill_test.start(s, [], skill="combat", difficulty=4, source="statue probe")
        finish_test(s, SeqRng([]))
        self.assertEqual(s.decision_queue[0].id, "grotesque-reaction")

        events: list[dict] = []
        skill_test.resolve_grotesque_reaction(
            s,
            {"kind": "grotesque_reaction", "choice": "use", "card": statue},
            events,
            SeqRng(["-2", "+1"]),
        )
        self.assertEqual(s.card_instances[statue].uses["charges"], 3)
        self.assertEqual(s.decision_queue[0].id, "grotesque-choice")
        choice = next(option.payload for option in s.decision_queue[0].options if option.payload["token"] == "+1")
        skill_test.resolve_grotesque_choice(s, choice, events, SeqRng([]))

        result = s.limits["last_skill_test"]
        self.assertEqual(result["token"], "+1")
        self.assertEqual(result["extra_tokens"], [])
        self.assertEqual(result["modifier"], 1)
        self.assertTrue(result["success"])
        chaos_events = [event for event in events if event["type"] == "chaos_token"]
        self.assertEqual(chaos_events[-1]["data"]["ignored"], ["-2"])

    def test_cryptic_research_is_fast_during_turn_and_draws_three(self) -> None:
        s = state()
        cryptic = add_card(s, "01043")
        draws = [add_card(s, code, "deck") for code in ("01016", "01017", "01018")]
        outside_turn: list = []
        actions.add_fast_options(s, outside_turn, during_turn=False)
        self.assertFalse(any(option.payload.get("card") == cryptic for option in outside_turn))
        during_turn: list = []
        actions.add_fast_options(s, during_turn, during_turn=True)
        self.assertTrue(any(option.payload.get("card") == cryptic for option in during_turn))

        actions.resolve_fast_ability(s, {"ability": "cryptic_research", "card": cryptic}, [])
        self.assertTrue(all(card_id in s.investigator.hand for card_id in draws))
        self.assertIn(cryptic, s.investigator.discard)
        self.assertEqual(s.investigator.resources, 10)
        self.assertEqual(s.investigator.actions_remaining, 3)

    def test_shotgun_damage_is_success_margin_with_minimum_one_and_maximum_five(self) -> None:
        for combat, token, expected in ((1, "0", 1), (10, "+1", 5)):
            with self.subTest(expected=expected):
                s = state()
                s.investigator.combat = combat
                shotgun = add_card(s, "01029", "play")
                priest = add_enemy(s, "01116")
                mask = add_card(s, "50043", "discard", "mask")
                s.enemies[priest].attachments.append(mask)  # 7 health keeps max-damage target alive.

                actions.execute(
                    s,
                    {
                        "kind": "action",
                        "action": "asset_fight",
                        "asset": shotgun,
                        "enemy": priest,
                        "boost": 3,
                        "damage": 1,
                        "shotgun": True,
                    },
                    [],
                    SeqRng([token]),
                )
                finish_test(s, SeqRng([token]))
                self.assertEqual(s.enemies[priest].damage, expected)
                self.assertEqual(s.card_instances[shotgun].uses["ammo"], 1)

    def test_mind_wipe_3_rejects_elite_and_preserves_attachment_granted_aloof(self) -> None:
        s = state()
        wipe = add_card(s, "50008")
        masked = add_enemy(s, "01160", engaged=False, instance_id="masked")
        mask = add_card(s, "50043", "discard", "mask")
        s.enemies[masked].attachments.append(mask)
        elite = add_enemy(s, "01116", engaged=False, instance_id="elite")
        self.assertTrue(enemies.is_aloof(s, masked))

        options: list = []
        actions.add_fast_options(s, options)
        targets = {
            option.payload.get("enemy")
            for option in options
            if option.payload.get("ability") == "mind_wipe"
        }
        self.assertIn(masked, targets)
        self.assertNotIn(elite, targets)

        actions.resolve_fast_ability(s, {"ability": "mind_wipe", "card": wipe, "enemy": masked}, [])
        self.assertEqual(enemies.enemy_damage_horror(s, masked), (0, 0))
        self.assertTrue(enemies.mind_wiped(s, masked))
        self.assertTrue(enemies.is_aloof(s, masked))

    def test_extra_ammunition_targets_only_controlled_firearms(self) -> None:
        s = state()
        extra = add_card(s, "01026")
        firearm = add_card(s, "01016", "play")
        melee = add_card(s, "01020", "play")
        options = actions.legal_actions(s)
        targets = {
            option.payload.get("asset")
            for option in options
            if option.payload.get("action") == "extra_ammo"
        }
        self.assertEqual(targets, {firearm})

        before = s.card_instances[firearm].uses["ammo"]
        actions.execute(
            s,
            {"kind": "action", "action": "extra_ammo", "card": extra, "asset": firearm},
            [],
            SeqRng([]),
        )
        self.assertEqual(s.card_instances[firearm].uses["ammo"], before + 3)
        self.assertNotIn("ammo", s.card_instances[melee].uses)
        self.assertIn(extra, s.investigator.discard)
        self.assertEqual(s.investigator.resources, 8)


if __name__ == "__main__":
    unittest.main()
