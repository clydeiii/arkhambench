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

## [ENGINE CHANGELOG — 2026-07-03 rules-conformance audit]

The engine was audited line-by-line against the Rules Reference. Play-relevant changes:
- AoO now matches paper rules: fight, evade, parley, and resign actions NEVER provoke attacks of opportunity (fighting enemy A no longer provokes enemy B). Engage, move, investigate, draw, resource, play, and other activated abilities provoke from EVERY engaged ready enemy.
- There is NO boost window after the chaos token is revealed. Physical Training / Hyperawareness must be used before the reveal. Plan tests with the full bag in mind.
- Autofail counts your skill value as 0: failing Grasping Hands/Rotting Remains via autofail deals the FULL test difficulty in damage/horror. Autofail is much more dangerous now.
- Enemies exhaust after their enemy-phase attack. You choose attack/AoO order when engaged with multiple enemies.
- Silver Twilight Acolyte's doom no longer advances the agenda instantly — doom advances only at the mythos check (or Ancient Evils). Agenda advance removes ALL doom in play.
- Exhausted enemies at your location engage you the moment they ready in upkeep.
- Slots are now enforced (2 hands, 1 ally — playing over a full slot discards the occupant).

## [2026-07-03T22:15:51+00:00] Run sonnet5-mini-g2 · Round 8

AoO trap: ANY action besides fight/evade/parley/resign while engaged triggers a full attack from EVERY engaged enemy (confirmed again this game — played Hyperawareness while engaged w/ Swarm+Ghoul Priest, ate both attacks: 3dmg+2hor). Before playing assets/moving/investigating, first fight or evade every engaged enemy, or accept you WILL eat all their attacks.

## [2026-07-03T22:15:51+00:00] Run sonnet5-mini-g2 · Round 8

FIGHT does not disengage an enemy — only EVADE does. A successful Fight still leaves the enemy engaged, and it makes its normal enemy-phase attack anyway. If your goal is to prevent this round's attack (e.g. sanity is critical), you must EVADE, not fight, even if fighting 'succeeds'. Misreading the option list and picking Fight instead of Evade at 3/5 horror vs Ghoul Priest is what killed me (fight succeeded, Ghoul Priest still attacked for 2dmg+2hor -> 5/5 horror, dead).

## [2026-07-03T22:15:51+00:00] Run sonnet5-mini-g2 · Round 8

Enemies auto-re-engage every round: any ready unengaged enemy at your location engages you automatically (upkeep, after exhausted cards ready). Evading only buys ONE round of safety unless you also spend an action to MOVE AWAY before it readies again. Against Hunter enemies this just delays — they'll path back — but distance still buys turns.

## [2026-07-03T22:15:51+00:00] Run sonnet5-mini-g2 · Round 8

Ghoul Priest (Elite 4/5/4, dmg2/hor2, Hunter, Retaliate, Victory2) is a serious threat to Roland's fragile 5 sanity — two hits (4 horror) can be fatal alone. CRITICAL: Act3 'What Have You Done?' requires DEFEATING Ghoul Priest to advance — you cannot just dodge it forever and still resolve the scenario; commit to killing it (ideally with a real weapon like .38 Special/Guard Dog, not just Knife) while sanity/health still has margin, rather than stalling until you're too fragile to risk the fight.

## [2026-07-03T22:15:51+00:00] Run sonnet5-mini-g2 · Round 8

Skull chaos token = -1 per Ghoul enemy AT your location, counted regardless of engagement status (a disengaged-but-present Ghoul Priest still adds -1 to skull draws).

## [2026-07-03T22:15:52+00:00] Run sonnet5-mini-g2 · Round 8

