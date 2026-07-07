# Phase C3 Report

## Implemented

- Replaced the Devourer Below stub with playable `the_devourer_below` and `return_to_the_devourer_below` setup, act/agenda flow, locations, resolutions, and campaign output.
- Reused the Midnight Masks cult machinery for The Devourer's Cult where applicable: Disciple of the Devourer, Mask of Umordhoth, doom-on-enemy math, spawn-location choices, Aloof attachment behavior, and cultist search/draw helpers.
- Added C3 engine hooks for scenario actions, movement/reveal behavior, encounter revelations, agenda advancement, enemy defeat, enemy phase, end-of-round effects, chaos-token aftermath, and skill-test callbacks.
- Wired campaign setup inputs and outputs:
  - cultists got away
  - past midnight
  - Ghoul Priest alive
  - Lita in deck through the campaign deck/standalone flag
  - elderthing persistence through `chaos_bag_additions`
  - `weakness_gained`/`weaknesses_added` persistence
  - C2 killed-flag fixes for no-resolution and Umordhoth's Hunger, while R3 Lita sacrifice survives
- Added mission briefing warnings for doom pressure, no-resolution/resign consequences, got-away cultist spawns, and Return vault scaling.
- Added `tests/test_phase_c3_devourer_below.py` covering the requested setup, graph, location, act/agenda, Umordhoth, Return vault, chaos-token, resolution, and campaign-adapter cases.

## Spec / JSON Notes

- The spec says to follow JSON on conflicts. Core card JSON for `01158` Umordhoth's Wrath has a real revelation effect: willpower(5), and for each point failed choose discard a card or take 1 damage and 1 horror. I implemented that JSON text.
- The Return Corpse-Taker text allows Rivertown or Main Path; this scenario uses Main Path per the C3 spec.

## Validation

- `python3 -m unittest discover -s tests` => 261 tests passing.
- Core fuzz, all clean:
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --investigator roland --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --investigator daisy --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --investigator skids --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --investigator agnes --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --investigator wendy --invariants-only`
- Return fuzz, all clean:
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --investigator roland --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --investigator daisy --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --investigator skids --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --investigator agnes --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --investigator wendy --invariants-only`

No git commit was made.

## Fixes Batch 11 — Showcase-Campaign Audits + hy3 Lane

- Extended cost-at-initiation coverage to the fast-ability path, with Forbidden
  Knowledge paying horror before its secret/resource effect and fast asset plays
  reusing normal slot-overflow enforcement.
- Tightened search presenters so eligible hits must be chosen: Arcane Initiate
  and Research Librarian no longer offer decline/no-hit options when a legal card
  was found.
- Corrected timing reversals: Return Mysterious Gateway's back-side test resolves
  before The Barrier becomes current; committed skill effects resolve during ST.7
  before interrupted action callbacks; Shrivelling symbol horror resolves at
  token reveal; successful On Wings of Darkness is a no-op.
- Corrected rules reversals for Aloof and Umordhoth's Hunger: unengaged Aloof
  enemies must be engaged before fighting, and Hunger kills after discarding the
  investigator's last card.
- Routed substituted-skill investigations through after-fail investigation
  windows, including "Look what I found!" and Rabbit's Foot-style reactions.
- Reused Midnight Masks got-away cultist parley/forced routes inside The Devourer
  Below and pinned the Midnight Masks skull modifier to highest Cultist doom.
- Swept clue-discovery logging and same-named enemy auditability: on-defeat clue
  reactions log only actual discoveries, and enemy attack/move/engage lines now
  include instance ids.

Validation:

- `python3 -m unittest discover -s tests` => 327 tests passing.
- Full six-scenario fuzz matrix, all clean:
  - `python3 -m arkham.fuzz --games 50 --scenario the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --invariants-only`

No git commit was made.

## Fixes Batch 8 — Loop 2 + XP Coverage

- Removed the phantom post-turn fast window and kept remaining fast windows scoped
  to their legal timing.
- Corrected enemy-doom advancement timing: enemy doom waits for the next agenda
  check unless an effect explicitly permits advancement.
- Added missing rules enforcement for Hunting Nightgaunt token doubling, Young
  Deep One engagement horror, weakness filtering for optional discard costs, token
  cleanup on leave play, and effect-based enemy move disengagement.
- Routed weaknesses added to hand through revelation, moved paid plays to limbo
  before AoO with no post-cost refunds, fixed Leo De Luca (0/1) turn-start actions,
  and recomputed static skill modifiers at ST.5.
- Filled the requested display gaps for setup effects, Disciple clue placement,
  token-pool clue gains, and actual-amount Drawn to the Flame logging.
