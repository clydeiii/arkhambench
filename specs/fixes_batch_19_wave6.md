# Fixes batch 19 — ledger 134 (Dissonant Voices vs special-window event plays)

Tests in tests/test_fixes_batch_19.py. Full suite green.

arkham/skill_test.py legal_lucky_cards: exclude cards where
dissonant_blocks(state, code) is true (both hand copies and the Amulet
discard-top path). Then AUDIT every other special-window event-play legality
helper for the same gap — Ward of Protection's revelation-cancel window,
"Look what I found!" after-fail window, and any other SPECIAL_WINDOW_PLAYS
offering built outside actions.py's guarded menus — and add the same check
where missing. Do not change dissonant_blocks itself.

Tests: (a) would-fail window with Dissonant Voices in threat area and Lucky!
in hand -> no play option offered, test fails normally; (b) same via Wendy's
Amulet discard-top; (c) Ward's cancel window under Dissonant Voices -> no
cancel offer (if the gap existed); (d) without Dissonant Voices all offers
unchanged.
