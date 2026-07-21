#!/usr/bin/env python3
"""Wave-7 per-session telemetry: tokens, time, cost.

Subcommands (both append one JSON line to logs/show3-telemetry.jsonl and print
nothing on success):

  claude <session_json> --meta k=v ...
      Parse a `claude -p --output-format json` result: usage token fields and
      the CLI's own total_cost_usd. Also appends the result text to the agent
      log named in --meta agent_log=... for human-readable transcripts.

  codex <agent_log> <marker_file> --meta k=v ...
      Parse the trailing "tokens used" total from the codex output and harvest
      the input/cached/output/reasoning split from ~/.codex/sessions rollout
      files modified after <marker_file>.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "logs" / "show3-telemetry.jsonl"


def parse_meta(argv: list[str]) -> dict:
    meta = {}
    if "--meta" in argv:
        for pair in argv[argv.index("--meta") + 1:]:
            if "=" in pair:
                key, value = pair.split("=", 1)
                meta[key] = value
    return meta


def emit(row: dict) -> None:
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def cmd_claude(argv: list[str]) -> int:
    meta = parse_meta(argv)
    path = Path(argv[0])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # session died before emitting JSON
        emit({**meta, "error": f"unparseable session json: {exc}", "ts": int(time.time())})
        return 0
    usage = data.get("usage", {})
    row = {
        **meta,
        "input_tokens": usage.get("input_tokens", 0),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "cli_cost_usd": data.get("total_cost_usd"),
        "duration_ms": data.get("duration_ms"),
        "num_turns": data.get("num_turns"),
        "is_error": data.get("is_error", False),
        "ts": int(time.time()),
    }
    row["total_tokens"] = (
        row["input_tokens"] + row["cache_creation_input_tokens"]
        + row["cache_read_input_tokens"] + row["output_tokens"]
    )
    emit(row)
    agent_log = meta.get("agent_log")
    if agent_log:
        with Path(agent_log).open("a", encoding="utf-8") as handle:
            handle.write(str(data.get("result", "")) + "\n")
    return 0


def cmd_codex(argv: list[str]) -> int:
    meta = parse_meta(argv)
    agent_log, marker = Path(argv[0]), Path(argv[1])
    tokens_total = None
    try:
        tail = agent_log.read_text(encoding="utf-8", errors="replace")[-4000:]
        nums = re.findall(r"tokens used\s*\n?\s*([\d,]+)", tail)
        if nums:
            tokens_total = int(nums[-1].replace(",", ""))
    except Exception:
        pass
    # token_count events are PER-TURN: sum every event for true billed flows
    split = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0,
             "reasoning_output_tokens": 0}
    turns = 0
    marker_mtime = marker.stat().st_mtime if marker.exists() else 0
    sessions = Path.home() / ".codex" / "sessions"
    for rollout in sessions.rglob("rollout-*.jsonl"):
        if rollout.stat().st_mtime <= marker_mtime:
            continue
        try:
            for line in rollout.read_text(encoding="utf-8", errors="replace").splitlines():
                if '"input_tokens"' not in line:
                    continue
                try:
                    event = json.loads(line)
                except Exception:
                    continue
                text = json.dumps(event)
                vals = {}
                for key in split:
                    found = re.findall(rf'"{key}":\s*(\d+)', text)
                    if found:
                        vals[key] = int(found[-1])
                if vals:
                    turns += 1
                    for key, value in vals.items():
                        split[key] += value
        except Exception:
            continue
    row = {**meta, **split, "tokens_used_reported": tokens_total,
           "turns": turns, "ts": int(time.time())}
    row["total_tokens"] = (split["input_tokens"] + split["output_tokens"]
                           + split["reasoning_output_tokens"])
    emit(row)
    return 0


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "claude":
        return cmd_claude(rest)
    if cmd == "codex":
        return cmd_codex(rest)
    if cmd == "opencode":
        return cmd_opencode(rest)
    print(f"unknown subcommand {cmd}", file=sys.stderr)
    return 2




def cmd_opencode(argv: list[str]) -> int:
    """opencode <start_epoch> <end_epoch> <model_substr> --meta k=v ...
    Sum usage of opencode.db messages in the window matching the model."""
    import sqlite3

    meta = parse_meta(argv)
    start, end, model_substr = int(argv[0]), int(argv[1]), argv[2]
    db = Path.home() / ".local/share/opencode/opencode.db"
    totals = {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0,
              "cache_read_tokens": 0, "cache_write_tokens": 0, "opencode_cost_usd": 0.0}
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        rows = conn.execute(
            "SELECT data FROM message WHERE time_created BETWEEN ? AND ? AND data LIKE ?",
            ((start - 60) * 1000, (end + 60) * 1000, f"%{model_substr}%"),
        ).fetchall()
        conn.close()
        for (raw,) in rows:
            try:
                data = json.loads(raw)
            except Exception:
                continue
            tokens = data.get("tokens") or {}
            if not tokens:
                continue
            totals["input_tokens"] += tokens.get("input", 0)
            totals["output_tokens"] += tokens.get("output", 0)
            totals["reasoning_tokens"] += tokens.get("reasoning", 0)
            cache = tokens.get("cache") or {}
            totals["cache_read_tokens"] += cache.get("read", 0)
            totals["cache_write_tokens"] += cache.get("write", 0)
            totals["opencode_cost_usd"] += float(data.get("cost") or 0)
    except Exception as exc:
        totals["error"] = f"db read failed: {exc}"
    row = {**meta, **totals, "ts": int(time.time())}
    row["total_tokens"] = (row["input_tokens"] + row["output_tokens"]
                           + row["reasoning_tokens"] + row["cache_read_tokens"]
                           + row["cache_write_tokens"])
    emit(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
