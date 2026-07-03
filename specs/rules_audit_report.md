# Rules Audit Report

Verification:
- `python3 -m unittest discover -s tests` — PASS (85 tests)
- `python3 -m arkham.fuzz --games 200` — PASS (`R3: 2`, `no_resolution: 198`)

## Part 1

- 1.1 FIXED — Removed per-target AoO exemption; Fight/Evade/Parley/Resign action types are globally safe, Engage and other actions provoke all ready engaged enemies.
- 1.2 FIXED — Action cost is paid before AoOs; AoOs resolve before the action effect resumes.
- 1.3 FIXED — Autofail now sets total skill value to 0 before fail margin and log message are computed.
- 1.4 FIXED — Removed the post-reveal boost window; playing guide updated to say boosts happen before reveal.
- 1.5 FIXED — Enemy-phase attacks exhaust the attacking enemy; AoO and retaliate attacks do not.
- 1.6 FIXED — Multiple AoOs and multiple enemy-phase attacks now present player-chosen attack-order decisions.
- 1.7 FIXED — `place_doom` now requires `can_advance=True`; agenda advancement clears all doom in play.
- 1.8 FIXED — Upkeep readying now immediately checks ready enemy engagement.

## Part 2

- 2.1 PASS — Round 1 mythos skip and later mythos order verified; encounter enemies without spawn text spawn engaged with the drawer.
- 2.2 PASS — Upkeep order verified, including ready engagement check from 1.8 and hand-size discard.
- 2.3 PASS — New games advance directly to the first Investigation phase after round-1 mythos skip.
- 2.4 PASS — End-of-round effects expire/discard at upkeep/end-round boundary; Mind over Matter limit cleanup is preserved.
- 2.5 PASS — Commit rules, matching/wild icons, no resource cost, invalid-icon exclusion, and ST.8 discard verified.
- 2.6 PASS — Ties succeed; skill and difficulty floors verified, including Flashlight reducing shroud to 0.
- 2.7 FIXED — Hard/Expert cultist now recursively reveals until a non-cultist token; token aftermath checks all revealed tokens. Other token effects verified.
- 2.8 PASS — For-this-test boosts expire at test end; Vicious Blow, Deduction, Guts, and Manual Dexterity riders verified.
- 2.9 PASS — Hunter movement, shortest-path choice, Barricade blocking for non-Elite, Elite bypass, no movement at investigator location, and engagement on arrival verified.
- 2.10 PASS — Engagement on spawn/move/investigator move, engaged enemies moving with Roland, and Engage provoking other enemies verified.
- 2.11 PASS — Evade success exhausts/disengages; failure has no AoO/Alert penalty; only engaged enemies are evadable.
- 2.12 PASS — Ghoul Priest Retaliate fires on failed fights while ready and does not exhaust; exhausted priest does not retaliate.
- 2.13 PASS — Enemy defeat routing, victory display/discard, Roland and Evidence! reactions, and controlled-source defeat hooks verified.
- 2.14 PASS — Damage/horror assignment capacity, simultaneous attack damage/horror handling, and asset destruction verified.
- 2.15 PASS — Investigator defeat trauma, exact-once trauma guard, Cover Up game-end check, and no-resolution outcome verified.
- 2.16 PASS — Empty player deck reshuffle/horror and encounter deck reshuffle/no horror verified.
- 2.17 PASS — Fast cards/abilities cost resources where applicable, cost no action, and do not provoke AoOs.
- 2.18 FIXED — Hand/ally slots now enforce capacity with discard choice; Lita is excluded from ally slot pressure.
- 2.19 PASS — Uses decrement/gate abilities; First Aid discards empty, Flashlight persists at 0 supplies.
- 2.20 FIXED — Unique assets are blocked by title while an in-play copy exists; Lita remains slotless story ally.
- 2.21 PASS — Hand size is checked only during upkeep 4.5.
- 2.22 FIXED — Old Book of Lore draws now resolve weakness revelation; normal draw-action/upkeep weakness revelation was already verified.
- 2.23 PASS — Setup resources, weakness-free opening hand replacement, mulligan, and shuffle-back behavior verified.
- 2.24 PASS — Gathering act/agenda objectives, Parlor barrier, resolutions, XP, Lita scoring, and scenario outcomes verified unchanged by these fixes.
