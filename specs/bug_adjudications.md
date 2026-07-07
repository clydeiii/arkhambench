# Engine bug-report adjudications

Running ledger of agent-filed `./ahlcg bug` reports and their verdicts. Sources of
authority: card JSON (data/cards), Rules Reference, campaign guide
(data/rules/night_of_the_zealot_campaign_guide.pdf).

## fable5-bughunt game-01 (Roland, Return, seed 1001) — 2026-07-04

1. **"Agenda 2 advanced to agenda 3 without spawning the set-aside Ghoul Priest."**
   **NOT A BUG.** The Ghoul Priest spawns from Act 2b "The Barrier" ("Spawn the
   set-aside Ghoul Priest in the Hallway"), not from any agenda. Agenda 2b "Rise of
   the Ghouls" only digs a Ghoul enemy out of the encounter deck/discard. The agent's
   premise (priest via agenda 2b) was mistaken; a game that never advances Act 2
   never sees the priest.

2. **"no_resolution xp 4 but victory display only 2 — expected no resolution bonus."**
   **NOT A BUG.** Campaign guide, The Gathering, "If no resolution was reached":
   each investigator earns Victory X *and* "2 bonus experience as he or she gains
   insight into the hidden world of the Mythos" (and the lead earns Lita). VP 2 +
   2 insight = 4 XP is correct.

Quality note: both reports were specific, checkable, and cited log evidence — the
reporting channel works; the claims just didn't survive the source texts.

## fable5-bughunt game-02 (Daisy, Return, seed 1002) — 2026-07-04

3. **Self-retraction of report 1**: the agent verified in game 2 that Act 2b spawns
   the Ghoul Priest and asked to close its own agenda-spawn claim. Matches
   adjudication (one nuance: the spawn is on Act 2b in core The Gathering as well —
   it never lived on the agenda).

## fable5-bughunt game-03 (Skids, Return, seed 1003) — 2026-07-04

4. **"Elusive offers a move to my current location / with no valid destination."**
   **CONFIRMED BUG — first verified agent find.** `elusive_destinations` did not
   exclude the investigator's own location (RR "Move": an entity cannot move to its
   current placement), and the play was offered even when it could not change the
   game state (no destination, no engaged enemies). Fixed same day: current location
   excluded, option/exec gated on a legal destination or an engaged enemy;
   regression test added (ElusiveDestinationTests). Credit: Fable 5, game 3, R1.

5. **"After Bathroom's 'end your turn' forced effect, the fast window still offered
   Skids's action-buy and Elusive."** **CONFIRMED BUG — second verified find.** The
   `inv_end` fast window (presented once actions are spent or drained) was flagged
   `during_turn=True`; per the RR turn structure it sits AFTER the turn ends, where
   "during your turn" plays and Skids's ability are illegal. Flipped to
   `during_turn=False` — the window now offers only any-window triggered abilities.
   Credit: Fable 5, game 3, R8.

   ~~Noted while adjudicating: unrestricted fast events (e.g. Cunning Distraction)
   cannot be played in non-turn windows.~~ **RETRACTED after checking card texts:**
   Cunning Distraction is NOT Fast (plain Evade event), and every fast player card
   in the five decks is turn-restricted by its own text (Elusive/Mind over Matter/
   Working a Hunch "only during your turn", On the Lam "after your turn begins") or
   by the RR asset-play rule (Magnifying Glass, Switchblade). Triggered fast
   abilities (Beat Cop, Forbidden Knowledge, Arcane Initiate, Stray Cat, Hospital
   Debts) are already offered in every window including enemy-phase pre-attack.
   The engine's window handling is RAW-correct for the full card pool in scope.

## fable5-bughunt game-04 (Agnes, Return, seed 1004) — 2026-07-04

6. **"Act objective never offered in the player window after my last action."**
   **CONFIRMED BUG — third verified find, and it exposed an overcorrection in fix
   #5.** Two layers: (a) the RR timing chart keeps a player window open after the
   LAST action, still during the turn — fix #5 had made the whole inv_end window
   post-turn, which was only correct for forced "end your turn" effects; now a
   `turn_forcibly_ended` flag (set by the Return Bathroom) decides, restoring
   Skids's legal post-3rd-action buy. (b) The act Objective is a free triggered
   ability legal in any during-turn player window, but was only ever offered in
   the action menu — now offered in during-turn fast windows too
   (act_advance_available shared helper). Regression tests:
   PostActionWindowTests. Credit: Fable 5, game 4, R8.

