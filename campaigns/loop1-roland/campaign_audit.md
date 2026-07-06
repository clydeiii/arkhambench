## Finding 1 — Final campaign log erased the cultists who got away

Step: `campaign record` after `return_to_the_devourer_below`

The campaign log should preserve recorded campaign facts. The rules reference says to record scenario results in the campaign log, and the campaign guide says `campaign record` ingests `result.json` and updates that log.

Evidence:
- Midnight Masks recorded all six cultists as escaped in [result.json](/Users/clyde/ahlcg/campaigns/loop1-roland/runs/c-loop1-roland-2/result.json:4).
- Devourer setup correctly received those six names in [meta.json](/Users/clyde/ahlcg/campaigns/loop1-roland/runs/c-loop1-roland-3/meta.json:6).
- But final [campaign.json](/Users/clyde/ahlcg/campaigns/loop1-roland/campaign.json:41) has `"cultists_got_away": []`.

Why this matters: Act 1b `Investigating the Trail` searches for enemies recorded under “Cultists Who Got Away” and spawns them at Main Path. The completed scenario already had the right setup input, so the corruption appears to happen after recording Devourer, but the persisted campaign log is now wrong for any later consumer, replay, continuation, or transfer.

XP ledger and deck legality otherwise reconciled. Trauma and starting damage/horror into the next scenarios also reconciled.
