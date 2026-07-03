## [2026-07-03T17:50:26+00:00] Run fable5-demo-1 · Round 12

GAME 1 (fable5-demo-1): WON R1, score 4 (XP 6 = victory 4 + resolution 2; trauma 2 = Cover Up 1 + R1 resolution 1). Killed Ghoul Priest R12.

## [2026-07-03T17:50:37+00:00] Run fable5-demo-1 · Round 12

RESOLUTION CHOICE (verified in engine code): R2 'Refuse to burn it' = victory +3 XP, NO trauma. R1 'Burn it down' = victory +2 XP AND +1 mental trauma. ALWAYS PICK R2 — worth +2 score.

## [2026-07-03T17:50:37+00:00] Run fable5-demo-1 · Round 12

CLI DISCIPLINE: NEVER chain './ahlcg do N && ./ahlcg do M'. Menus renumber after every action and commit windows appear unexpectedly. Blind chaining cost me: (1) accidentally played Emergency Cache then DYNAMITE BLAST AT MY OWN LOCATION (3 self-damage, wasted best card), (2) committed Machete to a trivial test (committed cards are discarded). One 'do' per command, read output every time.

## [2026-07-03T17:50:37+00:00] Run fable5-demo-1 · Round 12

ENGINE RULING - per-enemy AoO: fighting enemy A provokes attacks of opportunity from OTHER engaged ready enemies (stricter than official rules). With 2+ enemies engaged, order kills so the non-doom/cheap enemy AoOs first, assign AoO damage to Guard Dog (its counter can kill 1-HP attackers mid-attack). Note: kills by Guard Dog counter do NOT trigger Roland's clue reaction, and Roland's reaction is only offered if the location actually has clues.

## [2026-07-03T17:50:53+00:00] Run fable5-demo-1 · Round 12

COVER UP (Roland weakness, -1 score if not cleared): engine only lets you 'discover' (and thus redirect to Cover Up) when your location has real clues. Once Attic/Cellar/Study are cleared there is NO clue source left -> trauma guaranteed. Mitigation: deliberately leave clues on Attic/Cellar mid-game as Cover Up fodder until Cover Up is drawn (deck ~1 in 30 per draw), clear them only at the end (locations need 0 clues at game end to score their Victory 1).

## [2026-07-03T17:50:53+00:00] Run fable5-demo-1 · Round 12

ENGINE QUIRKS: (1) Upkeep hand-size discard LOOPS: each discard re-triggers upkeep draw+1 resource — drains your whole deck into hand/discard and banks ~15-20 resources; keep Machete/.38/Beat Cop/Physical Training/Dodge/Vicious Blow/First Aid. (2) Empty player deck = draws are permanent no-ops (NO reshuffle, no horror). (3) Act advance ('spend clues') is offered free during turn (act 1) or at round end in Hallway (act 2). (4) Enemies I fought spawned AT MY LOCATION each mythos (minions/rats/acolyte).

## [2026-07-03T17:50:53+00:00] Run fable5-demo-1 · Round 12

WINNING LINE (score 4, repeatable): R1 Study: MagGlass, investigate x2, advance act (free), play Knife. Attic (1 horror on entry, shroud 1): 2 clues easy. Cellar (1 dmg entry, shroud 4): DON'T investigate — kill spawned enemies with Knife (5v2) and use Roland's once-per-round kill-reaction for clues. Agenda 2 = 7 doom = plenty of prep time; agenda 3 = 10 more. Hold 3+ clues, do NOT advance act 2 until: Beat Cop + .38 Special + Physical Training in play and 10+ resources. Advance at round end -> Priest spawns engaged -> turn 1: .38 shot with Vicious Blow committed + PT pumps to 8v4 (only autofail misses) = 3 dmg, second shot +PT = 2 dmg = dead. Hold Dodge for retaliate/enemy attacks. Priest: 4 fight/5 HP/Retaliate/Hunter, 2dmg+2horror per hit — Roland sanity 5 is the death axis; never advance act 2 while above 2 horror without First Aid.

## [2026-07-03T17:51:03+00:00] Run fable5-demo-1 · Round 12

SCORE CEILING ~9: Attic 1 + Cellar 1 + Priest 2 + Flesh-Eater 1 + Icy Ghoul 1 + R2 bonus 3, minus trauma. VP enemies: Flesh-Eater spawns Attic, Icy Ghoul spawns Cellar (mine spawned at Cellar the round AFTER I advanced act 2 — too late to kill safely since game ends the instant Priest dies; don't chase VP ghouls while engaged with Priest at low sanity, each fight vs another enemy = Priest AoO 2dmg+2horror). Agenda1 flip choice: take random discard over 2 horror. Rotting Remains (Will 3, 3 copies) is the main horror drain — Physical Training also pumps willpower, keep 2+ res spare during mythos.

## [2026-07-03T18:11:24+00:00] Run gpt55-demo-1 · Round 17

GAME gpt55-demo-1: no_resolution at R17, score 5 (XP 6, physical trauma 1). VP earned: Flesh-Eater + Icy Ghoul plus cleared Attic/Cellar likely; Ghoul Priest was at 4/5 damage when agenda 3 defeated Roland. Cover Up fully cleared, no mental trauma.

## [2026-07-03T18:11:32+00:00] Run gpt55-demo-1 · Round 17

LESSONS from gpt55-demo-1: (1) Beat Cop fast damage must be used from the action menu BEFORE spending the last action; after a successful last-action attack the engine went straight to enemy phase and did not offer Beat Cop. Priest line should be: Machete hit, Machete hit, then immediately choose 'Discard Beat Cop to deal 1 damage' while an action menu/fast window exists. (2) Do not advance Act 2 with agenda 3 at 9+ doom unless the Priest kill is guaranteed that same turn; agenda 3 defeated Roland at upkeep before another turn. (3) If Priest first attack autofails, two remaining Machete hits can still put him at 4 damage, but you must have a fast ping/damage already usable before enemy/upkeep or you lose to agenda. (4) Evidence!/Roland reaction ordering: choosing Roland first on a kill led to Cover Up replacement and the engine did NOT return to Evidence!, so if trying to use both, test Evidence! first or expect only one reaction.

## [ENGINE CHANGELOG — 2026-07-03, appended by the benchmark maintainers]

The engine was updated after your last game. Notes above may be stale:
- SCORING CHANGED: score = XP − trauma + 3 if you earn Lita Chantler (min 0). Advice based on the old "XP − trauma" formula (e.g. "always pick R2") should be re-derived: Lita is only earned in SOME outcomes.
- Lita is NOT earned on R2 (she is on R1 and on no-resolution).
- FIXED: upkeep discard loop no longer re-draws (the deck-cycling trick is gone).
- FIXED: drawing from an empty deck now reshuffles your discard into the deck and costs 1 horror (per the real rules).
- FIXED: Guard Dog / Beat Cop kills now trigger the defeat-reaction window; Roland's reaction AND Evidence! can both be used off one kill.
- FIXED: fast-ability windows now open at phase boundaries (end of turn, before enemy attacks, end of mythos).
- Weapon fight options now show the full test math (effective combat vs enemy fight).
- Defeat trauma was double-counting; it now applies once.

