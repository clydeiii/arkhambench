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

## [2026-07-06T02:13:02+00:00] Run c-loop2-daisy-2 · Round 5

Round 1 Lost to Narôgath - Daisy's low combat/agility made fighting the boss difficult. Need to prioritize defensive tech like Flashlight or evasion cards in future upgrades. Consider removing weak cards to add stronger combat options like Overpower or Bullet-proof Vest.

## [2026-07-06T02:14:21+00:00] Run c-loop2-daisy-3 · Round 2

Devourer Below R2 loss: Necronomicon pulled (3h), failed evasion/fight on Grave-Eater, defeated at 4/5 damage. Doom 0→1→5 immediately. Daisy has 3 physical trauma. Need focused strategy for next attempt.

## [2026-07-06T03:43:38+00:00] Run c-loop3-agnes-3 · Round 4

Campaign failed: loop3-agnes (Roland driven insane on Devourer Below). Agenda pressure (3/4 opening) combined with horror from encounter deck proved too strong. Key lesson: need more horror protection or combat plan for this scenario. Ritual Site strategy requires stronger investigator or horror management. Agnes was killed earlier, so this ends the campaign run.

## [2026-07-06T12:17:58+00:00] Run c-show-fable-roland-1 · Round 16

ENGINE TRAP: never chain a second './ahlcg do' after any action that starts a skill test — the commit menu renumbers options and the chained pick commits a card instead of Done. This game it burned .38 Special, Deduction, Evidence!, Guard Dog, Flashlight, and Dynamite Blast. One command at a time during tests; always read the menu first.

## [2026-07-06T12:18:07+00:00] Run c-show-fable-roland-1 · Round 16

Rules: playing a non-fast asset while engaged provokes an attack of opportunity (took 2/2 playing .45 vs Corpse-Hungry Ghoul). Play weapons before engaging; fast cards (Magnifying Glass) are safe. Failed EVADE does not trigger Retaliate, only failed attacks do.

## [2026-07-06T12:18:07+00:00] Run c-show-fable-roland-1 · Round 16

Return to The Gathering map intel: Act1 clues Study(1)/Bedroom(kill-reaction)/Bathroom(1), spend in Guest Hall; Act2 clues Cellar(1), Ghoul Pits(1, shroud 4 - use Roland kill-reaction), Field of Graves(shroud 2); Parlor locked until Act3. Ghoul Pits reveal: agility(3), spawns 1 rat per point failed. Field of Graves reveal: willpower(4), random discard per point failed. Obscuring Fog +2 shroud on Attic. 4+ Ancient Evils possible (Ghoul Pits search reshuffles discard).

## [2026-07-06T12:18:16+00:00] Run c-show-fable-roland-1 · Round 16

Ghoul Priest (5hp, fight 4, Retaliate, 2/2): each Machete swing is ~60% solo; engaging below 5 damage headroom means one fail = defeated. Agenda 3 at Act 1/2 = worst ending (R3), at Act 3 = defeat +1 phys trauma, same as dying to the Priest - so if health is low, racing to Act 3 and swinging is strictly correct. Defeat at Act 3 in Return Gathering still earned Lita + 5 XP, house standing. Next time: reach Act 3 by round 12 with weapon + Dodge in hand, keep health above 5.

## [2026-07-06T12:33:07+00:00] Run c-show-fable-roland-2 · Round 10

Return/Midnight Masks loss autopsy (Roland, horror-defeat R10): Hunting Nightgaunt DOUBLES negative chaos tokens on evade attempts (evade 1 but -1 becomes -2; only +1/0/0/eldersign pass at agi 2 = 25%). NEVER plan to evade it — fight it (no doubling) or avoid engaging. It attacks 1dmg/1hor every enemy phase; with sanity 5 that's a 4-round clock by itself.

## [2026-07-06T12:33:17+00:00] Run c-show-fable-roland-2 · Round 10

Midnight Masks strategy for next time: horror is THE loss axis for Roland (sanity 5 + Cover Up +Narôgath 1dmg/2hor attacks). Keep a soak ally alive at all times (Guard Dog died R7); play Lita/Beat Cop the moment ally slot frees while UNENGAGED. Once engaged at 4/5 horror there are no safe actions: non-fight/evade actions (incl. resign, moves, 0-cost allies) provoke AoO = death. Resign a round EARLY while unengaged rather than gamble evades. Also: chaos bag ran 3 autofails + heavy negatives in 13 pulls — budget tests assuming ~40% miss on 5v3.

## [2026-07-06T12:33:27+00:00] Run c-show-fable-roland-2 · Round 10

Return/Midnight Masks mechanics learned: (1) Act ability = spend 2 clues to draw from Cultist deck — clues in POOL are the currency, and Disciple spawn effects/tablet tokens STEAL pool clues (Disciple: 'place 1 clue on its location' takes yours). (2) Crypt Chill (will 3 vs 4) discards an asset — lost the .38 Special R2; keep a junk asset in play as sacrifice. (3) Mask of Umordhoth adds ~2 HP to a cultist. (4) Narôgath: 4hp fight 3, attacks 1dmg/2hor, Hunter after On Wings of Darkness disengage. (5) Killing a doom-laden cultist REMOVES its doom from the agenda count — worth prioritizing. (6) Working a Hunch is fast: safe while engaged, and can clear Cover Up via the replace-discovery choice.

