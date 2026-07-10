#!/usr/bin/env python3
"""Export benchmark findings to viewer/data/results.json for the findings page.

Aggregates bench/<label>/results.csv-era data via viewer/data/index.json (runs
already exported to the viewer, so every game we cite is browsable), campaign
arcs via viewer/data/campaigns.json + campaign_summary mtimes (chronological
play order), and playtest-program stats from specs/bug_adjudications.md.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROTATION = ["roland", "daisy", "skids", "agnes", "wendy"]

WAVES = [
    {
        "id": "b1", "title": "Main run — US frontier models", "date": "2026-07-05",
        "note": "Frozen engine, seeds 1001–1010, per-agent notebooks starting empty.",
        "agents": [
            ("fable5-b1", "Fable 5", "claude", "US"),
            ("sonnet5-b1", "Sonnet 5", "claude", "US"),
            ("gpt55-b1", "GPT-5.5", "codex", "US"),
            ("opus48-b1", "Opus 4.8", "claude", "US"),
        ],
    },
    {
        "id": "b2", "title": "Open-weights run — China models", "date": "2026-07-08",
        "note": "Same seeds/rotation via opencode + OpenRouter; engine ~30 fixes newer than b1.",
        "agents": [
            ("glm52-b2", "GLM-5.2", "opencode", "CN"),
            ("kimi26-b2", "Kimi k2.6", "opencode", "CN"),
            ("dsv4f-b2", "DeepSeek v4-flash", "opencode", "CN"),
            ("hy3-b2", "Hunyuan 3", "opencode", "CN"),
        ],
    },
    {
        "id": "b3", "title": "The compaction experiment — Hunyuan 3 rerun", "date": "2026-07-09",
        "note": "One variable changed vs b2: notebook compaction became compress-not-discard.",
        "agents": [
            ("hy3-b3", "Hunyuan 3 (fixed memory)", "opencode", "CN"),
        ],
    },
    {
        "id": "b4", "title": "GPT-5.6 family — release day +1", "date": "2026-07-10",
        "note": "All three tiers within 24h of GA; engine 19 fixes newer than b2.",
        "agents": [
            ("sol56-b4", "GPT-5.6 Sol", "codex", "US"),
            ("terra56-b4", "GPT-5.6 Terra", "codex", "US"),
            ("luna56-b4", "GPT-5.6 Luna", "codex", "US"),
        ],
    },
]

CAMPAIGN_MODELS = [
    ("show-fable-", "Fable 5", "US"),
    ("show-gpt-", "GPT-5.5", "US"),
    ("show-hy3-", "Hunyuan 3", "CN"),
    ("show-sol-", "GPT-5.6 Sol", "US"),
    ("show-terra-", "GPT-5.6 Terra", "US"),
    ("show-luna-", "GPT-5.6 Luna", "US"),
]


def main() -> int:
    index = {e["name"]: e for e in json.loads((ROOT / "viewer/data/index.json").read_text())}
    campaigns = json.loads((ROOT / "viewer/data/campaigns.json").read_text())

    waves = []
    for wave in WAVES:
        agents = []
        for label, name, harness, region in wave["agents"]:
            games = []
            for i in range(1, 11):
                slug = f"{label}-game-{i:02d}"
                entry = index.get(slug)
                if not entry:
                    continue
                games.append({
                    "slug": slug,
                    "n": i,
                    "score": entry.get("score", 0),
                    "seed": entry.get("seed"),
                    "investigator": ROTATION[(i - 1) % 5],
                    "outcome": entry.get("outcome"),
                    "win": entry.get("outcome") in ("R1", "R2") and entry.get("score", 0) > 0,
                })
            scores = [g["score"] for g in games]
            if not scores:
                continue
            agents.append({
                "label": label, "name": name, "harness": harness, "region": region,
                "games": games,
                "mean": round(sum(scores) / len(scores), 2),
                "final20": round(sum(scores[-2:]) / 2, 2) if len(scores) == 10 else None,
            })
        waves.append({**{k: wave[k] for k in ("id", "title", "date", "note")}, "agents": agents})

    camp_models = []
    for prefix, name, region in CAMPAIGN_MODELS:
        rows = []
        for c in campaigns:
            if not c["name"].startswith(prefix):
                continue
            legs = c.get("legs", [])
            summary_path = ROOT / "campaigns" / c["name"] / "campaign_summary.json"
            mtime = summary_path.stat().st_mtime if summary_path.exists() else 0
            rows.append({
                "name": c["name"],
                "investigator": c["investigator"],
                "score": sum(l.get("score", 0) for l in legs),
                "legs": [
                    {"slug": l["run"], "scenario": l["scenario"].replace("return_to_the_", ""),
                     "resolution": l.get("resolution"), "score": l.get("score", 0)}
                    for l in legs
                ],
                "_mtime": mtime,
            })
        rows.sort(key=lambda r: r["_mtime"])
        for i, r in enumerate(rows):
            r["order"] = i + 1
            del r["_mtime"]
        if rows:
            camp_models.append({"name": name, "region": region, "campaigns": rows})

    ledger = (ROOT / "specs/bug_adjudications.md").read_text()
    entries = len(re.findall(r"^\d+\. \*\*", ledger, re.M))
    findings = {
        "ledger_entries": entries,
        "confirmed_fixed": len(re.findall(r"FIXED", ledger)),
        "not_a_bug": len(re.findall(r"NOT[ -]A[ -]BUG", ledger, re.I)),
        "auditors": [
            {"name": "GPT-5.6 Sol", "confirmed": 18, "claims": 21, "note": "C7 audit wave, 28 games"},
            {"name": "Fable 5", "confirmed": 6, "claims": 8, "note": "b1-era live hunts"},
            {"name": "GPT-5.5", "confirmed": 5, "claims": 8, "note": "b1-era audits + hunts"},
            {"name": "Hunyuan 3", "confirmed": 3, "claims": 70, "note": "swarm + b2/b3 reports"},
        ],
        "vignettes": [
            {"title": "The memory that deleted itself",
             "text": "Hunyuan 3 wrote the exact lesson that would have saved its next Roland game — then destroyed it while compacting its own notebook. One semantic contract on the compact command later, the same decision flipped and the game went from 0 to its best score ever.",
             "slug": "hy3-b3-game-06"},
            {"title": "The weakness that came back from the dead",
             "text": "A defeated Mob Enforcer — a player-deck weakness — was routed to the encounter discard, reshuffled into the encounter deck, and drawn back into play as a fresh enemy. Impossible under the rules; found by the Sol audit wave.",
             "slug": "c7l1-gpt-5.6-luna-skids-devourer_below"},
            {"title": "The parley that ate two treacheries",
             "text": "Alma Hill's parley draws three encounter cards. The engine resolved them in a loop that overwrote its own decision queue — Masked Horrors' doom and Hunting Shadow's damage silently vanished. Three auditor findings, one root cause.",
             "slug": "c7l2-daisy-midnight_masks"},
            {"title": "The reaction that froze the game",
             "text": "Heirloom of Hyperborea's draw reaction interleaved with Blinding Light's skill test and orphaned it — no token, no decision, no way forward. GPT-5.6 Luna spent 14 sessions documenting the stall in its notebook before the engine learned to revive orphaned tests.",
             "slug": None},
        ],
    }

    out = {
        "generated": "see git history",
        "waves": waves,
        "campaigns": camp_models,
        "findings": findings,
    }
    out_path = ROOT / "viewer/data/results.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    total_games = sum(len(a["games"]) for w in waves for a in w["agents"])
    print(f"results.json: {len(waves)} waves, {total_games} games, "
          f"{sum(len(m['campaigns']) for m in camp_models)} campaigns, ledger {entries}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
