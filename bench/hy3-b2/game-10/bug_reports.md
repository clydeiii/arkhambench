## 2026-07-08T04:30:10+00:00
- Round: 8
- Phase: Investigation
- Description: Menu mislabels actions: when the action menu lists 'Evade <enemy>' as option N (e.g. 4) and 'Fight <enemy>' as N-1 (e.g. 3), issuing 'do N' executes FIGHT, not Evade. Reproduced twice (R7 and R8) — 'do 4' ran Fight Grave-Eater both times although the displayed menu had Evade at 4. This caused me to waste actions and take unchosen attacks. Need the displayed option number to match the executed action.

## 2026-07-08T04:33:28+00:00
- Round: 8
- Phase: Enemy
- Description: Defeat rule error: Wendy was at exactly 7 damage on 7 health (dmg7/7) after taking 1 damage from Grave-Eater's attack, and the engine declared 'GAME OVER: defeated'. Rules: a card is defeated only when it has MORE damage than health; at damage == health the investigator is alive (just at the brink). The game should have continued (and the attacker's damage would then push to 8, defeating). Premature game over.

## 2026-07-08T04:33:58+00:00
- Round: 8
- Phase: Enemy
- Description: DECISION-WINDOW DESYNC / PHANTOM COMMIT WINDOW (caused my death, R8). After a failed skill test, the engine re-presents a stale commit window for the SAME test. At R8, a failed 'Fight Swarm of Rats' showed '1 action left' with a normal action menu (Evade Grave-Eater = option 6), but sending 'do 6' was rejected as invalid because the real pending decision was a re-shown 'Commit cards to Fight Swarm of Rats (combat vs 1). 1. Done' window. This blocked me from evading the ready+engaged Grave-Eater, so in the enemy phase both enemies hit and I reached 7 damage (engine treats >=7 as defeated) -> GAME OVER. Also observed at R6/R7: a command sent during a turn-end auto-advance (my redraw 'do 3' on the Attic -4 reaction) got applied to the NEXT turn's investigation menu, initiating an unintended 'Fight Grave-Eater'. Consequence: commands routed to stale/phantom prompts, actions land on wrong decisions. Expected: each command applies to the currently displayed decision only, and failed-test commit windows must not re-appear after the test resolved.

