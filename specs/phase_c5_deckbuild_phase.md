# Phase C5 — campaign-start deckbuilding (free 0-XP swaps)

Motivation (Clyde, 2026-07-06): agents burn scarce XP on 1-XP purchases of level-0
cards ("sidegrading" — Fable 5 did it 17 times across 5 showcase campaigns). Real
players build their deck before a campaign; killbray's lists are a netdeck default.
Give agents a free deckbuilding window at CAMPAIGN START only.

## Mechanics

- New campaign phase `deckbuild`, entered by `./ahlcg campaign new` (before the first
  `campaign next`). NOT offered between scenarios (mid-campaign changes stay XP-only).
- `./ahlcg deckbuild options` — list every legal 0-XP swap-in for the investigator:
  implemented level-0 player cards (REGISTRY-gated, class/level access per
  CLASS_ACCESS, no signatures/weaknesses/story assets), annotated with how many
  copies the deck currently has (respect the 2-per-title cap counting ALL levels).
  Also print the current deck list so the agent can pick swap-outs.
- `./ahlcg deckbuild swap --in <code> --out <code>` — free, repeatable. The out-card
  must be a non-protected level-0 card currently in the deck (protecting signatures,
  weaknesses, story assets; also protect level>0 cards — none exist at campaign
  start, but guard anyway). Validate with the existing upgrade.validate_deck after
  each swap (final=False) and at done (final=True: exactly 30).
- `./ahlcg deckbuild done` — lock the deck, phase -> scenario.
- `./ahlcg campaign next` while phase == deckbuild: auto-run `deckbuild done` (agents
  that don't care skip the phase without friction).
- Record the swaps in campaign.json as `deckbuild_swaps: [{"in": code, "out": code}]`
  so exports/audits can show the pre-campaign build. scripts/export_campaign.py will
  pick this up separately (not your concern beyond writing the field).

## Docs

- docs_agent/campaign_guide.md: new "Before the first scenario" section — explain the
  free window, that mid-campaign level-0 additions cost 1 XP (per the RR), and that
  sidegrading during upgrade phases is usually XP-inefficient.
- While you're in the guide: add one explicit rules warning to the clue section of
  docs_agent/playing_guide.md if not already present: "Spent clues go to the token
  pool. They NEVER return to the location. Investigating a 0-clue location discovers
  nothing." (Motivated by a Fable transcript acting on the opposite belief.)

## Tests

1. Swap legality: in-card class/level gating (wendy cannot swap in Shrivelling),
   2-per-title cap (third copy rejected), protected out-cards rejected (signature,
   weakness, Lita), unknown codes rejected.
2. Free-ness: xp_unspent unchanged by any number of swaps.
3. Lifecycle: new -> deckbuild phase; swaps apply to deck-1.json materialization;
   done -> scenario; `campaign next` from deckbuild auto-locks; deckbuild commands
   rejected after the campaign starts and during upgrade phases.
4. deckbuild_swaps recorded.

Keep the suite green (301 now). Update specs/phase_c2_report.md with a C5 section.
Do NOT git commit.