Cover Up (Roland's signature weakness): enters with 3 clues; its [reaction] letting you redirect clue discoveries into it is OPTIONAL — decline until your act's clue requirement is met, then redirect leftover discoveries to clear it. At game end ANY clues remaining on it cost only a FLAT 1 mental trauma (not per-clue), so it's low priority, not worth detouring for.

## [2026-07-03T22:15:52+00:00] Run sonnet5-mini-g2 · Round 8

Result (sonnet5-mini-g2, seed unspecified): died R8 to insanity (horror 5/5) vs Ghoul Priest at Hallway, resolution no_resolution. XP 3, trauma mental2/physical0, final score 4. Root cause: got pinned at Hallway for ~5 rounds re-fighting/evading Ghoul Priest+adds every round instead of retreating with a weapon-up plan; then misclicked Fight instead of Evade at a sanity-critical moment. Next time: (1) never linger at a Hunter-Elite's location beyond 1-2 rounds without a kill plan — retreat and build up weapons/allies elsewhere first; (2) double check option numbers before submitting 'do' when a wrong pick is fatal; (3) prioritize getting a real weapon (.38 Special/Guard Dog) online before round 5-6 instead of banking 10+ unused resources.

## [2026-07-03T22:26:23+00:00] Run sonnet5-mini-g3 · Round 9

Result (sonnet5-mini-g3): died R9 to insanity (horror 5/5), resolution no_resolution. XP 4, trauma mental2/physical0, score 5 (up from g2's 4). Never melee'd Ghoul Priest at all (avoided the retaliate trap) but still died: burned all resources pumping Hyperawareness to evade Priest round after round, leaving only 1 resource for the critical R9 evade -> pumped agility to only 3 vs difficulty 4 -> failed -> cultist token dealt 1 horror on the FAILED test (5/5) -> dead. Also note: cultist chaos token's '-1, take 1 horror on fail' applies to ANY failed test, not just willpower/sanity ones -- it hit an AGILITY evade test here.

## [2026-07-03T22:26:31+00:00] Run sonnet5-mini-g3 · Round 9

LESSON for next game: Ghoul Priest (4/5/4, Hunter+Retaliate, dmg2/hor2) cannot be safely meleed with just a Knife -- max single-hit is 2 dmg (thrown) vs its 5 HP, so ANY non-lethal fight action guarantees a Retaliate counter-attack (2dmg+2hor), and repeating that to whittle it down stacks retaliates faster than you can out-damage it. Only fight it once you have a weapon/combo that can kill in 1-2 actions in a single turn (e.g. .38 Special x2 shots), and budget resources SPECIFICALLY for that turn. Otherwise the only lever is repeated Evade (agility 2 base vs its evade 4 -- needs +2 net, only the +1 token in the bag beats that unpumped), which requires committing serious resources to Hyperawareness (was spending 5-6 resources per evade attempt for reliable success). Since Priest re-engages every upkeep, this cost repeats EVERY round it's alive -- do not spend down to 0-1 resources on a 'safe' round, since the very next round's evade needs the same budget again. Better plan: kill or permanently lose Priest early (Hunter still finds you if you just walk away one room), or bank resources deliberately (skip a round's actions if needed) rather than spending to zero, so the evade budget is always available.

## [2026-07-03T22:34:15+00:00] Run sonnet5-mini-g4 · Round 10

Result (sonnet5-mini-g4): WON via defeating Ghoul Priest, resolution R1 'Burn it down'. XP 6, trauma mental2 (1 from R1 choice + 1 uncleared Cover Up), Lita earned, score 7 -- new best (prior best was 5). Never advanced Act 2 until Machete+Beat Cop+Guard Dog+10 resources were online; killed 2 Swarm-of-Rats and a Ghoul Minion for free clues via Roland's kill-reaction before engaging the Priest.

## [2026-07-03T22:34:17+00:00] Run sonnet5-mini-g4 · Round 10

LESSON: Machete's +1 dmg bonus ('this attack deals +1 damage') only applies if the attacked enemy is the ONLY enemy engaged with you -- with 2 enemies engaged (Priest+Minion) Machete only hit for 1 dmg, not 2. Always clear secondary adds first (they die in 1 hit anyway) before committing Machete swings to a tough single target like Ghoul Priest.

## [2026-07-03T22:34:19+00:00] Run sonnet5-mini-g4 · Round 10

CORRECTION on Retaliate: it is NOT limited to fight actions. I played Dynamite Blast (an event, 3 dmg to all enemies+self at location) against Ghoul Priest expecting no counter since it's not a 'fight' -- Priest still made a full Retaliate attack (2dmg+2hor) back at me. Retaliate triggers on ANY damage dealt to the enemy that doesn't defeat it, regardless of source. Budget for 1 retaliate per non-lethal hit even from AOE/burst events, not just weapon swings.

## [2026-07-03T22:34:24+00:00] Run sonnet5-mini-g4 · Round 10

WINNING KILL SEQUENCE vs Ghoul Priest (5 HP, dmg2/hor2, Hunter+Retaliate) with Ghoul Minion also engaged: (1) Beat Cop fast-discard ping (auto-targets an enemy, don't rely on choosing which -- it hit the Minion here, not the Priest); (2) Fight Minion with Machete solo (1 dmg, enough since Minion already pinged down) -- now Priest is the only enemy engaged; (3) Dynamite Blast at own location (5 res, 3 dmg to Priest + 3 dmg to self, triggers 1 Retaliate: 2dmg+2hor) brings Priest to 2 HP; (4) Fight Priest with Machete (now solo-engaged, 2 dmg bonus) for the exact kill, lethal hit takes no Retaliate. Total self cost: 3(blast)+2(retaliate)=5 dmg, 2 hor, ONE retaliate instead of the 2+ that killed prior runs. Took 3 actions total, all in one round.

## [2026-07-03T22:34:26+00:00] Run sonnet5-mini-g4 · Round 10

SCORING: with Lita's +3 bonus now in the formula, re-derive the R1-vs-R2 choice per game: R1 'Burn it down' = +2 XP, +1 mental trauma, EARNS Lita -> net +4. R2 'Refuse to burn it' = +3 XP, no trauma, NO Lita -> net +3. R1 now edges out R2 by 1 net point (opposite of the pre-Lita-formula advice to always pick R2) -- pick R1 for defeating-the-Priest resolutions.

## [2026-07-03T22:34:28+00:00] Run sonnet5-mini-g4 · Round 10

ENGINE QUIRK: playing an Ally when your 1 Ally slot is already occupied auto-discards the incumbent with no confirmation/cancel step -- I lost a full-health Guard Dog by playing Beat Cop without checking slot occupancy first. Always check what's already in your Ally/Hand slots before playing a new card of the same slot type.

## [2026-07-04T20:30:22+00:00] Run none · Round ?

BUGHUNT game-01 Return/Roland: Run became unplayable R3 during Bedroom investigate commit confirmation; ./ahlcg do/state/actions/score/bug all fail with 'missing hidden state: runs/mch/hidden.blob'. Could not finish or file ./ahlcg bug because the bug command hits the same error. Earlier suspected log/UI bug: Machete option showed Combat(5) and final math used combat 5, but test-start log printed combat 4 vs 2.

## [2026-07-04T20:30:28+00:00] Run none · Round ?

Return/Roland opening lesson: Mag Glass + Machete is a strong keep; Flashlight conflicts with hand slots once both are in play, so committing it for the Study clue was good. Return Act 1 needs 3 clues spent from Guest Hall, but Guest Hall revealed with 0 clues in this run; Bedroom had 1 clue and Obscuring Fog can be cleared by a successful investigate. Cover Up is optional on each clue discovery, so decline it when Act tempo is urgent and use later spare clue discoveries/Roland kill triggers to clear it.

