# Playing Guide — how to play AHLCG through the `ahlcg` CLI

You are playing *Arkham Horror: The Card Game* (solo) through a rules-enforcing engine.
You never adjudicate rules — the engine computes what's legal and offers you numbered
choices. Your job is to make good decisions.

## The loop

```
./ahlcg new --seed <n>        # start a game (creates runs/<name>, sets .current_run)
./ahlcg state                 # read the board
./ahlcg do <n> --why "..."    # pick option n, recording one sentence of reasoning
```

Every `do` prints what happened (chaos token drawn, damage dealt, cards drawn...) and
then the next decision point with numbered options. Always pass `--why` with a short
reason for the pick — it goes into the game log for post-game analysis and has no
effect on the game. If you lose track, `./ahlcg actions` re-prints the current decision
and `./ahlcg state` the full board.

Other commands:

- `./ahlcg card <name-or-code>` — full text of any card (yours or an encounter card).
- `./ahlcg bug "<description>"` — report a suspected engine rules bug (something it
  allowed that should be illegal, or blocked that should be legal). Reporting is
  rewarded; knowingly exploiting an unreported bug is penalized. Play on as adjudicated
  after reporting.
- `./ahlcg log --tail 30` — recent transcript (what happened this game).
- `./ahlcg score` — current metrics; final score once the game ends.
- `./ahlcg campaign ...` and `./ahlcg upgrade ...` — persistent campaign play and XP
  spending; see `docs_agent/campaign_guide.md`.

## Reference documents

- `docs_agent/rules_reference.md` — the full game rules (searchable; consult when unsure
  what a keyword like Hunter, Retaliate, or Attack of Opportunity means).
- `docs_agent/scenario_reference.md` — your investigator, deck, difficulty, the encounter
  deck contents, and how scoring works. **Read this before your first game.**
- `docs_agent/campaign_guide.md` — campaign flow, XP purchases, deck-size rules, and
  replacement-investigator warnings.

## The notebook — your persistent memory

The notebook survives across games. Use it: record what worked, what killed you, encounter
deck contents you've learned to fear, opening-hand priorities, quantitative lessons
("Ghoul Priest with 5 health took me 3 attacks"). Review it at the start of each game.

```
./ahlcg note show
./ahlcg note add "Agenda 1 flips on round 4 — be out of the Study by then."
./ahlcg note compact --file new_notebook.md    # rewrite/condense it whenever it gets bloated
```

If you cannot write files, compact via stdin instead:

```
./ahlcg note compact -f - <<'EOF'
(the new, condensed notebook content)
EOF
```

Compaction archives the old version; you never lose history, but keep the live notebook
sharp and actionable.

## Practical tips on driving the engine

- Option labels contain the math you need: `Fight Ghoul Minion — test Combat(4) vs 2`
  means you're at 4 against difficulty 2 before the chaos token (bag contents are in
  `state`; the token modifies your skill, ties succeed).
- During a skill test you'll get a commit window (add cards from hand for their icons,
  or pay resources for eligible boosts before the token is revealed). Committed cards are
  discarded win or lose.
- Spent clues go to the token pool. They NEVER return to the location. Investigating a
  0-clue location discovers nothing.
- The engine asks for confirmation before likely-mistake actions: investigating a
  location with 0 clues, or taking an action that will provoke attacks of opportunity.
  "Yes" is sometimes correct, such as accepting an attack to play a critical asset;
  use `--why` on the confirmation to record that reasoning.
- At phase boundaries (end of your turn, before enemy attacks, end of mythos) you may get
  a fast-ability window (e.g. Beat Cop's ping) — use it or pass.
- The engine only asks when there's a real choice; forced effects happen automatically
  and show up in the output.
- Invalid input never hurts you — it just re-prints the options.
- The game is over when output says GAME OVER; `./ahlcg score` then shows your result.
