#!/usr/bin/env python3
"""Report exercised XP-card coverage across one or more AHLCG run dirs.

A card is EXERCISED when a log records that its asset entered play, its event
resolved, it was committed to a test, or one of its triggered abilities was
used.  Every other XP card is DORMANT.  The ability-use column is deliberately
separate: playing a permanent such as Police Badge does not prove that its
ability text was exercised.

Usage:
  python3 scripts/xp_coverage.py bench/c7-coverage
  python3 scripts/xp_coverage.py runs/game-01 runs/game-02
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

RESOLUTION_EVENTS = {
    "card_played",
    "event_attached",
    "event_played",
    "card_committed",
    "close_call",
    "sure_gamble",
}

# Events emitted by activated/reaction abilities on XP assets.  These are
# counted independently from entering play or being committed.
ABILITY_EVENTS = {
    "aquinnah",
    "beat_cop_ability",
    "book_of_shadows",
    "cat_burglar",
    "disc_of_itzamna",
    "encyclopedia",
    "grotesque_statue",
    "police_badge",
    "rabbits_foot",
    "skill_boost",
}


def load_xp_cards() -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "data" / "cards").glob("*.json")):
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(rows, list):
            continue
        for card in rows:
            if int(card.get("xp") or 0) > 0:
                cards[str(card["code"])] = card
    if len(cards) != 32:
        raise RuntimeError(f"expected 32 XP cards in data/cards, found {len(cards)}")
    return cards


def game_dirs(target: Path) -> list[Path]:
    if (target / "log.jsonl").is_file():
        return [target]
    return sorted(
        path.parent
        for path in target.rglob("log.jsonl")
        if path.parent.is_dir()
    )


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def event_code(data: dict[str, Any], instances: dict[str, str]) -> str | None:
    card_code = data.get("card_code")
    if card_code:
        return str(card_code)
    card_id = data.get("card")
    return instances.get(str(card_id)) if card_id is not None else None


def scan_run(
    run_dir: Path,
    xp_cards: dict[str, dict[str, Any]],
) -> tuple[set[str], Counter[str], Counter[str]]:
    state = load_json(run_dir / "state.json")
    raw_instances = state.get("card_instances", {}) if isinstance(state, dict) else {}
    instances = {
        str(instance_id): str(instance.get("card_code", ""))
        for instance_id, instance in raw_instances.items()
        if isinstance(instance, dict)
    }
    in_deck = {code for code in instances.values() if code in xp_cards}
    exercised: Counter[str] = Counter()
    abilities: Counter[str] = Counter()
    log_path = run_dir / "log.jsonl"
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return in_deck, exercised, abilities

    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        event_type = str(event.get("type", ""))
        data = event.get("data") or {}
        if not isinstance(data, dict):
            continue
        code = event_code(data, instances)
        if code in xp_cards and event_type in RESOLUTION_EVENTS:
            exercised[code] += 1
        if code in xp_cards and event_type in ABILITY_EVENTS:
            abilities[code] += 1
            exercised[code] += 1

        # Weapon activations identify the asset in the action message rather
        # than carrying its instance ID.  Shotgun is the sole XP weapon.
        if event_type == "action_spent" and data.get("action") == "asset_fight":
            if "with Shotgun" in str(data.get("message", "")):
                abilities["01029"] += 1
                exercised["01029"] += 1

    return in_deck, exercised, abilities


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    xp_cards = load_xp_cards()
    runs: list[Path] = []
    for arg in sys.argv[1:]:
        runs.extend(game_dirs(Path(arg)))
    runs = sorted(set(runs))
    if not runs:
        print("No run dirs containing log.jsonl found.", file=sys.stderr)
        return 1

    deck_runs: Counter[str] = Counter()
    resolutions: Counter[str] = Counter()
    abilities: Counter[str] = Counter()
    for run_dir in runs:
        in_deck, run_resolutions, run_abilities = scan_run(run_dir, xp_cards)
        deck_runs.update(in_deck)
        resolutions.update(run_resolutions)
        abilities.update(run_abilities)

    print("| Code | Card | Type | XP | Runs | Status | Resolutions | Ability uses |")
    print("|---|---|---|---:|---:|---|---:|---:|")
    dormant: list[str] = []
    for code, card in sorted(xp_cards.items()):
        status = "EXERCISED" if resolutions[code] else "DORMANT"
        if status == "DORMANT":
            dormant.append(code)
        print(
            f"| {code} | {markdown_escape(str(card.get('name', code)))} "
            f"| {card.get('type_code', '')} | {int(card.get('xp') or 0)} "
            f"| {deck_runs[code]} | {status} | {resolutions[code]} | {abilities[code]} |"
        )

    if dormant:
        labels = ", ".join(f"{code} {xp_cards[code]['name']}" for code in dormant)
        print(f"\nDORMANT ({len(dormant)}): {labels}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
