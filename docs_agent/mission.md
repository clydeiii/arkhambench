# Your mission

You are playing *Arkham Horror: The Card Game* — solo scenario "The Gathering" — through
the `./ahlcg` CLI in this repository. You are Roland Banks. Your goal is to finish the
scenario with the **highest score** you can. Score = experience earned − trauma suffered
(details in `docs_agent/scenario_reference.md`).

This is also a learning exercise: you (and other agents) will play this scenario many
times across sessions. A persistent notebook (`./ahlcg note ...`) survives between games —
it is your only memory from past playthroughs. Use it well:

1. **Start** by reading `docs_agent/playing_guide.md`, `docs_agent/scenario_reference.md`,
   and your notebook (`./ahlcg note show`).
2. **Play deliberately.** Before each decision, consider the board state, the odds (the
   chaos bag is listed in `state`), and the clock (agenda doom). Rules questions:
   consult `docs_agent/rules_reference.md` or `./ahlcg card <name>`.
3. **Take notes as you learn** — after mistakes, surprises, and at game end (what you'd
   do differently, what worked, key numbers). Notes are for your future self: make them
   concrete and actionable. Compact the notebook (`./ahlcg note compact`) when it gets
   bloated.
4. **Finish the game.** Play until GAME OVER, then run `./ahlcg score`, record your
   final lessons in the notebook, and report your result.

Start a new game with:

```
./ahlcg new --run runs/<your-run-name>
```

(a seed is chosen randomly if omitted). Then play: `./ahlcg state`, `./ahlcg do <n>`,
repeat. Good luck, investigator.