## [2026-07-06T12:33:45+00:00] Run c-show-fable-roland-2 · Round 10

CRITICAL Midnight Masks scoring lesson: generic 'Disciple of the Devourer' kills do NOT count as interrogations. The interrogatable cultists are the NAMED ones (Alma Hill, Jeremiah Pierce, Peter Warren, Ruth Turner, Victoria Devereux, Narôgath) drawn from the Cultist deck via the act's spend-2-clues ability. Strategy next campaign: farm clue pool early and spam cultist-deck draws from round 2-3; each named cultist not drawn+defeated 'gets away' and adds setup doom to Devourer Below (we shipped 6 there this time).

## [2026-07-06T12:36:01+00:00] Run c-show-fable-roland-2 · Round 10

Devourer Below prep (Roland, phys 1 / mental 2 trauma, all 6 cultists got away = heavy setup doom): bought Dr. Milan + Mag Glass(1) for the Ritual Site clue path. Opening priorities: mulligan hard for Machete (x2 in deck, never drawn in Midnight Masks) + Milan; keep an ally soak alive at all times; Roland starts at 2/5 effective sanity headroom is 3 mental-trauma-adjusted, so treat ANY 2-horror hit as near-lethal — Dodge and willpower pumps (Physical Training) are life-savers; Silver Twilight Acolyte weakness feeds agenda doom every attack, kill it instantly (3hp fight 2).

## [2026-07-06T12:50:15+00:00] Run c-show-fable-roland-3 · Round 8

CLI pitfall: never chain './ahlcg do N && ./ahlcg do M' — the action menu renumbers after every decision. In TDB R1 this made me hit 'Pass (end turn)' instead of 'Play Dr. Milan Christopher', wasting a full setup turn. Always read the fresh menu before each do.

## [2026-07-06T12:50:23+00:00] Run c-show-fable-roland-3 · Round 8

Campaign math: letting all 6 cultists get away in Midnight Masks starts (Return to) The Devourer Below at 3/4 agenda doom — agenda 1 flips on round 2 and the solo clue race is essentially lost from setup. Interrogating cultists in scenario 2 is the real defense for scenario 3; treat Midnight Masks cultist hunting as a scenario-3 investment, not optional VP.

## [2026-07-06T12:50:34+00:00] Run c-show-fable-roland-3 · Round 8

TDB endgame facts learned the hard way: Umordhoth (solo) = 6 hp, fight 8 / evade 6 with Vault of Earthly Demise, attack 3dmg/3hor, Massive + Hunter — 'Engage Umordhoth' appearing in the menu does NOT mean you're free; moving from his location provokes AoO from him AND every other engaged enemy. Corpse-Taker's attack is 1 dmg / 2 HORROR (killed Roland at 3/5 sanity). 'The Ritual Begins' flip forces willpower vs 6, failure = gain a random basic weakness (Amnesia). Umordhoth's Hunger discards a card and an empty hand is lethal — always hold one. When double-engaged with lethal AoOs and Resign is on the menu, resign: defeat gave the same no_resolution plus extra mental trauma.

## [2026-07-06T12:50:45+00:00] Run c-show-fable-roland-3 · Round 8

Test-margin discipline: this NotZ bag (standard) has -3, -4, elderthing -5, autofail = 4/17 tokens at -3 or worse. A test at skill+1 vs difficulty fails ~40% and skill+2 fails ~25%. Roland's 4-vs-3 basic attacks whiffed 5 of 6 early tries and burned three rounds on a 2hp Grave-Eater. When a kill or escape gates the turn plan, commit cards to reach +3 margin or bring a weapon; naked stat checks are for throwaway actions only.

## [2026-07-06T12:56:53+00:00] Run c-show-fable-daisy-1 · Round 5

Engine enforces one ally slot: playing Research Librarian DISCARDS Dr. Milan from play ('discarded for slot capacity') with no warning at play time. Check play-area slots before playing allies.

## [2026-07-06T12:59:49+00:00] Run c-show-fable-daisy-1 · Round 8

AoO rule enforced: activating abilities (e.g. Old Book of Lore) while engaged with a ready enemy provokes an attack. Evade/kill first or accept the hit.

## [2026-07-06T13:02:15+00:00] Run c-show-fable-daisy-1 · Round 8

FATAL LESSON (Daisy, Return to the Gathering): engagement persists through act advances and forced moves — 'enemy moved to X' + 'you moved to X' means it FOLLOWED YOU, still engaged. Always re-check 'Engaged enemies' in ./ahlcg state before ANY AoO-provoking action when at low health. Died at 4/5 dmg using Old Book of Lore while unknowingly still engaged.

## [2026-07-06T13:18:06+00:00] Run c-show-fable-daisy-2 · Round 7

Return/Midnight Masks (Daisy, resigned R7): Daisy CANNOT fight named cultists without setup. Narogath spawns ENGAGED when agenda 1 flips (~R6 with Corpse-Taker doom accelerating it). By then you need EITHER 2+ res + Blinding Light in hand, OR MoM+Knife combo ready, OR an ally soak in play. Milan died as a 3-point soak in one attack (1dmg/2hor exactly kills him) - worth it, saved Daisy.

## [2026-07-06T13:18:16+00:00] Run c-show-fable-daisy-2 · Round 7

