#!/usr/bin/env python3
"""Post-hoc rules audit of a completed game by a strong model.

The cheap way to hunt engine bugs: a fast/cheap agent PLAYS the game, then a
strong model AUDITS the finished transcript in one pass (reading a log costs a
small fraction of playing interactively). Usage:

    python3 scripts/audit_game.py bench/<label>/game-01 [more runs...] \
        [--model claude-fable-5] [--auditor-label audit]

Findings land in <run>/audit.md and on stdout.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build_prompt(run_dir: Path, adjudications: str) -> str:
    return f"""You are auditing a completed game of Arkham Horror: The Card Game for
RULES-ENFORCEMENT BUGS in the engine that ran it. You did not play this game; you are
reviewing the transcript the way a tournament judge reviews a match record.

The transcript: {run_dir}/log.md  (public information only; read it in full)
Any in-game bug reports the player filed: {run_dir}/bug_reports.md (may not exist)
Rules authority: docs_agent/rules_reference.md (the Rules Reference is final),
docs_agent/scenario_reference.md (scenario setup/scoring), docs_agent/decks_guide.md.
Card text lookup: `./ahlcg card <name-or-code>` — ALWAYS verify against exact card
text before reporting a finding about a card.

Audit in two passes:

1. PER-DECISION LEGALITY — for each decision in the log, were the offered options
   legal (nothing offered that rules forbid; nothing plainly missing that rules
   require)? Was each resolution's math right (the log prints full skill-test math)?
   Were costs charged correctly?

2. CROSS-STEP EXPECTATION TRACKING — reconstruct the state as you read (resources,
   actions, clues, doom, damage/horror, enemy positions, deck/hand counts) and flag
   places where the next step contradicts your model: a charged action with no
   effect, a Forced trigger that should have fired but did not, doom/clue totals
   that jump, an effect resolving in the wrong order, an ability used more often
   than its limit allows.

KNOWN ADJUDICATIONS (do not re-report; these were already ruled on):
{adjudications}

Report format — write EXACTLY this structure and nothing else:
- If you find nothing: the single line `AUDIT CLEAN`.
- Otherwise one block per finding:
  `## Finding <n> — <one-line summary>`
  `- Step/round: <log reference>`
  `- Severity: exploit | pro-player | display | unclear`
  `- Rule: <RR entry or exact card text you verified>`
  `- Evidence: <the log lines and why they violate the rule>`
Be precise and conservative: a finding you cannot ground in quoted card text or a
named RR entry is not a finding. Do not report play-quality mistakes — only rules
enforcement. Do not modify any files."""


def audit_run(run_dir: Path, model: str, adjudications: str) -> tuple[str, int]:
    prompt = build_prompt(run_dir, adjudications)
    allowed = (
        f"Read(docs_agent/**),Read({run_dir}/log.md),Read({run_dir}/bug_reports.md),Bash(./ahlcg card:*)"
    )
    disallowed = "Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Bash(./ahlcg new:*),Bash(./ahlcg do:*)"
    argv = [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--allowedTools",
        allowed,
        "--disallowedTools",
        disallowed,
        "--max-turns",
        "60",
    ]
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=ROOT)
    return proc.stdout.strip(), proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit completed games for engine rules bugs.")
    parser.add_argument("runs", nargs="+", help="run directories (each with log.md)")
    parser.add_argument("--model", default="claude-fable-5")
    args = parser.parse_args(argv)

    adjudications_path = ROOT / "specs" / "bug_adjudications.md"
    adjudications = adjudications_path.read_text(encoding="utf-8") if adjudications_path.exists() else "(none)"

    failures = 0
    for run in args.runs:
        run_dir = Path(run)
        if not (run_dir / "log.md").exists():
            print(f"skip {run_dir}: no log.md", file=sys.stderr)
            continue
        print(f"=== auditing {run_dir} with {args.model}")
        report, rc = audit_run(run_dir, args.model, adjudications)
        out = run_dir / "audit.md"
        out.write_text(report + "\n", encoding="utf-8")
        print(report)
        print(f"--- written to {out}")
        if rc != 0:
            failures += 1
            print(f"warning: auditor exited {rc} for {run_dir}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
