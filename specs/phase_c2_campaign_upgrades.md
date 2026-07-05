# Phase C2 — Campaign mode + XP deck-upgrade system

Goal: agents can play a full (Return to) Night of the Zealot campaign — Gathering →
Midnight Masks → Devourer Below — with a persistent campaign log, trauma carryover,
story assets/weaknesses, and an **XP deck-upgrade phase between scenarios** where the
agent is shown every legal purchase and must maintain deck size. Solo, one investigator.

Depends on phase C1 (Midnight Masks). The Devourer Below is phase C3; build the runner
so its scenario adapters are data-driven and DB slots in cleanly (its adapter can raise
"not implemented" until C3 lands).

Authority: campaign guide pp.1–3,8 (campaign setup, Expanded Campaign Rules, campaign
log) + AHLCG Rules Reference on spending experience. If anything below conflicts with
card JSON or the guide, flag it in the report rather than guessing.

## Campaign state — `campaign.json`

New CLI namespace `./ahlcg campaign ...` managing a campaign directory (e.g.
`campaigns/<name>/campaign.json` + one run dir per scenario inside it).

```json
{
  "campaign": "return_to_night_of_the_zealot",   // or night_of_the_zealot
  "difficulty": "standard",
  "seed": 42,                                     // master seed; per-scenario seeds derived
  "investigator": "roland",
  "killed_investigators": [],
  "trauma": {"physical": 0, "mental": 0},
  "xp_unspent": 0, "xp_earned_total": 0, "xp_spent_total": 0,
  "deck": {"slots": {"01020": 1, "...": 2}, "story_assets": ["01117"],
            "weaknesses": ["01102", "01096"]},
  "chaos_bag_additions": [],                      // e.g. ["elderthing"] from DB setup
  "log": {
    "your_house_standing": true,
    "ghoul_priest_alive": true,
    "lita_was_forced_to_find_others": false,
    "lita_earned": false, "lita_in_deck": false,
    "cultists_interrogated": [], "cultists_got_away": [],
    "past_midnight": false,
    "arkham_succumbed": null, "ritual_broken": null, "umordhoth_repelled": null,
    "lita_sacrificed": null, "notes": []
  },
  "scenarios": [
    {"scenario": "return_to_the_gathering", "run": "runs/c-<name>-1",
     "status": "complete", "resolution": "R1", "xp_earned": 5, "score": 4,
     "trauma_delta": {"physical": 0, "mental": 2}}
  ],
  "next": "return_to_the_midnight_masks",
  "phase": "scenario|upgrade|complete"
}
```

## Commands

- `./ahlcg campaign new --dir campaigns/<name> --investigator X --difficulty Y --seed N
  [--original]` — Return campaign by default; `--original` = plain NotZ. Snapshots the
  investigator's killbray starting deck into `deck`.
- `./ahlcg campaign status [--dir ...]` — human/agent-readable log + current phase +
  what to do next. A campaign-level `.current_campaign` pointer (like `.current_run`)
  so the bare commands work.
- `./ahlcg campaign next` — only in phase `scenario`: creates the run dir for the next
  scenario via the engine (equivalent of `ahlcg new` with all campaign inputs wired),
  sets `.current_run`, prints the mission brief. Campaign inputs per scenario:
  - Gathering: nothing special (fresh bag per difficulty).
  - Midnight Masks: `--house-burned` (from log), `--ghoul-priest-alive`,
    `--lita-forced-to-find-others`; deck = current campaign deck (incl. Lita if chosen,
    earned weaknesses).
  - Devourer Below (C3): got-away names/count, past-midnight, ghoul-priest-alive,
    chaos_bag_additions (elderthing added at DB setup, persisted).
  - Per-scenario seed: derive deterministically (e.g. master_seed*100 + scenario_index)
    so campaigns are reproducible.
