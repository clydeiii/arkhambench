from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from arkham.game import Game


CAMPAIGN_CONTEXT = {
    "campaign": "briefing-test",
    "scenario_number": 1,
    "scenario_total": 3,
    "trauma": {"physical": 0, "mental": 0},
    "xp_unspent": 0,
    "log": {},
}


def campaign_mission(scenario: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        Game.new(
            seed=20,
            difficulty="standard",
            deck_path=None,
            run_dir=run_dir,
            scenario=scenario,
            campaign_context=CAMPAIGN_CONTEXT,
        )
        return (run_dir / "mission.md").read_text(encoding="utf-8")


class CampaignMissionBriefingTests(unittest.TestCase):
    def test_gathering_run_gets_only_gathering_briefing(self) -> None:
        original = campaign_mission("the_gathering")
        returned = campaign_mission("return_to_the_gathering")

        for mission in (original, returned):
            self.assertIn("The Gathering briefing:", mission)
            self.assertIn("Lita Chantler", mission)
            self.assertNotIn("Devourer Below briefing", mission)
        self.assertIn("Escape the Study", original)
        self.assertIn("aberrant gateway leads only to the Guest Hall", returned)

    def test_midnight_masks_run_mentions_resign_is_offered(self) -> None:
        for scenario in ("the_midnight_masks", "return_to_the_midnight_masks"):
            with self.subTest(scenario=scenario):
                mission = campaign_mission(scenario)
                self.assertIn("The Midnight Masks briefing:", mission)
                self.assertIn("RESIGN IS OFFERED from round 1", mission)
                self.assertIn("Resolution 1", mission)
                self.assertNotIn("Devourer Below briefing", mission)

    def test_devourer_below_briefing_is_unchanged(self) -> None:
        briefing = """The Devourer Below briefing:
- Doom pressure is severe: agendas are 4/5/5, with Ancient Evils x3 and doom-on-enemy effects counting toward advancement.
- Decide early between the Ritual Site clue plan, defeating Umordhoth, or sacrificing Lita; resigning is no escape and records Arkham's destruction.
- Cultists who got away add setup doom and reappear at Main Path when Act 1 advances.
- In Return, Vault of Earthly Demise makes Umordhoth tougher if it appears while more acts remain.
"""

        for scenario in ("the_devourer_below", "return_to_the_devourer_below"):
            with self.subTest(scenario=scenario):
                self.assertIn(briefing, campaign_mission(scenario))


if __name__ == "__main__":
    unittest.main()
