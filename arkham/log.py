from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import GameState


def _next_seq(path: Path) -> int:
    if not path.exists():
        return 1
    seq = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                seq += 1
    return seq + 1


def event_line(event: dict[str, Any]) -> str:
    return json.dumps(event, sort_keys=True)


def status_line(state: GameState) -> str:
    investigator = state.investigator
    location = state.locations.get(investigator.location_id)
    location_name = location.name if location else investigator.location_id
    parts = [f"R{state.round}·{state.phase}"]
    if state.phase == "Investigation":
        parts[0] += f" a{investigator.actions_remaining}/3"
    doom = (state.agenda.doom if state.agenda else 0) + sum(
        instance.doom for instance in state.card_instances.values()
    ) + sum(enemy.doom for enemy in state.enemies.values())
    act_stage = state.act.stage if state.act else 0
    agenda_stage = state.agenda.stage if state.agenda else 0
    doom_threshold = state.agenda.threshold if state.agenda else 0
    return (
        f"[{parts[0]} | {location_name} | clu{investigator.clues} res{investigator.resources} | "
        f"dmg{investigator.damage}/{investigator.health} hor{investigator.horror}/{investigator.sanity} | "
        f"h{len(investigator.hand)} d{len(investigator.deck)} x{len(investigator.discard)} | "
        f"Act{act_stage} Agd{agenda_stage} doom{doom}/{doom_threshold}]"
    )


def render_event(event: dict[str, Any]) -> str:
    prefix = f"**R{event['round']} · {event['phase']}**"
    event_type = event["type"]
    data = event.get("data", {})
    if event_type == "decision_presented":
        rendered = f"{prefix} — Decision presented: {data.get('prompt', '')}"
        if event.get("status"):
            return f"{event['status']}\n{rendered}"
        return rendered
    if event_type == "decision_made":
        return f"{prefix} — Decision made: {data.get('label', '')}"
    if event_type == "action_taken":
        return f"{prefix} — {data.get('message', '')}"
    if event_type == "note_added":
        return f"{prefix} — Note added."
    if event_type == "game_end":
        rendered = f"{prefix} — GAME OVER: {data.get('summary', '')}"
        if event.get("status"):
            return f"{event['status']}\n{rendered}"
        return rendered
    if data.get("message"):
        return f"{prefix} — {data.get('message')}"
    return f"{prefix} — {event_type}: {data}"


class EventLog:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.jsonl_path = run_dir / "log.jsonl"
        self.md_path = run_dir / "log.md"

    def append(
        self,
        *,
        round: int,
        phase: str,
        type: str,
        data: dict[str, Any] | None = None,
        status: str | None = None,
        status_in_jsonl: bool = False,
    ) -> dict[str, Any]:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        event = {
            "seq": _next_seq(self.jsonl_path),
            "round": round,
            "phase": phase,
            "type": type,
            "data": data or {},
        }
        if status is not None and status_in_jsonl:
            event["status"] = status
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(event_line(event) + "\n")
        with self.md_path.open("a", encoding="utf-8") as handle:
            md_event = event if status is None else {**event, "status": status}
            handle.write(render_event(md_event) + "\n")
        return event


def read_markdown(run_dir: Path, tail: int | None = None) -> str:
    path = run_dir / "log.md"
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    if tail is not None:
        lines = lines[-tail:]
    return "\n".join(lines)


def read_jsonl(run_dir: Path, tail: int | None = None) -> str:
    path = run_dir / "log.jsonl"
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    if tail is not None:
        lines = lines[-tail:]
    return "\n".join(lines)
