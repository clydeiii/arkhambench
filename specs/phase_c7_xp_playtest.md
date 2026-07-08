# Phase C7 — XP-card playtest program (GPT-5.6 era)

Goal (Clyde, 2026-07-08): playtest the latter two campaign missions (Return to
Midnight Masks, Return to Devourer Below) with realistically-upgraded decks, and
exercise **ALL 32 XP cards** in real play. Drivers: gpt-5.6-luna, gpt-5.6-terra
(via codex), claude-haiku-4.5 (via claude CLI). Auditor: gpt-5.6-sol (transcript +
reasoning audits per scripts/audit_game.py). Final gate: Fable adjudicates into
specs/bug_adjudications.md (ledger currently at 77).

## Ground truth

- XP pool = 32 cards (14 upgrades of implemented titles, codes 500xx; 18 core
  XP cards, codes 010xx). All are registered/enforced; data/decks/coverage/
  holds 5 legal decks covering 32/32 (generator scripts/make_coverage_decks.py).
- Across the 10 real showcase campaigns, agents only ever PURCHASED 11 of 32.
  Never bought: Extra Ammunition, Police Badge, Beat Cop(2), Shotgun, Cryptic
  Research, Cat Burglar, Sure Gamble, Hot Streak(4), Mind Wipe(1), Book of
  Shadows, Grotesque Statue, Aquinnah, Will to Survive, Bulletproof Vest, Elder
  Sign Amulet, Hyperawareness(2), Barricade(3), Hard Knocks(2), Hot Streak(2),
  Mind Wipe(3), Rabbit's Foot(3).
- "In deck" ≠ "playtested". A card counts as EXERCISED only when its effect
  actually resolves in a game (played / triggered / committed, as appropriate
  to its type). Measure from log.md + log.jsonl, not decklists.

## Lane 1 — realistic upgraded decks (mission realism)

Use REAL upgrade decisions, not synthetic ones: the 10 showcase campaigns
(campaigns/show-{fable,gpt}-*/decks/deck-N.json) give per-investigator decks as
they actually entered MM (deck-2) and DB (deck-3). Pick per investigator the
higher-scoring campaign's snapshots → 5 MM decks + 5 DB decks.

- Runner: scripts/bench.py one-off games (`--scenario` MM/DB, `--deck <snapshot>`)
  or direct `./ahlcg new --deck`; standard difficulty; fresh seeds 11001+.
- Drivers rotate: luna, terra, haiku each play ≥3 MM + ≥3 DB (one per a sample
  of investigators) = 18+ games.
- Sol audits every transcript (rules audit + reasoning audit); Fable gates.

## Lane 2 — coverage decks (exercise the other 21)

data/decks/coverage/*.json already packs all 32 XP cards into 5 legal decks.

- Each coverage deck plays MM and DB once per driver tier (haiku for volume,
  luna/terra for quality) with a PROMPT DIRECTIVE appended (bench.py
  --prompt-note): "Coverage directive: this deck exists to exercise its XP
  cards. Over the game, PLAY or trigger every XP card in your deck at least
  once when legal, even when suboptimal — but never illegally. XP cards are
  worth more than score this run."
- After each wave, run the coverage tracker (below); rerun only decks holding
  still-unexercised cards, with the directive narrowed to name those cards.

## Coverage tracker (build first — small script)

scripts/xp_coverage.py: scan a set of run dirs; for each XP card code, classify
EXERCISED (asset entered play / event resolved / skill committed to a test /
triggered ability used — from log.jsonl event types) vs DORMANT (in deck, never
resolved). Output a 32-row markdown table + exit-nonzero list of dormant cards.
Also count triggered-ability uses separately for permanents (e.g. Police Badge's
exhaust ability, Book of Shadows' action) — entering play alone doesn't test the
ability text.

## Lane 3 — corner-trigger probes (cards agent play can't reliably reach)

Some card texts only fire in states agents rarely produce. For each, one
deterministic Game-API probe test (tests/test_xp_probes.py), like the batch-7+
regression style. Known candidates:
- Close Call (evader-return-to-encounter-deck timing), Sure Gamble (token
  reveal window math), Will to Survive (turn-long no-token commitment),
  Aquinnah (redirect while engaged by 2+), Bulletproof Vest/Elder Sign Amulet
  (soak-at-defeat ordering + ST.5 recompute), Grotesque Statue (draw-2-pick-1
  bag interaction), Cryptic Research (fast draw window at another investigator?
  solo = self), Shotgun (variable-damage math at min/max), Mind Wipe(3) (aloof/
  elite restrictions), Extra Ammunition (attach-target legality).
- Each probe asserts the RR-correct behavior; failures go to the ledger before
  any agent lane runs (cheap bugs first).

## Sequencing

1. Build scripts/xp_coverage.py + tests/test_xp_probes.py skeleton (codex spec;
   Fable reviews). Run probes → fix batch if needed.
2. Lane 2 haiku wave (10 games: 5 coverage decks × MM+DB) — volume first, it
   catches the easy 80%.
3. Lane 1 realistic wave with luna/terra (+haiku fill) — 18 games.
4. Sol audit pass over ALL transcripts (rules + reasoning), Fable gate, fix
   batch, regression tests.
5. Coverage report: 32/32 exercised or explicit per-card disposition (e.g.
   "unreachable in solo play — probe-only"). Fold summary into README's
   playtest section.

## Ops notes

- codex model flags: `-m gpt-5.6-luna` / `-m gpt-5.6-terra` / auditor
  `-m gpt-5.6-sol` (verify exact IDs on release day; websearch if 400s).
- Confirmations ON for playtest lanes (they're a rules surface too — C6).
- AHLCG_RUN pinning for any parallel lanes; never edit runner scripts
  mid-execution; nohup+disown for codex background waves.
- hy3 lesson applied: mission.md now warns compaction must preserve lessons;
  notebook archives readable via `./ahlcg note archive`.
