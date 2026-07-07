AUDIT CLEAN

I found no campaign-layer rules-enforcement bugs in `campaigns/show-gpt-skids`.

Checked:
- XP ledger: 4 earned from The Gathering, 0 from Midnight Masks, 0 from Devourer. Four level-0 purchases after scenario 1 cost 4 XP total. Final `xp_earned_total: 4`, `xp_spent_total: 4`, `xp_unspent: 0`; no negative step.
- Deck legality: `deck-1.json`, `deck-2.json`, and `deck-3.json` each have exactly 30 counted cards after excluding signatures, weaknesses, and Lita. Skids’s signatures and weaknesses persist; Lita appears only after being earned and included; no over-2 title copies or off-access cards found.
- Continuity: physical trauma from Midnight Masks is applied as `dmg1/8` at Devourer setup; campaign inputs flow into later setup (`Your House`, got-away doom, elderthing token, `past_midnight: false`, Lita-in-deck flag). Devourer death/killed state is recorded only at campaign end, with no later illegal return.
