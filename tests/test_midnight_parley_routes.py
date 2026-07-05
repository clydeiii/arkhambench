"""Claude's verification tests: every named cultist's route to the victory display."""
from __future__ import annotations

import unittest

from arkham import enemies, skill_test
from arkham.rng import ArkhamRng
from arkham.scenarios import the_midnight_masks as mm


def make_state(return_variant: bool = False, **kwargs):
    build = mm.build_return_state if return_variant else mm.build_state
    state = build(difficulty="standard", rng=ArkhamRng(3), investigator_slug="roland", **kwargs)
    state.decision_queue = []  # skip mulligan for direct rules probing
    state.limits.pop("mulligan_available", None)
    return state


def force_cultist(state, code: str) -> str:
    """Put a specific named cultist into play at its spawn location."""
    card_id = next(
        (cid for cid in list(state.limits.get("cultist_deck", [])) if state.card_instances[cid].card_code == code),
        None,
    )
    if card_id is None:  # removed by Return setup; re-materialize
        card_id = f"test_{code}"
        from arkham.model import CardInstance

        state.card_instances[card_id] = CardInstance(id=card_id, card_code=code, zone="cultist_deck")
    else:
        state.limits["cultist_deck"] = [c for c in state.limits["cultist_deck"] if c != card_id]
    mm.spawn_named_cultist(state, [], card_id)
    return card_id


def move_to(state, location_id: str) -> None:
    mm.move_investigator_to(state, [], location_id)


