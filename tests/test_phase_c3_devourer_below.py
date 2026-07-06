from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path

from arkham import actions, campaign, skill_test
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
from arkham.scenarios import the_devourer_below as d


def build(seed: int = 1, *, return_variant: bool = False, **kwargs):
    fn = d.build_return_state if return_variant else d.build_state
    return fn(difficulty="standard", rng=ArkhamRng(seed), deck_path=None, investigator_slug="roland", **kwargs)


def choose_state_with(codes: set[str], *, return_variant: bool = False):
    for seed in range(1, 300):
        state = build(seed, return_variant=return_variant)
        if codes <= {loc.code for loc in state.locations.values()}:
            return state
    raise AssertionError(f"no seed found for {codes}")


class PhaseC3DevourerTests(unittest.TestCase):
    def test_setup_counts_agents_and_priest(self) -> None:
        core = build(1)
        ret = build(1, return_variant=True)
        priest = build(1, ghoul_priest_alive=True)
        self.assertEqual(len(core.encounter_deck), 29)
        self.assertEqual(len(ret.encounter_deck), 31)
        self.assertEqual(len(priest.encounter_deck), 30)
        agent_codes = {core.card_instances[cid].card_code for cid in core.encounter_deck} & {
            code for counts in d.AGENT_SETS.values() for code in counts
        }
        self.assertEqual(sum(code in agent_codes for code in agent_codes), 2)
        core_counts = Counter(core.card_instances[cid].card_code for cid in core.encounter_deck)
        self.assertEqual(core_counts["01160"], 3)
        self.assertEqual(core_counts["01161"], 1)
        self.assertEqual(core_counts["01118"], 0)
        self.assertEqual(core_counts["01119"], 0)

    def test_got_away_doom_table(self) -> None:
        names = list(d.NAMED_CULTIST_BY_NAME)
        self.assertEqual(build(cultists_got_away=[]).agenda.doom, 0)
        self.assertEqual(build(cultists_got_away=names[:1]).agenda.doom, 1)
        self.assertEqual(build(cultists_got_away=names[:3]).agenda.doom, 2)
        self.assertEqual(build(cultists_got_away=names[:5]).agenda.doom, 3)

    def test_past_midnight_discards_two_after_mulligan(self) -> None:
        state = build(past_midnight=True)
        before = len(state.investigator.hand)
        d.resolve_scenario_choice(state, {"choice": "keep_hand"}, [], ArkhamRng(3))
        self.assertEqual(len(state.investigator.hand), max(0, before - 2))

    def test_woods_selection_and_back_connections(self) -> None:
        core = build(2)
        ret = build(2, return_variant=True)
        self.assertEqual(sum(1 for loc in core.locations.values() if loc.id != "main_path"), 4)
        self.assertEqual(sum(1 for loc in ret.locations.values() if loc.id != "main_path"), 4)
        for loc_id, loc in core.locations.items():
            if loc_id != "main_path":
                self.assertFalse(loc.revealed)
                self.assertEqual(loc.connections, ["main_path"])

    def test_inter_woods_edges_light_up_by_symbols(self) -> None:
        state = choose_state_with({"01151", "01152", "01155"})
        old_house = next(loc.id for loc in state.locations.values() if loc.code == "01152")
        twisting = next(loc.id for loc in state.locations.values() if loc.code == "01151")
        quiet = next(loc.id for loc in state.locations.values() if loc.code == "01155")
        for loc_id in [old_house, twisting, quiet]:
            d.reveal_location(state, [], loc_id)
        self.assertIn(twisting, state.locations[old_house].connections)
        self.assertIn(old_house, state.locations[twisting].connections)
        self.assertNotIn(quiet, state.locations[old_house].connections)

    def test_return_pair_edge_lights_up(self) -> None:
        state = choose_state_with({"50033", "50034"}, return_variant=True)
        willow = next(loc.id for loc in state.locations.values() if loc.code == "50033")
        lake = next(loc.id for loc in state.locations.values() if loc.code == "50034")
        d.reveal_location(state, [], willow)
        d.reveal_location(state, [], lake)
        self.assertIn(lake, state.locations[willow].connections)
        self.assertIn(willow, state.locations[lake].connections)

    def test_location_behaviors(self) -> None:
        state = choose_state_with({"01152", "01151", "01155"})
        old = next(loc.id for loc in state.locations.values() if loc.code == "01152")
        state.investigator.location_id = old
        state.locations[old].investigator_ids.append(state.investigator.id)
        d.reveal_location(state, [], old)
        label = next(option.label for option in actions.legal_actions(state) if option.payload.get("action") == "investigate")
        self.assertIn("Willpower", label)
        quiet = next(loc.id for loc in state.locations.values() if loc.code == "01155")
        state.investigator.location_id = quiet
        state.investigator.damage = 1
        d.reveal_location(state, [], quiet)
        events: list[dict] = []
        self.assertTrue(d.execute_action(state, {"action": "devourer_quiet_glade", "heal": "damage"}, events, ArkhamRng(1)))
        self.assertEqual(state.investigator.damage, 0)
        twist = next(loc.id for loc in state.locations.values() if loc.code == "01151")
        state.investigator.location_id = twist
        d.reveal_location(state, [], twist)
        self.assertTrue(d.before_move_from_twisting(state, "main_path", [],))
        self.assertEqual(state.active_skill_test["difficulty"], 3)

    def test_return_location_behaviors(self) -> None:
        state = choose_state_with({"50034", "50036", "50035", "50033"}, return_variant=True)
        lake = next(loc.id for loc in state.locations.values() if loc.code == "50034")
        bridge = next(loc.id for loc in state.locations.values() if loc.code == "50036")
        clearing = next(loc.id for loc in state.locations.values() if loc.code == "50035")
        willow = next(loc.id for loc in state.locations.values() if loc.code == "50033")
        state.investigator.location_id = lake
        self.assertTrue(d.location_extra_token_applies(state, {"on_success": {"kind": "investigate"}}))
        state.investigator.location_id = bridge
        self.assertTrue(d.location_extra_token_applies(state, {"on_success": {"kind": "evade"}}))
        state.investigator.location_id = clearing
        state.enemies["e"] = EnemyInstance(id="e", card_code="50038", location_id=clearing)
        self.assertEqual(d.damage_amount_to_enemy(state, "e", 3), 1)
        state.investigator.location_id = willow
        events: list[dict] = []
        d.after_skill_test(state, events, {"source": "Rotting Remains"}, {"success": True}, None)
        self.assertTrue(any(event["type"] == "surge" for event in events))

    def test_act_chain(self) -> None:
        got = list(d.NAMED_CULTIST_BY_NAME)[:2]
        state = build(cultists_got_away=got)
        state.investigator.clues = 3
        events: list[dict] = []
        d.advance_act(state, events, rng=ArkhamRng(1))
        self.assertIn("ritual_site", state.locations)
        self.assertEqual(state.act.stage, 2)
        self.assertEqual(len(state.locations["main_path"].enemy_ids), 2)
        d.advance_act(state, events, rng=ArkhamRng(2))
        self.assertEqual(state.act.stage, 3)
        state.investigator.clues = 2
        d.place_clue_on_act(state, events)
        d.place_clue_on_act(state, events)
        self.assertEqual(state.result["outcome"], "R1")

    def test_encounter_digs_preshuffle_discard_and_use_game_rng(self) -> None:
        orders = []
        for seed in [2, 9]:
            state = build()
            state.decision_queue = []
            state.encounter_deck = []
            state.encounter_discard = []
            state.card_instances["dig0"] = CardInstance(id="dig0", card_code="01163", zone="encounter_deck")
            state.encounter_deck.append("dig0")
            for index, code in enumerate(["01163", "01164", "01165", "01166", "01171"], start=1):
                cid = f"dig{index}"
                state.card_instances[cid] = CardInstance(id=cid, card_code=code, zone="encounter_discard")
                state.encounter_discard.append(cid)
            state.agenda.doom = state.agenda.threshold
            d.check_agenda_advance(state, [], rng=ArkhamRng(seed))
            orders.append([state.card_instances[cid].card_code for cid in state.encounter_discard])
            self.assertEqual(state.encounter_deck, [])
            self.assertCountEqual(state.encounter_discard, [f"dig{i}" for i in range(0, 6)])
        self.assertNotEqual(orders[0], orders[1])

        state = build()
        d.put_ritual_site_into_play(state, [])
        state.act.stage = 2
        state.encounter_deck = []
        state.encounter_discard = []
        for index, code in enumerate(["01163", "01164", "01165"], start=1):
            cid = f"actdig{index}"
            state.card_instances[cid] = CardInstance(id=cid, card_code=code, zone="encounter_discard")
            state.encounter_discard.append(cid)
        d.advance_act(state, [], rng=ArkhamRng(4))
        self.assertEqual(state.act.stage, 3)
        self.assertEqual(state.encounter_deck, [])
        self.assertCountEqual(state.encounter_discard, [f"actdig{i}" for i in range(1, 4)])

    def test_agenda_two_aura_stops_on_agenda_three(self) -> None:
        state = build()
        enemy = next(iter(state.encounter_deck))
        state.encounter_deck.remove(enemy)
        state.card_instances[enemy].card_code = "01160"
        state.enemies[enemy] = EnemyInstance(id=enemy, card_code="01160", location_id="main_path")
        state.locations["main_path"].enemy_ids.append(enemy)
        state.agenda.stage = 2
        self.assertEqual(d.enemy_fight_bonus(state, enemy), 1)
        self.assertEqual(d.enemy_evade_bonus(state, enemy), 1)
        d.advance_to_agenda3(state, [])
        self.assertEqual(d.enemy_fight_bonus(state, enemy), 0)
        self.assertEqual(d.enemy_evade_bonus(state, enemy), 0)

    def test_agenda_chain_and_combined_card(self) -> None:
        state = build()
        state.decision_queue = []
        events: list[dict] = []
        state.agenda.doom = 4
        d.check_agenda_advance(state, events, rng=ArkhamRng(2))
        self.assertEqual(state.agenda.stage, 2)
        self.assertTrue(any(enemy.doom == 1 for enemy in state.enemies.values()))
        state.active_skill_test = None
        d.advance_to_agenda3(state, events)
        self.assertEqual(state.agenda.stage, 3)
        d.advance_agenda3_to_devourer(state, events)
        self.assertEqual(state.act.code, "01145b")
        self.assertTrue(any(enemy.card_code == "01157" for enemy in state.enemies.values()))

    def test_umordhoth_massive_ready_attack_lita_and_r2(self) -> None:
        state = build(lita_in_deck=True)
        events: list[dict] = []
        d.put_ritual_site_into_play(state, events)
        d.spawn_umordhoth(state, events)
        state.investigator.location_id = "ritual_site"
        um = next(eid for eid, enemy in state.enemies.items() if enemy.card_code == "01157")
        self.assertIn(um, d.massive_attackers(state, set()))
        state.enemies[um].exhausted = True
        d.end_investigator_turn(state, events)
        self.assertFalse(state.enemies[um].exhausted)
        lita = next(cid for cid, inst in state.card_instances.items() if inst.card_code == "01117")
        state.investigator.play_area.append(lita)
        self.assertTrue(d.execute_action(state, {"action": "devourer_lita"}, events, ArkhamRng(1)))
        self.assertEqual(state.result["outcome"], "R3")
        state2 = build()
        d.put_ritual_site_into_play(state2, [])
        d.spawn_umordhoth(state2, [])
        um2 = next(eid for eid, enemy in state2.enemies.items() if enemy.card_code == "01157")
        d.after_enemy_defeated(state2, [], um2)
        self.assertEqual(state2.result["outcome"], "R2")

    def test_umordhoth_can_be_evaded_as_massive_enemy(self) -> None:
        state = build()
        events: list[dict] = []
        d.put_ritual_site_into_play(state, events)
        d.spawn_umordhoth(state, events)
        state.locations["main_path"].investigator_ids.remove(state.investigator.id)
        state.investigator.location_id = "ritual_site"
        state.locations["ritual_site"].investigator_ids.append(state.investigator.id)
        state.investigator.agility = 9
        um = next(eid for eid, enemy in state.enemies.items() if enemy.card_code == "01157")
        evade = next(option for option in actions.legal_actions(state) if option.payload.get("action") == "evade")
        self.assertEqual(evade.payload["enemy"], um)
        actions.execute(state, evade.payload, events, ArkhamRng(1))
        self.assertEqual(state.active_skill_test["difficulty"], 6)
        skill_test.finish_commit(state, ArkhamRng(1), events)
        self.assertTrue(state.enemies[um].exhausted)
        self.assertIsNone(state.enemies[um].engaged_with)
        self.assertNotIn(um, d.massive_attackers(state, set()))

    def test_return_vault_math(self) -> None:
        for stage, expected in [(1, 3), (2, 2), (3, 1)]:
            state = build(return_variant=True)
            state.act.stage = stage
            d.put_ritual_site_into_play(state, [])
            d.spawn_umordhoth(state, [])
            self.assertEqual(d.vault_resources(state), expected)
            um = next(eid for eid, enemy in state.enemies.items() if enemy.card_code == "01157")
            self.assertEqual(d.enemy_fight_bonus(state, um), expected)

    def test_token_effects_all_difficulties(self) -> None:
        for difficulty in ["easy", "standard", "hard", "expert"]:
            state = d.build_state(difficulty=difficulty, rng=ArkhamRng(1), deck_path=None, investigator_slug="roland")
            state.enemies["m"] = EnemyInstance(id="m", card_code="50038", location_id="main_path")
            state.locations["main_path"].enemy_ids.append("m")
            events: list[dict] = []
            d.apply_token_aftermath(state, events, {"token": "cultist", "success": True}, ArkhamRng(1))
            self.assertEqual(state.enemies["m"].doom, 1 if difficulty in {"easy", "standard"} else 2)
            d.apply_token_aftermath(state, events, {"token": "tablet", "success": True}, ArkhamRng(1))
            self.assertGreaterEqual(state.investigator.damage, 1)

    def test_resolutions_campaign_flags_and_weakness(self) -> None:
        state = build()
        d.finalize_result(state, [], outcome="no_resolution", resolution="no_resolution", summary="lost", resigned=True)
        self.assertTrue(state.result["investigator_killed"])
        self.assertTrue(state.result["campaign"]["arkham_succumbed"])
        state = build()
        d.finalize_result(state, [], outcome="R1", resolution="R1", summary="r1")
        self.assertEqual(state.result["xp"], state.result["victory_points"] + 5)
        self.assertEqual(state.result["trauma"]["mental"], 2)
        state = build()
        d.finalize_result(state, [], outcome="R2", resolution="R2", summary="r2")
        self.assertEqual(state.result["xp"], state.result["victory_points"] + 10)
        self.assertEqual(state.result["trauma"]["physical"], 2)
        state = build()
        d.finalize_result(state, [], outcome="R3", resolution="R3", summary="r3", rng=ArkhamRng(1))
        self.assertFalse(state.result["investigator_killed"])
        self.assertIn("weakness_gained", state.result["campaign"])

    def test_r3_madness_weakness_uses_rng_and_full_pool(self) -> None:
        gained = set()
        for seed in range(1, 12):
            state = build(seed)
            d.finalize_result(state, [], outcome="R3", resolution="R3", summary="r3", rng=ArkhamRng(seed))
            gained.add(state.result["campaign"]["weakness_gained"][0])
        self.assertLessEqual(gained, set(d.MADNESS_WEAKNESSES))
        self.assertGreater(len(gained), 1)
        self.assertEqual(set(d.MADNESS_WEAKNESSES), {"01096", "01097", "01099", "01100"})

    def test_dark_cult_original_spawns_at_any_empty_location(self) -> None:
        for code in ["01169", "01170"]:
            state = build()
            cid = f"spawn_{code}"
            state.card_instances[cid] = CardInstance(id=cid, card_code=code, zone="encounter_drawn")
            state.encounter_deck = [card_id for card_id in state.encounter_deck if card_id != cid]
            d.encounter_revelation(state, ArkhamRng(1), [], cid)
            self.assertEqual(state.decision_queue[0].id, "enemy-spawn-location")
            locations = {option.payload["location"] for option in state.decision_queue[0].options}
            self.assertGreater(len(locations), 1)
            self.assertNotEqual(locations, {"main_path"})

    def test_campaign_adapter_inputs_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            camp = campaign.create_campaign(root, investigator="roland", difficulty="standard", seed=7, original=True)
            camp["next"] = "the_devourer_below"
            camp["scenarios"] = [{}, {}]
            camp["log"]["cultists_got_away"] = ["Herman Collins"]
            camp["log"]["past_midnight"] = True
            camp["log"]["ghoul_priest_alive"] = True
            camp["log"]["lita_in_deck"] = True
            campaign.save_campaign(root, camp)
            run_dir, game = campaign.start_next_scenario(root)
            self.assertEqual(game.state.limits["campaign_inputs"]["cultists_got_away"], ["Herman Collins"])
            result = {
                "scenario": "the_devourer_below",
                "resolution": "R3",
                "xp": 0,
                "score": 0,
                "trauma": {"physical": 2, "mental": 2},
                "campaign": {"lita_sacrificed": True, "elderthing_added": True, "weakness_gained": ["01096"]},
            }
            from arkham.serialize import atomic_write_json

            atomic_write_json(run_dir / "result.json", result)
            recorded = campaign.record_current_run(root, str(run_dir))
            self.assertTrue(recorded["log"]["lita_sacrificed"])
            self.assertIn("elderthing", recorded["chaos_bag_additions"])
            self.assertIn("01096", recorded["deck"]["weaknesses"])


if __name__ == "__main__":
    unittest.main()