- Added `tests/test_fixes_batch_8.py` covering adjudication entries 34-45; updated
  older regressions and fuzz invariants to reflect the adjudicated limbo/window and
  enemy-doom timing behavior.

Validation:

- `python3 -m unittest discover -s tests` => 290 tests passing.
- Full six-scenario fuzz matrix, all clean:
  - `python3 -m arkham.fuzz --games 50 --scenario the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --invariants-only`

No git commit was made.

Fixes batch 1

## Fixes Batch 7 — Campaign Loop 1

- Fixed campaign-log family clobbering: Midnight Masks fields and Devourer outcome
  fields now apply only from their producing scenario family.
- Corrected display/statics issues: Deduction logs only actual additional clues,
  duplicate Magnifying Glass copies stack, and On Wings of Darkness skips no-op
  Rivertown moves.
- Split scenario chaos-symbol timing: unconditional token effects resolve at
  final-token reveal before success determination; fail-conditional effects remain
  at result time. Agenda advancement caused by reveal-time doom is deferred until
  the active skill test completes.
- Added deferred continuation handling for result-time token aftermath, Wrath
  damage choices, and AoO damage/horror reactions so pending decisions do not drop
  follow-up effects.
- Swept Midnight Masks helpers reused by Devourer so doom/objective/finalize tails
  dispatch through `arkham.effects` and stay scenario-aware.
- Added `tests/test_fixes_batch_7.py` covering adjudication entries 25-33,
  including the Devourer-vs-Midnight agenda leak and six-scenario dispatch canary.

Validation:

- `python3 -m unittest discover -s tests` => 278 tests passing.
- Full six-scenario fuzz matrix, all clean:
  - `python3 -m arkham.fuzz --games 50 --scenario the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --invariants-only`

No git commit was made.

## Fixes Batch 9 — Loop 3

- Extended the batch-6 cost-at-initiation sequencing from card plays to
  action-triggered activation costs, including Midnight Masks cultist-deck,
  Northside, Museum, and paid parley costs plus common asset-use costs. Paid
  activation costs are carried through AoO resumes to prevent double payment.
- Implemented Yithian Observer's attack Forced effect: random hand discard before
  attack damage/horror, or +1 damage/+1 horror for that attack when no discard is
  possible.
- Removed Devourer's explicit no-engage override from Main Path dig/spawn helpers,
  so ready non-Aloof enemies spawning at the investigator's location engage at the
  spawn resolution point.
- Added `tests/test_fixes_batch_9.py` covering adjudication entries 46-48.

Validation:

- `python3 -m unittest discover -s tests` => 295 tests passing.
- Full six-scenario fuzz matrix, all clean:
  - `python3 -m arkham.fuzz --games 50 --scenario the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --invariants-only`

No git commit was made.

## Fixes Batch 10 — Hard-Difficulty Playtest Round

- Corrected On Wings of Darkness ordering: failed-test damage/horror resolves
  before the "Then" disengage and move instructions.
- Routed all investigate-style tests through the scenario investigation-skill hook,
  including Flashlight and Burglary, so Cliffside/Old House/Tangled Thicket
  substitutions apply consistently.
- Changed encounter search helpers to offer a choice when 2+ distinct named
  eligible cards exist, covering Gathering hard-skull Ghoul search, Devourer
  hard-skull Monster search, Mysterious Chanting, Mask of Umordhoth, and Yellow
  Sign's Madness search.
- Implemented Offer of Power (`01178`): choose draw 2 plus 2 agenda doom with
  explicit can-advance, or take 2 horror.
- Added the requested six-scenario no-placeholder sweep over composable encounter
  card codes, including cultist decks, agents sets, Ghoul Priest, and got-away
  spawns. The sweep exposed and fixed two additional missing agent treacheries:
  The Yellow Sign (`01176`) and Dreams of R'lyeh (`01182`).
- Added regression coverage that two engaged Grave-Eater instances both attack in
  an AoO sequence before the interrupted action resumes.
- Changed simultaneous damage+horror defeat to present a physical/mental trauma
  choice and record exactly one trauma, leaving scenario-explicit kill flags
  unchanged.

Validation:

- `python3 -m unittest discover -s tests` => 301 tests passing.
- Full six-scenario fuzz matrix, all clean:
  - `python3 -m arkham.fuzz --games 50 --scenario the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_gathering --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_midnight_masks --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario the_devourer_below --invariants-only`
  - `python3 -m arkham.fuzz --games 50 --scenario return_to_the_devourer_below --invariants-only`

No git commit was made.