- `./ahlcg campaign record` — after the run reaches GAME OVER: ingest result.json +
  campaign block into campaign.json (XP earned, trauma deltas, log updates: house
  burned/standing, priest crossed out when defeated, Lita earned, cultists lists,
  past midnight, DB resolutions). Then:
  - If investigator was **killed or driven insane** (defeat by damage → killed,
    horror → insane; R3-of-Gathering trapped → killed; DB no-resolution → killed):
    record in `killed_investigators`, and the campaign continues ONLY if scenarios
    remain and a replacement is chosen: `./ahlcg campaign replace --investigator Z`
    (fresh killbray deck, 0 XP, 0 trauma; Lita transfers if earned). If it was the
    final scenario, campaign completes.
  - Advance `phase` to `upgrade` (or `complete` after the last scenario).
  - The Gathering resolutions grant XP per the guide (already implemented per-run);
    campaign only accumulates. Lita earned in every Gathering outcome except R2 —
    on earn, the agent may include her: `./ahlcg campaign lita --include|--skip`
    (she does not count toward deck size).
- Upgrade phase commands (phase `upgrade` only):
  - `./ahlcg upgrade options` — list EVERY legal purchase, with per-line: code, name,
    level, class, cost in XP, kind (`new` or `upgrade of <code>`), and whether a
    removal is required. Show `xp_unspent` and current deck size. Legality rules below.
  - `./ahlcg upgrade buy <code> [--remove <code>] [--replace <code>]` — `--replace`
    for same-title upgrades (removes the lower version, cost = level difference);
    `--remove` for new-card purchases when the deck is at size limit (removal must not
    be a signature, story asset, or weakness). Errors are precise (not enough XP,
    would exceed 2-per-title, class/level illegal, must remove a card, ...).
  - `./ahlcg upgrade remove <code>` — remove a non-signature/weakness/story card
    without buying (deck below minimum is illegal at `done`).
  - `./ahlcg upgrade done` — validates final deck (exactly 30 player cards + 2
    signatures + earned/basic weaknesses + optional story assets; ≤2 copies per title;
    class/level rules) and flips phase to `scenario`.

## Deckbuilding + XP rules (enforce exactly)

- Class access (secondary class capped at level 2):
  roland: guardian 0–5, seeker 0–2; daisy: seeker 0–5, mystic 0–2;
  skids: rogue 0–5, guardian 0–2; agnes: mystic 0–5, survivor 0–2;
  wendy: survivor 0–5, rogue 0–2; neutral 0–5 for everyone.
- New card: cost = max(1, level). Same-title upgrade: cost = (new level − old level),
  min 1; lower version leaves the deck (goes to collection).
- Max 2 copies per title (by name, across levels — two `Physical Training` total,
  regardless of level mix). Deck size stays exactly 30 (signatures, weaknesses, Lita
  excluded from the count).
- Buying a second copy of an XP card you already own once is a `new` purchase at full
  cost.
- XP can be banked across scenarios (`xp_unspent` persists).

## Purchasable pool

Everything the engine implements, i.e. all 73 currently-implemented level-0 player
cards **plus the full core + Return XP pool (32 cards)** — implement the missing ones:

Upgrades of implemented titles (reuse base logic, apply printed deltas from JSON —
icons/cost/effect): 01028 Beat Cop(2), 01040 Magnifying Glass(1), 01054 Leo De Luca(1),
01069 Blinding Light(2), 01084 Lucky!(2), 50001 Physical Training(2), 50002 Dynamite
Blast(2), 50003 Hyperawareness(2), 50004 Barricade(3), 50005 Hard Knocks(2), 50006 Hot
Streak(2), 50007 Arcane Studies(2), 50009 Dig Deep(2), 50010 Rabbit's Foot(3).

New implementations: 01026 Extra Ammunition(1), 01027 Police Badge(2), 01029
Shotgun(4), 01041 Disc of Itzamna(2), 01042 Encyclopedia(2), 01043 Cryptic Research(4),
01055 Cat Burglar(1), 01056 Sure Gamble(3), 01057 Hot Streak(4), 01068 Mind Wipe(1),
50008 Mind Wipe(3), 01070 Book of Shadows(3), 01071 Grotesque Statue(4), 01082
Aquinnah(1), 01083 Close Call(2), 01085 Will to Survive(3), 01094 Bulletproof Vest(3),
01095 Elder Sign Amulet(3).

Implement each from its JSON text; flag any whose rules interact with unimplemented
systems rather than approximating silently. Notes on the trickier ones:
- Shotgun: deals min 1 / max 6, +1 damage per point succeeded by.
- Grotesque Statue: reveal 2 chaos tokens, choose 1 to resolve (seeded RNG; the other
  is ignored/returned).
