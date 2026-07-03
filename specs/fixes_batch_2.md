# Fix batch 2 — findings from the GPT-5.5 demo game (runs/gpt55-demo-1)

1. **Missing fast-ability windows at phase boundaries.** DESIGN §5 says a player window
   is surfaced whenever at least one optional fast ability is legal. Today fast abilities
   (Beat Cop's discard-ping, fast asset plays like Magnifying Glass) are only offered
   inside the action menu and inside skill tests. Real case: the agent's last action
   killed nothing; it planned "Machete, Machete, then Beat Cop ping" but after the final
   action resolved the engine went straight to the enemy phase — the ping was never
   offered and the Ghoul Priest survived at 4/5. Add fast windows (decision point listing
   legal fast abilities + "Pass") at minimum:
   - end of the investigation phase (after the last action, before enemy phase),
   - start of the enemy phase after hunter movement, before enemy attacks,
   - end of the mythos phase (after encounter resolution, before investigation).
   Only surface when at least one fast ability is actually legal (unchanged principle).
   Beat Cop's ping and fast asset plays (Magnifying Glass) must appear there. Make sure
   this cannot loop (each window offered once per phase boundary unless state changed —
   e.g. after using an ability in the window, re-offer while more remain, "Pass" exits).

2. **Notebook bound to the run.** `ahlcg new` gains `--notebook PATH` (default:
   `./notebook.md` as today), stored in `meta.json`. `ahlcg note ...` resolves the
   notebook as: `--notebook` flag > `AHLCG_NOTEBOOK` env > current run's meta.json >
   `./notebook.md`. This lets the bench runner give each agent its own persistent
   notebook without relying on env vars surviving into agent subshells.

Tests for both (window surfacing incl. the Beat Cop scenario; notebook resolution order).
Run full suite + `python3 -m arkham.fuzz --games 100` clean. Write
specs/fixes_batch_2_report.md. No git commit.
