from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from arkham.cli import resolve_run_dir
from arkham.errors import EngineError

from tests.test_phase_c2_campaign import CampaignTempCase


class PlaySideForeignPointerGuardTests(CampaignTempCase):
    """Ledger 154: campaign play commands must not follow another lane's
    global .current_run pointer when their own campaign has no active run."""

    def setUp(self) -> None:
        super().setUp()
        self._saved_env = {
            key: os.environ.get(key) for key in ("AHLCG_CAMPAIGN", "AHLCG_RUN")
        }
        os.environ.pop("AHLCG_CAMPAIGN", None)
        os.environ.pop("AHLCG_RUN", None)

    def tearDown(self) -> None:
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        super().tearDown()

    def _campaign(self, name: str) -> Path:
        campaign_dir = self.campaign_dir(name)
        campaign_dir.mkdir()
        (campaign_dir / "campaign.json").write_text(
            json.dumps({"active_run": None}), encoding="utf-8"
        )
        return campaign_dir

    def _point_current_run(self, run_dir: Path) -> None:
        run_dir.mkdir(parents=True)
        (Path.cwd() / ".current_run").write_text(str(run_dir), encoding="utf-8")

    def test_campaign_refuses_foreign_global_pointer(self) -> None:
        campaign_dir = self._campaign("lane-a")
        foreign_run = self.campaign_dir("lane-b") / "runs" / "foreign"
        self._point_current_run(foreign_run)
        os.environ["AHLCG_CAMPAIGN"] = str(campaign_dir)

        with self.assertRaises(EngineError) as raised:
            resolve_run_dir(None)

        message = str(raised.exception)
        self.assertIn(str(foreign_run), message)
        self.assertIn(str(campaign_dir), message)

    def test_campaign_accepts_global_pointer_inside_campaign(self) -> None:
        campaign_dir = self._campaign("lane-a")
        own_run = campaign_dir / "runs" / "own"
        self._point_current_run(own_run)
        os.environ["AHLCG_CAMPAIGN"] = str(campaign_dir)

        self.assertEqual(resolve_run_dir(None), own_run)

    def test_global_pointer_remains_unrestricted_without_campaign(self) -> None:
        foreign_run = self.campaign_dir("lane-b") / "runs" / "foreign"
        self._point_current_run(foreign_run)

        self.assertEqual(resolve_run_dir(None), foreign_run)

    def test_ahlcg_run_outranks_campaign_and_global_pointer(self) -> None:
        campaign_dir = self._campaign("lane-a")
        global_run = self.campaign_dir("lane-b") / "runs" / "global"
        env_run = self.campaign_dir("lane-c") / "runs" / "explicit-env"
        self._point_current_run(global_run)
        env_run.mkdir(parents=True)
        os.environ["AHLCG_CAMPAIGN"] = str(campaign_dir)
        os.environ["AHLCG_RUN"] = str(env_run)

        self.assertEqual(resolve_run_dir(None), env_run)


if __name__ == "__main__":
    unittest.main()
