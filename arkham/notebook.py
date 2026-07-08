from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path


def resolve_notebook(path: str | None = None, run_dir: Path | None = None) -> Path:
    """Precedence: --notebook flag > AHLCG_NOTEBOOK env > run meta.json > ./notebook.md."""
    if path:
        return Path(path)
    if os.environ.get("AHLCG_NOTEBOOK"):
        return Path(os.environ["AHLCG_NOTEBOOK"])
    if run_dir is not None:
        meta_path = Path(run_dir) / "meta.json"
        if meta_path.exists():
            import json

            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                meta = {}
            if meta.get("notebook"):
                return Path(meta["notebook"])
    return Path.cwd() / "notebook.md"


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def add_note(
    notebook_path: Path,
    text: str,
    *,
    run_name: str | None = None,
    round_number: int | None = None,
) -> None:
    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    run_label = run_name or "none"
    round_label = str(round_number) if round_number is not None else "?"
    entry = f"## [{_timestamp()}] Run {run_label} · Round {round_label}\n\n{text}\n\n"
    with notebook_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def show(notebook_path: Path) -> str:
    if not notebook_path.exists():
        return ""
    return notebook_path.read_text(encoding="utf-8")


def compact(notebook_path: Path, body: str) -> Path:
    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    archive_dir = notebook_path.parent / "notebook_history"
    archive_dir.mkdir(parents=True, exist_ok=True)
    stem = _timestamp().replace(":", "")
    archive_path = archive_dir / f"{stem}.md"
    suffix = 1
    while archive_path.exists():
        archive_path = archive_dir / f"{stem}-{suffix}.md"
        suffix += 1
    previous = show(notebook_path)
    archive_path.write_text(previous, encoding="utf-8")
    notebook_path.write_text(body.rstrip() + "\n", encoding="utf-8")
    return archive_path


def list_archives(notebook_path: Path) -> list[Path]:
    archive_dir = notebook_path.parent / "notebook_history"
    if not archive_dir.exists():
        return []
    return sorted(archive_dir.glob("*.md"), key=lambda p: (p.stat().st_mtime_ns, p.name))


def read_archive(notebook_path: Path, which: str) -> tuple[Path, str]:
    """which is a 1-based index (oldest first) or 'latest'. Raises ValueError."""
    archives = list_archives(notebook_path)
    if not archives:
        raise ValueError("no archived notebooks exist")
    if which == "latest":
        path = archives[-1]
    else:
        try:
            index = int(which)
        except ValueError:
            raise ValueError(f"expected an archive number 1-{len(archives)} or 'latest', got {which!r}")
        if not 1 <= index <= len(archives):
            raise ValueError(f"archive number out of range: {index} (have 1-{len(archives)})")
        path = archives[index - 1]
    return path, path.read_text(encoding="utf-8")