Action budget trap: 'N actions left (1 Tome-only)' means N-1 generic. I planned 'evade then resign if fail' but the evade consumed my LAST generic action - resign was impossible, nearly died. When counting actions for a survival plan, subtract the Tome-only action FIRST. Also eldersign for Daisy is +0 (not +1).

## [2026-07-06T13:18:26+00:00] Run c-show-fable-daisy-2 · Round 7

Confirmed AGAIN (2nd death-adjacent time): moving away from an engaged enemy does NOT disengage - it follows. Paying an AoO to 'escape' buys NOTHING; the ONLY exits are successful evade, kill, or resign. Naked Daisy evade vs evade-3 enemies passes only on +1 (1/16=6%). Plan around this: never let Daisy get engaged by fight-3/evade-3 enemies without Blinding Light money (2 res) in reserve. Also: keep 2+ resources banked at ALL times for exactly this; I hit the R6 crisis with 0 res and Emergency Cache unplayable (play=AoO while engaged).

## [2026-07-06T13:18:35+00:00] Run c-show-fable-daisy-2 · Round 7

Midnight Masks cultist-hunt economics (Daisy run): interrogating Peter Warren cost ~2 clues + 4 actions + Knife + MoM + 2 dmg taken. Soft cultists (fight 2, 2-3hp) ARE killable via MoM(int 5)+Knife-throw(+2/2dmg). Do cultist draws EARLY (R2-4) while board is quiet; after agenda 1 flips (Narogath engaged + hunters), cultist hunting is over for a fragile investigator. Also Misk U 'search 6 for Tome/Spell' whiffed with 10+ targets in a 25-card deck - don't rely on it; and use Ma's Boarding House ally-fetch for Milan the moment you pass Southside.

## [2026-07-06T13:19:48+00:00] Run c-show-fable-daisy-2 · Round 7

