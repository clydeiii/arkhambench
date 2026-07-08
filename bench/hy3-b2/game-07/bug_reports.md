## 2026-07-08T02:41:18+00:00
- Round: 1
- Phase: Investigation
- Description: After resolving an Investigate skill test (commit window, committed 0 cards), the remaining-action menu omitted all asset-play options (Flashlight x2, Knife, Hyperawareness, Research Librarian all in hand, play area empty) and offered only 'Play Mind over Matter' (an event) and 'Pass'. Rules allow playing any number of assets per turn as actions, so these should be offered. Possibly the post-commit action list fails to re-include asset plays.

## 2026-07-08T02:42:36+00:00
- Round: 2
- Phase: Investigation
- Description: Research Librarian (pc0005) was just played as an asset (cost 2, no Fast keyword) and the engine immediately offered its '[action] Exhaust Research Librarian: search deck for a Tome' ability, allowing me to fetch Old Book of Lore the same turn. Assets enter play exhausted and cannot use an Exhaust ability the turn they are played, so this should not be offered until the next turn after it readies. (Lenient bug, used as adjudicated.)

## 2026-07-08T02:45:13+00:00
- Round: 3
- Phase: Investigation
- Description: Playing Flashlight (pc0025) forced a discard of an IN-PLAY asset — the only options offered were 'Discard Old Book of Lore' and 'Discard Knife', both of which are already in play, not in hand. An asset's play cost is never paid by discarding other in-play assets; this appears to be a bug (or pc0025 has erroneous text; card lookup by code 'pc0025' returned 'no card found'). As adjudicated I discarded Old Book of Lore to preserve Knife (required to kill the Ghoul Priest without dying to Retaliate).

## 2026-07-08T02:59:25+00:00
- Round: 10
- Phase: Investigation
- Description: Return to The Gathering: Parlor is listed as a connection of Hallway (and vice-versa) but is never offered as a Move destination. At Hallway (R7, 4 actions) the only move options were Cellar, Guest Hall, Attic — Parlor absent; at Hallway (R9, 4 actions) same. Parlor stays 'unrevealed' and unreachable. Act 2 ('The Barrier') requires 3 clues in the Hallway area; with Attic(1) + Field of Graves(1) the only remaining safe clue source is Parlor, which is unreachable, forcing the player through the Icy Ghoul in Cellar (lethal before the Priest fight). This missing move target blocks a legitimate win path.

## 2026-07-08T02:59:33+00:00
- Round: 10
- Phase: Investigation
- Description: Recurring action-menu bug: after resolving a Move or Investigate action that leaves exactly 1 action remaining, the next decision menu collapses to only 'Play <event>' + 'Pass' and omits Move / Investigate / Draw / Take Resource / Study-ability options. Observed repeatedly (end of R1 after investigate commit; R5 after move to Bathroom; R6 after move to Attic; R7 after move to Attic; R9 after move to Field of Graves). This silently wastes the player's final action every turn (e.g., cannot move back to Guest Hall after investigating, cannot chain a 4th move/investigate). The remaining action should still allow Move/Investigate/etc. as normal.

