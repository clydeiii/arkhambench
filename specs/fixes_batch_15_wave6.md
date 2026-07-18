# Fixes batch 15 — wave-6 K3 audit round 2 (ledger 117–121)

One engine fix + three transcript-observability improvements. Tests in
tests/test_fixes_batch_15.py. Do not touch campaigns/, bench/, notebooks/,
viewer/. Full suite must stay green (`python3 -m unittest discover tests`).

## Fix 1 — ledger 119: duplicate game_end on Devourer-family defeats

arkham/effects.py `end_game` (~line 673-690) dispatches to
the_devourer_below.finalize_result (which logs game_end at
the_devourer_below.py:~1224) and then logs game_end AGAIN at effects.py:~690.
Gathering/Midnight Masks finalize_result log game_end only on resolution
branches; Devourer resolutions/resigns call finalize_result directly (once).

Fix: in end_game, do not emit the terminal log when the dispatched
finalize_result already appended a game_end event (check `events` for an
existing game_end after dispatch; do NOT delete either existing log site —
direct finalize_result callers and non-family scenarios depend on them).

Test: Devourer defeat via advance/damage path → exactly ONE game_end event in
events and one GAME OVER line; Devourer R1 resolution → exactly one;
Gathering defeat → exactly one.

## Improvement 2 — ledger 117: doom source in the markdown log

Doom-placement log lines ("Placed 1 doom on X.") omit the source, which
caused a false audit finding. Wherever doom_placed events are logged with a
`source` field (grep log_event.*doom_placed), render the source into the
message: "Placed 1 doom on Corpse-Taker (Corpse-Taker's Forced)." /
"(Mask of Umôrdhoth)". Keep the jsonl event fields unchanged. Only annotate
when a source is present; agenda step-1.3 doom keeps its current wording.

Test: trigger Corpse-Taker's end-of-mythos Forced → log message contains the
source; step-1.3 agenda doom message unchanged.

## Improvement 3 — ledger 120: log Lita entering play

arkham/scenarios/the_gathering.py `advance_act_2` (~lines 713-727) moves
setaside_lita to zone "story" attached to the Parlor with no log_event. Add:
log_event(events, "lita_enters_play", "Lita Chantler was put into play in the
Parlor.", card=<lita instance id>) right after the placement, before the act
advance log so the transcript mirrors the printed card order (reveal Parlor →
Lita into play → spawn Ghoul Priest is the card's order — match it; move the
existing lines if needed).

Test: drive act 2 advance → events contain lita_enters_play between the
parlor reveal and act_advanced; transcript line present.

## Verification gate

Fable reviews the diff; suite green.
