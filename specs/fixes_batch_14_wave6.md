# Fixes batch 14 — wave-6 Kimi K3 audit findings (ledger 114–116)

Implement in arkham/, tests in tests/test_fixes_batch_14.py. Do not touch
campaigns/, bench/, notebooks/, viewer/. Full suite must stay green
(`python3 -m unittest discover tests`). Keep diffs minimal and in-idiom.

## Fix 1 — ledger 114: Lita Chantler must occupy the ally slot

`arkham/actions.py` `slotted_asset_ids()` hardcodes
`if state.card_instances[instance_id].card_code == "01117": continue`.
Remove that exemption. Lita (01117) has slot "Ally" in
data/cards/core_encounter.json and the campaign guide exempts her from deck
SIZE only.

Requirements:
- Playing an ally while Lita is in play (or playing Lita while another ally
  is in play) over the 1-ally limit must present the slot-overflow discard
  decision (existing `required_slot_discards` / `present_slot_discard_decision`
  flow).
- Gaining control of Lita via scenario effect (The Gathering resolution /
  Devourer setup story asset entry) must also enforce capacity: find where
  story assets enter play (`enforce_slot_capacity` call sites) and make sure
  that path covers her; RR: "If playing or GAINING CONTROL of an asset would
  put an investigator above his or her slot limit… must choose and discard".
- Charisma-style exceptions don't exist in the core set; no special cases.

Tests: (a) play second ally with Lita in play → overflow decision offered,
choosing the old ally discards it, both never coexist; (b) story-entry path
enforces too; (c) regression: 01070 (Holy Rosary? verify actual arcane-bonus
card) Arcane logic untouched.

## Fix 2 — ledger 115: restore the during-turn post-final-action fast window

`arkham/phases.py` investigation branch (~line 88): when
`actions_remaining == 0` the loop goes straight to
`resolve_dark_memory_end_turn` → `start_frozen_end_turn_test` → enemy phase.
Ledger #6/#18 mandate a during-turn player window after the final action,
BEFORE end-of-turn Forced effects; #34 only outlawed the post-turn window.
`present_fast_window(state, "inv_end", during_turn=True)` still exists and
passes its unit tests — batch 8 removed its call site.

Requirements:
- Before `resolve_dark_memory_end_turn`, offer
  `present_fast_window(state, "inv_end", during_turn=True)` and return if a
  decision was queued.
- Skip the window when `turn_forcibly_ended:{round}` is set (forced turn
  end — #6's flag).
- The window must close (pass) before Dark Memory / Frozen in Fear fire, and
  must not re-open after them (existing `fastwin:` guard key handles this —
  verify the key survives until round cleanup; it is already in the
  round-start limits filter).
- No post-turn window may reappear (#34 regression must stay covered).

Tests (INTEGRATION through the phase loop / advance_until_decision, not unit
calls): (a) with a ready fast-ability asset (e.g. Arcane Initiate 01063) in
play and 0 actions remaining, the loop presents the fast window before the
enemy phase; (b) after passing, Dark Memory (01013 in hand) fires and the
enemy phase begins with no second window; (c) with turn_forcibly_ended set,
no window and Forceds fire immediately; (d) with no legal fast options the
window auto-skips silently (no decision).

## Fix 3 — ledger 116 improvement: purchase ledger in campaign.json

`arkham/upgrade.py` (or wherever `upgrade buy` resolves): append each
successful transaction to `campaign["purchases"]` as
`{"window": <scenario_index at time of purchase>, "code": ..., "replaced":
code|null, "removed": code|null, "price": <xp charged>}`. Also record free
deckbuild swaps? NO — deckbuild is pre-campaign, skip. Persist via the normal
save; `campaign record`/summary must not strip it.

Tests: two buys (one --replace, one --remove) → purchases list has both rows
with correct prices; surviving after `upgrade done` and `campaign record`.

## Verification gate

Fable reviews the diff; suite green; then a 20-step smoke play of a Gathering
run via `./ahlcg` to confirm no decision-loop deadlocks from the new window.