7. **"Agenda 3's end-of-round doom tick was skipped when the act-2 objective
   decision was presented."** **CONFIRMED BUG — fourth verified find.** `end_round`
   returned early after queueing the objective decision, and the post-choice path
   never ran the tick, so any round where the objective was offered silently lost
   its ghoul doom. Per RR simultaneous-timing priority, Forced abilities resolve
   before optional ones: the tick now runs first, then the objective decision.
   (Consequence: a Priest spawned by advancing at that window does not tick until
   the next round's end — answering the reporter's timing question.) Regression
   test: EndRoundOrderingTests. Credit: Fable 5, game 4, R15.

8. **"Move action canceled after AoO resolved — paid the action and the attack,
   never moved."** **CONFIRMED BUG — fifth verified find, the worst of the run.**
   When a queued AoO attacker died mid-sequence (Agnes's reaction killed the Swarm
   of Rats between the Priest's attack and the rat's), `attack()` early-returned on
   the dead enemy and dropped the interrupted action's continuation. AoOs never
   cancel the provoking action (RR); the dead/exhausted branch now runs the resume
   like the suppressed-attack branch does. In the reporter's game this cost a
   resign line and likely the scenario. Regression test:
   DeadAooAttackerResumeTests. Credit: Fable 5, game 4, R15.

## fable5-bughunt game-05 (Wendy, Return, seed 1005) — 2026-07-04

9. **"'Advance act' appears twice in the same action menu."** **CONFIRMED BUG —
   sixth verified find; regression from fix #6 minutes earlier** (the objective was
   added by both legal_actions and add_fast_options, which the action menu also
   calls). Deduped via include_objective flag: only standalone fast windows add it.
   Regression test: ObjectiveDedupeTests. Credit: Fable 5, game 5, R6.

## gpt55-bughunt game-01 (Roland, Return, seed 1001) — 2026-07-04

10. **"Machete offered as Combat(5) but the test started as combat 4."**
    **PARTIAL — enforcement correct, log misleading.** The +1 was applied and the
    test resolved at 5 (visible in the same game's resolution line: "combat 5 + ...
    = 5 vs 2"), but `asset_fight` added the weapon boost AFTER skill_test.start had
    already logged the pre-boost base — every weapon's started-test message
    understated the value. Boost now folds into start() via base_boost so the log
    is truthful. Credit: GPT-5.5, game 1, R2 (first find of its run).

## gpt55-bughunt game-03 (Skids, Return, seed 1003) — 2026-07-04

11. **"Two Frozen in Fear copies should make the first move/fight/evade cost 3
    actions, engine charged 2."** **CONFIRMED BUG — GPT-5.5's first rules find.**
    Each copy is an independent Forced effect binding the same first qualifying
    action; effects stack absent a limit. `effective_action_cost` used a boolean
    has_threat check — now sums copies in the threat area. Regression test:
    FrozenInFearStackTests. Credit: GPT-5.5, game 3, R11.

## gpt55-bughunt game-05 (Wendy, Return, seed 1005) — 2026-07-04

12. **"Lucky! is offered as a normal play action (incl. via Wendy's Amulet) outside
    its 'when you would fail' window."** **CONFIRMED BUG — and it generalized:**
    Ward of Protection had the same hole (offerable as a generic play outside its
    revelation-cancel window). Both were missing from the generic-play exclusion
    list since their respective phases (V1). Replaced the ad-hoc code!=... chain
    with a named SPECIAL_WINDOW_PLAYS set including 01065 and 01080. Regression
    test: ReactionOnlyPlayTests. Credit: GPT-5.5, game 5, R6.

## Transcript-audit pass #1 (Fable 5 auditing 3 Haiku games, fresh seeds) — 2026-07-04

First run of the cheap-play/expensive-audit pipeline (scripts/audit_game.py).
Seven findings; all verified against code/state; fixes = specs/fixes_batch_5_audit.md.

13. **Dissonant Voices discarded to the PLAYER discard pile** (game-01) —
    CONFIRMED; discard_from_threat conflates ownership; encounter cards must return
    to the encounter discard. Verified in state.json (ec0019).
14. **Necronomicon fetched to hand never resolved its Revelation** (game-02) —
    CONFIRMED EXPLOIT: search-to-hand bypasses the weakness-enters-hand rule; the
    signature weakness was later randomly discarded, never entering play.
15. **Research Librarian auto-fetches with no decision** (game-02) — CONFIRMED:
    optional reaction force-fired, engine picked the target (the weakness!) over a
    legal Medical Texts.
16. **Sequential mulligan reveals replacements between choices** (game-02) —
    CONFIRMED deviation: RR requires a single simultaneous declaration.
17. **Take Resource granted 2 resources after an AoO** (game-03) — CONFIRMED
    CRITICAL: action effects double-execute whenever an AoO resolves without an
    interposing decision (resume chain + original stack both run the effect). Class
    bug affecting every AoO-provoking action with no soak in play, engine-wide,
    since phase B.
18. **Frozen in Fear end-of-turn test fired before the post-final-action window**
    (game-03) — CONFIRMED: end-of-turn Forced effects must wait for the during-turn
    window to close (same class as #6/#7).
19. (game-01 pass 2 + game-03 pass 2 found nothing else; game-01 was otherwise
    fully reconciled — 11 skill tests, all math verified by the auditor.)

20. **Daisy's Tome-only bonus action paid half of the Study's 2-action non-Tome
    ability** (game-02, audit finding 2) — CONFIRMED EXPLOIT. Multi-action costs
    now require enough UNRESTRICTED actions (the unused Tome action is reserved).
    Note: this finding was accidentally omitted from the batch-5 spec; codex's
    report flagged the omission — reviewer credit to the implementer.

Pipeline economics: 3 Haiku games + 3 Fable audits found 7 new confirmed defects —
including the double-execution class two live hunts missed — at roughly a tenth of
a live hunt's token cost. All fixed in fixes batch 5.

## Transcript-audit pass #2 (GPT-5.5 auditing 3 fresh Haiku games) — 2026-07-05

Diversity pass (Clyde's design: Haiku plays, GPT-5.5 audits, Claude verifies).
Four findings; three confirmed, one ruled correct-as-implemented. Fixes = batch 6.

21. **Dark Memory's resource cost unpaid during the AoO it provoked** (game-01) —
    CONFIRMED ordering defect: RR pays ALL costs at initiation, before AoOs; the
    engine paid resource costs in the effect phase. Materially invisible in this
    game but wrong ordering engine-wide for the generic play action.
22. **Sequential damage/horror application hid legal Leo soak** (game-02) —
    CONFIRMED: RR assigns all tokens then applies simultaneously; the engine
    applied damage (removing Leo) before horror assignment. Wendy could legally
    have soaked both on Leo.
23. **Leo's death clawed back an already-consumed bonus action** (game-02) —
    CONFIRMED per the additional-actions FAQ: the first qualifying action uses the
    bonus; discarding Leo later in the turn must not reduce remaining actions.
24. **Bathroom Forced fired after test resolution instead of at token reveal**
    (game-03) — **NOT A BUG (adjudicated)**: firing on the FINAL token is the
    correct cancellation semantics for Wendy's redraw (a canceled skull is not a
    revealed symbol for Forced purposes), and no reachable state reads the action
    count between reveal and resolution. Documented deviation, retained.

Auditor-diversity observation: GPT-5.5's finds (cost timing, simultaneity,
action-economy edge cases) are a different genre from Fable's (window/sequence
drops) — running BOTH auditors over the same corpus would likely stack coverage.

