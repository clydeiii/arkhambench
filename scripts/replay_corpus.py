from __future__ import annotations

import argparse
import json
import tempfile
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arkham.errors import EngineError
from arkham.game import Game


JsonDict = dict[str, Any]


@dataclass
class ReplayResult:
    run_dir: str
    status: str
    decisions_replayed: int
    step: int | None = None
    detail: str | None = None
    expected: Any = None
    actual: Any = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay recorded ArkhamBench decisions against the current engine."
    )
    parser.add_argument(
        "--dirs",
        nargs="+",
        default=["bench"],
        help="directories to scan for completed runs (default: bench)",
    )
    parser.add_argument("--out", help="write replay details as JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any run diverges or errors",
    )
    args = parser.parse_args(argv)

    roots = [Path(item) for item in args.dirs]
    run_dirs = find_run_dirs(roots)
    results = [replay_run(path) for path in run_dirs]
    print_report(results)
    if args.out:
        write_snapshot(Path(args.out), roots, results)
    if args.strict and any(result.status != "CLEAN" for result in results):
        return 1
    return 0


def find_run_dirs(roots: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    run_dirs: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        candidates = [root]
        if root.is_dir():
            candidates.extend(path for path in root.glob("game-*") if path.is_dir())
            candidates.extend(path for path in root.glob("*/game-*") if path.is_dir())
            candidates.extend(path for path in root.rglob("game-*") if path.is_dir())
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            if is_completed_run(candidate):
                seen.add(resolved)
                run_dirs.append(candidate)
    return sorted(run_dirs)


def is_completed_run(run_dir: Path) -> bool:
    return (run_dir / "result.json").exists() and (run_dir / "log.jsonl").exists()


def replay_run(run_dir: Path) -> ReplayResult:
    try:
        meta = read_json(run_dir / "meta.json")
        entries = read_jsonl(run_dir / "log.jsonl")
        prompts = [
            str(entry.get("data", {}).get("prompt", ""))
            for entry in entries
            if entry.get("type") == "decision_presented"
        ]
        choices = [
            dict(entry.get("data", {}))
            for entry in entries
            if entry.get("type") == "decision_made"
        ]
    except Exception as exc:
        return ReplayResult(str(run_dir), "ERROR", 0, detail=f"could not read run: {exc}")

    try:
        with tempfile.TemporaryDirectory(prefix="arkham-replay-") as tmp:
            game = Game.new(
                seed=int(meta.get("seed", 1)),
                difficulty=str(meta.get("difficulty", "standard")),
                deck_path=meta.get("deck"),
                run_dir=Path(tmp) / "run",
                scenario=str(meta.get("scenario", "the_gathering")),
                investigator=investigator_id(meta),
            )
            for step, choice in enumerate(choices):
                pending = game.current_decision()
                expected_prompt = prompts[step] if step < len(prompts) else None
                actual_prompt = pending.prompt if pending else None
                if actual_prompt != expected_prompt:
                    return ReplayResult(
                        str(run_dir),
                        "DIVERGED",
                        step,
                        step=step,
                        detail="prompt mismatch",
                        expected=expected_prompt,
                        actual=actual_prompt,
                    )

                try:
                    option_index = int(choice.get("option", 0))
                except (TypeError, ValueError):
                    return ReplayResult(
                        str(run_dir),
                        "DIVERGED",
                        step,
                        step=step,
                        detail="recorded option is not an integer",
                        expected=choice.get("option"),
                        actual=None,
                    )
                if pending is None or option_index < 1 or option_index > len(pending.options):
                    return ReplayResult(
                        str(run_dir),
                        "DIVERGED",
                        step,
                        step=step,
                        detail="recorded option is not currently legal",
                        expected=option_index,
                        actual=len(pending.options) if pending else 0,
                    )

                expected_label = choice.get("label")
                actual_label = pending.options[option_index - 1].label
                if actual_label != expected_label:
                    return ReplayResult(
                        str(run_dir),
                        "DIVERGED",
                        step,
                        step=step,
                        detail="chosen option label mismatch",
                        expected=expected_label,
                        actual=actual_label,
                    )

                try:
                    game.apply(option_index)
                except (EngineError, ValueError) as exc:
                    return ReplayResult(
                        str(run_dir),
                        "DIVERGED",
                        step,
                        step=step,
                        detail=f"recorded choice no longer applies: {exc}",
                        expected=expected_label,
                        actual=None,
                    )

            if len(prompts) > len(choices):
                step = len(choices)
                pending = game.current_decision()
                expected_prompt = prompts[step]
                actual_prompt = pending.prompt if pending else None
                if actual_prompt != expected_prompt:
                    return ReplayResult(
                        str(run_dir),
                        "DIVERGED",
                        step,
                        step=step,
                        detail="trailing prompt mismatch",
                        expected=expected_prompt,
                        actual=actual_prompt,
                    )
            return ReplayResult(str(run_dir), "CLEAN", len(choices))
    except Exception as exc:
        return ReplayResult(str(run_dir), "ERROR", 0, detail=str(exc))


def investigator_id(meta: JsonDict) -> str:
    investigator = meta.get("investigator")
    if isinstance(investigator, dict):
        return str(investigator.get("id") or "roland")
    if investigator:
        return str(investigator)
    return "roland"


def print_report(results: list[ReplayResult]) -> None:
    if not results:
        print("No completed runs found.")
        return
    for result in results:
        if result.status == "CLEAN":
            print(f"CLEAN     {result.run_dir} ({result.decisions_replayed} decisions)")
        elif result.status == "DIVERGED":
            print(
                f"DIVERGED  {result.run_dir} step {result.step}: "
                f"{result.detail}; expected={short(result.expected)!r} actual={short(result.actual)!r}"
            )
        else:
            print(f"ERROR     {result.run_dir}: {result.detail}")
    counts = {status: sum(1 for result in results if result.status == status) for status in ("CLEAN", "DIVERGED", "ERROR")}
    print(
        "Summary: "
        f"{counts['CLEAN']} CLEAN, {counts['DIVERGED']} DIVERGED, {counts['ERROR']} ERROR "
        f"({len(results)} runs)"
    )


def write_snapshot(path: Path, roots: list[Path], results: list[ReplayResult]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "dirs": [str(root) for root in roots],
        "summary": {
            "clean": sum(1 for result in results if result.status == "CLEAN"),
            "diverged": sum(1 for result in results if result.status == "DIVERGED"),
            "error": sum(1 for result in results if result.status == "ERROR"),
            "total": len(results),
        },
        "runs": [asdict(result) for result in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def short(value: Any, limit: int = 180) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def read_json(path: Path) -> JsonDict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[JsonDict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
