# Rules-conformance audit — engine vs Rules Reference

Authority: `docs_agent/rules_reference.md` (RR). Every item below carries the governing RR
quote. Where the engine (or DESIGN.md) disagrees with the RR, **the RR wins** — DESIGN.md
has already been corrected for Part 1 items. If you find the engine deviating on a Part 2
item, fix it and flag it in the report. If you believe an RR quote is being misread, flag
it in the report instead of implementing your own interpretation.

## Part 1 — Known deviations to FIX (each with a regression test)

### 1.1 Attack of opportunity exemption is by ACTION TYPE, not per-target enemy
RR: "Each time an investigator is engaged with one or more ready enemies and takes an
action other than to **fight**, to **evade**, or to activate a **parley** or **resign**
ability, each of those enemies makes an attack of opportunity against the investigator,
in the order of the investigator's choosing."

Fighting enemy A does NOT provoke enemy B. Evading enemy A does NOT provoke enemy B.
Remove the per-target exemption logic (`targeted_aoo_exempt_enemy`); the safe action set
is: fight, asset_fight (bold Fight designator), evade, parley (Lita), resign, plus
non-actions (advance_act, pass) and fast/free abilities (RR Fast: "Because fast cards do
not cost actions to play, they do not provoke attacks of opportunity"). Engage,
investigate (incl. Flashlight — Investigate designator is NOT exempt), move, draw,
resource, play, and other activates all provoke from EVERY engaged ready enemy.
Note this REVERSES the fix-batch-1 change (that spec was wrong).

### 1.2 AoO timing: after costs, before effects
RR: "An attack of opportunity is made immediately after all costs of initiating the
action that provoked the attack have been paid, but before the application of that
action's effect upon the game state."
Current engine makes AoOs before spending the action cost. Reorder: pay cost →
AoOs → effect. (Keep: one AoO per enemy per action even if the action costs 2.)

### 1.3 Autofail sets total skill value to 0
RR ST.6: "If an investigator automatically fails at a test via a card ability or
revealing the [auto_fail] symbol, his or her total skill value for that test is
considered 0." Failure margin must be computed from value 0 — e.g. Grasping Hands
(Agility 3) + autofail = take 3 damage regardless of committed icons. Fix the margin
computation and the log line (currently shows "failure (autofail) by 0" style).

### 1.4 NO player window after the chaos token reveal
RR Skill Test Timing chart: player windows exist only between ST.1→ST.2 and ST.2→ST.3.
There is no window during/after ST.3. Remove the post-reveal fast-ability window
entirely; Physical Training / Hyperawareness boosts are usable only in the pre-reveal
windows (i.e. the commit window we present). This makes tests genuinely risky again.
Update `docs_agent/playing_guide.md` ("sometimes a post-token window" sentence) to match.

### 1.5 Enemies exhaust after their enemy-phase attack
RR 3.3: "Upon completion of dealing the attack (and all abilities triggered by the
attack), exhaust the enemy." (AoO: "An enemy does not exhaust while making an attack of
opportunity." Retaliate: "An enemy does not exhaust after performing a retaliate
attack.") Only the enemy-phase framework attack exhausts.

### 1.6 Attacked investigator chooses enemy attack order (and AoO order)
RR 3.3: "If an investigator is engaged with multiple enemies, resolve their attacks in
the order of the attacked investigator's choosing." AoO: "...in the order of the
investigator's choosing." When 2+ enemies would attack in the enemy phase (or make AoOs),
present a decision for the order (one "attack next: X" choice at a time; skip the
decision when only one enemy).

### 1.7 Doom / agenda-advance semantics
RR 1.3: "Compare the total number of doom in play (on the current agenda and on each
other card in play) with the doom threshold... When the agenda deck advances, remove ALL
doom from play." And: "Unless a card otherwise specifies that it can advance the agenda,
this is the only time at which the agenda can advance."
Fixes: (a) on advance, remove all doom from every card in play (enemies, assets,
attachments), not just the agenda; (b) doom placement does NOT trigger an advance check
unless the source permits it — mythos step 1.3 checks; Ancient Evils checks ("This
effect can cause the current agenda to advance"); Silver Twilight Acolyte's forced doom
and Agenda 3's end-of-round doom do NOT check (they wait for the next mythos 1.3).
`place_doom` needs a `can_advance` flag (default False) with callers updated.

### 1.8 Readied enemies engage immediately
RR Enemy Engagement: "An exhausted unengaged enemy does not engage, but if an exhausted
enemy at the same location as an investigator becomes ready, it engages as soon as it is
readied." The upkeep ready step (4.3) must run an engagement check after readying.

## Part 2 — Conformance checklist to VERIFY (add a focused test per item unless one
already exists; fix on failure and note in report)

Phase framework (RR Phase Sequence timing chart + Framework Event Details):
- 2.1 Mythos skipped entirely in round 1; order in later rounds: doom → threshold check →
  encounter draw (drawn enemy with no spawn instruction spawns ENGAGED with drawer).
- 2.2 Upkeep order: reset actions → ready each exhausted card (then engagement check per
  1.8) → draw 1 → gain 1 resource → check hand size (max 8, choose & discard down).
- 2.3 Round-1 sequence: investigation is the first phase played.
- 2.4 "Until end of round" effects expire at 4.6 (Dissonant Voices discards at end of
  round; Mind over Matter lasts until end of round).