## Campaign playtest loop — round 1 (2026-07-05, Haiku campaigns 9001/9002)

25. **DB record pass clobbers MM campaign-log fields** (loop1-agnes) — CONFIRMED
    (found by Claude reviewing campaign.json before audits): `apply_campaign_log`
    applies the Midnight-Masks-shaped fields (`cultists_got_away`, `past_midnight`)
    from ANY scenario's campaign block, so recording the Devourer Below (whose block
    lacks them) resets the list/flag in the final log. Gameplay unaffected (DB setup
    read the log before being recorded); post-campaign log fidelity only.
    **FIXED (batch 7):** `apply_campaign_log` now gates Midnight Masks and Devourer
    campaign fields by the producing scenario family; regression covers MM then DB
    recording preserving got-away/past-midnight.

GPT-5.5 audit findings (campaign loop1-roland), Fable adjudications:

26. **Deduction logs a phantom "additional clue"** (runs 1+2) — CONFIRMED, display:
    state totals stay correct, but the Deduction handler logs unconditionally even
    when the location has 0 clues or the Masked Hunter blocks discovery. Log actual
    amounts only. **FIXED (batch 7):** Deduction logs only returned discoveries
    beyond the base clue; blocked/empty discoveries emit no phantom extra clue log.
27. **Magnifying Glass copies don't stack** (run 1) — CONFIRMED, anti-player:
    cards/player.py:326 uses boolean controls_code for 01030/01040, so a second
    copy adds nothing. Per RR, each copy in play applies its +1. **FIXED (batch 7):**
    investigation statics now count every Magnifying Glass copy in play.
28. **Unconditional chaos-symbol effects resolve after the test** (run 1 F3) —
    CONFIRMED, timing: RR ST.4 resolves symbol effects at reveal, before success is
    determined. Fail-conditional clauses ("If you fail...") stay at results. Engine
    applies everything post-test today. **FIXED (batch 7):** unconditional scenario
    token effects moved to final-token reveal with deferred skill-test/agenda
    continuations; fail-conditional effects remain at result time.
29. **On Wings of Darkness "moves" the investigator to their current location**
    (run 2 F1) — CONFIRMED, display: skip the move (and its log line) when already
    at the Central destination. **FIXED (batch 7):** Rivertown no-op move is skipped
    while non-Nightgaunt disengagement still resolves.
