from __future__ import annotations

import unittest

from arkham import actions, deckbuild, effects, skill_test, upgrade
from arkham.cards import player as player_cards
from arkham.errors import EngineError
from arkham.model import CardInstance, EnemyInstance
from arkham.rng import ArkhamRng
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
    state.enemies = {}
    for location in state.locations.values():
        location.enemy_ids = []


def add_card(state, code: str, card_id: str) -> str:  # type: ignore[no-untyped-def]
    state.card_instances[card_id] = CardInstance(
        id=card_id,
        card_code=code,
        zone="play",
        owner=state.investigator.id,
    )
    state.investigator.play_area.append(card_id)
    player_cards.setup_uses(state.card_instances[card_id])
    return card_id


def add_rat(state, enemy_id: str) -> str:  # type: ignore[no-untyped-def]
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


def skids_deckbuild_campaign() -> dict:
    return {
        "phase": "deckbuild",
        "investigator": "skids",
        "deck": upgrade.split_starting_deck("skids"),
        "deckbuild_swaps": [],
        "purchases": [],
        "scenarios": [],
        "xp_unspent": 0,
        "xp_spent_total": 0,
    }


class EnemiesDefeatedCounterTests(unittest.TestCase):
    def test_shrivelling_kill_in_midnight_masks_counts_once(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(21), investigator_slug="agnes")
        clear_state(state)
        shrivelling = add_card(state, "01060", "shrivelling")
        rat = add_rat(state, "mm-rat")

        actions.execute(
            state,
            {
                "kind": "action",
                "action": "asset_fight",
                "asset": shrivelling,
                "enemy": rat,
                "damage": 2,
                "skill": "willpower",
                "spend_use": "charges",
                "symbol_horror": True,
            },
            [],
            SeqRng(["0"]),
        )
        skill_test.finish_commit(state, SeqRng(["0"]), [])

        self.assertNotIn(rat, state.enemies)
        self.assertEqual(state.limits.get("enemies_defeated"), 1)

    def test_agnes_reaction_damage_kill_counts_once(self) -> None:
        state = mm.build_state(difficulty="standard", rng=ArkhamRng(21), investigator_slug="agnes")
        clear_state(state)
        rat = add_rat(state, "reaction-rat")

        effects.resolve_agnes_horror_reaction(
            state,
            {"enemy": rat, "key": "agnes_horror:regression"},
            [],
        )

        self.assertNotIn(rat, state.enemies)
        self.assertEqual(state.limits.get("enemies_defeated"), 1)

    def test_basic_fight_kill_in_gathering_is_not_double_counted(self) -> None:
        state = tg.build_engine_test_state(difficulty="standard", rng=ArkhamRng(21))
        clear_state(state)
        rat = add_rat(state, "gathering-rat")

        actions.execute(
            state,
            {"kind": "action", "action": "fight", "enemy": rat},
            [],
            SeqRng(["0"]),
        )
        skill_test.finish_commit(state, SeqRng(["0"]), [])

        self.assertNotIn(rat, state.enemies)
        self.assertEqual(state.limits.get("enemies_defeated"), 1)


class LeoDeLucaAdjudicationTests(unittest.TestCase):
    def test_deckbuild_swap_in_of_printed_level_zero_leo_is_accepted(self) -> None:
        campaign = skids_deckbuild_campaign()

        deckbuild.swap(campaign, in_code="01048", out_code="01044")

        self.assertEqual(campaign["deck"]["slots"]["01048"], 1)
        self.assertEqual(campaign["deckbuild_swaps"], [{"in": "01048", "out": "01044"}])

    def test_deckbuild_swap_in_of_level_one_leo_is_refused(self) -> None:
        campaign = skids_deckbuild_campaign()

        with self.assertRaisesRegex(EngineError, "01054 is not a level-0 card"):
            deckbuild.swap(campaign, in_code="01054", out_code="01044")

        self.assertNotIn("01054", campaign["deck"]["slots"])

    def test_upgrade_from_01048_to_01054_costs_one_xp(self) -> None:
        campaign = skids_deckbuild_campaign()
        deckbuild.swap(campaign, in_code="01048", out_code="01044")
        campaign["phase"] = "upgrade"
        campaign["xp_unspent"] = 1

        option = {item.code: item for item in upgrade.purchase_options(campaign)}["01054"]
        self.assertEqual((option.level, option.cost, option.kind), (1, 1, "upgrade of 01048"))

        upgrade.buy_card(campaign, "01054", replace="01048")

        self.assertEqual(campaign["xp_unspent"], 0)
        self.assertNotIn("01048", campaign["deck"]["slots"])
        self.assertEqual(campaign["deck"]["slots"]["01054"], 1)
        self.assertEqual(campaign["purchases"][-1]["price"], 1)


if __name__ == "__main__":
    unittest.main()