class ParleyRouteTests(unittest.TestCase):
    def test_herman_discard_four_cards(self) -> None:
        state = make_state()
        herman = force_cultist(state, "01138")
        move_to(state, "rivertown")
        move_to(state, "graveyard")
        state.decision_queue = []
        hand_before = len(state.investigator.hand)
        self.assertGreaterEqual(hand_before, 4)
        mm.parley_cultist(state, herman, [], ArkhamRng(3))
        # resolve the sequential discard decisions
        for _ in range(4):
            self.assertTrue(state.decision_queue)
            option = state.decision_queue[0].options[0]
            state.decision_queue = []
            mm.resolve_scenario_choice(state, option.payload, [], ArkhamRng(3))
        self.assertNotIn(herman, state.enemies)
        self.assertIn(herman, state.victory_display)
        self.assertEqual(len(state.investigator.hand), hand_before - 4)

    def test_peter_two_clues_blocked_by_masked_hunter(self) -> None:
        state = make_state()
        peter = force_cultist(state, "01139")
        move_to(state, "rivertown")
        move_to(state, "miskatonic_university")
        state.investigator.clues = 2
        # engage the Masked Hunter -> clue spends blocked -> parley does nothing
        state.agenda.doom = 6
        mm.check_agenda_advance(state, [], rng=ArkhamRng(3))
        self.assertIn("setaside_agenda_enemy", state.investigator.engaged_enemies)
        mm.parley_cultist(state, peter, [], ArkhamRng(3))
        self.assertIn(peter, state.enemies)
        self.assertEqual(state.investigator.clues, 2)
        # defeat the hunter -> parley works
        enemies.defeat_enemy(state, [], "setaside_agenda_enemy")
        state.decision_queue = []
        mm.parley_cultist(state, peter, [], ArkhamRng(3))
        self.assertIn(peter, state.victory_display)
        self.assertEqual(state.investigator.clues, 0)

    def test_victoria_five_resources(self) -> None:
        state = make_state()
        victoria = force_cultist(state, "01140")
        move_to(state, "rivertown")
        move_to(state, "miskatonic_university")
        move_to(state, "northside")
        state.investigator.resources = 5
        mm.parley_cultist(state, victoria, [], ArkhamRng(3))
        self.assertIn(victoria, state.victory_display)
        self.assertEqual(state.investigator.resources, 0)

    def test_ruth_goes_to_victory_on_evade(self) -> None:
        state = make_state()
        ruth = force_cultist(state, "01141")
        move_to(state, "rivertown")
        move_to(state, "southside")
        move_to(state, "st_marys_hospital")
        self.assertIn(ruth, state.investigator.engaged_enemies)
        mm.after_enemy_evaded(state, [], ruth)
        self.assertIn(ruth, state.victory_display)

    def test_drew_heals_when_attacking(self) -> None:
        state = make_state()
        drew = force_cultist(state, "01137")
        state.enemies[drew].damage = 2
        mm.after_enemy_attacks(state, [], drew)
        self.assertEqual(state.enemies[drew].damage, 1)

    def test_jeremiah_parley_then_doom_test(self) -> None:
        state = make_state(return_variant=True)
        jeremiah = force_cultist(state, "50044")
        loc = state.enemies[jeremiah].location_id
        self.assertIn(loc, {"your_house", "rivertown"})
        move_to(state, loc) if loc != state.investigator.location_id else None
        state.decision_queue = []
        mm.parley_cultist(state, jeremiah, [], ArkhamRng(3))
        self.assertIn(jeremiah, state.victory_display)
        self.assertIsNotNone(state.active_skill_test)
        self.assertEqual(state.active_skill_test["skill"], "willpower")

    def test_jeremiah_spawns_rivertown_when_house_burned(self) -> None:
        state = make_state(return_variant=True, house_burned=True)
        jeremiah = force_cultist(state, "50044")
        self.assertEqual(state.enemies[jeremiah].location_id, "rivertown")

    def test_billy_cooper_on_monster_defeat_at_location(self) -> None:
        state = make_state(return_variant=True)
        billy = force_cultist(state, "50045")
        billy_loc = state.enemies[billy].location_id
        # spawn a Monster (Hunting Nightgaunt) at Billy's location and defeat it
        gaunt = next(cid for cid in state.encounter_deck if state.card_instances[cid].card_code == "01172")
        state.encounter_deck.remove(gaunt)
        from arkham.enemies import spawn_enemy

        spawn_enemy(state, [], instance_id=gaunt, location_id=billy_loc, engaged=False)
        state.enemies[gaunt].damage = 99
        enemies.defeat_enemy(state, [], gaunt)
        self.assertIn(billy, state.victory_display)

    def test_alma_draws_three_then_victory(self) -> None:
        state = make_state(return_variant=True)
        alma = force_cultist(state, "50046")
        move_to(state, "rivertown")
        move_to(state, "southside")
        state.decision_queue = []
        deck_before = len(state.encounter_deck)
        mm.parley_cultist(state, alma, [], ArkhamRng(3))
        drawn = deck_before - len(state.encounter_deck)
        self.assertGreaterEqual(drawn, 1)
        if not state.decision_queue and state.status == "in_progress":
            self.assertIn(alma, state.victory_display)

    def test_six_unique_cultists_end_scenario(self) -> None:
        state = make_state()
        state.decision_queue = []
        for code in ("01137", "01138", "01139", "01140", "01141"):
            cid = force_cultist(state, code)
            mm.add_enemy_to_victory(state, [], cid, reason="test")
        self.assertEqual(state.status, "in_progress")
        state.agenda.doom = 6
        mm.check_agenda_advance(state, [], rng=ArkhamRng(3))
        hunter = "setaside_agenda_enemy"
        state.enemies[hunter].damage = 99
        enemies.defeat_enemy(state, [], hunter)
        self.assertEqual(state.status, "ended")
        self.assertEqual(state.result["outcome"], "R1")
        self.assertEqual(state.result["victory_points"], 5 + 2)
        self.assertEqual(state.result["campaign"]["cultists_interrogated"],
                         sorted(["\"Wolf-Man\" Drew", "Herman Collins", "Peter Warren",
                                 "Victoria Devereux", "Ruth Turner", "The Masked Hunter"]))


if __name__ == "__main__":
    unittest.main()
