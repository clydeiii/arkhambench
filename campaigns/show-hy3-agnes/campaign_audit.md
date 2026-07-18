Every dimension reconciles. Final verdict:

**AUDIT CLEAN**

What I verified across the three campaign steps of show-hy3-agnes:

**XP ledger.** Scenario 1 (Return to the Gathering, no_resolution): 1 victory point banked (the Victory-1 Attic variant — same pattern as adjudication 82) + 2 insight bonus = 3 XP, matching `xp: 3`. Scenario 2 (R1 resign, empty victory display) and scenario 3 (killed) each earned 0. Purchases: deck-1→deck-2 replaced Blinding Light (01066, L0) with Blinding Light (01069, L2) — same-title upgrade, cost 2; deck-2→deck-3 bought a new Blinding Light L0 for max(1, 0) = 1, removing one Stray Cat to hold 30. Running balance 3 → 1 → 0, never negative; `xp_earned_total` 3 = `xp_spent_total` 3 + `xp_unspent` 0. ✓

**Deck legality.** All three decks count exactly 30 (signatures 01012/01013, weakness 01098, and Lita 01117 excluded); transcript deck sizes corroborate materialization (33 total in scenario 1 → d28 after the 5-card hand; 34 in scenarios 2–3 → d29). Every card is Mystic ≤5, Survivor ≤2, or Neutral — legal for Agnes; deck-3's Blinding Light title tops out at 2 copies across levels (1× L0 + 1× L2). Both signatures and Haunted appear in every deck; nothing forbidden was removed. The `deckbuild_swaps` entries (Blinding Light in / Forbidden Knowledge out, Ward of Protection in / Fearless out) are the free pre-campaign level-0 swaps, consistent with deck-1's odd single copies.

**Continuity.** Scenario 1 ends defeated by horror (8/8 sanity) → 1 mental trauma; scenario 2 opens with exactly `hor1/8 dmg0/6`, at Your House (house standing). Ghoul Priest alive → drawn from the Midnight Masks encounter deck in R3. Scenario 2's resign recorded all 6 cultists as got away, none interrogated; scenario 3 setup placed 3 doom from those 6 (the half-ratio table already adjudicated NOT A BUG in entry 45) and added the elderthing token, matching `chaos_bag_additions`. `past_midnight` false → no opening-hand discard, and the full opening hand was indeed kept. Lita earned in scenario 1, absent from deck-1, present in decks 2–3 and in the scenario-2/3 deck counts. Scenario 3: 6 damage on 6 health → 1 physical trauma, final trauma (1 mental, 1 physical); Devourer no-resolution correctly kills Agnes (`arkham_succumbed`, `killed_investigators: ["agnes"]`), campaign completes with `next: null`, and the final log preserves the Midnight-Masks fields (got-away list, past_midnight) — confirming the entry-25 fix held.

No findings to report.
