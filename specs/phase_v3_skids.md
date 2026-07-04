# Phase V3 — "Skids" O'Toole + rogue package

Prereq: phase V1 merged (V2 not required). Read `specs/phase_v1_investigators.md` and
`specs/phase_v1_report.md` first. Rules authority: RR + vendored JSON; flag conflicts.

Goal: every card in `data/decks/killbray/skids.json` implemented; `--investigator skids`
passes validation and full games are playable.

Already implemented: guardian cards (01016/01018/01024/01025), neutrals, Skids ability +
elder sign (V1).

## Cards

- **01010 On the Lam** (event, 1, Tactic, icons I/A/wild×2): "Fast. Play after your turn
  begins. Until the end of the round, non-[[Elite]] enemies cannot attack you." Fast play
  window: after your turn begins (offer in during-turn fast windows). Effect: a
  round-scoped flag that suppresses ALL attacks against you by non-Elite enemies —
  attacks of opportunity AND enemy-phase attacks (they simply don't attack; they do not
  exhaust from a suppressed attack). Ghoul Priest is Elite and still attacks. Expire at
  end of round.
- **01011 Hospital Debts** (weakness treachery, Task): "Revelation — Put Hospital Debts
  into play in your threat area. [fast]: Move 1 resource from your resource pool to
  Hospital Debts. (Limit twice per round.) Forced — When the game ends, if Hospital
  Debts has fewer than 6 resources on it: You earn 2 fewer experience for this scenario."
  Threat-area permanent; fast ability in all fast windows (limit 2/round via
  state.limits); scoring hook: −2 XP at finalize if <6 resources banked (XP floor 0 per
  existing scoring rules — flag if the engine lacks a floor).
- **01044 Switchblade** (asset, 1, Hand, Weapon/Melee/Illicit, FAST): playing it is a
  fast play (no action, no AoO). "[action]: Fight. If you succeed by 2 or more, this
  attack deals +1 damage."
- **01045 Burglary** (asset, 1, Talent): "[action] Exhaust Burglary: Investigate. If you
  succeed, instead of discovering clues, gain 3 resources." Investigate action via
  activate → it IS an investigate action for AoO purposes? NO — RR: activate abilities
  that initiate investigation are Activate actions with the Investigate designation;
  AoO exemption covers fight/evade/parley/resign only, and *Investigate was never
  exempt* — investigating while engaged provokes AoO already today. Keep behavior
  consistent with the engine's existing treatment of investigate-while-engaged.
  Success replaces clue discovery entirely (no clues, exactly 3 resources).
- **01047 .41 Derringer** (asset, 3, Hand, Firearm, uses 3 ammo): "[action] Spend 1
  ammo: Fight. +2 [combat] for this attack. If you succeed by 2 or more, +1 damage."
  Same shape as the implemented .45 Automatic; succeed-by bonus like Switchblade.
- **01049 Hard Knocks** (asset, 2, Talent): repeatable fast resource pumps for combat
  and agility during a skill test — same pattern as implemented Physical Training
  (01017) / Hyperawareness (01034), pre-reveal only.
- **01050 Elusive** (event, 2, Fast, during your turn): "Disengage from each enemy
  engaged with you and move to a revealed location with no enemies." Fast → no AoO.
  Decision lists eligible destinations (revealed, zero enemies); RAW the move is not
  optional and ignores connections (any revealed empty location); if no eligible
  location exists, disengage still happens, no move. Flag if you read RAW differently.
- **01052 Sneak Attack** (event, 2): "Deal 2 damage to an exhausted enemy at your
  location." Plain event play (an Action to play → PROVOKES AoO from other ready
  engaged enemies). Target choice among exhausted enemies at your location; victory
  display credit flows through the normal defeat path.
- **01053 Opportunist** (skill, wild): "Commit only to a skill test you are performing.
  If you succeed by 3 or more, return Opportunist to your hand after this test instead
  of discarding it." Solo: every test is yours except... commit windows only exist on
  your own tests today — verify and keep. Return-to-hand on succeed-by-3+.

## Tests

1. Skids fuzz N=25 clean; validation passes.
2. On the Lam: AoO suppressed for non-Elite, enemy-phase attacks skipped without
   exhausting the enemy, Ghoul Priest (Elite) still attacks, expires next round.
3. Hospital Debts: fast banking limit 2/round; game-end −2 XP iff <6 banked; score
   floor respected.
4. Burglary: success → +3 resources, 0 clues discovered; exhaust enforced; provokes
   AoO while engaged.
5. Switchblade fast play costs no action; succeed-by-2 → 2 total damage.
6. Elusive: disengages 2 enemies, moves anywhere revealed & empty, no AoO.
7. Sneak Attack: only exhausted enemies targetable; AoO from a second ready enemy.
8. Opportunist: succeed by 3 returns to hand; by 2 discards.
9. Derringer ammo depletion; +2 combat shown in the fight option label (existing
   weapon-label convention).
10. Full suite + fuzz 50 green.

Write `specs/phase_v3_report.md`. Do not git commit.
