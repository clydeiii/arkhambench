#!/usr/bin/env python3
"""Detect general-strategy mistakes in run dirs — the "new player errors" lens.

Detectors (Clyde's examples from hy3-b2 game-01, 2026-07-08):
  aoo        — attacks of opportunity provoked (enemy_attack source field)
  handlimit  — forced discards to hand size at upkeep (kept 8+ cards)
  lastdraw   — spent the FINAL action of a turn on the basic draw action
  unarmedin  — moved into a location holding a ready enemy with no weapon in play

Usage:
  python3 scripts/strategy_mistakes.py bench/hy3-b2            # whole bench label
  python3 scripts/strategy_mistakes.py runs/somegame           # single run
  python3 scripts/strategy_mistakes.py bench/hy3-b2 bench/hy3-b3   # comparison table
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_weapon_codes() -> set[str]:
    codes: set[str] = set()
    for path in (ROOT / "data" / "cards").glob("*.json"):
        try:
            cards = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if not isinstance(cards, list):
            continue
        for card in cards:
            traits = card.get("traits") or ""
            if "weapon" in traits.lower():
                codes.add(card["code"])
    return codes


WEAPONS = load_weapon_codes()


def scan_run(run_dir: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {"aoo": [], "handlimit": [], "lastdraw": [], "unarmedin": []}
    log_path = run_dir / "log.jsonl"
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            data = event.get("data", {})
            if event.get("type") == "enemy_attack" and data.get("source") == "attack of opportunity":
                found["aoo"].append(f"R{event.get('round')}: {data.get('message', '')}")
            if event.get("type") == "decision_presented" and "Discard to hand size" in (data.get("prompt") or ""):
                found["handlimit"].append(f"R{event.get('round')}: {data.get('prompt')}")
    timeline_path = run_dir / "timeline.jsonl"
    if timeline_path.exists():
        for line in timeline_path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            chose, state = entry.get("chose"), entry.get("state") or {}
            inv = state.get("investigator") or {}
            if not chose:
                continue
            label = chose if isinstance(chose, str) else chose.get("label", "")
            if label.startswith("Draw 1 card") and inv.get("actions_remaining") == 1:
                found["lastdraw"].append(f"R{entry.get('round')}: drew with final action")
            if label.startswith("Move to "):
                target_name = label[len("Move to "):].strip()
                for loc in (state.get("locations") or {}).values():
                    if loc.get("name") != target_name or not loc.get("enemy_ids"):
                        continue
                    enemies = state.get("enemies") or {}
                    ready = [e for e in loc["enemy_ids"] if not enemies.get(e, {}).get("exhausted")]
                    if not ready:
                        continue
                    armed = any(
                        (state.get("card_instances") or {}).get(cid, {}).get("card_code") in WEAPONS
                        for cid in inv.get("play_area") or []
                    )
                    if not armed:
                        found["unarmedin"].append(
                            f"R{entry.get('round')}: moved to {target_name} "
                            f"(ready enemies: {len(ready)}) with no weapon in play"
                        )
    return found


def game_dirs(target: Path) -> list[Path]:
    games = sorted(target.glob("game-*"))
    return [g for g in games if g.is_dir()] or [target]


def main() -> int:
    targets = [Path(arg) for arg in sys.argv[1:]]
    if not targets:
        print(__doc__)
        return 1
    keys = ["aoo", "handlimit", "lastdraw", "unarmedin"]
    for target in targets:
        print(f"\n=== {target}")
        totals = {k: 0 for k in keys}
        for game in game_dirs(target):
            found = scan_run(game)
            counts = {k: len(found[k]) for k in keys}
            for k in keys:
                totals[k] += counts[k]
            if any(counts.values()):
                summary = "  ".join(f"{k}={counts[k]}" for k in keys if counts[k])
                print(f"{game.name}: {summary}")
                for k in keys:
                    for detail in found[k]:
                        print(f"    [{k}] {detail}")
        print(f"TOTALS {target.name}: " + "  ".join(f"{k}={totals[k]}" for k in keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
