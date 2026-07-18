# Fixes batch 17 — ledger 125 (Locked Door pool: all in-play locations)

Single conformance fix. Tests in tests/test_fixes_batch_17.py; update any
batch-3 tests that assert the revealed-only pool. Full suite green.

arkham/encounter.py locked_door_targets (~line 264-275): drop the
`location.revealed` filter — candidates are ALL in-play locations without a
Locked Door attached; unrevealed locations contribute clues == 0. Keep the
existing unique-max auto-attach / tie-choice logic unchanged.

Tests: (a) one revealed 0-clue location + three unrevealed in play -> 4-way
tie decision presented listing all four; (b) revealed location with 1 clue +
unrevealed others -> unique max auto-attach (unchanged); (c) unrevealed
location chosen -> door attaches there and blocks investigation after reveal
per existing attached-door rules.