- Sure Gamble: play AFTER revealing a token with negative modifier, switch its sign —
  needs the pre-resolution reaction window on token reveal (fast, engine already has
  commit windows; add a token-reaction window gated to cards in hand that allow it).
- Close Call: after you evade an enemy — shuffle that non-Elite, non-weakness enemy
  back into the encounter deck.
- Will to Survive: this turn, do not reveal chaos tokens for skill tests (auto-treat
  as +0 revealless; tests auto-compare stat vs difficulty).
- Aquinnah(1): reaction when an enemy attacks — redirect the DAMAGE to another enemy
  at your location (horror still hits you).
- Cryptic Research: draw 3 (fast, at a location — solo: yourself).
- Mind Wipe: blank a non-Elite enemy's text until end of phase.
- Elder Sign Amulet: +2 sanity soak. Bulletproof Vest: +2 health soak.
- Police Badge: +1 willpower; exhaust+discard on your turn: gain 2 actions.
- Encyclopedia: exhaust: +2 to a chosen skill for an investigator at your location
  this phase. Book of Shadows: exhaust: add 1 charge to a Spell asset. Cat Burglar:
  +1 agility, exhaust: disengage + move.
- Disc of Itzamna: reaction when non-Elite enemy spawns at your location: discard it
  (the enemy).

## Agent-facing docs

- `docs_agent/campaign_guide.md`: the full flow (campaign new → next → play → record →
  upgrade options/buy/done → next ...), XP rules with worked examples, warnings
  (trauma persistence, killed = investigator gone, Lita choice, weakness additions).
- mission.md for campaign runs should surface: campaign context (scenario k of 3,
  trauma carried, log facts that matter) — extend the existing template machinery.
- Update `docs_agent/playing_guide.md` index if it lists commands.

## Scoring / reporting

- `campaign_summary.json` at completion: per-scenario rows (resolution, xp, trauma,
  score) + totals; campaign_score = sum of per-scenario scores (same
  max(0, XP−trauma) per scenario, trauma counted per-scenario delta, not cumulative);
  plus final outcome flags (arkham_succumbed / ritual_broken / umordhoth_repelled /
  lita_sacrificed, killed list).
- `./ahlcg campaign status` shows a compact table of the same.

## Tests

1. Campaign lifecycle: new → next(Gathering) → simulate result ingestion (synthesize a
   finished run or drive a scripted mini-game) → record updates log/xp/trauma → upgrade
   phase gates commands → done → next(MM) passes correct flags/deck.
2. XP math: level-0 add costs 1; upgrade 0→2 costs 2; 0→3 costs 3; second copy full
   price; insufficient XP rejected; banked XP persists.
3. Deck legality: 2-per-title cap across levels; secondary-class level cap (skids
   cannot buy Shotgun; roland cannot buy Cryptic Research or Barricade(3); wendy CAN
   buy Hot Streak(2) [rogue 0–2] but NOT Sure Gamble(3)); removal restrictions
   (signature/weakness/story protected); size-30 invariant at `done`.
4. Options listing exactness: for a roland with 6 XP and stock deck, the options list
   matches a golden expected set (pin it in the test).
5. Each new XP card: at least one behavior test (Shotgun damage math, Sure Gamble sign
   flip, Will to Survive tokenless turn, Aquinnah redirect, Disc discard-on-spawn,
   Grotesque Statue choose-of-2, Police Badge extra actions, Close Call shuffle-back,
   soak assets absorb, Cryptic Research draw, upgrades' deltas e.g. Beat Cop(2)
   discard-for-damage, Lucky!(2) draw, Leo(1) cost 5, Dynamite Blast(2) no AoO...).
6. Lita includable after earning, excluded from deck size, transfers on investigator
   replacement; earned Madness weaknesses persist into subsequent scenario decks.
7. Killed investigator flow: replace command, fresh deck/0 XP, killed list grows,
   trauma reset for the new investigator.
8. Determinism: same master seed → identical scenario seeds and variant draws.

## Report

`specs/phase_c2_report.md`: built/deviations/conflicts, tests before/after, any pool
exclusions with reasons. No git commits.
