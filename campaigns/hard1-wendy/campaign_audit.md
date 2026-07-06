## Finding 1 — Simultaneous defeat recorded both trauma types and killed Wendy

**Campaign step:** `c-hard1-wendy-3` record / final `campaign.json`

**Evidence:** Wendy is at `dmg5/7 hor6/7`, then Yithian Observer deals `2 damage and 2 horror` in one attack, leaving her at `dmg7/7 hor8/7`: [log.md](/Users/clyde/ahlcg/campaigns/hard1-wendy/runs/c-hard1-wendy-3/log.md:313). The result records both `mental: 1` and `physical: 1`, plus `investigator_killed: true`: [result.json](/Users/clyde/ahlcg/campaigns/hard1-wendy/runs/c-hard1-wendy-3/result.json:19). Campaign state then carries both trauma and adds Wendy to `killed_investigators`: [campaign.json](/Users/clyde/ahlcg/campaigns/hard1-wendy/campaign.json:36), [campaign.json](/Users/clyde/ahlcg/campaigns/hard1-wendy/campaign.json:94).

**Rule:** If an investigator is defeated by simultaneously taking damage to health and horror to sanity, they choose which type of trauma to suffer: [rules_reference.md](/Users/clyde/ahlcg/docs_agent/rules_reference.md:440). Killed/insane status only follows trauma reaching printed health/sanity, or a card/resolution explicitly doing so: [rules_reference.md](/Users/clyde/ahlcg/docs_agent/rules_reference.md:1427).

**Impact:** Wendy should receive one chosen trauma, not both. With prior campaign trauma `physical 1 / mental 0`, either legal choice leaves her far below Wendy’s printed `7/7`, so the final killed-investigator log is also unsupported by the provided rules authority.

XP ledger, deck legality over time, Lita/weakness persistence, and the checked setup continuity inputs otherwise reconciled cleanly.
