## 2026-07-27T16:24:28+00:00
- Round: 12
- Phase: Mythos
- Description: Guard Dog ping triggered TWICE on a single enemy attack (R11 enemy phase, Corpse-Hungry Ghoul attack): 'Guard Dog dealt 1 damage to the attacking enemy' appeared two times for one attack, dealing 2 total. Card text: 'After an enemy attack deals damage to Guard Dog: Deal 1 damage to the attacking enemy' — should trigger once per attack. Same bug as reported in an earlier session; still live.

## 2026-07-27T16:47:34+00:00
- Round: 14
- Phase: Investigation
- Description: Final XP accounting looks wrong. Game-26 (Roland, return_to_the_gathering) ended R1 burn with victory display = {Corpse-Hungry Ghoul (ec0029), Ghoul Priest, Attic}. Final XP = 6. Decomposition: Priest 2 + original Attic 2 + R1 burn bonus 2 = 6, which leaves Corpse-Hungry Ghoul contributing 0 XP despite being in the victory display and docs_agent/scenario_reference.md listing it as 'Victory 1'. Either CHG's Victory keyword is missing in the card data, or the XP tally is dropping it. (Side note, possibly intended: Grave-Eater x3 and Acolyte of Umordhoth/Silver Twilight Acolyte kills did NOT enter the victory display at all — consistent with them having no Victory keyword, but flagging in case.)