Skill tests (RR ST.1–ST.8):
- 2.5 Commit rules: performing investigator commits any number of cards bearing a
  matching or wild icon; icons add +1 each; committing pays no resource cost; cards
  without an appropriate icon cannot be committed; committed cards discard at ST.8.
- 2.6 Ties succeed (value ≥ difficulty); skill value floor 0; difficulty floor 0
  (Flashlight −2 on shroud 1 → difficulty 0).
- 2.7 Token effects: Easy/Standard scenario card — skull −X (X = Ghouls at your
  location), cultist −1 + 1 horror on fail, tablet −2 + 1 damage if Ghoul at your
  location; Hard/Expert versions per scenario card back (verify the "cultist: reveal
  another token" recursion works on hard/expert); elder sign = Roland +1 per clue on his
  location; autofail per 1.3 above.
- 2.8 ST.7: "for this test" boosts expire at test end; Vicious Blow (+1 dmg on successful
  attack), Deduction (+1 clue on successful investigate of your location), Guts/Manual
  Dexterity (draw 1 on success, max 1 committed per test — card text limit).

Enemies (RR Hunter / Enemy Engagement / Retaliate / AoO):
- 2.9 Hunter: only ready+unengaged hunters move, one connection along shortest path
  toward nearest investigator; blocked move (Barricade, non-Elite only — Ghoul Priest is
  Elite and ignores Barricade) → does not move; enemies at an investigator's location do
  not move; engagement on arrival.
- 2.10 Engagement: ready unengaged enemy engages when it spawns at / moves into / is
  moved into the investigator's location; engaged enemies move WITH the investigator;
  Engage is a valid action (and provokes AoOs from other engaged enemies per 1.1).
- 2.11 Evade: success exhausts AND disengages; failed evade = no AoO, no other penalty
  (Gathering pool has no Alert); evading is only possible against enemies engaged with
  you.
- 2.12 Retaliate (Ghoul Priest): fires after a FAILED fight test against it while it is
  READY; retaliate attack does not exhaust it; it fires even during your own turn attacks
  but never when the priest is exhausted.
- 2.13 Enemy defeat: damage ≥ health → victory display if Victory X else encounter
  discard; defeat reactions window (Roland once/round, Evidence!) — both usable off one
  kill; kills by any source you control (Guard Dog counter, Beat Cop ping, Dynamite)
  count as "you defeated".

Damage/horror/defeat:
- 2.14 Attack damage/horror dealt simultaneously; assignment among investigator +
  eligible in-play assets with health/sanity; an asset cannot be assigned more
  damage/horror than its remaining capacity... (RR "Dealing Damage/Horror": verify each
  point assigned to a card with remaining capacity only); asset destroyed at
  damage ≥ health or horror ≥ sanity.
- 2.15 Investigator defeat: damage ≥ 9 or horror ≥ 5 → defeated; physical trauma if by
  damage, mental if by horror (both if both simultaneously); trauma exactly once;
  Gathering: defeat = no_resolution outcome with Cover Up game-end check applied.
- 2.16 Empty player deck: shuffle discard into deck, draw, then take 1 horror upon
  completion of the entire draw (RR "Empty Deck"); empty encounter deck: shuffle
  discard, no horror.

Cards/economy:
- 2.17 Fast: fast assets playable during any player window on your turn; fast events per
  their instructions; fast plays and [free] abilities never provoke AoOs; playing fast
  cards costs resources but no action.
- 2.18 Slots: 2 hands, 1 ally; playing over a full slot forces discard of the occupant
  (player choice); Lita is slotless (story ally).
- 2.19 Uses: ammo/supplies decrement, gate the ability at 0; First Aid discards itself
  when empty; Flashlight persists at 0 supplies.
- 2.20 Unique (✦): a second copy of a unique card cannot enter play while one is in play
  (pool check: Beat Cop/Milan etc. are 1-ofs, but verify the rule exists for Lita).
- 2.21 Hand size checked only at upkeep 4.5.
- 2.22 Weakness draws (Cover Up, Silver Twilight Acolyte): revelation resolves
  immediately whenever drawn (upkeep, draw action, Old Book search? — searches do NOT
  trigger revelation unless card says drawn; Old Book of Lore "draws it" = a draw →
  weakness revelation DOES resolve; verify).
- 2.23 Setup: 5 resources, opening hand 5 with weakness ignore/set-aside/replace,
  single mulligan of any number of cards, set-aside cards shuffled back after.

Scenario (campaign guide, already encoded — verify unchanged by fixes):
- 2.24 Act 1 advance (2 clues, spend during your turn, free), act 2 objective at round
  end in Hallway (3 clues), act 3 objective on Ghoul Priest defeat → R1/R2 choice;
  agenda thresholds 3/7/10 with correct flip effects; Parlor barrier until act 3;
  resolutions/XP/score per DESIGN §12–13 (score = max(0, XP − trauma + 3·Lita); R2 does
  NOT earn Lita).

## Deliverables
- All Part 1 fixes with regression tests; Part 2 verified (tests added where missing).
- `python3 -m unittest discover -s tests` green; `python3 -m arkham.fuzz --games 200` clean.
- `specs/rules_audit_report.md`: per-item PASS / FIXED / FLAGGED status with one-line
  notes. No git commit (sandbox).
