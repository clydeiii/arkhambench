# Phase C2 fixes batch 1 — campaign review findings

Claude's review of phase C2. Fix all; add a regression test per item; update
specs/phase_c2_report.md with a "Fixes batch 1" section. If your phase-C2 test battery
already fixed one of these, note that instead.

## 1. CRITICAL: carried trauma double-counts

`Game.new(trauma=...)` currently does BOTH `state.trauma = carried` and
`investigator.damage/horror += carried`. `state.trauma` is the scenario's OWN trauma
ledger: `finalize_result` reports it as `result["trauma"]` and scores
`max(0, xp - total_trauma(state))`, and `campaign record` adds `result["trauma"]` to
campaign totals. Net effect: carried trauma is (a) re-added to campaign totals every
scenario (1 physical after scenario 1 becomes 2 after scenario 2 with no new trauma),
and (b) wrongly deducted from every later scenario's score.

Fix: keep the starting damage/horror application (that part is RR-correct); do NOT
seed `state.trauma` with the carryover. If display needs it, store
`state.limits["carried_trauma"]` separately. `result["trauma"]` must be the delta
earned in THIS scenario only.

Test: campaign trauma {physical:1, mental:2} → next scenario starts with 1 damage /
2 horror, `state.trauma == {}`-equivalent, a resign ends with result trauma 0/0 and
score unaffected; record() leaves campaign trauma at 1/2.

## 2. CRITICAL: killed/insane detection

`investigator_killed_or_insane` treats any full-damage/horror defeat as
killed/insane, and any R3 as killed. Per the campaign guide (p.4 "Trauma, Death, and
Insanity"): a defeated investigator ADVANCES to the next scenario with the party
unless the resolution explicitly says killed/insane; permanent death occurs only when
(a) the scenario text says so, or (b) accumulated physical trauma ≥ printed health
(killed) / mental trauma ≥ printed sanity (insane).

Fix:
- Each scenario's finalize_result emits explicit booleans in the result:
  `investigator_killed`, `investigator_insane`. The Gathering: killed=True ONLY for
  R3 (trapped in the burning house = agenda-out at act ≤ 2 per existing logic).
  Midnight Masks: both always False. (Devourer Below in C3 will set killed for
  no-resolution and Umôrdhoth's Hunger.)
- campaign.record uses those flags, then additionally checks accumulated trauma vs
  printed health/sanity AFTER adding this scenario's delta (killed/insane by trauma).
- Remove the damage/horror-based and summary-string heuristics entirely.

Tests: damage-defeat in MM with low trauma → NOT killed, phase=upgrade; Gathering R3
→ killed, phase=replace; accumulated physical trauma reaching health (e.g. two
scenarios of trauma vs agnes' 6 health) → killed.

## 3. Lita flags

`the_gathering.campaign_log` emits `lita: "seeking_others"` whenever Lita is not
earned, and campaign.apply maps that to `lita_was_forced_to_find_others=True`. But
"Lita was forced to find others" is ONLY the R3 note. R2 (refused/kicked out): Lita
not earned, flag stays False. Also R3: per the guide, if the lead investigator was
killed, the REPLACEMENT investigator earns the Lita card — so R3 should still set
`lita_earned=True` (the replacement may include her).

Fix campaign_log to emit `lita: "earned" | "not_earned" | "forced_to_find_others"`
(the last only on R3) and map accordingly. Test R2 vs R3.

## 4. replace_investigator guards

Reject a replacement who is in `killed_investigators` (killed investigators cannot
return) and reject replacing with the same still-current investigator. Test both.

## 5. record guards + xp_spent_total

- `record_current_run`: if the recorded result identifies its scenario (campaign
  block or result field) and it differs from `campaign["next"]`, raise an error
  naming both — protects against `.current_run` pointing at an unrelated run.
- Do not zero `xp_spent_total` on death; it is a campaign-lifetime statistic. (Zeroing
  `xp_unspent` is correct — the replacement starts at 0.)

## 6. upgrade options list ALL legal purchases

`purchase_options` filters out unaffordable cards, so an agent can't see what to save
for. Include them with an `affordable: false` flag (CLI marks them, e.g. "(need 4 XP,
have 2)"); `buy` keeps rejecting insufficient XP. Golden-test the roland/6 XP listing
accordingly.

Constraints: keep the suite green; no git commits.
