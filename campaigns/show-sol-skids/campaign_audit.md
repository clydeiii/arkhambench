Audit complete. Everything reconciles except three items — one material rules-enforcement bug and two bookkeeping defects.

## Finding 1 — Elderthing token added to the Devourer Below chaos bag despite `past_midnight: false`

**Campaign step:** Return to the Devourer Below setup (run `c-show-sol-skids-3`, log line 23) / `campaign.json` → `chaos_bag_additions`.

**Rule:** The Devourer Below setup gates the elderthing token addition (together with the random opening-hand discard) on the campaign log reading "it is past midnight."

**Evidence:** The campaign log has `past_midnight: false` (Midnight Masks ended at agenda 2, doom 2/8 — midnight never struck), and the engine correctly applied *half* the conditional: no opening-hand discard occurred. But setup still logged "Setup added 1 elderthing token to the chaos bag," and `campaign.json` records `chaos_bag_additions: ["elderthing"]`. The token was absent from scenarios 1–2 (0 log hits), confirming it was injected specifically at DB setup, not campaign creation.

**Materiality:** The token was revealed in R5 of scenario 3 on Investigate Tangled Thicket (combat 4 vs shroud 2): `token -5 = 0 vs 2` — a test that succeeds by 2 against every legitimate standard-bag token except autofail was flipped to failure, costing a clue in a scenario that was subsequently lost racing the agenda.

**Cross-campaign confirmation:** all four sibling `show-sol-*` campaigns also have `past_midnight: false` yet all carry the elderthing addition — the engine adds it unconditionally; only luna/terra campaigns actually reached midnight.

## Finding 2 — Final XP ledger inconsistent: earned 6 − spent 5 = 1, but `xp_unspent` is 0

**Campaign step:** recording of scenario 3 (`campaign.json` ledger fields).

**Recomputation:** Scenario 1 earned 5 (victory display: Ghoul Priest 2 VP + Ghoul Pits 1 VP, +2 insight bonus per the Gathering resolution — matches the rulebook's own 5-XP example) and spent 5 (Beat Cop→Beat Cop(2) same-title upgrade = 2; Sure Gamble(3) new = 3; the Knife removal keeping the deck at 30 is free). Unspent 0 after upgrades ✓. Scenario 2 earned 0 ✓ (no VP, no purchases, deck-3 = deck-2). Scenario 3 earned 1 (Screeching Byakhee, Victory 1) — `xp_earned_total` became 6, `xp_spent_total` stayed 5, yet `xp_unspent` is 0 instead of 1. The three fields don't reconcile at the final step. Presumably the killed-investigator path drops the final award from unspent while still counting it in earned-total; whichever side is intended, the ledger is internally inconsistent. Bookkeeping only (Skids is dead and the campaign is complete), never negative at any step.

## Finding 3 — Scenario 3 `result.json` reports `enemies_defeated: 0`; the transcript shows 3

**Campaign step:** `c-show-sol-skids-3/result.json` (the artifact `campaign record` ingests).

**Evidence:** The run-3 transcript logs three enemy defeats — Acolyte of Umôrdhoth (R2), Screeching Byakhee (R3), Grave-Eater (R4) — and state.json holds the Byakhee in the victory zone. Run 1's counter was accurate (3 defeats logged, 3 reported), and run 2's genuine 0 is correct (its only "was defeated" line is Skids himself), so the counter is broken specifically on run 3's no-resolution/killed finalize path. Stats-level only: the 1 XP flowed through the victory display correctly.

---

**Clean dimensions:** Deck legality — all three materialized decks are exactly 30 counted cards; max 2 per title holds including Beat Cop across levels (01018 + 01028); class/level access respected (Guardian ≤2: Beat Cop 2; Rogue ≤5: Sure Gamble 3; all else level 0); both signatures (On the Lam, Hospital Debts) and the Mob Enforcer basic weakness present in every deck; the in-scenario-3 Amnesia gain is correctly recorded in the campaign deck; Lita (01117) appears only after being earned and included, and doesn't count toward 30. Continuity — mental trauma 1 from Gathering R1 shows as 1 starting horror in scenario 2; the 9/8-damage defeat adds 1 physical trauma showing as 1 starting damage in scenario 3; house burned → Rivertown start; dead Ghoul Priest never shuffled in; 6 got-away cultists → 3 setup doom plus got-away spawns; defeat in Midnight Masks correctly routed to R1; the resign in Devourer Below correctly ended as no-resolution with Skids killed (per the adjudicated DB kill rule); campaign closed immediately with `next: null`. Hospital Debts penalty 0 is correct — the card never entered play in any scenario.
