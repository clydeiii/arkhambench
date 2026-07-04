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
