# Fixes batch 8 — playtest loop round 2 + XP-coverage audits (ledger 34–45)

Adjudicated findings (specs/bug_adjudications.md 34–45 carry full evidence). One
regression test per item; keep the suite green (278 now); re-run the 6-scenario fuzz
matrix; update ledger entries with FIXED notes; append a batch-8 section to
specs/phase_c3_report.md.

## Timing / windows

1. (34) **Remove the phantom post-turn fast window.** RR chart: no player window
   between 2.2.2 and 2.3. Also enforce play restrictions inside remaining windows:
   cards saying "Play only during your turn" (Mind over Matter) are not offered
   outside the owner's turn; RR also forbids voluntarily spending actions/fast
   assets outside your turn.
2. (35) **Enemy-doom placements advance the agenda only at mythos 1.3** (or via
   explicit "can advance" text: Masked Horrors, Offer of Power, Jeremiah Pierce,
   Corpse-Taker's dump). Placing doom on Acolyte/Wizard/Disciple/Initiate/Mask must
   NOT trigger an immediate advance; the 1.3 check (and explicit-permission
   placements) counts total doom in play as today. Follow the Gathering's existing
   Acolyte adjudication pattern.

## Rules enforcement

3. (36) **Hunting Nightgaunt**: while evading it, double each revealed token's
   NEGATIVE modifier (autofail unaffected; positive tokens unchanged; elder sign
   per its value).
4. (37) **Young Deep One**: Forced after it engages — investigator takes 1 horror
   (spawn-engage, move-engage, ready-engage, massive n/a).
5. (38) **Weakness cards are not payable as optional discard costs**: exclude
   weaknesses from choose-and-discard COST pickers (Wendy's canonical ability,
   Herman Collins parley, Warehouse willpower-icon discard, Umôrdhoth's Wrath
   choice is an effect "you must choose" — effects may discard weaknesses, costs
   may not; audit each choose-discard site and classify cost vs effect).
6. (39) **Doom (and all tokens) return to the pool when a card leaves play** —
   defeat, discard, victory display, add-to-victory parleys. Agenda math drops it
   immediately.
7. (40) **Moving an engaged enemy to another location disengages it** (Corpse-
   Taker Forced move; any future effect-based enemy moves). It stops attacking a
   non-co-located investigator; Hunter re-engagement works normally later.
8. (41) **A weakness added to hand resolves as if drawn** (RR Weakness): the
   agenda-2 Madness gain routes through the revelation path (Psychosis → threat
   area, its Forced live from then on; Amnesia/Paranoia/Hypochondria resolve their
   printed revelations). R3's add-to-DECK path stays as-is (not a hand entry).
9. (42) **Paid play costs are never refunded by AoO outcomes.** The batch-6
   abort-refund applies only when the play is aborted BEFORE costs are considered
   paid per Appendix I; a random discard removing the being-played card fizzles
   the play with costs lost. Make the being-played card immune to random-discard
   selection while in limbo if the RR supports it — it does: a card being played
   has left hand when costs are paid (it is "in play or about to be") — so
   Grave-Eater's discard should never have been able to select Machete. Implement
   BOTH: the being-played card is not in hand during AoO resolution, and no refund
   on fizzle.
10. (44) **Leo De Luca grants his additional action every turn while in play**
    (either copy, max one per Leo per turn; C2 clawback rules from the earlier FAQ
    fix still apply). Root-cause why only the entry turn worked.

## Display / logging

11. (43) **Recompute skill-value modifiers at ST.5** after ST.4 chaos effects
    (assets discarded to soak ST.4 damage no longer contribute; both the printed
    math and the outcome).
12. (45) **Logging batch**: (a) log scenario-setup effects (got-away doom amount
    and names, elderthing addition, past-midnight discards already logged?); (b)
    Disciple's agenda>=2 forced clue placement emits an event; (c) Museum clue gain
    reads "gained 1 clue from the token pool"; (d) verify the entry-26 fix covers
    Drawn to the Flame's discover logging (test at a 1-clue location); extend the
    actual-amount logging to all discover effects if not.