TDB prep (Daisy, 5 cultists got away = heavy setup doom, agenda will flip fast): plan is the CLUE RACE, not combat. Bought Drawn to the Flame (2 testless clues) over Deduction. Opening: mulligan for MagGlass/Old Book/allies; fetch Milan is not available in TDB (no Ma's Boarding House) so protect drawn allies. Keep 2+ res banked for Blinding Light evades; MoM+Knife is the only kill line (2hp max realistically). Umordhoth: do NOT fight (fight 8 w/ Vault); sacrifice-Lita ending may be the realistic out - check resolution values before committing. Resigning TDB = Arkham destroyed, treat as last resort.

## [2026-07-06T13:37:54+00:00] Run c-show-fable-daisy-3 · Round 5

Return TDB solo defeat autopsy (Daisy, R5): with 5 got-away cultists the clock is agenda1 flip R2, agenda2 flip R4 — there is NO setup window. Engine rule that decided the game: ready enemies at your location RE-ENGAGE during UPKEEP, so a successful evade buys exactly one enemy phase and kiting from the same location is impossible. Correct play: after ANY successful evade, spend remaining actions MOVING away (hunter loses a full round crossing the hub; non-hunters like Grave-Eater never follow). I instead stayed at Old House to play Librarian/Book and got locked into a 2-enemy engagement with 1 hp of headroom = mathematically dead by R5.

## [2026-07-06T13:38:08+00:00] Run c-show-fable-daisy-3 · Round 5

Return TDB mechanics learned (Daisy run): (1) Mask of Umordhoth with no cultist in play = YOU pick and spawn one from a menu - pick Disciple (1hp, one-time doom/clue steal) over Corpse-Taker (recurring doom). (2) While agenda 2 'The Ritual Begins' is active, Byakhee tested at fight/evade 4 (+1/+1); reverts at agenda 3. (3) Agenda 2 flip test is willpower vs 6 - unwinnable at will 3, budget for a random weakness (Paranoia stripped all resources). (4) Tablet token in TDB = -3 AND 1 damage immediately, even mid-test - lethal at low HP. (5) Skull = -1 here. (6) Old House investigates with WILLPOWER (3 for Daisy, worse than int 5). (7) Grave-Eater attack = 1dmg/1hor + random hand discard. (8) Daisy eldersign = +0 plus draw 1.

## [2026-07-06T13:38:08+00:00] Run c-show-fable-daisy-3 · Round 5

Cross-scenario trauma math: entering TDB with 1 physical trauma meant Daisy had 4 effective HP; two engaged 1-dmg enemies = dead in 2 rounds regardless of play. When a campaign's final scenario starts with heavy setup doom AND trauma, the win conditions requiring rounds 8+ (Lita sacrifice, act 3) are out of reach - the honest evaluation at R4 was to sprint to Main Path and RESIGN while unengaged (Arkham destroyed either way, but avoids +1 trauma and keeps agency). Resign is only available at Main Path in TDB.

## [2026-07-06T13:57:26+00:00] Run c-show-fable-skids-1 · Round 14

Return/Gathering KILLER FACT: agenda 3 'They're Getting Out!' completing = R3 = investigator KILLED (not a flee ending). Never plan to 'ride out the agenda' in this scenario — the doom clock is a hard death timer. Ancient Evils x3 means doom 10 can arrive 2+ rounds early, and upkeep ALSO adds doom in agenda 3 (2/round baseline). Treat Return/Gathering as: be ready to advance act 2 and kill Ghoul Priest by ~R11, or you lose the investigator.

## [2026-07-06T13:57:37+00:00] Run c-show-fable-skids-1 · Round 14

Return/Gathering (Skids run) mechanics: (1) Return Bedroom + 'Breaking the Wall' act transition + Field of Graves entry ALL punish failed tests with random hand discards — hand was stripped to 0 twice; hold cards loosely, play assets ASAP. (2) Crypt Chill x2 ate Switchblade+Knife: junk-asset-as-sacrifice lesson confirmed again. (3) Locked Door blocks investigate until Combat/Agility 4 test — Hard Knocks resource pumps solved it (6v4). (4) Flashlight is the tempo unlock for shroud-3 rooms (3v1); Overpower's draw got it back after a discard. (5) Skids elder sign = +2 AND +2 res. (6) Icy Ghoul wanders (Hunter-ish) but didn't force a fight all game. (7) Hospital Debts: pay 2/turn in fast windows; ended 4/6 = -2 XP would've applied but XP was 0 anyway.

## [2026-07-06T13:57:49+00:00] Run c-show-fable-skids-1 · Round 14

Skids death autopsy (Return/Gathering R14): root cause was CLUE TEMPO, not the final gamble — 10 of 13 naked investigates failed R6-R9 (int 3 vs shroud 3 with -1/-2/-2/-3/-4/tablet/autofail bag ~ 40-45% pass). By the time Flashlight+Hard Knocks fixed the math (R12), 3x Ancient Evils had erased the margin. For low-int investigators: play Flashlight round 1-2 if drawn, treat shroud 3 as UNTESTABLE naked, and bank Skids' 2res=action ability for double Flashlight investigates. Also: the act-2 advance prompt appears in UPKEEP at the Hallway — by then mythos of next round fires first; don't count 'end of round N' doom, count MYTHOS of round N (Ancient Evils = instant +1).

## [2026-07-06T13:58:32+00:00] Run c-show-fable-skids-1 · Round 14

Agnes prep for Return/Midnight Masks (fresh deck, 0 XP, Lita earned-not-in-deck): mulligan for Shrivelling (only kill tool, will 6 vs fight 2-3 cultists) + Arcane Initiate/Holy Rosary. Ward of Protection: SAVE for Ancient Evils or Narogath-class spawns — this campaign runs 3x Ancient Evils. Use Drawn to the Flame for testless clues to fuel the act's 2-clue cultist-deck draws EARLY (R2-4, per Daisy lesson). Agnes will 5 passes Crypt Chill (vs 4)/Frozen (vs 3) naturally. Watch her health 6 — physical hits are her weak axis; keep soak (Initiate takes horror? no, Initiate is doom+fetch; horror soak = Rosary/herself at sanity 8).

## [2026-07-06T14:14:52+00:00] Run c-show-fable-skids-2 · Round 11

Agnes engine mastered (Return/MM, resigned R11 alive): FK/Shrivelling horror = AMMO. Every horror source triggers Agnes's 1-dmg ping to an engaged enemy - FK fast-use in the ENEMY-PHASE window pings BEFORE attacks resolve (killed things pre-attack twice). Kill pattern vs 3-4hp: Shrivelling(2) + symbol-horror ping(1) + Shrivelling(2). Arkham Asylum Downtown heals 3 horror/action - it's the reload station for the whole engine; Police Station refills Flashlight.

## [2026-07-06T14:15:07+00:00] Run c-show-fable-skids-2 · Round 11

Narôgath (Return/MM boss cultist) SOLVED solo: card says health 4 but +3/investigator = 7 real hp (state display shows base 4 - don't trust it). Elite = Stray Cat auto-evade DOESN'T work. Attack 1dmg/2hor. He spawns engaged at agenda-1 flip; evade (3v3, commit +1) then run 2 locations. His Prey text pulls him around the map; killing him = 2VP + unblocks Parley + ends hunter pressure. Cost me ~5 Shrivelling charges + 3 pings over 2 turns - budget the whole kit.

## [2026-07-06T14:15:07+00:00] Run c-show-fable-skids-2 · Round 11

Return/MM economics (Agnes solo): 1 interrogation (Peter Warren) is what a fragile solo investigator realistically gets. Clue math dies after ~R8: Obscuring Fog (+2 shroud) + Locked Door + shroud-4 ring locations = no more 2-clue batches; Drawn to the Flame is the ONLY reliable late fuel (2 testless clues, costs 1 doom via encounter draw). Hunting Shadow with 0 clues = FORCED 2 dmg - at <=2 hp every mythos draw is ~15% instant death; resign the moment the board has no bankable value. Agenda 2 completing = past midnight TRUE in log - resign before doom 8/8 to keep it False.

## [2026-07-06T14:17:12+00:00] Run c-show-fable-skids-2 · Round 11

TDB prep (Agnes, 4 cultists got away, 0 trauma, resigned MM at R11 alive): bought Ward of Protection x2 (cancel Ancient Evils - 3 in deck) + 'Look what I found!' x2 (testless clues for Ritual Site plan); cut Knife x2/Baseball Bat x2 (combat 2 = dead cards). Lita INCLUDED: 0-cost 3/3 soak, +1 dmg reaction applies to Shrivelling vs Monsters (3dmg/hit), and enables sacrifice ending - the realistic solo out since Umordhoth fight 8 is unwinnable. Opening: mulligan for Shrivelling+Flashlight+Lita; play Heirloom BEFORE spells; FK horror = pings+resources but budget sanity 8 hard (MM run peaked 7/8).

## [2026-07-06T14:28:56+00:00] Run c-show-fable-skids-3 · Round 5

TDB FATAL TRAP (Agnes resigned R5): the 4 got-away cultists spawn at Main Path when Act 1 advances and engage INSTANTLY when you enter (no pass-through in this engine, matches official rules). Main Path is the ONLY route to Ritual Site, so solo you face 4 simultaneous engagements: AoO wall = Billy 2dmg + Herman 1/1 + Ruth 1dmg + Alma 0/2hor = 4dmg/3hor BOTH for staying (enemy phase) and leaving (AoOs). At <=4 spare HP this is checkmate. COUNTER-PLAY next time: (1) do NOT advance Act 1 until prepped — full HP, Shrivelling charged, soak ally in play; (2) advance act while standing ON Main Path is equally fatal (they spawn+engage there); (3) treat the spawn as a 4-VP farm ONLY with a real combat plan, else keep act 1 unadvanced and farm woods clues/XP; (4) fewer cultists-got-away in Midnight Masks remains the true fix. Also: engine bug filed — Alma/Herman parley actions (victory-display escapes) not in menu.

## [2026-07-06T14:29:06+00:00] Run c-show-fable-skids-3 · Round 5

Umordhoth's Wrath (will vs 5) fail-by-X = X picks of 'take 1dmg+1hor OR discard 1 card' — with a thin hand this shreds it (lost Emergency Cache + Stray Cat + took 1/1 failing by 3 at will 4). Agnes elder sign = +1 PER HORROR ON HER (+4 at 4 horror) — at high horror ES becomes an auto-pass; factor into risk math. Haunted (Agnes signature) = -1 ALL skills, 2 actions to clear; it flips 'safe' 5v3 will tests into coin flips at the worst time. Old House investigates via WILLPOWER (great for Agnes, 5v2). Killing a doom-carrying enemy (Grave-Eater) removes its doom from the agenda.

## [2026-07-06T14:54:42+00:00] Run c-show-fable-agnes-1 · Round 17

Return/Gathering SOLVED solo (Agnes R2, 7XP, 0 trauma, doom 9/10 — contrast Skids death R14): the winning engine was Arcane Studies + banked resources (~15 by R11) = buyable test successes for BOTH int investigates and will Shrivelling. Study (Aberrant Gateway) draw-3 (2 actions) is the dig engine while banking. Key route facts: act 1 clues must be spent IN Guest Hall; act 2 spends at HALLWAY at round END (plan moves to end there); 3rd act-2 clue hides in Ghoul Pits (shroud 4, agility-3 entry test, fail spawns 2 rats) — bring Flashlight. Obscuring Fog on Study makes its clue need Drawn to the Flame.

## [2026-07-06T14:54:55+00:00] Run c-show-fable-agnes-1 · Round 17

Ghoul Priest solo kill recipe (Agnes): Shrivelling charges = 1 per ATTACK (4 charges = 4 attacks, not 2) — killed GP (5hp) in ONE round: pumped attack (2dmg) + cultist-recoil horror taken on AGNES = free ping (1dmg) + Rosary-committed attack (2dmg). Shrivelling recoil on symbol tokens is BONUS damage for Agnes, take it on her when sanity allows. Tablet in Gathering = 1 dmg (soak on Leather Coat). Skull = -1 per Ghoul in play (0 ghouls = -0). Dark Memory: pay it off when doom has slack (1 action + 2 res + 1 doom) instead of eating 2 horror every turn-end.

## [2026-07-06T14:54:55+00:00] Run c-show-fable-agnes-1 · Round 17

Engine UI traps (cost me tempo): (1) mulligan set-aside menu TOGGLES — picking same option twice cancels it; (2) menu numbers SHIFT between prompts — never chain './ahlcg do N' blind, the same N can become 'Move' next prompt (this walked me into a Corpse-Hungry Ghoul engagement); (3) playing an asset while engaged = AoO fires BEFORE the asset lands (can't soak with it); (4) Arcane Initiate refuses to fetch Drawn to the Flame (Spell event) — asset Spells only, possible engine bug; (5) act advance is an explicit menu option/round-end prompt, only offered at the objective location.

## [2026-07-06T14:55:14+00:00] Run c-show-fable-agnes-1 · Round 17

Return/MM prep (Agnes campaign show-fable-agnes, 0 trauma, GP dead, house standing, 7 XP spent): deck now has Ward of Protection x2 (SAVE for Ancient Evils/Narogath-class spawns), Look what I found! x2 (near-miss investigates at int 2 become clues — great for the 2-clue cultist batches), Lucky!, and Arcane Studies(2) (free to play, 2/2 icons — play it R1-2 and bank resources; it was the MVP of Gathering). Reuse skids-2 MM playbook: interrogate early R2-4, Narogath is 7hp solo w/ Prey, Asylum heals 3 horror/action, resign before doom 8/8 to keep past-midnight False.

## [2026-07-06T15:05:22+00:00] Run c-show-fable-agnes-2 · Round 7

BUG? Return to Midnight Masks: Narôgath at 6/4 damage and not defeated — enemy defeat check not firing for the agenda-2 spawned cultist. Repro: campaigns/show-fable-agnes run 2, R6-R7, Shrivelling x2 + Agnes pings x2. Verify whether Narôgath has an intended 'cannot be defeated' effect; if not, defeat processing is broken for him.

## [2026-07-06T15:13:19+00:00] Run c-show-fable-agnes-2 · Round 11

Return to Midnight Masks: 'Wolf-Man' Drew (with Mask of Umordhoth) RETALIATES, attacks for 2 damage, and HEALS 1 on every attack. Never swing at him at even odds with ≤4 health left — a failed fight = retaliate + enemy-phase attack = 4 damage in one round. Interrogate cheaper cultists via parley instead (Herman Collins: discard 4 cards, no test).

## [2026-07-06T15:13:26+00:00] Run c-show-fable-agnes-2 · Round 11

Agnes engine notes: eldersign = +1 per horror on her (revealed eldersign at 5 horror = +5, turned Crypt Chill into success by 7). Hunting Shadow spends YOUR clue pool, the location does not refill — don't re-investigate an emptied location after paying it. Hand-size discard can legally dump Dark Memory (event weakness) from hand. Drawing a card provokes attacks of opportunity from engaged enemies.

## [2026-07-06T15:14:13+00:00] Run c-show-fable-agnes-2 · Round 11

show-fable-agnes going into Return to Devourer Below: 5 cultists got away (Drew, Pierce, Narôgath, Warren, Devereux) = heavy setup doom + they reappear at Main Path when Act 1 advances. Agnes has 1 physical trauma (starts at 1/6 damage) — avoid the fight-Umordhoth plan; favor Ritual Site clues (Arcane Studies(2) now pumps int+will) or sacrificing Lita (not earned, so likely clue plan). Move fast: agendas 4/5/5 with Ancient Evils x3.

## [2026-07-06T15:33:42+00:00] Run c-show-fable-agnes-3 · Round 11

Return to TDB (solo, Agnes, defeat): once agenda 3 completes, Umordhoth (evade 6, fight 5+Vault, Hunter, Massive, readies at END of each investigator turn) is checkmate for a solo non-fighter — he camps/chases the only door to Ritual Site and every AoO or attack one-shots. The scenario must effectively be WON before agenda 3 advances; prioritize act tempo over safety from round 1, and skipping Lita in Midnight Masks removes the sacrifice out entirely.

## [2026-07-06T15:33:53+00:00] Run c-show-fable-agnes-3 · Round 11

Return to TDB mechanics learned: (1) 5 escaped cultists = +3 setup doom, agenda 1 starts 3/4. (2) Disciple of the Devourer spawns steal 1 of YOUR clues when past agenda 1 (plus doom) — they cost me the act-1 advance twice; kill them same round (1 hp) or hold a spare clue. (3) Umordhoth's Hunger kills any investigator with an empty hand — always bank 1 card. (4) Great Willow makes treacheries surge; leave ASAP. (5) skull = -X per MONSTER in play (Disciples are Cultists, not Monsters).

## [2026-07-06T15:33:53+00:00] Run c-show-fable-agnes-3 · Round 11

CLI lesson: never chain './ahlcg do N && ./ahlcg do M' through commit/option submenus — option numbering shifts between prompts and the second call misfires (this game it accidentally committed Ward of Protection, losing the Ancient Evils cancel). One command per decision inside any test/commit window. Also: engine bug filed — 'Look what I found!' is never offered after failing an investigate by <=2.

## [2026-07-06T15:53:58+00:00] Run c-show-fable-wendy-1 · Round 12

Return/Gathering WENDY line (survived R12 timeout, Lita EARNED+recruited, 3XP, 1 phys trauma): parleying Lita (int 4 test, Parlor, act 3) sets lita_earned=true even when the scenario ends by agenda-3 timeout with outcome no_resolution — resigning without her would NOT have (Agnes killed GP, never parleyed, lita false). Solo kill on GP (5hp) is unrealistic at combat 1; the right Wendy line is: evade everything, parley Lita, let doom run out. Timeout cost only 1 physical trauma + GP alive in log.

## [2026-07-06T15:54:10+00:00] Run c-show-fable-wendy-1 · Round 12

Wendy engine notes (Return/Gathering): (1) Wendy's Amulet is the whole engine — play it R1-2: replays TOP discard event (Cunning Distraction evade-all from discard = testless GP neutralizer, cost 5) and bottom-decks played events (Lucky! recycles). (2) Wendy redraw ability works repeatedly (once per test at least) — junk commits (MD/Pickpocketing/Knife) are redraw ammo; it converted -4 into a pass twice. (3) Abandoned and Alone removed my discard FROM GAME (lost LWIF x2 + Perception + Dig Deep) — with Wendy, do NOT bank key events in discard for Amulet; play them or hold them. (4) Return Bathroom drains ALL remaining actions after its investigate. (5) 'They're Getting Out' adds ~2 doom/upkeep with 2 enemies near Hallway — agendas ran 3+7+10 in ~12 rounds. (6) exhausted enemies don't retaliate/AoO: evade-then-act ordering is life-or-death at high horror.

## [2026-07-06T15:54:18+00:00] Run c-show-fable-wendy-1 · Round 12

Return/MM prep (Wendy, 1 phys trauma, Lita IN DECK, GP alive, deck: +Lucky!(2) +Sneak Attack -Knife): plan = evade+Sneak Attack (testless 2dmg on exhausted enemy) as the kill kit for 1-3hp cultists; interrogate early R2-4 per Daisy/Agnes lessons; Narogath is 7hp solo (Prey, spawns engaged at agenda-1 flip) — evade+Backstab(3)+Sneak(2)+Sneak(2) is the only realistic kill; resign before doom 8/8 to keep past-midnight False; GP alive means he may be in the MM/TDB encounter pool — Lita gives +1 dmg vs him and 3/3 soak. Watch sanity 7: this run ended 6/7 horror with zero horror heals in deck.

## [2026-07-06T16:08:43+00:00] Run c-show-fable-wendy-2 · Round 8

Return/MM WENDY SOLVED-ish (resigned R8, 4XP, 0 new trauma, 2 interrogated): KILLING a named cultist counts as INTERROGATED in the campaign log (Narôgath kill = interrogated + 2VP) — killing beats parley when feasible. Narôgath kill recipe at combat 1: evade (exhaust) -> Backstab 3 (agility 4v3, fight-action so no AoO) -> Sneak Attack 2 testless -> next turn Backstab#2 = 7hp done over 2 turns for ~5 res. Ma's Boarding House fetches Lita/Leo from deck (1 action). Lucky!(2) draws a card on play — it dug out the second Backstab for the kill.

## [2026-07-06T16:08:52+00:00] Run c-show-fable-wendy-2 · Round 8

Return/MM traps learned (Wendy run): (1) Disciple of the Devourer spawn STEALS a clue from your pool to place on its location (and can add doom) — never end a turn holding 1 clue; spend pairs on the cultist deck same turn. (2) Amnesia (basic weakness) = discard hand to 1 card at upkeep — brutal mid-combo; play assets out of hand early. (3) Ghoul Priest alive in log = he spawns via encounter deck in MM, hunts, attacks 2dmg/2hor; Wendy cannot kill him (fight 4, 5hp) — 4v4 evade is 25% with skulls scaling on cultists; treat GP arrival as a resign timer. (4) Parley interrogation (Pierce) = willpower 4 test. (5) Mask of Umordhoth lets you CHOOSE which cultist to draw — pick Disciple (1hp).

## [2026-07-06T16:09:03+00:00] Run c-show-fable-wendy-2 · Round 8

TDB prep (Wendy, campaign show-fable-wendy): 4 cultists got away (Drew, Cooper, Collins, Devereux) = setup doom + Main Path wall when Act 1 advances. Lita IN DECK = sacrifice ending live (the realistic solo out per agnes-3 failure). Bought Elusive (disengage+move, the Main Path wall escape), Close Call(2) (evade -> shuffle enemy into encounter deck — permanent removal; use on a wall cultist or GP-class hunter), Leo(1) (cost 5). Plan: rush act tempo from R1 (agnes lesson: game must be won before agenda 3), fetch Lita via Ma's-style ally search if available, evade+Elusive past the wall to Ritual Site, sacrifice Lita. Watch: scenario must be effectively decided before Umordhoth (evade 6) is out.

## [2026-07-06T16:10:31+00:00] Run c-show-fable-wendy-3 · Round 1

return_to_devourer: Main Path starts with 0 clues — Act 1 clues are on the unrevealed Arkham Woods locations; move there before investigating. Also: never chain 'do' commands — a reaction prompt (Wendy's ability) can eat the second command and waste a card.

## [2026-07-06T16:18:06+00:00] Run c-show-fable-wendy-3 · Round 6

return_to_devourer (Wendy, standard): DEFEATED R6 at 2/3 Act-1 clues. Killers: (1) Umordhoth's Wrath fail-by-4 with empty hand = 4x(1dmg+1horror) — keep 2+ cards in hand as Wrath insurance; (2) Return bag is savage: elderthing=-5 (and can chain a second token), tablet deals 1 damage on reveal during failures — treat any test with <=+2 margin as a coin flip; (3) entering trauma'd finale at 1 dmg with a 7-stamina investigator leaves zero buffer. Next time: bank defensive cards (Lucky!/Elusive) for mythos, don't burn them on marginal investigates, and consider resigning while alive once health drops to ~2 remaining since no_resolution scores 0 anyway.

## [2026-07-06T16:24:10+00:00] Run c-show-gpt-roland-1 · Round 10

Campaign lesson: prioritize clearing Frozen in Fear and engaged enemies before greedy clue lines; Roland needs early weapon/talent setup, and Lita/Physical Training help stabilize combat and will tests after mental trauma.

## [2026-07-06T16:29:58+00:00] Run c-show-gpt-roland-2 · Round 7

Return Midnight Masks: Narogath effectively has extra solo health beyond compact display; do not engage late with low sanity unless enough burst damage or soak is ready. Prioritize early weapons/soak and clue tempo; resigning can preserve trauma when only one cultist is secured.

## [2026-07-06T16:32:38+00:00] Run c-show-gpt-roland-3 · Round 4

show-gpt-roland finale: Return TDB resigned R4 for no_resolution/0XP after Yithian Observer pinned Roland at Main Path and Ghoul Priest spawned while Roland was 5 dmg/4 horror. Key lesson: with 5 cultists escaped and 3 setup doom, every early action must be clue tempo or decisive enemy control; .38 at 5v5 is unreliable into Yithian Observer, and committing Guard Dog as an icon saved one shot but removed crucial soak. If Offer of Power appears, taking doom over horror preserves sanity but can still cascade into agenda-2 elderthing/Paranoia. Resign at Main Path is the preservation line once Roland reaches 4/5 horror with hunters engaged.

## [2026-07-06T16:44:14+00:00] Run c-show-gpt-daisy-1 · Round 10

Return Gathering Daisy: keep Ward for Crypt Chill when setup assets are down; Act 2 objective prompts at end of round in Hallway, so use remaining actions to prep before advancing. Lita + Knife can burst Ghoul Priest: normal hit then throw for 5 total damage.

## [2026-07-06T16:50:47+00:00] Run c-show-gpt-daisy-2 · Round 7

Return Midnight Masks: Daisy can cash early cultists with Milan/Working a Hunch, but avoid ending engaged with cultists at low health; keep at least one clue or cancel available for Hunting Shadow/False Lead chains, and treat The Masked Hunter as a resign-or-evade-now threat.

## [2026-07-06T16:58:55+00:00] Run c-show-gpt-daisy-3 · Round 6

Return Devourer Below Daisy lesson: with four cultists escaped, doom pressure is extreme; prioritize fast Act 1 clue progress over setup, and avoid spending the early Tome action unless it directly finds tempo. Corpse-Taker at Main Path must be killed or evaded before its doom transfer snowballs; Lita plus Mind over Matter can kill it, but Frozen in Fear can consume the action needed for the second hit.

## [2026-07-06T17:09:00+00:00] Run c-show-gpt-skids-1 · Round 12

Skids Return Gathering lesson: prioritize early clue compression and tempo; do not let hunters stack before Act 3. Flashlight/Perception are key for shroud 4 Cellar, and Lita/Machete-style damage is needed before engaging Ghoul Priest.

## [2026-07-06T17:14:07+00:00] Run c-show-gpt-skids-2 · Round 6

show-gpt-skids Return/MM defeat R6: Masked Ruth became a trap when fought while Narogath was engaged; Mask of Umordhoth inflated her durability enough that repeated 4v2 Machete swings did not finish her before Hunting Shadow killed Skids. Next Skids MM line: do not commit to Ruth/Narogath without burst damage or an escape banked; if Narogath spawns on top of you, prioritize Elusive/resign survival over grinding masked cultists. Train Station can jump to any Arkham location and is powerful tempo, but still needs enough actions/resources left to resolve the enemy safely.

## [2026-07-06T17:20:49+00:00] Run c-show-gpt-skids-3 · Round 7

Return Devourer with Skids: six cultists getting away creates brutal starting doom and enemy pressure. Prioritize a reliable weapon in the opener over Leo/economy, avoid getting trapped in Twisting Paths without intellect commits, and keep at least one card in hand because Acolyte of Umordhoth can become non-evadable when empty-handed.

## [2026-07-06T17:32:28+00:00] Run c-show-gpt-agnes-1 · Round 14

show-gpt-agnes Return/Gathering R3 loss: Act tempo was too slow. Agenda 3 adds end-round doom for each Ghoul in Hallway/Parlor; with Icy Ghoul in Parlor plus another Ghoul in Hallway, doom jumped from 8 to 10 before Act 2 could advance. For future Return/Gathering runs, reach Act 2 by ~R8-9, save Drawn to the Flame for Cellar/last Act-2 clue, and do not spend multiple early turns drawing/setup after Act 1 clues are available.

## [2026-07-06T17:38:42+00:00] Run c-show-gpt-agnes-2 · Round 8

Return Midnight Masks: overcommitted to Narogath with empty .45 and low hand; if Narogath appears, either evade/move if possible or ensure backup weapon/commits before engaging. Jeremiah parley is risky at high doom; need faster early cultist draw and avoid spending entire turns on setup after first cultist.

## [2026-07-06T17:43:07+00:00] Run c-show-gpt-agnes-3 · Round 3

Return Devourer: with all cultists escaped, opening at 3 doom and drawing Ghoul Priest early makes Roland's no-weapon hands extremely fragile. Lita plus Knife is not enough if the Knife throw misses; prioritize mulliganing harder for a firearm or Beat Cop over keeping clue skills.

## [2026-07-06T17:52:08+00:00] Run c-show-gpt-wendy-1 · Round 9

Return Gathering Wendy: Act 2 advances only at end of round while in Hallway with 3+ clues; plan to end there. Survival Instinct is excellent in Act 3 to disengage the enemy pile and move to Parlor for Lita/resign.

## [2026-07-06T18:01:57+00:00] Run c-show-gpt-wendy-2 · Round 8

Campaign lesson: In Return Midnight Masks with Wendy, avoid drawing cultists when Ghoul Priest/Masked Hunter are one step away unless an escape action is already secured; Elusive and upgraded Dig Deep were added for Devourer mobility and evade reliability.

## [2026-07-06T18:14:24+00:00] Run c-show-gpt-wendy-3 · Round 10

show-gpt-wendy finale: Return TDB ended no_resolution R10, 0XP, +1 mental trauma. Key trap: Throw Lita to Umordhoth is an action that provokes AoOs from every engaged enemy; moving to Main Path with escaped cultists still engaged Lita/Wendy, and Peter's 1 damage discarded already-damaged Lita before the sacrifice could resolve. To use Lita, arrive at Main Path/Ritual line with enemies evaded/disengaged first and keep Lita with at least 2 damage soak remaining, or use Elusive/Cunning Distraction before the sacrifice turn. Great Willow is also deadly late because successful treachery tests surge; leave it before agenda 3 if possible.

