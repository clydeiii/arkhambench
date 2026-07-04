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
