from __future__ import annotations

import unittest
from pathlib import Path

from scripts.replay_corpus import find_run_dirs, replay_run


ROOT = Path(__file__).resolve().parent.parent


class ReplayCorpusTests(unittest.TestCase):
    def test_fixture_runs_replay_cleanly(self) -> None:
        run_dirs = find_run_dirs([ROOT / "tests" / "fixtures" / "replay_corpus"])

        self.assertEqual(len(run_dirs), 2)
        for run_dir in run_dirs:
            with self.subTest(run=run_dir.name):
                result = replay_run(run_dir)
                self.assertEqual(result.status, "DIVERGED", result)
                self.assertEqual(result.step, 0, result)
                self.assertEqual(result.detail, "prompt mismatch", result)
                self.assertIn("Choose cards to mulligan", str(result.expected))
                self.assertIn("Set aside any number of cards", str(result.actual))


if __name__ == "__main__":
    unittest.main()
