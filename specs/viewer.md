# Run viewer — timeline capture, replay exporter, and static web UI

Goal: a human can step through every state change of any recorded game, seeing exactly
what the agent saw and did: the location map (connections, clues, shroud, attachments,
enemies), the player board (stats, resources, hand, play area, threat area, deck/discard),
agenda/act/doom, chaos bag, the events between steps, and the decision presented at each
step with the option the agent chose. Precision over prettiness. No build tooling, no JS
dependencies, no server-side code — a static `viewer/` folder served by
`python3 -m http.server`.

## Part A — timeline capture (engine)

1. `Game.new` and `Game.apply` append one JSON line to `<run>/timeline.jsonl`:
```json
{"i": 0, "round": 1, "phase": "Investigation", "status": "<status_line>",
 "chose": null | {"decision_id": "...", "option": 3, "label": "..."},
 "events": [{"type": "...", "message": "..."}],
 "pending": null | {"id": "...", "prompt": "...", "options": ["label", ...]},
 "state": <GameState.public_dict()>}
```
   - `chose` = the option just applied (null for the initial line from `Game.new`).
   - `events` = the rendered events that resulted from that choice (or from setup).
   - `pending` = decision_queue[0] after advancing (null when game over).
   - Append atomically (single `write` of one line) and never crash the game on
     timeline IO errors (log to stderr and continue).

## Part B — exporter (`arkham/export.py`, runnable `python3 -m arkham.export`)

```
python3 -m arkham.export --run <run-dir> [--out viewer/data] [--label NAME]
python3 -m arkham.export --all-bench bench/<label> [--out viewer/data]
```

- If `<run>/timeline.jsonl` exists: assemble directly.
- Else: **replay** — `Game.new(seed, difficulty, deck)` from meta.json, then re-apply
  each `decision_made` event (option index) from log.jsonl in order, snapshotting
  public state after each apply. Verify as you go: the reconstructed pending decision's
  prompt must equal the next `decision_presented` prompt from log.jsonl; on mismatch,
  stop, emit the timeline up to the divergence, and print a loud warning (engine has
  changed since the run was recorded). Replay must not write into the original run dir.
- Output `viewer/data/<name>.json`:
```json
{"meta": {"name", "run_dir", "seed", "difficulty", "engine_version", "exported_at",
          "complete": true|false, "divergence_step": null|int},
 "cards": {"01001": {"name", "type_code", "faction_code", "cost", "text", "traits",
            "icons": {"willpower","intellect","combat","agility","wild"},
            "health", "sanity", "enemy_fight", "enemy_evade", "enemy_damage",
            "enemy_horror", "shroud", "clues", "doom", "victory", "is_unique", "slot"}},
 "steps": [{"i", "round", "phase", "status", "events", "decision":
            {"prompt", "options": [...], "chosen": int|null, "chosen_label": str|null},
            "state": <public_dict>}],
 "result": <result.json contents or null>}
```
  - Steps are decision-centric: step i shows the state WHEN decision i was pending, the
    events that led to it, and (from the next timeline line) which option was chosen.
    Final step: `decision: null`, plus result.
  - `cards` covers every card code appearing anywhere in any snapshot (instances,
    locations, agenda/act codes, victory display).
- Rebuild `viewer/data/index.json`: `[{"name", "file", "seed", "difficulty", "steps",
  "outcome", "score", "complete"}]` (scan existing exports; stable order).
- Export now: both `bench/sonnet5-mini` games (current engine — replay must verify
  cleanly). Do NOT export the old `runs/*demo*` runs (pre-audit engine; replay diverges).

## Part C — viewer (static app: `viewer/index.html`, `viewer/app.js`, `viewer/style.css`)

Vanilla JS (ES modules fine), fetches `data/index.json` then a chosen run JSON. Layout:

```
┌──────────────────────────────────────────────────────────────────────┐
│ run selector ▾ | ⏮ ◀ step 37/142 ▶ ⏭ | jump-to-round ▾ | status line │
├─────────────────────────────────────────────┬────────────────────────┤
│                LOCATION MAP                 │ SCENARIO PANEL         │
│   (SVG: nodes + connection lines)           │ agenda: name 5/7 doom  │
│   each node: name, shroud◆, clues●,         │ act: name, clue req    │
│   victory pts, attachment chips,            │ chaos bag (16 tokens)  │
│   enemy chips (dmg, exhausted, engaged),    │ victory display        │
│   investigator marker (Roland)              │ enc deck N / discard M │
│                                             │ (discard examinable)   │
├─────────────────────────────────────────────┴────────────────────────┤
│ EVENT TICKER: events since previous step (scrollable, monospace)     │
├───────────────────────────────────────────────────────────────────────┤
│ DECISION: prompt + numbered options; chosen one highlighted ✓;        │
│           un-chosen options dimmed (this is what the agent declined)  │
├───────────────────────────────────────────────────────────────────────┤
│ PLAYER BOARD: Roland ♥3/9 🧠1/5 | res 4 | clues 2 | actions 2/3       │
│ play area: [card][card][card]  threat: [card]                        │
│ hand: [card][card][card][card]  deck 21 | discard 9 (examinable)     │
└───────────────────────────────────────────────────────────────────────┘
```

Requirements:
- **Card rendering**: thumbnail = image from
  `https://arkhamdb.com/bundles/cards/{code}.png` with `onerror` fallback to a text box
  (name, cost, icons). Every card chip/thumb is clickable → modal showing the full-size
  image AND the engine's card data (from `cards`) side by side. Show per-instance
  overlays on thumbs: uses (ammo/supplies), damage/horror tokens, clue/doom tokens,
  "exhausted" badge (rotate 90° or grey out).
- **Map**: fixed layout for known Gathering ids (study center; hallway center, attic
  above, cellar lower-left, parlor right); unknown location ids fall back to a circle.
  Unrevealed locations render face-down style (grey, shroud "?"). Connections = lines.
  Enemy chips live on their location (or on the player-board threat area when engaged —
  show them in BOTH: on map at Roland's location with an "engaged" ring, and in threat).
- **Deltas**: values that changed vs the previous step get a yellow flash/highlight
  (resources, damage, horror, clues, doom, hand count...). Cards that entered a zone
  this step get the same highlight.
- **Examinable piles**: player discard, encounter discard, victory display, hand — click
  the pile count/section header to open a modal listing the cards (each clickable).
- **Skill test overlay**: when `state.active_skill_test` is non-null, show a strip above
  the decision panel: skill, base, committed cards, difficulty, token (if revealed).
- **Navigation**: buttons + ArrowLeft/ArrowRight keyboard; jump-to-round select; a
  step slider; URL hash `#run=<name>&step=37` so a specific moment is linkable.
- **Result screen**: on the final step show the result.json block (outcome, XP, trauma,
  score, campaign log) prominently.
- No external assets except arkhamdb card images. Readable on a laptop screen; light
  theme fine; monospace for event/status text.

## Part D — serve + docs + tests

- `scripts/view.sh`: exports any bench/run dirs passed as args (skip already-exported),
  then `python3 -m http.server 8765` from repo root and print
  `http://localhost:8765/viewer/`.
- README section "Watching a game" with the two commands.
- Tests: timeline lines written by new/apply (count = decisions+1, parse, has state);
  exporter on a scripted mini-game (replay path: assert steps == decisions, chosen
  labels align with log, divergence detection triggers on a doctored log); index.json
  rebuild; cards dict covers all codes in snapshots. Viewer JS is not unit-tested — but
  validate `viewer/data/*.json` against steps schema in a test if exports exist.
- `python3 -m unittest discover -s tests` green; fuzz 50 clean.
- Report: specs/viewer_report.md. No git commit.
