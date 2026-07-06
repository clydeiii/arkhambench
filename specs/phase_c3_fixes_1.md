# Phase C3 fixes batch 1 — Devourer Below review findings (+ weakness pool)

Claude's review of phase C3. Fix all; regression test per item; append "Fixes batch 1"
to specs/phase_c3_report.md.

## 1. Wrong Ghouls set in the original encounter deck

CORE_ENCOUNTER_COUNTS uses 01118 ×3 and 01119 ×1 — those are **Flesh-Eater** and
**Icy Ghoul** from The Gathering's own set (qty 1 each in the collection!). The Ghouls
set is **Ghoul Minion 01160 ×3** and **Ravenous Ghoul 01161 ×1** (Grasping Hands 01162
×3 is already right). Fix the codes; ensure both enemies' behaviors work in this
scenario (Ravenous Ghoul's Prey is irrelevant solo). Update the setup-count test to
pin the exact codes, not just totals.

## 2. Encounter digs: missing pre-shuffle + fixed-seed RNG

Agenda 1→2 ("shuffle the encounter discard pile into the encounter deck and discard
cards from the top until a Monster enemy is discarded") and Act 2→3 (same wording, 1
enemy) must BOTH: (a) unconditionally shuffle the discard pile into the deck FIRST —
not only when the deck is empty; (b) use the GAME RNG threaded from the caller —
`spawn_enemy_from_top_until` currently constructs `ArkhamRng(1)`, which makes every
reshuffle produce the same permutation. Thread `rng` through advance_act /
check_agenda_advance callers. Test: seed-varied reshuffle order differs; discard pile
is empty after the dig (all shuffled in, non-matches discarded on top of it).

## 3. Agenda-2 aura applies during agenda 3

`enemy_fight_bonus`/`enemy_evade_bonus` use `stage >= 2`. "Each enemy gets +1 fight
and +1 evade" is printed on agenda 2 (The Ritual Begins) only — it stops when agenda
3 (Vengeance Awaits) becomes current. Fix to stage == 2. Test both transitions.

## 4. R3 weakness is deterministic

`finalize_result` R3 branch calls `gain_madness_weakness(state, events, None, ...)`
→ always Amnesia. Thread the game RNG into finalize (resolve_scenario_choice /
execute_action have it) so R3's Madness weakness is random. Test: different seeds can
yield different weaknesses (or at least assert rng.choice is exercised).

## 5. Umôrdhoth cannot be evaded

Evade options list only `investigator.engaged_enemies`; a Massive enemy is never in
that list, so no evade is ever offered against Umôrdhoth — but per RR, an
investigator may take the evade action against a Massive enemy at their location
(success exhausts it; there is no disengage). Offer Evade for ready Massive enemies
at the investigator's location; on success exhaust only (no disengage, no
Pickpocketing-style disengage hooks breaking); AoO from other engaged enemies applies
as normal for an evade action (none — evade is AoO-safe). Test: Umôrdhoth in play at
investigator's location → Evade offered at difficulty 6 (+vault X in Return); success
exhausts him; massive_attackers excludes him until the end-of-turn ready.

## 6. Dark Cult spawns (original variant)

`encounter_revelation` sends Acolyte (01169) to the FARTHEST empty location and
Wizard of the Order (01170) to Main Path. Both cards read "Spawn – Any empty
location" — same player-choice flow as the Midnight Masks implementation
(`spawn_any_empty_location_enemy`). Disciple of the Devourer / Corpse-Taker
(farthest) are correct as-is. Test both.

## 7. Complete the basic-weakness pool (task #26)

Implement the three unimplemented core basic weaknesses, per their JSON text, as
playable player-deck cards (REGISTRY entries + revelation behavior when drawn):
- **Psychosis (01099)** — Madness treachery.
- **Hypochondria (01100)** — Madness treachery.
- **Stubborn Detective (01103)** — Humanoid Detective enemy weakness (spawns engaged;
  while at your location, treat your location as if it had no clue-related text? —
  implement exactly per JSON text; if the text interacts with an unimplemented system,
  flag it).
Then: every "random basic Madness weakness" effect (Devourer agenda 2, R3) draws
uniformly from the FULL implemented Madness pool: Amnesia 01096, Paranoia 01097,
Psychosis 01099, Hypochondria 01100 (game RNG). Weakness cards gained mid-campaign
must be playable in later scenarios (they already persist via campaign record).
Tests: each new weakness's revelation behavior; the Madness pool contains all 4.

Constraints: keep the suite green (261 now); re-run the C3 fuzz matrix; no commits.
