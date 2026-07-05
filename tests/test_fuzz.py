from __future__ import annotations

import unittest

from arkham.fuzz import run_fuzz


class FuzzSmokeTests(unittest.TestCase):
    def test_random_legal_choices_satisfy_invariants(self) -> None:
        outcomes = run_fuzz(5)
        self.assertEqual(sum(outcomes.values()), 5)


if __name__ == "__main__":
    unittest.main()
