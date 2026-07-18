The audit is complete. All the mechanical dimensions check out, but there is one major data-integrity finding plus a corroborating harness finding.

---

## Finding 1 — Scenario 1's recorded result is another campaign's game (cross-lane run contamination)

**Campaign step:** scenario 1 record (`campaign.json` scenarios[0])

`campaigns/show-terra-skids/campaign.json` records scenario 1 from `run: .../show-luna-skids/runs/c-show-luna-skids-1` — a run belonging to the **luna** model's campaign. The evidence chain:

- Terra's own scenario-1 run dir (`runs/c-show-terra-skids-1`) exists but has **no result.json**, `meta.json` status `in_progress`, and its log ends at the very first decision (the opening-hand mulligan). It was created 2026-07-10T18:27:19; terra's run-2 was created at 18:28:45 — so `campaign record` ran ~86 seconds after the scenario-1 game was created, consuming luna's completed result instead of a terra game.
- The recorded values (xp 2, trauma mental 1, score 1, `no_resolution`, lita earned, house standing, ghoul priest alive) match `show-luna-skids/runs/c-show-luna-skids-1/result.json` exactly, and that same run is also legitimately recorded as luna's scenario 1 — the one game is counted in **both** models' campaigns.
- The contaminating game was played with **luna's deck-1** (Switchblade/Pickpocketing-line build per luna's deckbuild swaps), which differs materially from terra's deck-1 (Machete/Evidence!/Knife/Perception build) — so it isn't even a same-inputs replay; the two campaigns share only the seed (9403).

Downstream, everything scenario-1-derived in this campaign (2 XP that paid for the Beat Cop upgrade, 1 mental trauma carried as starting horror, house-standing → Your House start in MM, Lita earned/in deck, Ghoul Priest alive → shuffled into MM) is internally consistent but sourced from a game the terra model never played. For the benchmark this means terra's campaign score double-counts a luna game and terra's actual scenario-1 play is missing entirely.

Blast radius (checked all five terra campaigns): `show-terra-roland` has the same defect — its scenario 1 points at `show-sol-roland/runs/c-show-sol-roland-1`. Agnes, daisy, and wendy are clean.

Root cause is the ledger-108 family (`.current_run` cross-lane race). I'm not re-reporting that adjudicated bug itself — the finding is that these runs were recorded **today (2026-07-10)**, i.e. after the ledger-108 fix landed, so either the show/b4 driver's record call doesn't pass `AHLCG_RUN`/`--run`, or another unguarded path remains. The affected scenario-1 records (terra-skids, terra-roland) need rerunning to be trustworthy.

## Finding 2 — Foreign agent's note misfiled into this campaign's run-3 transcript

**Campaign step:** scenario 3 transcript (`runs/c-show-terra-skids-3/log.md`, R1)

Run 3's log contains, mid-setup, a note written by an agent playing an **Agnes** campaign: *"Campaign record without an explicit run path targets stale .current_run from another campaign (show-terra-skids-3) instead of the active Agnes campaign run…"*. The note both describes the live race and demonstrates it — the agent's `note` command followed the same stale pointer and appended into terra-skids-3's transcript. This contaminates the transcript (a scenario audit could misread it as this game's reasoning) and confirms Finding 1's race was active during this wave for commands invoked without `--run`.

---

## Dimensions verified clean

**XP ledger.** The Gathering `no_resolution` = 0 VP + 2 insight = 2 XP (per adjudication 2); upgrade 1 = Beat Cop(0)→Beat Cop(2) same-title replace, cost 2 (level difference); unspent 2−2=0, matching run-2's meta snapshot. MM R2 = victory display 1 (Billy Cooper interrogated) = 1 XP; upgrade 2 = Dodge (new level-0) = max(1,0) = 1 XP with a Knife removed to hold 30; unspent 0, matching run-3's meta. DB: killed, 0 VP, 0 XP (the Hospital Debts −2 penalty is recorded but correctly floors at 0, never going negative). Totals: earned 3 = 2+1+0, spent 3, unspent 0; non-negative at every step. Campaign score 2 = (2−1)+(1−0)+0 per the score formula.

**Deck legality.** All three decks materialize exactly 30 counted cards (On the Lam + Hospital Debts signatures, Mob Enforcer weakness, and Lita story asset correctly excluded). Beat Cop totals 2 copies across levels 0+2 — at the title cap, legal. Beat Cop(2) sits at Skids's Guardian 0–2 access limit; all other cards are Rogue/Guardian level-0 or Neutral. Signatures present in every deck; Mob Enforcer never removed; Lita (01117) appears in deck-2 only after being earned in scenario 1 and persists to deck-3; Paranoia (01097), gained during scenario 3, lands in the final campaign-deck weakness list (no later deck exists to require it, so deck-3's lacking it is correct).

**Continuity.** Trauma: 1 mental after scenario 1 → both run-2 and run-3 open at `hor1/6`; scenario 2 delta 0/0 (R2, not defeated); scenario 3 delta 1 mental (horror 8 ≥ sanity 6, single trauma type per the batch-10 rule) → final 2/0. Log flow: house standing → run 2 starts at **Your House**; Ghoul Priest alive → verified shuffled into Return MM by card accounting (10 drawn instances + 14 undrawn = 24 = the 23-card Return deck + priest, never drawn); got-away list (5 names) → DB setup doom logged naming all five; past midnight → opening-hand discards + elder thing token added at DB setup (matches `chaos_bag_additions`); Billy Cooper interrogation flows to the log and victory display. The final campaign log retains MM fields after the DB record (ledger-25 fix holding). Skids killed in the final scenario, `killed_investigators` recorded, `next: null` — no return.

Two caveats on setup magnitudes I could not ground in the in-scope docs (neither `docs_agent/campaign_guide.md` nor `scenario_reference.md` states them): DB setup placed **3 doom for 5 got-away cultists** and discarded **2** opening-hand cards for past midnight. Ledger 45 previously adjudicated the got-away doom table as guide-correct, so I defer to that rather than file a finding; the transcript audit may want to confirm the discard count against the guide PDF. One cosmetic observation, not filed: encounter-card instances in run 2's `state.json` carry a defaulted `"owner": "roland"` in this Skids game (same hardcoded-identity family as ledger 83/109, state-representation only).

**Bottom line:** the campaign's ledger, decks, and continuity machinery all behaved correctly given their inputs — but scenario 1's input is another model's game, so this campaign (and show-terra-roland) should be excluded or rerun for benchmark purposes until the record-path race in the show/b4 driver is closed.
