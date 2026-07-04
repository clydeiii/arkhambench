from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import data as card_data
from .errors import EngineError
from .game import Game


JsonDict = dict[str, Any]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run", help="single run directory to export")
    source.add_argument("--all-bench", help="bench label directory containing game-* runs")
    parser.add_argument("--out", default="viewer/data", help="output data directory")
    parser.add_argument("--label", default=None, help="export name for --run")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    if args.run:
        export_run(Path(args.run), out_dir, name=args.label)
    else:
        export_bench(Path(args.all_bench), out_dir)
    rebuild_index(out_dir)
    return 0


def export_bench(bench_dir: Path, out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for run_dir in sorted(path for path in bench_dir.iterdir() if path.is_dir() and path.name.startswith("game-")):
        paths.append(export_run(run_dir, out_dir, name=f"{bench_dir.name}-{run_dir.name}", rebuild=False))
    rebuild_index(out_dir)
    return paths


def export_run(run_dir: Path, out_dir: Path, *, name: str | None = None, rebuild: bool = True) -> Path:
    run_dir = Path(run_dir)
    export_name = name or run_dir.name
    meta = _read_json(run_dir / "meta.json") or {}
    result = _read_json(run_dir / "result.json")
    timeline_path = run_dir / "timeline.jsonl"

    if timeline_path.exists():
        timeline = _read_jsonl(timeline_path)
        complete = True
        divergence_step = None
    else:
        timeline, complete, divergence_step = _replay_timeline(run_dir, meta)

    payload = _assemble_export(
        name=export_name,
        run_dir=run_dir,
        meta=meta,
        result=result,
        timeline=timeline,
        complete=complete,
        divergence_step=divergence_step,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{_slug(export_name)}.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if rebuild:
        rebuild_index(out_dir)
    return out_path


def rebuild_index(out_dir: Path) -> list[JsonDict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[JsonDict] = []
    for path in sorted(out_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        meta = payload.get("meta", {})
        result = payload.get("result") or {}
        rows.append(
            {
                "name": str(meta.get("name", path.stem)),
                "file": path.name,
                "seed": meta.get("seed"),
                "difficulty": meta.get("difficulty"),
                "steps": len(payload.get("steps", [])),
                "outcome": result.get("outcome"),
                "score": result.get("score"),
                "complete": bool(meta.get("complete", False)),
            }
        )
    rows.sort(key=lambda row: (str(row["name"]), str(row["file"])))
    (out_dir / "index.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rows


def _assemble_export(
    *,
    name: str,
    run_dir: Path,
    meta: JsonDict,
    result: JsonDict | None,
    timeline: list[JsonDict],
    complete: bool,
    divergence_step: int | None,
) -> JsonDict:
    steps = _steps_from_timeline(timeline)
    scenario = None
    for step in steps:
        if isinstance(step.get("state"), dict) and step["state"].get("scenario"):
            scenario = str(step["state"]["scenario"])
            break
    scenario_card = SCENARIO_REFERENCE_CARDS.get(scenario or "")
    return {
        "meta": {
            "name": name,
            "run_dir": str(run_dir),
            "seed": meta.get("seed"),
            "difficulty": meta.get("difficulty"),
            "engine_version": meta.get("engine_version"),
            "exported_at": _now(),
            "complete": complete,
            "divergence_step": divergence_step,
            "scenario": scenario,
            "scenario_card": scenario_card,
            "investigator": meta.get("investigator"),
        },
        "cards": _card_bundle(steps, extra_codes=[scenario_card] if scenario_card else []),
        "steps": steps,
        "result": result,
    }


def _steps_from_timeline(timeline: list[JsonDict]) -> list[JsonDict]:
    steps: list[JsonDict] = []
    for index, line in enumerate(timeline):
        pending = line.get("pending")
        chose = timeline[index + 1].get("chose") if index + 1 < len(timeline) else None
        decision = None
        if pending is not None:
            option = chose.get("option") if isinstance(chose, dict) else None
            chosen_label = chose.get("label") if isinstance(chose, dict) else None
            decision = {
                "prompt": pending.get("prompt", ""),
                "options": list(pending.get("options", [])),
                "chosen": option,
                "chosen_label": chosen_label,
            }
        steps.append(
            {
                "i": int(line.get("i", index)),
                "round": int(line.get("round", 0)),
                "phase": str(line.get("phase", "")),
                "status": str(line.get("status", "")),
                "events": list(line.get("events", [])),
                "decision": decision,
                "state": line.get("state", {}),
            }
        )
    return steps


def _replay_timeline(run_dir: Path, meta: JsonDict) -> tuple[list[JsonDict], bool, int | None]:
    log_entries = _read_jsonl(run_dir / "log.jsonl")
    prompts = [
        str(entry.get("data", {}).get("prompt", ""))
        for entry in log_entries
        if entry.get("type") == "decision_presented"
    ]
    choices = [
        dict(entry.get("data", {}))
        for entry in log_entries
        if entry.get("type") == "decision_made"
    ]

    with tempfile.TemporaryDirectory(prefix="arkham-export-") as tmp:
        replay_dir = Path(tmp) / "run"
        game = Game.new(
            seed=int(meta.get("seed", 1)),
            difficulty=str(meta.get("difficulty", "standard")),
            deck_path=meta.get("deck"),
            run_dir=replay_dir,
            scenario=str(meta.get("scenario", "the_gathering")),
            investigator=str((meta.get("investigator") or {}).get("id", "roland")),
        )
        divergence_step: int | None = None
        for step, choice in enumerate(choices):
            expected_prompt = prompts[step] if step < len(prompts) else None
            pending = game.current_decision()
            actual_prompt = pending.prompt if pending else None
            if actual_prompt != expected_prompt:
                divergence_step = step
                _warn_divergence(run_dir, step, expected_prompt, actual_prompt)
                break
            try:
                game.apply(int(choice.get("option", 0)))
            except (EngineError, ValueError) as exc:
                divergence_step = step
                _warn_divergence(run_dir, step, f"legal option {choice.get('option')}", str(exc))
                break

        if divergence_step is None and len(prompts) > len(choices):
            pending = game.current_decision()
            expected_prompt = prompts[len(choices)]
            actual_prompt = pending.prompt if pending else None
            if actual_prompt != expected_prompt:
                divergence_step = len(choices)
                _warn_divergence(run_dir, divergence_step, expected_prompt, actual_prompt)

        return _read_jsonl(replay_dir / "timeline.jsonl"), divergence_step is None, divergence_step


def _warn_divergence(run_dir: Path, step: int, expected: object, actual: object) -> None:
    print(
        f"WARNING: replay diverged for {run_dir} at decision step {step}: "
        f"expected {expected!r}, got {actual!r}",
        file=sys.stderr,
    )


# Scenario reference cards (chaos-token effects) per scenario id.
SCENARIO_REFERENCE_CARDS = {"the_gathering": "01104"}


def _card_bundle(steps: list[JsonDict], extra_codes: list[str] | None = None) -> JsonDict:
    codes: set[str] = set(extra_codes or [])
    all_cards = card_data.cards_by_code()
    for step in steps:
        state = step.get("state", {})
        if not isinstance(state, dict):
            continue
        _collect_codes_from_state(state, codes, all_cards)
    return {code: _card_export(all_cards.get(code, {"code": code, "name": code})) for code in sorted(codes)}


def _collect_codes_from_state(state: JsonDict, codes: set[str], all_cards: dict[str, JsonDict]) -> None:
    investigator = state.get("investigator") or {}
    if isinstance(investigator, dict):
        _add_code(codes, investigator.get("card_code"))

    instances = state.get("card_instances") or {}
    if isinstance(instances, dict):
        for instance in instances.values():
            if isinstance(instance, dict):
                _add_code(codes, instance.get("card_code"))

    enemies = state.get("enemies") or {}
    if isinstance(enemies, dict):
        for enemy in enemies.values():
            if isinstance(enemy, dict):
                _add_code(codes, enemy.get("card_code"))

    locations = state.get("locations") or {}
    if isinstance(locations, dict):
        for location in locations.values():
            if isinstance(location, dict):
                _add_code(codes, location.get("code"))

    for key in ("agenda", "act"):
        item = state.get(key)
        if isinstance(item, dict):
            _add_code(codes, item.get("code"))

    for item_id in state.get("victory_display") or []:
        if isinstance(instances, dict) and item_id in instances and isinstance(instances[item_id], dict):
            _add_code(codes, instances[item_id].get("card_code"))
        elif isinstance(locations, dict) and item_id in locations and isinstance(locations[item_id], dict):
            _add_code(codes, locations[item_id].get("code"))
        elif str(item_id) in all_cards:
            _add_code(codes, item_id)


def _add_code(codes: set[str], value: object) -> None:
    if value:
        codes.add(str(value))


def _card_export(card: JsonDict) -> JsonDict:
    return {
        "name": card.get("name"),
        "type_code": card.get("type_code"),
        "faction_code": card.get("faction_code"),
        "cost": card.get("cost"),
        "text": card.get("text"),
        "traits": card.get("traits"),
        "icons": {
            "willpower": int(card.get("skill_willpower") or 0),
            "intellect": int(card.get("skill_intellect") or 0),
            "combat": int(card.get("skill_combat") or 0),
            "agility": int(card.get("skill_agility") or 0),
            "wild": int(card.get("skill_wild") or 0),
        },
        "health": card.get("health"),
        "sanity": card.get("sanity"),
        "enemy_fight": card.get("enemy_fight"),
        "enemy_evade": card.get("enemy_evade"),
        "enemy_damage": card.get("enemy_damage"),
        "enemy_horror": card.get("enemy_horror"),
        "shroud": card.get("shroud"),
        "clues": card.get("clues"),
        "doom": card.get("doom"),
        "victory": card.get("victory"),
        "is_unique": card.get("is_unique"),
        "slot": card.get("slot"),
    }


def _read_json(path: Path) -> JsonDict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[JsonDict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _slug(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", name.strip()).strip("-")
    return slug or "run"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