30. **Umôrdhoth's Wrath resolves only one failure point via the damage path**
    (run 3 F1) — CONFIRMED, pro-player: the damage-assignment resume
    ({kind: scenario, choice: wrath_continue}) never re-enters the choice loop, so
    fail-by-3 cost one choice instead of three. **FIXED (batch 7):** damage
    assignment can resume scenario choices; Wrath loops through the full margin.
31. **Token aftermath silently skipped while a decision is pending** (run 3 F2) —
    CONFIRMED, pro-player: skill_test.apply_scenario_token_aftermath returns early
    if state.decision_queue is non-empty (e.g. the treachery's own damage
    assignment), dropping the DB tablet damage entirely. Aftermath must queue, not
    vanish. **FIXED (batch 7):** result-time token aftermath queues behind pending
    damage/decisions and drains once the queue clears.
32. **Agnes reaction during an AoO drops the provoking action's continuation**
    (loop1-agnes run 3) — CONFIRMED, anti-player: move action provoked an Acolyte
    AoO; Agnes's "after horror" reaction resolved; the move never continued (action
    spent, investigator still at Main Path, attacker alive). Variant of the fixed
    dropped-continuation bug, triggered by the reaction decision interleaving.
    **FIXED (batch 7):** AoO attacks that deal damage/horror now always carry a
    resume; interposed horror reactions preserve the provoking action.
33. **DB games run the Midnight Masks agenda machine in parallel** (coverage-skids-
    devourer_below, seed 9506) — CONFIRMED, CRITICAL: the Devourer reuses MM helpers
    (place_doom_on_enemy, mysterious_chanting, attach_mask, disciple spawns) whose
    tails call MM's module-local check_agenda_advance regardless of state.scenario.
    Any enemy-doom placement in a DB game advances a phantom MM agenda: spawns a
    set-aside Masked Hunter fallback, and at "stage 2" ends the game with MM's
    "R2: the clock struck midnight" finalize (observed: DB result with MM resolution
    and MM-shaped campaign block). Invisible to invariants-only fuzz; caught by one
    coverage playtest game. Fix: shared helpers dispatch through the scenario-aware
    effects.check_agenda_advance / finalize; add a canary test asserting a game's
    result summary/resolution belongs to its scenario. **FIXED (batch 7):** MM
    shared helpers now dispatch agenda/objective/finalize through `arkham.effects`;
    DB wizard-doom and six-scenario canary regressions cover the leak.

## Campaign playtest loop — round 2 (Haiku campaigns 9003/9004, post-batch-7)

34. **Phantom fast window after the investigator's turn ends** (loop2-daisy runs
    1+3) — CONFIRMED, exploit: RR timing chart has NO player window between 2.2.2
    (turn ends) and 2.3 (phase ends); the engine offers one, and even allowed Mind
    over Matter ("Play only during your turn") inside it. Remove the post-turn
    window; enforce during-your-turn play restrictions in all fast windows.
    **FIXED (batch 8):** removed the `inv_end` fast window from the phase loop;
    remaining fast windows still distinguish during-turn card plays from any-window
    triggered abilities. Regression covers no post-turn fast decision.
