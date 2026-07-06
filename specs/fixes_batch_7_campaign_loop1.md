# Fixes batch 7 — campaign playtest loop round 1 (ledger entries 25–31)

Findings from Haiku campaigns 9001/9002, audited by GPT-5.5, adjudicated by Claude
(specs/bug_adjudications.md entries 25–31 have full evidence). One regression test per
item. Keep the suite green (268 now); re-run the full fuzz matrix (all 6 scenarios).
Update the ledger entries with "FIXED" notes and append to specs/phase_c3_report.md.

## 1. Campaign log clobber (entry 25)

`arkham/campaign.py apply_campaign_log` applies Midnight-Masks-shaped fields from ANY
result's campaign block: recording the Devourer Below resets `cultists_got_away` to []
and `past_midnight` to False in the final log. Only apply each field when the block's
`scenario` is the scenario family that produces it (got_away/past_midnight/
ghoul_priest_defeated_here → midnight masks family; arkham_succumbed etc. → devourer
family). Test: record MM block then DB block → got_away/past_midnight survive.

## 2. Deduction phantom logging (entry 26)

Route Deduction's (and any similar "discover additional clue" effect's) extra
discovery through the normal discover_clue path and log only what was actually
discovered (0 when the location is empty or discovery is blocked). State math is
already correct — this is the log/event layer. Test: Deduction success at a 0-clue
location emits no "additional clue" event; while engaged with the Masked Hunter,
emits the blocked event only.

## 3. Magnifying Glass stacking (entry 27)

`cards/player.py` effective skill for investigations: +1 PER COPY of 01030/01040 in
play (two copies = +2; one of each = +2). Audit other always-on statics gated by
controls_code for the same bug (e.g. Police Badge willpower, Holy Rosary, Dig Deep-
style are exhaust/spend abilities — only fix true statics). Test: two Magnifying
Glasses → Intellect base +2 on investigate options and resolution.

## 4. Chaos-symbol timing split (entry 28)

Resolve UNCONDITIONAL scenario symbol effects at token reveal (RR ST.4), before
success determination and before test results: Gathering tablet (Ghoul → 1 damage),
DB tablet (Monster → damage/horror), MM cultist doom placement, DB cultist doom
placement, MM hard-tablet/easy-tablet clue drops stay fail-conditional (they say "If
you fail"). Fail-conditional effects ("If you fail, ...") remain at results as today.
Consequences to honor: damage taken at ST.4 can defeat the investigator mid-test
(test then doesn't complete — match existing mid-test defeat handling); doom placed
at ST.4 can advance the agenda only after the test completes (defer the
check_agenda_advance call if a test is active, same pattern as existing deferred
advances). Tests: DB tablet during a fight applies damage before the fight's damage;
Gathering tablet unchanged totals but new ordering; MM cultist doom lands even when
the test then fails or succeeds.

## 5. Umôrdhoth's Wrath full margin (entry 30)

Fail by N must present N sequential choices. The damage path's resume
({kind: "scenario", choice: "wrath_continue"}) never re-enters continue_wrath —
either wire that resume kind through the damage-assignment completion path or
restructure so wrath_damage decrements and, after the assignment resolves, the next
choice is presented (the discard path already loops). Test: fail by 3, choose damage
each time → 3 damage + 3 horror total across three prompts; mixed discard/damage
paths also fully resolve.

## 6. Token aftermath must not vanish behind pending decisions (entry 31)

`apply_scenario_token_aftermath` early-returns when `state.decision_queue` is
non-empty, silently dropping effects (DB tablet skipped while Rotting Remains' horror
assignment was pending). With fix 4, unconditional effects move to reveal time; for
whatever remains at results time (fail-conditional effects), queue the aftermath to
run after the pending decision resolves instead of dropping it. Test: Rotting
Remains reveals tablet with a Monster present → both the treachery horror AND the
tablet damage apply.

## 7. On Wings of Darkness no-op move (entry 29)

When the investigator is already at the Central destination, skip the move and its
log line (disengage still happens). Test: resolve at Rivertown → no
investigator_moved event; resolve elsewhere → moved.

## 8. Reaction during AoO drops the provoking action (entry 32)

A move action provoking an AoO whose damage/horror triggers a reaction decision
(Agnes's "after 1+ horror" ability) loses its continuation: the action is spent but
the move never resolves. The resume-after-AoO chain must survive interleaved
reaction decisions (it already survives the attacker dying — extend the same resume
mechanism). Test: Agnes engaged with an Acolyte takes a move action, AoO deals
horror, Agnes uses the reaction → the move then completes; also test declining the
reaction.

## 9. CRITICAL: cross-scenario agenda dispatch (entry 33)

the_midnight_masks.place_doom_on_enemy (and check_act_objective /
add_enemy_to_victory tails) call MM's module-local check_agenda_advance even when
the running scenario is the Devourer Below (which imports these helpers). Observed:
a DB game ended with MM's "R2: the clock struck midnight" and an MM-shaped campaign
block (runs/coverage-skids-devourer_below). Make every shared helper dispatch
through the scenario-aware path (effects.check_agenda_advance), never module-local;
sweep ALL cross-module imports of MM helpers used by the_devourer_below for the same
leak (finalize_result, check_act_objective, victory handling). Tests: (a) DB game
with Wizard of the Order accruing doom crosses MM's stage-1 threshold → only DB
agenda logic fires, no hunter spawn, no MM resolution; (b) canary: for each
scenario, force each agenda threshold and assert result summaries/agenda names
belong to that scenario's family.
