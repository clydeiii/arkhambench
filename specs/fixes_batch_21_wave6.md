# Fixes batch 21 — ledger 137-138

Tests in tests/test_fixes_batch_21.py. Full suite green.

## Fix 1 — ledger 137: central enemies_defeated counter

Move the increment from the_gathering.py (~line 753) into
arkham/enemies.py defeat_enemy so every defeat path (basic fight, asset
fight, event damage, reaction damage, direct effects) in every scenario
counts once. Remove the scenario-local increment; keep the three
finalize_result readers unchanged. Tests: Shrivelling kill in MM and a
reaction-damage kill count; no double-count on a basic fight kill in
Gathering.

## Fix 2 — ledger 138: Leo De Luca xp:1 without breaking starters

data/cards: set 01048 xp to 1 (printed level). Then:
- deckbuild swap must now refuse 01048 as swap-IN (level-0 only) — test it.
- Skids's printed suggested starter legitimately contains Leo: ensure
  starter/campaign deck validation still accepts the fixed starter lists
  as-is (whitelist by starter membership if validate_deck would now
  reject — check what validate_deck actually enforces about levels before
  adding anything).
- upgrade options/pricing: buying a second Leo (max copies permitting)
  prices at max(1,1)=1 (unchanged numerically); upgrade-of relationships
  unaffected (no level-0 Leo exists).
- Audit data/cards for OTHER cards whose xp field disagrees with print in
  the implemented pool (compare every 0-xp card that ledger/docs call
  leveled; at minimum spot-check the other starter-deck level-1 allies) and
  fix any found the same way. Report which.
