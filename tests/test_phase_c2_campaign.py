from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from arkham import campaign, upgrade
from arkham.errors import EngineError
from arkham.scenarios import the_midnight_masks


class CampaignTempCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.root = Path(self.tmp.name)
        self._campaign_counter = 0
        self._saved_pointers: dict[Path, str | None] = {}
        for name in (".current_campaign", ".current_run"):
            path = Path.cwd() / name
            self._saved_pointers[path] = path.read_text(encoding="utf-8") if path.exists() else None

    def tearDown(self) -> None:
        for path, text in self._saved_pointers.items():
            if text is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(text, encoding="utf-8")
        self.tmp.cleanup()

    def campaign_dir(self, name: str = "camp") -> Path:
        return self.root / name

    def write_result(self, run_dir: Path, **overrides: object) -> None:
        result = {
            "scenario": "return_to_the_gathering",
            "resolution": "R1",
            "outcome": "R1",
            "xp": 5,
            "score": 3,
            "trauma": {"physical": 0, "mental": 2},
            "damage_taken": 0,
            "horror_taken": 2,
            "investigator_killed": False,
            "investigator_insane": False,
            "campaign_log": {
                "house": "burned_down",
                "ghoul_priest_still_alive": False,
                "lita": "earned",
            },
            "weaknesses_added": ["01096"],
            "summary": "test result",
        }
        result.update(overrides)
        (run_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")


class CampaignLifecycleTests(CampaignTempCase):
    def test_campaign_lifecycle_record_upgrade_done_and_midnight_inputs(self) -> None:
        camp_dir = self.campaign_dir()
        state = campaign.create_campaign(camp_dir, investigator="roland", difficulty="standard", seed=42)
        self.assertEqual(state["phase"], "scenario")
        self.assertEqual(upgrade.counted_deck_size(state["deck"], "roland"), 30)

        run_dir, game = campaign.start_next_scenario(camp_dir)
        self.assertEqual(json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))["seed"], 4201)
        self.assertEqual(game.state.scenario, "return_to_the_gathering")
        self.write_result(run_dir)

        recorded = campaign.record_current_run(camp_dir, run_arg=str(run_dir))
        self.assertEqual(recorded["phase"], "upgrade")
        self.assertEqual(recorded["xp_unspent"], 5)
        self.assertEqual(recorded["xp_earned_total"], 5)
        self.assertEqual(recorded["trauma"], {"physical": 0, "mental": 2})
        self.assertFalse(recorded["log"]["your_house_standing"])
        self.assertFalse(recorded["log"]["ghoul_priest_alive"])
        self.assertTrue(recorded["log"]["lita_earned"])
        self.assertIn("01096", recorded["deck"]["weaknesses"])

        with self.assertRaisesRegex(EngineError, "upgrade phase"):
            campaign.start_next_scenario(camp_dir)

        campaign.choose_lita(camp_dir, include=True)
        done = campaign.finish_upgrade(camp_dir)
        self.assertEqual(done["phase"], "scenario")
        self.assertEqual(done["xp_unspent"], 5)

        mm_dir, mm_game = campaign.start_next_scenario(camp_dir)
        self.assertEqual(json.loads((mm_dir / "meta.json").read_text(encoding="utf-8"))["seed"], 4202)
        self.assertEqual(
            mm_game.state.limits["campaign_inputs"],
            {"house_burned": True, "ghoul_priest_alive": False, "lita_forced": False},
        )
        all_codes = [instance.card_code for instance in mm_game.state.card_instances.values()]
        self.assertIn("01117", all_codes)
        self.assertIn("01096", all_codes)

    def test_lita_transfers_when_killed_investigator_is_replaced(self) -> None:
        camp_dir = self.campaign_dir()
        campaign.create_campaign(camp_dir, investigator="roland", difficulty="standard", seed=7)
        run_dir, _ = campaign.start_next_scenario(camp_dir)
        self.write_result(
            run_dir,
            resolution="R3",
            outcome="R3",
            damage_taken=0,
            trauma={"physical": 0, "mental": 0},
            score=0,
            xp=0,
            investigator_killed=True,
            lita_earned=True,
            campaign_log={
                "house": "standing",
                "ghoul_priest_still_alive": True,
                "lita": "forced_to_find_others",
            },
            summary="R3",
        )

        recorded = campaign.record_current_run(camp_dir, run_arg=str(run_dir))
        self.assertEqual(recorded["phase"], "replace")
        self.assertEqual(recorded["killed_investigators"], ["roland"])
        self.assertTrue(recorded["log"]["lita_earned"])
        self.assertTrue(recorded["log"]["lita_was_forced_to_find_others"])

        campaign.choose_lita(camp_dir, include=True)
        replaced = campaign.replace_investigator(camp_dir, investigator="wendy")
        self.assertEqual(replaced["investigator"], "wendy")
        self.assertEqual(replaced["phase"], "scenario")
        self.assertEqual(replaced["xp_unspent"], 0)
        self.assertEqual(replaced["trauma"], {"physical": 0, "mental": 0})
        self.assertIn("01117", replaced["deck"]["story_assets"])
        self.assertEqual(upgrade.counted_deck_size(replaced["deck"], "wendy"), 30)

    def test_seed_determinism_for_scenario_seeds_and_variant_draws(self) -> None:
        observations = []
        for name in ("a", "b"):
            camp_dir = self.campaign_dir(name)
            campaign.create_campaign(camp_dir, investigator="roland", difficulty="standard", seed=99)
            run_dir, game = campaign.start_next_scenario(camp_dir)
            meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
            observations.append(
                (
                    meta["seed"],
                    game.state.limits.get("return_variant:attic"),
                    game.state.limits.get("return_variant:cellar"),
                    [game.state.card_instances[card_id].card_code for card_id in game.state.investigator.hand],
                )
            )
        self.assertEqual(observations[0], observations[1])

    def test_carried_trauma_does_not_count_as_scenario_trauma(self) -> None:
        camp_dir = self.campaign_dir()
        camp = campaign.create_campaign(camp_dir, investigator="roland", difficulty="standard", seed=5)
        camp["scenarios"].append({"scenario": "return_to_the_gathering"})
        camp["next"] = "return_to_the_midnight_masks"
        camp["trauma"] = {"physical": 1, "mental": 2}
        campaign.save_campaign(camp_dir, camp)

        run_dir, game = campaign.start_next_scenario(camp_dir)
        self.assertEqual(game.state.investigator.damage, 1)
        self.assertEqual(game.state.investigator.horror, 2)
        self.assertEqual(game.state.trauma, {})
        self.assertEqual(game.state.limits["carried_trauma"], {"physical": 1, "mental": 2})

        the_midnight_masks.resign(game.state, [])
        game.save()
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["trauma"], {})
        self.assertEqual(result["score"], result["xp"])
        recorded = campaign.record_current_run(camp_dir, run_arg=str(run_dir))
        self.assertEqual(recorded["trauma"], {"physical": 1, "mental": 2})

    def test_midnight_masks_full_damage_defeat_does_not_kill_without_explicit_flag_or_trauma_threshold(self) -> None:
        camp_dir = self.campaign_dir()
        campaign.create_campaign(camp_dir, investigator="roland", difficulty="standard", seed=8)
        run_dir, _ = campaign.start_next_scenario(camp_dir)
        self.write_result(run_dir, trauma={"physical": 0, "mental": 0})
        recorded = campaign.record_current_run(camp_dir, run_arg=str(run_dir))
        self.assertEqual(recorded["phase"], "upgrade")
        campaign.finish_upgrade(camp_dir)

        mm_dir, _ = campaign.start_next_scenario(camp_dir)
        self.write_result(
            mm_dir,
            scenario="return_to_the_midnight_masks",
            resolution="R1",
            outcome="R1",
            damage_taken=9,
            trauma={"physical": 1, "mental": 0},
            campaign_log=None,
            campaign={"scenario": "return_to_the_midnight_masks"},
            summary="Roland Banks was defeated",
        )
        recorded = campaign.record_current_run(camp_dir, run_arg=str(mm_dir))
        self.assertEqual(recorded["phase"], "upgrade")
        self.assertEqual(recorded["killed_investigators"], [])

    def test_accumulated_physical_trauma_at_health_kills_investigator(self) -> None:
        camp_dir = self.campaign_dir()
        campaign.create_campaign(camp_dir, investigator="agnes", difficulty="standard", seed=9)
        run_dir, _ = campaign.start_next_scenario(camp_dir)
        self.write_result(run_dir, trauma={"physical": 3, "mental": 0}, campaign_log={"lita": "not_earned"})
        recorded = campaign.record_current_run(camp_dir, run_arg=str(run_dir))
        self.assertEqual(recorded["phase"], "upgrade")
        campaign.finish_upgrade(camp_dir)

        mm_dir, _ = campaign.start_next_scenario(camp_dir)
        self.write_result(
            mm_dir,
            scenario="return_to_the_midnight_masks",
            trauma={"physical": 3, "mental": 0},
            campaign_log=None,
            campaign={"scenario": "return_to_the_midnight_masks"},
        )
        recorded = campaign.record_current_run(camp_dir, run_arg=str(mm_dir))
        self.assertEqual(recorded["phase"], "replace")
        self.assertEqual(recorded["killed_investigators"], ["agnes"])

    def test_gathering_lita_log_distinguishes_r2_from_r3(self) -> None:
        camp_dir = self.campaign_dir("r2")
        campaign.create_campaign(camp_dir, investigator="roland", difficulty="standard", seed=10)
        run_dir, _ = campaign.start_next_scenario(camp_dir)
        self.write_result(
            run_dir,
            resolution="R2",
            outcome="R2",
            lita_earned=False,
            trauma={"physical": 0, "mental": 0},
            campaign_log={"house": "standing", "ghoul_priest_still_alive": False, "lita": "not_earned"},
        )
        recorded = campaign.record_current_run(camp_dir, run_arg=str(run_dir))
        self.assertFalse(recorded["log"]["lita_earned"])
        self.assertFalse(recorded["log"]["lita_was_forced_to_find_others"])

        camp_dir = self.campaign_dir("r3")
        campaign.create_campaign(camp_dir, investigator="roland", difficulty="standard", seed=11)
        run_dir, _ = campaign.start_next_scenario(camp_dir)
        self.write_result(
            run_dir,
            resolution="R3",
            outcome="R3",
            xp=0,
            score=0,
            lita_earned=True,
            investigator_killed=True,
            trauma={"physical": 0, "mental": 0},
            campaign_log={"house": "standing", "ghoul_priest_still_alive": True, "lita": "forced_to_find_others"},
        )
        recorded = campaign.record_current_run(camp_dir, run_arg=str(run_dir))
        self.assertTrue(recorded["log"]["lita_earned"])
        self.assertTrue(recorded["log"]["lita_was_forced_to_find_others"])

    def test_replacement_rejects_current_and_killed_investigators(self) -> None:
        camp_dir = self.campaign_dir()
        camp = campaign.create_campaign(camp_dir, investigator="roland", difficulty="standard", seed=12)
        camp["phase"] = "replace"
        campaign.save_campaign(camp_dir, camp)
        with self.assertRaisesRegex(EngineError, "already the current investigator"):
            campaign.replace_investigator(camp_dir, investigator="roland")

        camp["killed_investigators"] = ["wendy"]
        campaign.save_campaign(camp_dir, camp)
        with self.assertRaisesRegex(EngineError, "was killed and cannot return"):
            campaign.replace_investigator(camp_dir, investigator="wendy")

    def test_record_rejects_result_for_wrong_scenario_and_preserves_lifetime_xp_spent_on_death(self) -> None:
        camp_dir = self.campaign_dir()
        camp = campaign.create_campaign(camp_dir, investigator="roland", difficulty="standard", seed=13)
        camp["xp_spent_total"] = 4
        campaign.save_campaign(camp_dir, camp)
        run_dir, _ = campaign.start_next_scenario(camp_dir)
        self.write_result(run_dir, scenario="return_to_the_midnight_masks")
        with self.assertRaisesRegex(EngineError, "return_to_the_midnight_masks.*return_to_the_gathering"):
            campaign.record_current_run(camp_dir, run_arg=str(run_dir))

        self.write_result(run_dir, investigator_killed=True, resolution="R3", outcome="R3", xp=0, score=0, trauma={"physical": 0, "mental": 0})
        recorded = campaign.record_current_run(camp_dir, run_arg=str(run_dir))
        self.assertEqual(recorded["phase"], "replace")
        self.assertEqual(recorded["xp_spent_total"], 4)
        self.assertEqual(recorded["xp_unspent"], 0)


