All verification paths are complete. Everything reconciles — here's the full audit.

**AUDIT CLEAN**

## 1. XP ledger — reconciled exactly

| Step | Event | Earned | Spent | Unspent |
|---|---|---|---|---|
| S1: Return to the Gathering, no_resolution | VP 1 + 2 insight bonus = **3 XP** (matches adjudication #2) | 3 | — | 3 |
| Upgrade 1 | Blinding Light(2) 01069 `--replace` Blinding Light(0) 01066: level diff 2−0 = **2 XP** | | 2 | 1 |
| S2: Return to the Midnight Masks, R1 | VP 2 = **2 XP** | 5 | | 3 |
| Upgrade 2 | Bulletproof Vest(3) 01094 new = max(1,3) = **3 XP**, `--remove` Stray Cat to hold 30 | | 5 | 0 |
| S3: Return to the Devourer Below, no_resolution, killed | VP 0 = **0 XP** | 5 | 5 | 0 |

Recomputed totals match `xp_earned_total: 5`, `xp_spent_total: 5`, `xp_unspent: 0`, and the mid-campaign snapshots in each run's meta.json (`xp_unspent` 0 → 1 → 0 at scenario starts) confirm the engine charged exactly 2 and 3. Never negative at any step.

## 2. Deck legality over time — all three decks legal

- **Size**: deck-1 = 15 titles × 2 = 30 counted; deck-2 = 30 (−1 Blinding Light(0), +1 Blinding Light(2)); deck-3 = 30 (−1 Stray Cat, +1 Bulletproof Vest). Signatures (Heirloom 01012, Dark Memory 01013), weakness (Haunted 01098), and Lita (01117) correctly excluded from the count.
- **Max 2 per title across levels**: the only split title is Blinding Light 0/2 at 1+1 = 2 copies. ✓
- **Class access**: mystic cards all 0–2 (Agnes 0–5 ✓), survivor cards all level 0 (Agnes 0–2 ✓), neutral incl. Bulletproof Vest(3) ✓. The eight opening free swaps (Ward, Blinding Light, Lucky!, "Look what I found!" in; Baseball Bat, Knife, Overpower, Arcane Studies out) are all level-0-for-level-0 and in-class.
- **Weaknesses**: Haunted present in all three decks, never removed; Dark Memory in all three; Hypochondria (01100) gained during scenario 3 and recorded in the campaign deck's weakness list (no later deck exists to require it). Lita appears only from deck-2 onward, after being earned in S1 and explicitly included.

## 3. Continuity — all facts flowed correctly

- **Trauma**: deltas 1/1/0 physical → S1 opens at dmg0/6, S2 at dmg1/6, S3 at dmg2/6 (verified in each transcript's opening status line); campaign total physical 2. No trauma assigned to the killed investigator in S3.
- **House standing** (S1 no-resolution) → S2 begins at Your House with the location in play.
- **Ghoul Priest alive** → passed into S2's setup inputs (meta.json); the priest never surfaced in the 8-round game, which is consistent (deck contents are in hidden.blob, so the shuffle itself is the scenario audit's domain — the campaign-layer input is correct).
- **Cultist ledger**: 5 got away + 1 interrogated ("Wolf-Man" Drew) = 6, the full Return-to MM cultist pool → S3 setup placed **3 doom** on agenda 1a (correct for 5–6 got away; agenda opens at doom 3/4) and Lita/got-away/past-midnight inputs match.
- **Past midnight false** → no opening-hand discard in S3 (full 5-card hand kept through mulligan). ✓
- **Elder thing token**: added by Devourer Below setup (logged), recorded in `chaos_bag_additions`. ✓
- **Death is final**: Agnes killed by Umôrdhoth's Hunger (discard-to-empty kill, per adjudication #67), added to `killed_investigators`, campaign phase `complete`, `next: null` — no purchases or scenarios after death. Outcome flags (`arkham_succumbed` true, repelled/broken/sacrificed false) are consistent with a DB no-resolution.

No campaign-layer defects found.
