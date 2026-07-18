from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from arkham import campaign
from arkham.cli import resolve_run_dir
from arkham.errors import EngineError

from tests.test_phase_c2_campaign import CampaignTempCase


class CampaignRunIsolationTests(CampaignTempCase):
    """Ledger 113: parallel campaign lanes playing twin scenarios/seeds raced on
    the global .current_run pointer, so `campaign record` (and mid-game play
    commands) could bind a FOREIGN lane's run. The campaign now stamps its own
    active_run and never trusts the global pointer."""

    def _twin_campaigns(self) -> tuple[Path, Path, Path, Path]:
        a_dir = self.campaign_dir("lane-a")
        b_dir = self.campaign_dir("lane-b")
        campaign.create_campaign(a_dir, investigator="roland", difficulty="standard", seed=9401)
        campaign.create_campaign(b_dir, investigator="roland", difficulty="standard", seed=9401)
        a_run, _ = campaign.start_next_scenario(a_dir)
        b_run, _ = campaign.start_next_scenario(b_dir)  # overwrites .current_run
        return a_dir, b_dir, a_run, b_run

    def test_active_run_is_stamped_and_cleared(self) -> None:
        a_dir, _, a_run, _ = self._twin_campaigns()
        state = campaign.load_campaign(a_dir)
        self.assertEqual(state["active_run"], str(a_run))
        self.write_result(a_run)
        recorded = campaign.record_current_run(a_dir)
        self.assertIsNone(recorded["active_run"])

    def test_record_uses_own_active_run_not_global_pointer(self) -> None:
        a_dir, _, a_run, b_run = self._twin_campaigns()
        # global pointer says lane B; both runs are the same scenario, so the
        # scenario-name guard cannot tell them apart
        self.assertEqual(
            (Path.cwd() / ".current_run").read_text(encoding="utf-8"), str(b_run)
        )
        self.write_result(a_run, xp=5)
        self.write_result(b_run, xp=9)
        recorded = campaign.record_current_run(a_dir)
        self.assertEqual(recorded["scenarios"][0]["run"], str(a_run))
        self.assertEqual(recorded["xp_earned_total"], 5)

    def test_record_refuses_foreign_run_without_explicit_arg(self) -> None:
        a_dir, _, a_run, b_run = self._twin_campaigns()
        # simulate a pre-fix campaign (no active_run) whose deterministic run
        # dir is gone: resolution falls to the poisoned global pointer
        state = campaign.load_campaign(a_dir)
        state["active_run"] = None
        campaign.save_campaign(a_dir, state)
        import shutil

        shutil.rmtree(a_run)
        self.write_result(b_run)
        with self.assertRaisesRegex(EngineError, "does not belong to campaign"):
            campaign.record_current_run(a_dir)

    def test_record_falls_back_to_deterministic_run_dir(self) -> None:
        a_dir, _, a_run, b_run = self._twin_campaigns()
        state = campaign.load_campaign(a_dir)
        state["active_run"] = None  # pre-fix campaign state
        campaign.save_campaign(a_dir, state)
        self.write_result(a_run, xp=5)
        self.write_result(b_run, xp=9)
        recorded = campaign.record_current_run(a_dir)
        self.assertEqual(recorded["scenarios"][0]["run"], str(a_run))
        self.assertEqual(recorded["xp_earned_total"], 5)

    def test_resolve_run_dir_prefers_campaign_active_run(self) -> None:
        a_dir, _, a_run, b_run = self._twin_campaigns()
        saved = {k: os.environ.get(k) for k in ("AHLCG_RUN", "AHLCG_CAMPAIGN")}
        try:
            os.environ.pop("AHLCG_RUN", None)
            os.environ["AHLCG_CAMPAIGN"] = str(a_dir)
            # .current_run points at lane B, but the campaign's own state wins
            self.assertEqual(resolve_run_dir(None), Path(str(a_run)))
            os.environ["AHLCG_RUN"] = str(b_run)  # explicit env still outranks
            self.assertEqual(resolve_run_dir(None), Path(str(b_run)))
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
