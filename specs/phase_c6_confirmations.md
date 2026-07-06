# Phase C6 — confirmation prompts for likely-mistake actions

Motivation (Clyde, 2026-07-06): agents repeatedly take actions that cannot help or
that hurt them without realizing it — investigating a location with no clues
(Fable's "re-earnable clue" episode), or provoking attacks of opportunity they
didn't account for (the single most common death cause since the first Sonnet
demos). Digital adaptations of the game confirm such actions; we should too.

## Mechanics

When the investigator picks a flagged action, do NOT execute it. Present a
confirmation decision first; the action is only initiated (action spent, costs
paid, AoOs made) on "yes". "Cancel" returns to the action menu with nothing spent.

Trigger 1 — pointless investigation: the basic Investigate action at a location
with 0 clues. Prompt: "«Location» has no clues — investigating discovers nothing.
Proceed?" (Card-ability investigations like Burglary/Flashlight follow their own
value and are NOT gated — Burglary wants resources, not clues... actually gate
Flashlight the same way when the location has 0 clues, since its only output is
discovery; do NOT gate Burglary, whose success yields resources.)

Trigger 2 — provoking attacks of opportunity: any action that will provoke >=1 AoO
(non-exempt action while engaged with ready, non-exhausted enemies, including
Massive presence). Prompt lists each attacker with its damage/horror: "This will
provoke: Ghoul Priest (2 dmg/2 hor)[, ...]. Proceed?" Compute attackers with the
same logic the AoO queue uses — no drift.

Rules of the feature:
- Confirmations are UI-layer: they must not alter rules outcomes, timing, or costs.
  No game effect may trigger between confirm and execution (present-confirm ->
  execute synchronously on yes).
- Both options carry through the normal decision/--why machinery (agents' stated
  reasons for proceeding anyway are gold for reasoning audits).
- Log compactly: one `confirmation` event when shown, choice recorded as usual.
- Config: on by default. `ahlcg new --no-confirmations` disables (persisted in
  state); `arkham/fuzz.py` builds games with confirmations DISABLED (random walks
  would just coin-flip them; invariant density matters more).
- The viewer needs no changes (confirmations render as ordinary decisions).

## Docs

docs_agent/playing_guide.md: short note that the engine asks for confirmation on
zero-value investigations and AoO-provoking actions, that "yes" is sometimes right
(e.g. eating an AoO to play a critical asset), and that --why on the confirm is
encouraged.

## Tests

1. Investigate at 0-clue location -> confirmation; cancel -> action NOT spent, menu
   again; yes -> normal test starts. At >=1 clue -> no confirmation.
2. Flashlight at 0-clue location gated; Burglary never gated.
3. AoO confirm: engaged ready enemy + play action -> confirmation listing the
   enemy; yes -> costs paid at initiation, AoO fires, action resolves (order per
   the batch-9 rules); cancel -> nothing spent, no AoO. Exempt actions
   (fight/evade/parley/resign) never confirm. Exhausted/aloof enemies don't count.
4. --no-confirmations: neither trigger fires; fuzz path uses it.
5. Both prompts' decisions appear in log.md with --why capture.

Keep the suite green (305 now). Do NOT git commit.