35. **Enemy-doom placements advance the agenda outside step 1.3** (loop2-daisy run
    2) — CONFIRMED: RR 1.3 is the only agenda-advance timing absent explicit card
    permission (precedent: the Gathering's Acolyte adjudication). MM/DB
    check-on-placement advanced agenda 1 the moment a Disciple spawn-doom hit the
    threshold. Doom-on-enemy placements must wait for 1.3 (or an explicit
    "this can advance" card: Masked Horrors, Offer of Power, Jeremiah, Corpse-Taker).
    **FIXED (batch 8):** enemy-doom helper no longer checks agenda advancement by
    default; explicit agenda-doom effects still opt in with `can_advance`.
    Regression covers threshold enemy doom waiting for the next agenda check.
36. **Hunting Nightgaunt token-doubling not implemented** (loop2-wendy run 2) —
    CONFIRMED: "double the negative modifier of each revealed chaos token" while
    evading it; engine applied -1 as -1.
    **FIXED (batch 8):** evade tests against Hunting Nightgaunt double each
    negative token modifier, including alternate reveal paths. Regression covers
    `-1` resolving as `-2`.
37. **Young Deep One engagement Forced deals no horror** (loop2-wendy run 3) —
    CONFIRMED, pro-player: "After Young Deep One engages you: take 1 horror" never
    fired on spawn-engage or move-engage.
    **FIXED (batch 8):** `engage_enemy` fires Young Deep One's Forced horror on
    engagement. Regression covers direct engagement.
38. **Weaknesses offered as optional discard costs** (loop2-wendy run 3) —
    CONFIRMED, exploit: Wendy's token-cancel accepted Amnesia as the discarded
    card; RR: a player may not optionally discard a weakness from hand unless a
    card explicitly permits it. Sweep ALL choose-and-discard costs (Wendy, Herman
    parley, Hunting Shadow-style choices are effects not costs — costs only).
    **FIXED (batch 8):** optional discard-cost pickers now filter weaknesses
    (Wendy, Herman, Warehouse, slot overflow). Regression covers Wendy and Herman.

Coverage-game audit findings (10 XP-deck games), Fable adjudications:

39. **Doom stays counted after its card leaves play** (coverage-agnes-DB) —
    CONFIRMED: RR Leaves Play returns all tokens to the pool; a defeated Arcane
    Initiate's doom kept counting and advanced the agenda a round early. Applies to
    all doom-carrying cards (Acolyte, Wizard, Disciple, Corpse-Taker, Initiate).
    **FIXED (batch 8):** player-card and encounter-card leave-play helpers clear
    card tokens; defeated enemies no longer leave doom in agenda math. Regression
    covers Arcane Initiate and a defeated doom enemy.
40. **Moving an engaged enemy away does not disengage it** (coverage-daisy-DB) —
    CONFIRMED: Corpse-Taker's Forced end-of-phase move left engagement intact and
    it attacked from Main Path while Daisy stood at Cliffside, two rounds running.
    **FIXED (batch 8):** effect-based enemy moves clear engagement when the enemy
    is moved away from the investigator's location. Regression covers an engaged
    enemy moved to another location.
41. **Weakness added to hand doesn't resolve as if drawn** (coverage-daisy-DB) —
    CONFIRMED, pro-player: RR Weakness requires resolving Revelation on non-draw
    hand entry; Psychosis sat in hand as a dead card instead of entering the threat
    area (its horror→direct-damage Forced consequently never fired).
    **FIXED (batch 8):** Devourer agenda-2 Madness gains to hand route through
    `add_player_card_to_hand`, preserving revelation handling; deck additions stay
    deck-only. Regression covers Psychosis entering the threat area.
42. **Paid play costs refunded when the played card leaves hand during AoO**
    (coverage-roland-DB) — CONFIRMED, pro-player: Grave-Eater's AoO random discard
    hit the being-played Machete and the batch-6 abort-refund returned the 3
    resources; RR: paid costs stay paid, the play simply fizzles.
    **FIXED (batch 8):** paid plays move the card to limbo before AoO, so random
    hand discards cannot select it; resumed/fizzled plays no longer refund paid
    resources. Regression covers both limbo selection and no-refund fizzle.
43. **Skill-test modifiers not re-evaluated after ST.4 effects** (coverage-skids-DB
    F2) — CONFIRMED, display: Lita was discarded soaking ST.4 tablet damage but her
    +1 combat still appeared in the ST.5 math (outcome unchanged in evidence; could
    flip marginal tests). Recompute active modifiers at ST.5.
    **FIXED (batch 8):** `compute_result` recalculates static base skill at ST.5
    while retaining paid boosts and ability base boosts. Regression covers Lita
    leaving play before final combat math.
44. **Leo De Luca's additional action only granted on his entry turn**
    (coverage-wendy-MM) — CONFIRMED, anti-player: R2-R6 turns began at 3 actions
    with Leo in play; a later second copy correctly showed 4.
    **FIXED (batch 8):** turn-start action calculation recognizes both Leo copies;
    existing clawback behavior remains intact. Regression covers the level-1 copy
    and no clawback after actions are already spent.
45. **Setup/display gaps** (multiple) — CONFIRMED, display: (a) setup effects are
    unlogged — got-away doom on agenda 1a looked "unexplained" to the auditor
    (skids-DB F1 itself: NOT A BUG, setup doom per campaign guide table); (b)
    Disciple's forced clue placement resolves silently at agenda>=2; (c) Museum
    logs the clue gain as if placed on the location; (d) Drawn to the Flame logs 2
    discovered where 1 existed (pre-batch-7 transcript — verify entry-26's fix
    generalizes; extend if not).
    **FIXED (batch 8):** setup logs note got-away doom and elderthing addition,
    Disciple clue placement logs in automatic and choice paths, token-pool clue
    gains name the investigator, and Drawn to the Flame logs the actual discovered
    amount. Regression covers all four display cases.

## Campaign playtest loop — round 3 (Haiku campaigns 9005/9006, post-batch-8)

5 of 8 audits CLEAN (incl. both campaign layers). Three findings, all confirmed:

46. **Activate-ability costs paid after attacks of opportunity** (loop3-skids run
    2) — CONFIRMED: RR AoO fires "after all costs... have been paid, but before the
    action's effect". Batch 6 fixed this for card-play resource costs; activate
    abilities (act cultist-draw clue spend, Museum 2-horror) still pay after the
    AoO. Evidence shows a case where paying first would have defeated Skids before
    the effect — outcome-relevant, not cosmetic.
    **FIXED (batch 9):** action-triggered activation costs now pay at initiation
    before AoOs and carry paid-cost markers through AoO resumes; regressions cover
    cultist-deck clue spend before AoO and Museum horror defeat before effect/AoO.
47. **Yithian Observer's Forced attack-discard unimplemented** (loop3-skids run 3)
    — CONFIRMED, pro-player: "When Yithian Observer attacks you: discard 1 card at
    random; if you cannot, +1 damage and +1 horror." Three attacks, no discards.
    **FIXED (batch 9):** Yithian Observer attack resolution discards randomly
    before damage/horror assignment, or adds +1/+1 for that attack if hand is empty.
48. **Spawn-engagement queued behind intervening resolutions** (loop3-skids run 3,
    loop3-agnes run 3) — CONFIRMED, display/ordering: ready enemies spawning at the
    investigator's location engage only after other queued effects (agenda advance,
    Wrath, Disciple spawn decision) resolve; RR engagement is immediate.
    **FIXED (batch 9):** Devourer agenda/act dig spawns now use the shared immediate
    spawn engagement rule; regression asserts agenda-back Main Path spawn engages
    immediately after the spawn event and before agenda advancement logging.

