#!/usr/bin/env python3
"""Generate the README results charts as dependency-free SVGs from bench data.

    python3 scripts/make_charts.py [--labels fable5-b1,opus48-b1,...] [--out results]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

B2_AGENTS = [
    ("glm52-b2", "GLM-5.2", "#b83280"),
    ("kimi26-b2", "Kimi k2.6", "#dd6b20"),
    ("dsv4f-b2", "DeepSeek v4-flash", "#319795"),
    ("hy3-b2", "Hunyuan 3", "#718096"),
]

AGENTS = [
    ("fable5-b1", "Fable 5", "#6b46c1"),
    ("opus48-b1", "Opus 4.8", "#2b6cb0"),
    ("sonnet5-b1", "Sonnet 5", "#d69e2e"),
    ("gpt55-b1", "GPT-5.5", "#38a169"),
]
ROTATION = ["R", "D", "S", "A", "W", "R", "D", "S", "A", "W"]
INVESTIGATORS = ["roland", "daisy", "skids", "agnes", "wendy"]


def load(label: str) -> list[dict]:
    path = ROOT / "bench" / label / "bench.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    games = sorted(data["games"], key=lambda g: int(g["game"]))
    return [g for g in games if g.get("status") == "complete"]


def svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Helvetica, Arial, sans-serif">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
    ]


def scores_by_game(out: Path, agents=None, title="Score per game (Return to The Gathering, shared seeds)") -> None:
    width, height = 760, 420
    left, right, top, bottom = 60, 170, 40, 70
    plot_w, plot_h = width - left - right, height - top - bottom
    max_score, games = 10, 10
    parts = svg_header(width, height)
    parts.append(f'<text x="{left}" y="24" font-size="17" font-weight="bold">{title}</text>')

    def x(i: int) -> float:  # game index 1..10
        return left + (i - 1) * plot_w / (games - 1)

    def y(s: float) -> float:
        return top + plot_h - s * plot_h / max_score

    for s in range(0, max_score + 1, 2):
        parts.append(f'<line x1="{left}" y1="{y(s)}" x2="{left+plot_w}" y2="{y(s)}" stroke="#e2e2e2"/>')
        parts.append(f'<text x="{left-10}" y="{y(s)+4}" font-size="11" text-anchor="end" fill="#555">{s}</text>')
    for i in range(1, games + 1):
        parts.append(f'<text x="{x(i)}" y="{top+plot_h+18}" font-size="11" text-anchor="middle" fill="#555">{i}</text>')
        parts.append(f'<text x="{x(i)}" y="{top+plot_h+34}" font-size="10" text-anchor="middle" fill="#999">{ROTATION[i-1]}</text>')
    parts.append(f'<text x="{left+plot_w/2}" y="{height-16}" font-size="12" text-anchor="middle" fill="#555">game (investigator: R=Roland D=Daisy S=Skids A=Agnes W=Wendy)</text>')
    # final-20% window shading (games 9-10)
    parts.insert(3, f'<rect x="{x(9)-8}" y="{top}" width="{x(10)-x(9)+16}" height="{plot_h}" fill="#f6f0fa"/>')
    parts.append(f'<text x="{x(9.5)}" y="{top+14}" font-size="10" text-anchor="middle" fill="#8a6bb8">scored window</text>')

    legend_y = top + 6
    for label, name, color in (agents or AGENTS):
        games_data = load(label)
        pts = [(int(g["game"]), float(g["score"])) for g in games_data]
        if not pts:
            continue
        path = " ".join(f'{"M" if i == 0 else "L"}{x(g)},{y(s)}' for i, (g, s) in enumerate(pts))
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for g, s in pts:
            parts.append(f'<circle cx="{x(g)}" cy="{y(s)}" r="3.5" fill="{color}"/>')
        wins = {int(g["game"]) for g in games_data if str(g.get("resolution", "")).startswith("R") and g.get("resolution") != "R3"}
        for g, s in pts:
            if g in wins:
                parts.append(f'<circle cx="{x(g)}" cy="{y(s)}" r="7" fill="none" stroke="{color}" stroke-width="1.5"/>')
        parts.append(f'<rect x="{left+plot_w+14}" y="{legend_y-9}" width="12" height="12" fill="{color}"/>')
        parts.append(f'<text x="{left+plot_w+32}" y="{legend_y+2}" font-size="12">{name}</text>')
        legend_y += 22
    parts.append(f'<text x="{left+plot_w+14}" y="{legend_y+4}" font-size="10" fill="#777">◯ = won (R1/R2)</text>')
    parts.append("</svg>")
    out.write_text("\n".join(parts), encoding="utf-8")


def second_visit_deltas(out: Path) -> None:
    width, height = 760, 300
    left, top, bottom = 60, 46, 60
    plot_w, plot_h = width - left - 30, height - top - bottom
    parts = svg_header(width, height)
    parts.append(f'<text x="{left}" y="24" font-size="17" font-weight="bold">Second visit vs first visit, per investigator (learning signal)</text>')
    lo, hi = -6, 9

    def y(v: float) -> float:
        return top + plot_h - (v - lo) * plot_h / (hi - lo)

    for v in range(lo, hi + 1, 3):
        parts.append(f'<line x1="{left}" y1="{y(v)}" x2="{left+plot_w}" y2="{y(v)}" stroke="#e2e2e2"/>')
        parts.append(f'<text x="{left-10}" y="{y(v)+4}" font-size="11" text-anchor="end" fill="#555">{v:+d}</text>')
    parts.append(f'<line x1="{left}" y1="{y(0)}" x2="{left+plot_w}" y2="{y(0)}" stroke="#888" stroke-width="1.5"/>')

    n_agents = len(AGENTS)
    group_w = plot_w / len(INVESTIGATORS)
    bar_w = group_w / (n_agents + 1.5)
    for gi, inv in enumerate(INVESTIGATORS):
        gx = left + gi * group_w
        parts.append(f'<text x="{gx+group_w/2}" y="{top+plot_h+22}" font-size="12" text-anchor="middle" fill="#333">{inv.title()}</text>')
        for ai, (label, name, color) in enumerate(AGENTS):
            games = load(label)
            visits = [float(g["score"]) for g in games if g.get("investigator") == inv]
            if len(visits) != 2:
                continue
            delta = visits[1] - visits[0]
            bx = gx + (ai + 0.75) * bar_w
            y0, y1 = y(0), y(delta)
            parts.append(
                f'<rect x="{bx}" y="{min(y0, y1)}" width="{bar_w*0.85}" height="{abs(y1-y0) or 1}" fill="{color}"/>'
            )
    legend_x = left
    for label, name, color in AGENTS:
        parts.append(f'<rect x="{legend_x}" y="{height-26}" width="11" height="11" fill="{color}"/>')
        parts.append(f'<text x="{legend_x+16}" y="{height-16}" font-size="11">{name}</text>')
        legend_x += 110
    parts.append("</svg>")
    out.write_text("\n".join(parts), encoding="utf-8")


def game_steps(label: str, game: int) -> int | None:
    log = ROOT / "bench" / label / f"game-{game:02d}" / "log.md"
    if not log.exists():
        return None
    return sum(1 for line in log.read_text(encoding="utf-8").splitlines() if "Decision presented" in line)


def steps_and_score(out: Path, agents: list[tuple[str, str, str]], title: str) -> bool:
    rows = []
    for label, name, color in agents:
        games = load(label)
        if not games:
            continue
        steps = [s for s in (game_steps(label, int(g["game"])) for g in games) if s is not None]
        if not steps:
            continue
        rows.append((name, color, sum(steps) / len(steps), sum(float(g["score"]) for g in games) / len(games)))
    if not rows:
        return False
    width = 760
    row_h, top, left = 64, 56, 150
    height = top + row_h * len(rows) + 70
    max_steps = max(r[2] for r in rows) * 1.15
    max_score = 10.0
    bar_w = width - left - 130
    parts = svg_header(width, height)
    parts.append(f'<text x="16" y="26" font-size="17" font-weight="bold">{title}</text>')
    parts.append(f'<text x="16" y="44" font-size="11" fill="#777">per-model averages over the 10-game gauntlet — steps = decisions faced before the game ended; score = XP − trauma (0–10)</text>')
    y = top
    for name, color, steps, score in rows:
        parts.append(f'<text x="{left-10}" y="{y+18}" font-size="13" text-anchor="end" font-weight="bold">{name}</text>')
        w_steps = steps / max_steps * bar_w
        parts.append(f'<rect x="{left}" y="{y}" width="{w_steps:.1f}" height="20" fill="{color}"/>')
        parts.append(f'<text x="{left+w_steps+6:.1f}" y="{y+15}" font-size="12" fill="#333">{steps:.0f} steps</text>')
        w_score = score / max_score * bar_w
        parts.append(f'<rect x="{left}" y="{y+24}" width="{w_score:.1f}" height="12" fill="{color}" opacity="0.45"/>')
        parts.append(f'<text x="{left+w_score+6:.1f}" y="{y+34}" font-size="11" fill="#555">score {score:.2f}</text>')
        y += row_h
    parts.append(f'<text x="{left}" y="{y+18}" font-size="10" fill="#999">solid bar: mean decisions per game (longer = survived longer) · faded bar: mean score (0–10 scale)</text>')
    parts.append("</svg>")
    out.write_text("\n".join(parts), encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results")
    args = parser.parse_args()
    out_dir = ROOT / args.out
    out_dir.mkdir(exist_ok=True)
    scores_by_game(out_dir / "scores_by_game.svg")
    scores_by_game(out_dir / "scores_by_game_b2.svg", B2_AGENTS,
                   "Score per game — open-weights run (same seeds and rotation)")
    second_visit_deltas(out_dir / "second_visit_deltas.svg")
    B4_AGENTS = [
        ("sol56-b4", "GPT-5.6 Sol", "#c05621"),
        ("terra56-b4", "GPT-5.6 Terra", "#2f855a"),
        ("luna56-b4", "GPT-5.6 Luna", "#2b6cb0"),
    ]
    scores_by_game(out_dir / "scores_by_game_b4.svg", B4_AGENTS,
                   "Score per game — GPT-5.6 family (same seeds and rotation)")
    if steps_and_score(out_dir / "steps_vs_score_b4.svg", B4_AGENTS, "Game length vs score — GPT-5.6 family"):
        print("steps_vs_score_b4.svg written")
    scores_by_game(
        out_dir / "scores_by_game_hy3_b3.svg",
        [("hy3-b2", "Hunyuan 3 (b2: destructive compaction)", "#718096"),
         ("hy3-b3", "Hunyuan 3 (b3: compress-not-discard)", "#2b6cb0")],
        "Hunyuan 3, same 10 seeds — before/after the notebook-compaction fix",
    )
    if steps_and_score(out_dir / "steps_vs_score_b1.svg", AGENTS, "Game length vs score — main run (US frontier models)"):
        print("steps_vs_score_b1.svg written")
    if steps_and_score(out_dir / "steps_vs_score_b2.svg", B2_AGENTS, "Game length vs score — open-weights run (China open models)"):
        print("steps_vs_score_b2.svg written")
    print(f"charts written to {out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
