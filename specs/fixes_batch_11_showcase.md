# Fixes batch 11 — showcase-campaign audits + hy3 lane (ledger 56, 60–62, 64–71)

Evidence: specs/bug_adjudications.md. One regression test per item; suite green (312
now); 6-scenario fuzz matrix; FIXED ledger notes; batch-11 section in
specs/phase_c3_report.md. NOTE: two items reverse earlier Claude adjudications —
existing tests asserting the old behavior must be updated (66, 67).

1. (60) Fast triggered abilities pay costs at initiation (Forbidden Knowledge's
   1 horror before the secret->resource effect) — extend the cost-at-initiation
   machinery to the fast-ability path; sweep other fast abilities with costs
   (Physical Training-style pays resources — verify ordering there too).
2. (61) Searches with >=1 eligible candidate must not offer a decline option
   (Arcane Initiate, Old Book of Lore, Ma's Boarding House, Miskatonic search,
   Encyclopedia-style — sweep all search-choice presenters). Decline remains only
   when zero eligible cards were found.
3. (62) Act/agenda advancement: the back-side instructions (including tests and
   their consequences) fully resolve BEFORE the next act/agenda becomes current
   (Mysterious Gateway; sweep other act backs with tests).
4. (64) "Look what I found!" (and all after-fail-while-investigating windows:
   Rabbit's Foot etc.) must trigger on investigations using substituted skills
   (Cliffside agility / Old House willpower / Tangled Thicket combat). Root-cause:
   likely the trigger filters on intellect or the source label.
5. (65) Fast-asset plays enforce slot capacity exactly like normal plays
   (simultaneous choose-and-discard when exceeding hand/arcane/ally/body slots).
6. (66) Aloof: an investigator CANNOT attack an aloof enemy while it is unengaged
   (RR). Offer an Engage basic action for aloof enemies at the location; fights
   only after engagement. Update the C1-era test that asserted the opposite.
7. (67) Umôrdhoth's Hunger: resolve the random discard FIRST, then kill each
   investigator with an empty hand (discard-to-empty kills). Update the C3-era
   test asserting check-before-discard.
8. (68) Committed skill-card success/failure effects (Perception, Overpower,
   Guts...) resolve during ST.7, before any interrupted/provoking action
   continues (Twisting Paths move resume came first).
9. (69) Shrivelling's "if symbol revealed, take 1 horror" resolves at token
   reveal (with reaction windows — Agnes's ping — evaluated at that point), not
   after attack results. Same reveal-time machinery as batch 7 item 4.
10. (70) The Devourer Below offers the unique got-away cultists' printed
    parley/forced routes (Alma Hill, Jeremiah, Herman, Peter, Victoria, Ruth,
    Billy) by reusing the MM builders in DB's action options and hooks.
11. (71) Wendy's Amulet elder-sign auto-success prints as automatic success
    (difficulty treated as 0) in the skill-test math line.
12. (56) Sweep ALL clue-discovery logging paths (on-defeat reactions, Drawn to
    the Flame, any discover effect) to log only actual amounts discovered and the
    blocked message when prevented — generalize the entry-26 fix.

## (placeholder) hy3 swarm confirmations

Appended after GPT-5.5 adjudication of the swarm's bug reports.

## hy3 swarm confirmations (ledger 74-76)

13. (74) Midnight Masks standard skull: X = highest doom among Cultist enemies in
    play at reveal time. Code-check the scan (engaged cultists? attachment doom?)
    against the transcript (Peter Warren 2 doom -> -1 applied); fix and pin a test.
14. (75) On Wings of Darkness: on a SUCCESSFUL test, nothing happens (no damage,
    no disengage, no move). RR "Then" — pre-then failure clause must resolve for
    the post-then move. Update the batch-7-era tests and entry-29 no-op logic.
15. (76) Enemy-phase and AoO attack queues: verify only ENGAGED (or Massive
    co-located) enemies can attack; add instance-id disambiguation to enemy
    attack/move log lines (two same-named enemies were indistinguishable in the
    audit trail). Test: engaged + unengaged same-code enemies -> exactly one
    attack, from the engaged instance, and the log identifies it.
