# Fix batch 1 — findings from Claude's manual verification playthrough (runs/verify1, seed 42)

Rules bugs (fix + add a regression test each):

1. **Double encounter draw after agenda advance.** In
   `the_gathering.finish_mythos_after_agenda_choice`, `encounter.draw_encounter` is called
   unconditionally. When the agenda advanced because of a card drawn during the mythos
   ENCOUNTER step (e.g. Ancient Evils, seen at seed 42 round 3: Ancient Evils → agenda
   flip → choice → a SECOND card, Frozen in Fear, was drawn), the mythos encounter draw
   has already happened and must NOT repeat. Track whether the encounter step already ran
   this round (check the `mythos_encounter_drawn:{round}` flag BEFORE setting it) and only
   draw if it hadn't.

2. **Agenda 2 mill uses a fixed RNG.** `advance_agenda_2` builds
   `ArkhamRng(round*1000+7)` — every game mills the same order regardless of seed,
   violating DESIGN §1.3 (single seeded RNG). Use the game's RNG instance (thread it in
   like other flows). Same for any other place a fresh ArkhamRng is constructed mid-game
   (grep for `ArkhamRng(` outside game creation).

3. **Attacks of opportunity: per-enemy exemption + engage provokes.** Current
   `SAFE_FROM_AOO` is a global action set including `engage`. Correct rule: when Roland
   takes an action while engaged with ready enemies, EACH such enemy makes an AoO except
   the specific enemy being fought/evaded/parleyed by that action. So: Fight enemy A while
   also engaged with B → B makes an AoO, A does not. Engage C → all current ready engaged
   enemies AoO. Resign/advance-act/pass never provoke (pass isn't an action). Fast plays
   never provoke. Update `attacks_of_opportunity` to take the targeted enemy id (if any)
   and skip only it; remove `engage` from the safe set; keep `parley_lita` safe for Lita
   only (there's no other enemy target case in this pool — but AoOs from OTHER engaged
   enemies during parley must still fire).

4. **Action affordability with additional costs.** With Frozen in Fear in play and 1
   action remaining, Move was offered and executed for effectively free
   (`max(0, remaining - cost)` clamp; seen at seed 42 round 8). Per RR you cannot take an
   action whose full cost you cannot pay. Compute the effective cost (incl. Frozen tax)
   during legal-action generation and exclude unaffordable options; also guard in
   `spend_action` (raise EngineError if cost > remaining).

5. **Doom must not carry over when the agenda advances.** `effects.py` fixture path does
   `state.agenda.doom -= threshold`. When an agenda flips, all doom on the agenda is
   discarded — surplus does not carry (e.g. two doom placed in one round on a 3-threshold
   with 2 already there → new agenda starts at 0). Verify The Gathering path too, and
   verify the threshold check uses TOTAL doom in play (agenda + Silver Twilight Acolyte
   forced doom + any card doom) while the flip only clears the agenda's own doom
   (doom on other cards remains and still counts toward the new threshold per RR).

Cosmetic/quality (fix, light tests where sensible):

6. **Event round/phase stamping.** Log events during a `do` that crosses phase/round
   boundaries get stamped with the round/phase AFTER advancement (seed 42: the round-1
   investigate's chaos token logged as round 2; enemy-phase events logged with phase
   "Investigation"). Stamp events with the round/phase current at the moment the event
   occurs (snapshot at emit time, before any advancement in the same call).

7. **Autofail margin label.** "Frozen in Fear: failure by -1" — on autofail with value ≥
   difficulty, report "failure (autofail)" and margin 0 for per-point effects (code
   already guards margin>0; make the number non-negative and the label clear).

8. **`state` rendering: card names.** Play area / threat area / attachments show raw
   instance ids (`pc0014`). Render as "Magnifying Glass (pc0014)" everywhere a card
   instance is listed. Also show enemy damage and exhausted/engaged status in the
   Locations section (e.g. "Ghoul Priest [4/5 dmg 1, exhausted, engaged]"), and show
   ally damage/horror next to play-area allies.

Run `python3 -m unittest discover -s tests` until green, run
`python3 -m arkham.fuzz --games 100` clean, update specs/fixes_batch_1_report.md with
what changed. Do not git commit (sandbox).