## Hard-difficulty playtest round (Haiku campaigns 9101/9102, hard)

49. **On Wings of Darkness resolves movement before its damage/horror** (hard1-
    roland run 2) — CONFIRMED, display/ordering: pre-"Then" text (1 horror + 1
    damage) must fully resolve before the disengage/move.
    **FIXED (batch 10):** failed On Wings now queues the damage/horror assignment
    with a scenario resume, so the non-Nightgaunt disengage and Central move run
    only after that assignment and any interposed choices fully resolve.
50. **Card-driven investigations bypass location skill substitution** (hard1-
    roland run 3) — CONFIRMED: Flashlight's Investigate at Cliffside tested
    intellect; Cliffside substitutes agility for ANY investigation (Old House/
    Tangled Thicket likewise). Route every investigate-type test through the
    scenario's investigation-skill hook.
    **FIXED (batch 10):** Flashlight, Burglary, and basic investigate all use the
    shared investigation-skill hook and labels now reflect the substituted skill.
51. **Search effects auto-select instead of offering the player's choice**
    (hard1-wendy run 1) — CONFIRMED: RR Search lets the searching player choose
    among eligibles; hard-skull Ghoul search, DB hard-skull Monster search,
    Mysterious Chanting, and Mask of Umordhoth searches all auto-pick the first
    match. Offer a decision when 2+ distinct eligible cards exist.
    **FIXED (batch 10):** encounter-deck/discard search helpers now auto-resolve
    only one distinct named candidate and otherwise present a choice; Mask search
    continuations survive spawn-location decisions.
52. **Offer of Power resolves as a placeholder (unimplemented)** (hard1-wendy run
    3) — CONFIRMED, pro-player: the mandatory Revelation (draw 2 + 2 doom-can-
    advance, or 2 horror) was skipped entirely; log literally says "no placeholder
    effect". Sweep ALL encounter cards reachable in every scenario deck for
    placeholder resolution and implement what's missing; add a suite test that no
    composable deck card resolves as placeholder.
    **FIXED (batch 10):** Offer of Power is fully implemented. The no-placeholder
    sweep covers all six scenario families plus cultist decks, agents sets, Ghoul
    Priest, and got-away agenda spawns; it also exposed and fixed The Yellow Sign
    and Dreams of R'lyeh.
53. **Duplicate engaged enemies collapse to one AoO attack** (hard1-wendy run 3) —
    CONFIRMED, pro-player: two ready engaged Grave-Eaters produced one attack in
    the AoO queue.
    **FIXED (batch 10):** AoO regression coverage asserts two engaged Grave-Eater
    instances produce two attacks before the interrupted action resumes; damage
    assignment now defers interrupted resumes behind interposed decisions.
54. **Simultaneous damage/horror defeat assigns both trauma types** (hard1-wendy
    campaign audit) — PARTIAL: the double trauma is CONFIRMED (RR: the player
    chooses physical OR mental on simultaneous defeat); the "killed unsupported"
    half is NOT A BUG (DB no-resolution explicitly kills each surviving/defeated
    investigator per the campaign guide).
    **FIXED (batch 10):** simultaneous defeat now presents a solo physical/mental
    trauma choice and records exactly one selected trauma; explicit scenario kill
    flags remain unchanged.

## Open-weights playtest lane (hy3 via opencode/OpenRouter)

