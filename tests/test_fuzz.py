from __future__ import annotations

import unittest

from arkham.fuzz import run_fuzz


class FuzzSmokeTests(unittest.TestCase):
    def test_random_legal_choices_do_not_crash(self) -> None:
        outcomes = run_fuzz(8)
        self.assertEqual(sum(outcomes.values()), 8)


if __name__ == "__main__":
    unittest.main()
