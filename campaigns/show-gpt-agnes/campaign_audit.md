## Finding 1 — Earned Lita did not transfer to the replacement deck

Step: `campaigns/show-gpt-agnes/decks/deck-2.json`

After The Gathering, the result records `lita_earned: true` and Agnes killed. Campaign rules say a killed investigator is replaced with a fresh deck, but “earned story assets such as Lita transfer” ([campaign_guide.md](/Users/clyde/ahlcg/docs_agent/campaign_guide.md:87)).

The replacement Roland deck for Midnight Masks omits `01117` Lita Chantler ([deck-2.json](/Users/clyde/ahlcg/campaigns/show-gpt-agnes/decks/deck-2.json:5)), while the next deck includes her ([deck-3.json](/Users/clyde/ahlcg/campaigns/show-gpt-agnes/decks/deck-3.json:24)). Final campaign state also says `lita_earned: true` and `lita_in_deck: true` ([campaign.json](/Users/clyde/ahlcg/campaigns/show-gpt-agnes/campaign.json:52)).

Impact: Roland played Midnight Masks without an earned transferred story asset that later appeared for Devourer. XP ledger, counted deck sizes, weaknesses, killed-investigator replacement, trauma carryover, and Devourer setup inputs otherwise reconciled.