55. **hy3-trial-1 report 1 (AoO on asset play)** — NOT A BUG: playing a card is an
    action and provokes attacks of opportunity per the RR (exemptions are by action
    type: fight/evade/parley/resign). hy3 had the rule inverted; useful calibration
    for adjudicating its future reports.
56. **Phantom "discovered 1 clue after defeating an enemy" log while Masked Hunter
    blocks discovery** (hy3-trial-1 report 2) — CONFIRMED, display: the on-defeat
    clue-discovery reaction logs unconditionally even when discovery is prevented
    (state stays correct). Same family as entry 26 (Deduction) — the fix missed
    this path. Sweep ALL discovery-logging paths for the actual-amount rule.
    **FIXED (batch 11):** Roland's on-defeat reaction now logs only when
    `discover_clue` returns an actual discovery amount; blocked discovery logs only
    the prevention event.
57. **glm-trial-1 reports 1/2 (AoO on asset play; Machete "discard cost")** — NOT A
    BUG ×2: plays provoke AoOs (exemptions are fight/evade/parley/resign); the
    "discard for Machete" was hand-slot management (2 Magnifying Glasses + Machete
    > 2 hand slots) — hy3 independently identified that correctly. Notably BOTH
    open-weights models believe asset plays don't provoke — add an explicit AoO
    line to docs_agent/playing_guide.md.
