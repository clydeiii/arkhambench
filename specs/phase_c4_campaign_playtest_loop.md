# Phase C4 — Campaign playtest loop (Haiku plays / GPT-5.5 audits / Fable confirms)

Not a codex build spec (Claude implements the harness) — this documents the loop design
so runs are reproducible and the pattern survives context loss.

## Roles

- **Player**: `claude-haiku-4-5` via claude CLI — cheap, produces full campaign
  transcripts. One campaign = Gathering → upgrade → Midnight Masks → upgrade →
  Devourer Below, all Return variants, standard difficulty (until phase C5 hard runs).
- **Auditor**: GPT-5.5 via `codex exec` (read-only) — judge-style transcript audit of
  each scenario's log.md + campaign.json + the upgrade-phase decisions. Fallback if
  codex credits die mid-loop: `claude --model claude-opus-4-8`. (Ping Clyde on codex
  outage: he refills.)
- **Adjudicator**: Fable 5 (this session) — verifies each audit finding against engine
  code + rules PDFs; ledger in specs/bug_adjudications.md (continue numbering); fixes
  via codex fix-batch specs; regression test per confirmed bug.

## Harness

- `scripts/campaign_demo.sh <agent> <name> [seed]` — drives one full campaign in a
  campaigns/<name> dir: repeatedly invokes the agent with the campaign CLI docs
  (docs_agent/campaign_guide.md), resume-hardened like bench.py (skip finished
  scenarios via campaign.json phase; agent must run `./ahlcg campaign record` +
  upgrade phase itself — that IS part of the benchmark surface being tested).
- Audit prompts per scenario (extend scripts/audit_game.py):
  - `--campaign <dir>` mode: audits scenario logs in order, PLUS a new
    **upgrade-phase audit**: given campaign.json history and the docs, check every
    purchase's legality/cost math independently (class access, level caps, 2-per-title,
    deck size, XP arithmetic) and cross-scenario continuity (trauma carryover, Lita,
    weaknesses persisting, chaos-bag additions, got-away lists feeding DB spawns/doom).
  - Auditors do NOT read arkham/, tests/, or specs/ — transcript + docs_agent + card
    lookups only.
- Known-adjudication suppression: embed the current ledger's not-a-bug list in the
  audit prompt (same as audit passes 1–2).

## Loop schedule (per Clyde's goal: "a few times")

Round k: 2 Haiku campaigns (fresh seeds) → audits (GPT-5.5) → Fable adjudication →
codex fix batch (if any confirmed) → regression tests → next round. Stop when a round
produces zero confirmed engine defects (or after 3 rounds, whichever first), then move
to hard-difficulty implementation + the phase C5 hard-mode loop (fresh seeds).

## Seeds

Campaign master seeds: round 1 = 9001, 9002; round 2 = 9003, 9004; round 3 = 9005,
9006. Hard-mode round (C5): 9101, 9102 (+9103, 9104 if a second hard round needed).
Investigators: rotate roland, agnes (r1); daisy, wendy (r2); skids + best-coverage
pick (r3) so all five appear across the loop.