class UpgradeMathAndLegalityTests(CampaignTempCase):
    def new_upgrade_campaign(self, investigator: str = "roland", xp: int = 6, name: str | None = None) -> dict:
        self._campaign_counter += 1
        dirname = name or f"{investigator}-{self._campaign_counter}"
        camp = campaign.create_campaign(self.campaign_dir(dirname), investigator=investigator, difficulty="standard", seed=1)
        camp["phase"] = "upgrade"
        camp["xp_unspent"] = xp
        camp["xp_earned_total"] = xp
        return camp

    def test_xp_math_and_banked_xp(self) -> None:
        camp = self.new_upgrade_campaign(xp=10, name="roland-xp-math")
        upgrade.buy_card(camp, "01091", remove="01019")
        self.assertEqual(camp["xp_unspent"], 9)

        upgrade.buy_card(camp, "50002", replace="01024")
        self.assertEqual(camp["xp_unspent"], 7)

        upgrade.buy_card(camp, "01028", remove="01019")
        self.assertEqual(camp["xp_unspent"], 5)

        upgrade.buy_card(camp, "01028", remove="01016")
        self.assertEqual(camp["xp_unspent"], 3)

        with self.assertRaisesRegex(EngineError, "not enough XP"):
            upgrade.buy_card(camp, "01029", remove="01024")

        campaign.save_campaign(self.campaign_dir("roland-xp-math"), camp)
        done = campaign.finish_upgrade(self.campaign_dir("roland-xp-math"))
        self.assertEqual(done["xp_unspent"], 3)

        wendy = self.new_upgrade_campaign("wendy", xp=3)
        upgrade.buy_card(wendy, "50010", replace="01075")
        self.assertEqual(wendy["xp_unspent"], 0)

    def test_deck_legality_named_cases_and_protected_removals(self) -> None:
        skids = self.new_upgrade_campaign("skids", xp=10)
        with self.assertRaisesRegex(EngineError, "not legal for skids"):
            upgrade.buy_card(skids, "01029", remove="01044")

        roland = self.new_upgrade_campaign("roland", xp=10)
        with self.assertRaisesRegex(EngineError, "not legal for roland"):
            upgrade.buy_card(roland, "01043", remove="01019")
        with self.assertRaisesRegex(EngineError, "not legal for roland"):
            upgrade.buy_card(roland, "50004", remove="01019")

        wendy = self.new_upgrade_campaign("wendy", xp=10)
        upgrade.buy_card(wendy, "50006", remove="01086")
        self.assertEqual(wendy["deck"]["slots"]["50006"], 1)
        with self.assertRaisesRegex(EngineError, "not legal for wendy"):
            upgrade.buy_card(wendy, "01056", remove="01086")

        capped = self.new_upgrade_campaign("skids", xp=10)
        upgrade.buy_card(capped, "01028", replace="01018")
        with self.assertRaisesRegex(EngineError, "would exceed 2 copies of Beat Cop"):
            upgrade.buy_card(capped, "01028", remove="01016")

        protected = self.new_upgrade_campaign("roland", xp=1)
        protected["deck"]["story_assets"].append("01117")
        for code in ("01006", "01102", "01117"):
            with self.assertRaisesRegex(EngineError, "protected"):
                upgrade.remove_card(protected, code)

        undersized = self.new_upgrade_campaign("roland", xp=1, name="undersized")
        upgrade.remove_card(undersized, "01016")
        campaign.save_campaign(self.campaign_dir("undersized"), undersized)
        with self.assertRaisesRegex(EngineError, "exactly 30"):
            campaign.finish_upgrade(self.campaign_dir("undersized"))

    def test_roland_six_xp_options_golden(self) -> None:
        camp = self.new_upgrade_campaign("roland", xp=6)
        got = [
            (o.code, o.name, o.level, o.faction, o.cost, o.kind, o.removal_required, o.affordable)
            for o in upgrade.purchase_options(camp)
        ]
        expected = [
            ("01016", ".45 Automatic", 0, "guardian", 1, "new", True, True),
            ("01018", "Beat Cop", 0, "guardian", 1, "new", True, True),
            ("01024", "Dynamite Blast", 0, "guardian", 1, "new", True, True),
            ("01025", "Vicious Blow", 0, "guardian", 1, "new", True, True),
            ("01026", "Extra Ammunition", 1, "guardian", 1, "new", True, True),
            ("01027", "Police Badge", 2, "guardian", 2, "new", True, True),
            ("01028", "Beat Cop", 2, "guardian", 2, "new", True, True),
            ("01029", "Shotgun", 4, "guardian", 4, "new", True, True),
            ("01031", "Old Book of Lore", 0, "seeker", 1, "new", True, True),
            ("01032", "Research Librarian", 0, "seeker", 1, "new", True, True),
            ("01033", "Dr. Milan Christopher", 0, "seeker", 1, "new", True, True),
            ("01034", "Hyperawareness", 0, "seeker", 1, "new", True, True),
            ("01035", "Medical Texts", 0, "seeker", 1, "new", True, True),
            ("01036", "Mind over Matter", 0, "seeker", 1, "new", True, True),
            ("01037", "Working a Hunch", 0, "seeker", 1, "new", True, True),
            ("01040", "Magnifying Glass", 1, "seeker", 1, "upgrade of 01030", False, True),
            ("01041", "Disc of Itzamna", 2, "seeker", 2, "new", True, True),
            ("01042", "Encyclopedia", 2, "seeker", 2, "new", True, True),
            ("01091", "Overpower", 0, "neutral", 1, "new", True, True),
            ("01092", "Manual Dexterity", 0, "neutral", 1, "new", True, True),
            ("01093", "Unexpected Courage", 0, "neutral", 1, "new", True, True),
            ("01094", "Bulletproof Vest", 3, "neutral", 3, "new", True, True),
            ("01095", "Elder Sign Amulet", 3, "neutral", 3, "new", True, True),
            ("50001", "Physical Training", 2, "guardian", 2, "upgrade of 01017", False, True),
            ("50002", "Dynamite Blast", 2, "guardian", 2, "upgrade of 01024", False, True),
            ("50003", "Hyperawareness", 2, "seeker", 2, "new", True, True),
        ]
        self.assertEqual(got, expected)

    def test_purchase_options_include_unaffordable_legal_cards(self) -> None:
        camp = self.new_upgrade_campaign("roland", xp=2)
        options = {option.code: option for option in upgrade.purchase_options(camp)}
        self.assertIn("01029", options)
        self.assertEqual(options["01029"].cost, 4)
        self.assertFalse(options["01029"].affordable)
        with self.assertRaisesRegex(EngineError, "not enough XP"):
            upgrade.buy_card(camp, "01029", remove="01024")


if __name__ == "__main__":
    unittest.main()