58. **Cross-game .current_run contamination** (glm-trial-1 report + refile note) —
    CONFIRMED, HARNESS (not engine; Claude's fault): concurrent agent lanes share
    the repo-root .current_run pointer; glm's commands mutated hy3's swarm game
    and vice versa. Fix: global --run flag on do/state/note/bug/score overriding
    the pointer; agent prompts pass it explicitly. First three swarm results
    (roland gathering/MM/DB) are contaminated and must be rerun.
59. **glm-trial-1 reports 4-6 (fight deals skill-value damage; fast events never
    offered; draw provokes AoO)** — NOT A BUG ×3: attacks deal weapon/base damage
    per the RR, not skill value; Working a Hunch verified offered in a clean game
    (the report was a contamination artifact); draw actions provoke AoOs.

## Showcase-campaign audit findings (10 Fable/GPT campaigns, pre-batch-10 engine)

60. **Forbidden Knowledge resolves effect before horror cost** — CONFIRMED, exploit:
    fast-ability path missed the batch-6/9 cost-at-initiation rule; secret/resource
    moved before the 1 horror was paid, three separate times.
    **FIXED (batch 11):** Forbidden Knowledge pays horror at fast-ability
    initiation and resumes the secret/resource effect only after the horror window.
61. **Search allowed "Draw no Spell" with an eligible Spell found** (Arcane
    Initiate vs Dark Memory) — CONFIRMED: RR Search obligates finding when an
    eligible option exists; decline options are only legal when nothing eligible
    was found. (Distinct from batch-10's search-choice fix, which added choice
    among candidates.)
    **FIXED (batch 11):** Arcane Initiate and Research Librarian no longer offer
    decline/no-hit options when an eligible card was found; existing forced search
    presenters already omitted decline.
62. **Act advances before the act-back finishes resolving** (Mysterious Gateway ×3
    campaigns) — CONFIRMED, ordering/display: the back-side willpower test must
    complete before the next act is current.
    **FIXED (batch 11):** Return Act 1 now keeps Mysterious Gateway current while
    Breaking the Wall's test resolves, then switches to The Barrier from ST.7.
63. **Dark Memory as hand-size discard** — NOT A BUG (adjudicated): RR 4.5 hand-
    size maintenance is a compelled discard, not an "optional choose to discard";
    the weakness prohibition governs optional discards and costs. Noted as an
    official ambiguity; engine behavior stands.
64. **"Look what I found!" window not offered after qualifying failed
    investigations** — CONFIRMED: fail-by-2-or-less at Cliffside produced no play
    window; suspect the skill-substitution path (agility investigations) broke the
    "while investigating" trigger detection. Verify Rabbit's Foot-style windows on
    substituted-skill investigations too.
    **FIXED (batch 11):** failed investigation tests now carry an investigation
    marker on both success and failure paths, including scenario skill substitutions
    and Flashlight-style tests.
65. **Fast assets bypass hand-slot enforcement** (Magnifying Glass over 2 hand
    slots for 5 rounds) — CONFIRMED, exploit: the fast-play path skips the slot-
    capacity discard the normal play path enforces.
    **FIXED (batch 11):** fast asset plays now pay cost up front and call the normal
    play/slot-overflow path with paid-cost context.
66. **Aloof enemies attackable while unengaged** — CONFIRMED, exploit — and the
    C1 spec itself was wrong (Claude's error): RR Aloof forbids attacking an
    unengaged aloof enemy. Require an Engage action first; fix spec-derived tests.
    **FIXED (batch 11):** fight target generation excludes unengaged Aloof enemies;
    the basic Engage action remains available and fighting becomes legal after
    engagement.
67. **Umôrdhoth's Hunger: discard-to-empty must kill** — CONFIRMED, pro-player —
    reverses Claude's earlier ruling: the card's two sentences resolve in order
    (discard, then kill-check), so an investigator whose last card is discarded IS
    killed. Update the C3-era test.
    **FIXED (batch 11):** Return Devourer Hunger discards first, then checks for an
    empty hand and kills discard-to-empty investigators.
68. **Committed-card success effects resolve after interrupted actions resume**
    (Perception draw after the Twisting Paths move completed) — CONFIRMED,
    ordering: ST.7 committed-card effects resolve inside the test, before the
    provoking action continues.
    **FIXED (batch 11):** committed skill success effects now resolve before the
    skill-test callback; callbacks defer if the ST.7 effect opens a decision.
69. **Shrivelling's symbol-horror resolves after attack results** — CONFIRMED:
    same reveal-time family as batch-7 item 4; the rider must resolve at reveal
    (evidence showed it changing Agnes-reaction legality).
    **FIXED (batch 11):** Shrivelling's symbol horror moved to the token-reveal
    step, before attack success/failure and damage.
70. **Got-away unique cultists have no parley routes in the Devourer Below**
    (Alma Hill unparleyable at Main Path) — CONFIRMED: DB's action options don't
    include the MM parley builders for spawned got-away cultists.
    **FIXED (batch 11):** Devourer action generation and hooks reuse the Midnight
    Masks parley/forced routes for got-away unique cultists.
71. **Wendy's Amulet elder-sign auto-success math display** — CONFIRMED, display:
    result line printed "5 vs 4" instead of auto-success difficulty-0 treatment.
    **FIXED (batch 11):** Wendy's Amulet elder-sign auto-success reports the test
    against difficulty 0 in the result math.

## hy3 swarm round 1 (20 games, 71 reports; GPT-5.5 adjudicated, Fable final gate)

Verdict flow: 71 reports -> GPT: 17 confirmed / 6 code-check / 48 not-a-bug ->
Fable downgraded 2 of GPT's 5 merged confirmations on primary evidence:

72. **"Weapon +1 damage not applied"** — NOT A BUG (Fable reversal of GPT): the
    cited fights happened at Corpse-Ridden Clearing, whose printed text caps each
    attack at 1 damage; the C3 implementation is correct.
73. **"Non-Hunter enemies moved in enemy phase"** — NOT A BUG (Fable reversal):
    agenda 3 "They're Getting Out!" forcibly moves each unengaged Ghoul toward the
    Parlor at end of enemy phase; Flesh-Eater/Acolyte/Corpse-Hungry are Ghouls.
74. **MM standard skull applied -1 with Peter Warren at 2 doom** — CONFIRMED
    (code-check during fix): skull X = highest doom among Cultist enemies in play;
    verify the scan and the doom count at reveal time.
    **FIXED (batch 11):** standard/easy Midnight Masks skull is pinned to the
    highest doom on any Cultist enemy in play at reveal time.
75. **On Wings of Darkness must do NOTHING on a successful test** — CONFIRMED,
    reverses Claude's C1 adjudication (third self-reversal): RR "Then" requires
    the pre-then effect to resolve in full; on success the failure clause never
    resolved, so no damage, no disengage, no move. Update batch-7 entry-29 and
    batch-11 tests accordingly.
    **FIXED (batch 11):** successful On Wings tests are a no-op; only failures
    queue damage/horror followed by the Then disengage/move.
76. **Same-named enemy attack attribution** — NEEDS-CODE-CHECK: with two
    Grave-Eaters (one engaged, one unengaged at Main Path) the enemy-phase queue
    attacked "Grave-Eater" — verify only the engaged instance can attack, and add
    instance disambiguation to enemy log lines so future audits can tell.
    **FIXED (batch 11):** enemy phase remains engaged-only plus Massive co-located
    enemies, and enemy attack/move/engage log lines include the instance id.
77. **Hunting Shadow omitted "Spend 1 clue" with a clue available** (roland MM
    replay) — NOT A BUG (Fable reversal of GPT's CONFIRMED-NEW): the Masked
    Hunter had spawned engaged with Roland that same mythos phase; its aura
    forbids spending clues, so the damage branch was correctly forced. Both the
    reporter and the adjudicator missed the aura.

Swarm round 1 CLOSED: ~76 hy3 reports across 21 games -> 2 confirmed engine
defects (MM skull doom scan; On Wings success no-op — a Claude self-reversal)
+ 1 display defect from the trial (entry 56), all FIXED in batch 11. hy3
precision ~4%, but free and tireless; the GPT adjudication layer + Fable final
gate filtered cleanly (3 GPT verdicts reversed on primary evidence).
