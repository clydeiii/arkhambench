#!/usr/bin/env python3
"""Download card images used by exported runs into viewer/img/ (local cache).

arkhamdb.com throttles bursts of hotlinked image requests, which makes the viewer
flaky. This fetches each needed image once, politely (spaced requests), into
viewer/img/{code}.png. The viewer prefers the local cache and falls back to
arkhamdb, then to text rendering. Images are (c) FFG — the cache is gitignored
and for private research use only.

Usage: python3 scripts/fetch_card_images.py [--data viewer/data] [--delay 1.5]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://arkhamdb.com/bundles/cards/"
# Double-sided cards whose backs the viewer shows (unrevealed locations,
# act/agenda backs in modals).
DOUBLE_SIDED_PREFIXES = ("011",)  # Gathering locations/acts/agendas live in 011xx


def needed_codes(data_dir: Path) -> set[str]:
    codes: set[str] = set()
    for path in sorted(data_dir.glob("*.json")):
        if path.name in {"index.json", "campaigns.json"}:
            continue
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        codes.update(run.get("cards", {}).keys())
        for step in run.get("steps", []):
            state = step.get("state", {})
            for loc in (state.get("locations") or {}).values():
                if loc.get("code"):
                    codes.add(str(loc["code"]))
            for key in ("agenda", "act"):
                obj = state.get(key) or {}
                if obj.get("code"):
                    codes.add(str(obj["code"]))
    return codes


def variants(codes: set[str]) -> list[str]:
    out = set()
    for code in codes:
        out.add(f"{code}.png")
        # Backs for double-sided scenario cards (locations, acts, agendas,
        # investigators). Harmless 404s are skipped quietly.
        out.add(f"{code}b.png")
    return sorted(out)


def known_missing(dest: Path) -> set[str]:
    ledger = dest / "missing.txt"
    if not ledger.exists():
        return set()
    return {line.strip() for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()}


def record_missing(dest: Path, name: str) -> None:
    ledger = dest / "missing.txt"
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(name + "\n")


def fetch(name: str, dest: Path, delay: float, missing: set[str]) -> str:
    target = dest / name
    if target.exists() and target.stat().st_size > 0:
        return "cached"
    if name in missing:
        # Negative cache: most misses are card backs that do not exist
        # (single-sided cards) — no point re-asking arkhamdb every deploy.
        return "known-missing"
    request = urllib.request.Request(BASE + name, headers={"User-Agent": "ArkhamBench viewer cache (private research)"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read()
    except Exception as exc:  # noqa: BLE001 - report and continue
        if "404" in str(exc) or "500" in str(exc):
            record_missing(dest, name)
        time.sleep(delay)
        return f"miss ({exc})"
    target.write_bytes(payload)
    time.sleep(delay)
    return "fetched"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(ROOT / "viewer" / "data"))
    parser.add_argument("--out", default=str(ROOT / "viewer" / "img"))
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()

    dest = Path(args.out)
    dest.mkdir(parents=True, exist_ok=True)
    names = variants(needed_codes(Path(args.data)))
    if not names:
        print("no exported runs found; nothing to fetch")
        return 0
    missing = known_missing(dest)
    print(f"fetching {len(names)} images into {dest} (delay {args.delay}s; {len(missing)} known-missing skipped)")
    fetched = cached = missed = 0
    for name in names:
        status = fetch(name, dest, args.delay, missing)
        if status == "fetched":
            fetched += 1
            print(f"  {name}: fetched")
        elif status in ("cached", "known-missing"):
            cached += 1
        else:
            missed += 1
            print(f"  {name}: {status}", file=sys.stderr)
    print(f"done: {fetched} fetched, {cached} cached, {missed} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
