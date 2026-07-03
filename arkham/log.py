from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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


def render_event(event: dict[str, Any]) -> str:
    prefix = f"**R{event['round']} · {event['phase']}**"
    event_type = event["type"]
    data = event.get("data", {})
    if event_type == "decision_presented":
        return f"{prefix} — Decision presented: {data.get('prompt', '')}"
    if event_type == "decision_made":
        return f"{prefix} — Decision made: {data.get('label', '')}"
    if event_type == "action_taken":
        return f"{prefix} — {data.get('message', '')}"
    if event_type == "note_added":
        return f"{prefix} — Note added."
    if event_type == "game_end":
        return f"{prefix} — GAME OVER: {data.get('summary', '')}"
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
    ) -> dict[str, Any]:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        event = {
            "seq": _next_seq(self.jsonl_path),
            "round": round,
            "phase": phase,
            "type": type,
            "data": data or {},
        }
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(event_line(event) + "\n")
        with self.md_path.open("a", encoding="utf-8") as handle:
            handle.write(render_event(event) + "\n")
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
