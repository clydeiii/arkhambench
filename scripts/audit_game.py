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
enforcement. Do not modify any files. Do NOT read the engine source (arkham/), card
data JSON (data/), tests, or specs — audit strictly from the transcript, the
docs_agent/ documents, and `./ahlcg card` lookups, like a judge who has the rulebook
but not the implementation."""


def _opencode_argv(model: str, prompt: str) -> list[str]:
    # opencode has no tool-restriction flags; the prompt's honor-system rules
    # apply (same trust level as the codex branch). Needs OPENROUTER_API_KEY
    # in the environment for openrouter/* models.
    import os

    return [os.path.expanduser("~/.opencode/bin/opencode"), "run", "-m",
            model.split(":", 1)[1], prompt]


def audit_run(run_dir: Path, model: str, adjudications: str) -> tuple[str, int]:
    prompt = build_prompt(run_dir, adjudications)
    if model == "codex":
        # codex CLI default model; default sandbox is read-only, which is all
        # an auditor needs (the script itself writes audit.md from stdout).
        argv = ["codex", "exec", prompt]
    elif model.startswith("codex:"):
        argv = ["codex", "exec", "-m", model.split(":", 1)[1], prompt]
    elif model.startswith("opencode:"):
        argv = _opencode_argv(model, prompt)
    else:
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


def build_campaign_prompt(campaign_dir: Path, adjudications: str) -> str:
    return f"""You are auditing the CAMPAIGN LAYER of a completed Arkham Horror LCG
campaign for rules-enforcement bugs in the engine that ran it. The scenario
transcripts are audited separately — your job is everything BETWEEN scenarios.

Campaign state: {campaign_dir}/campaign.json (read in full)
Materialized decks per scenario: {campaign_dir}/decks/deck-*.json
Per-scenario results: the result.json in each run dir listed in campaign.json.
Rules authority: docs_agent/campaign_guide.md (campaign flow + XP rules),
docs_agent/rules_reference.md, docs_agent/decks_guide.md. Card lookup:
`./ahlcg card <name-or-code>`.

Audit these dimensions:

1. XP LEDGER — recompute every scenario's earned XP from its result and every
   purchase's cost (new card = max(1, level); same-title upgrade = level
   difference, min 1). Verify xp_unspent/xp_earned_total/xp_spent_total are
   consistent at every step and never negative.
2. DECK LEGALITY OVER TIME — for each deck-N.json: exactly 30 counted cards
   (signatures, weaknesses, story assets excluded), max 2 copies per title
   across levels, class/level access respected for the investigator, signatures
   present, weaknesses never removed, earned weaknesses/story assets persist to
   later decks.
3. CONTINUITY — trauma accumulates correctly from per-scenario deltas and shows
   up as starting damage/horror in the NEXT scenario's transcript; campaign log
   facts flow into scenario setup (house standing/burned -> start location,
   Ghoul Priest alive -> shuffled in, cultists got away -> Devourer doom/spawns,
   past midnight -> opening-hand discard, elderthing token added); killed
   investigators never return; Lita appears in decks only after being earned
   and included.

KNOWN ADJUDICATIONS (do not re-report):
{adjudications}

Report format: `AUDIT CLEAN` or `## Finding <n> — ...` blocks exactly as in a
scenario audit (Step/round becomes the campaign step or deck file). Findings must
be grounded in the campaign guide's stated rules or exact card text. Do not modify
any files. Do NOT read arkham/, data/cards JSON, tests/, or specs/ other than what
is listed above."""


def build_reasoning_prompt(run_dir: Path) -> str:
    return f"""You are auditing the REASONING of an AI agent that played Arkham Horror:
The Card Game, looking for RULES MISCONCEPTIONS in its stated rationales — beliefs
about the game that are factually wrong, whether or not they changed the outcome.

The transcript: {run_dir}/log.md. The agent's one-line rationales appear as italic
"why" lines after each "Decision made" line. Rules authority:
docs_agent/rules_reference.md, docs_agent/scenario_reference.md, and exact card text
via `./ahlcg card <name-or-code>`.

For each rationale that asserts something about the RULES or the GAME STATE, check it:
- rules beliefs ("clues return to locations", "fighting disengages", "this cancels
  the token") — verify against the RR/card text;
- state beliefs ("the location still has clues", "I can afford this") — verify
  against the transcript's status lines.
Ignore pure strategy judgments ("safer to leave") and hindsight mistakes; report only
FALSE FACTUAL BELIEFS. This is not a rules-enforcement audit of the engine — the
engine may have behaved correctly while the agent believed otherwise.

Report format — exactly:
- `REASONING CLEAN` if nothing found; otherwise one block per item:
  `## Misconception <n> — <the false belief, quoted>`
  `- Step/round: <log reference>`
  `- Truth: <the correct rule/state, with RR entry or card text>`
  `- Consequence: <wasted action / bad play / harmless comment>`
Do not modify files. Do NOT read arkham/, data/, tests/, or specs/."""


def audit_reasoning(run_dir: Path, model: str) -> tuple[str, int]:
    prompt = build_reasoning_prompt(run_dir)
    if model == "codex":
        argv = ["codex", "exec", prompt]
    elif model.startswith("codex:"):
        argv = ["codex", "exec", "-m", model.split(":", 1)[1], prompt]
    elif model.startswith("opencode:"):
        argv = _opencode_argv(model, prompt)
    else:
        allowed = f"Read(docs_agent/**),Read({run_dir}/log.md),Bash(./ahlcg card:*)"
        disallowed = "Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**)"
        argv = ["claude", "-p", prompt, "--model", model,
                "--allowedTools", allowed, "--disallowedTools", disallowed, "--max-turns", "40"]
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=ROOT)
    return proc.stdout.strip(), proc.returncode


def audit_campaign(campaign_dir: Path, model: str, adjudications: str) -> tuple[str, int]:
    prompt = build_campaign_prompt(campaign_dir, adjudications)
    if model == "codex":
        argv = ["codex", "exec", prompt]
    elif model.startswith("codex:"):
        argv = ["codex", "exec", "-m", model.split(":", 1)[1], prompt]
    elif model.startswith("opencode:"):
        argv = _opencode_argv(model, prompt)
    else:
        allowed = (
            f"Read(docs_agent/**),Read({campaign_dir}/campaign.json),Read({campaign_dir}/campaign_summary.json),"
            f"Read({campaign_dir}/decks/**),Read({campaign_dir}/runs/*/result.json),"
            f"Read({campaign_dir}/runs/*/log.md),Bash(./ahlcg card:*)"
        )
        disallowed = "Read(arkham/**),Read(data/**),Read(tests/**),Read(specs/**),Bash(./ahlcg new:*),Bash(./ahlcg do:*)"
        argv = ["claude", "-p", prompt, "--model", model,
                "--allowedTools", allowed, "--disallowedTools", disallowed, "--max-turns", "80"]
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=ROOT)
    return proc.stdout.strip(), proc.returncode


def campaign_run_dirs(campaign_dir: Path) -> list[Path]:
    import json

    campaign = json.loads((campaign_dir / "campaign.json").read_text(encoding="utf-8"))
    return [Path(row["run"]) for row in campaign.get("scenarios", [])]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit completed games for engine rules bugs.")
    parser.add_argument("runs", nargs="*", help="run directories (each with log.md)")
    parser.add_argument("--campaign", help="campaign dir: audit each scenario run, then the campaign layer")
    parser.add_argument("--campaign-only", action="store_true",
                        help="with --campaign: audit only the campaign layer, skip its scenario runs")
    parser.add_argument("--reasoning", action="store_true",
                        help="also audit each run's agent rationales for rules misconceptions (-> reasoning_audit.md)")
    parser.add_argument("--model", default="claude-fable-5")
    parser.add_argument("--out-name", default="audit.md", help="report filename written into each run dir")
    args = parser.parse_args(argv)
    if not args.runs and not args.campaign:
        parser.error("give run directories and/or --campaign")

    adjudications_path = ROOT / "specs" / "bug_adjudications.md"
    adjudications = adjudications_path.read_text(encoding="utf-8") if adjudications_path.exists() else "(none)"

    run_list = [Path(run) for run in args.runs]
    if args.campaign and not args.campaign_only:
        run_list.extend(campaign_run_dirs(Path(args.campaign)))

    failures = 0
    for run_dir in run_list:
        if not (run_dir / "log.md").exists():
            print(f"skip {run_dir}: no log.md", file=sys.stderr)
            continue
        print(f"=== auditing {run_dir} with {args.model}")
        report, rc = audit_run(run_dir, args.model, adjudications)
        out = run_dir / args.out_name
        out.write_text(report + "\n", encoding="utf-8")
        print(report)
        print(f"--- written to {out}")
        if rc != 0:
            failures += 1
            print(f"warning: auditor exited {rc} for {run_dir}", file=sys.stderr)
        if args.reasoning:
            print(f"=== reasoning audit {run_dir} with {args.model}")
            report, rc = audit_reasoning(run_dir, args.model)
            (run_dir / "reasoning_audit.md").write_text(report + "\n", encoding="utf-8")
            print(report)
            if rc != 0:
                failures += 1

    if args.campaign:
        campaign_dir = Path(args.campaign)
        print(f"=== auditing campaign layer {campaign_dir} with {args.model}")
        report, rc = audit_campaign(campaign_dir, args.model, adjudications)
        out = campaign_dir / "campaign_audit.md"
        out.write_text(report + "\n", encoding="utf-8")
        print(report)
        print(f"--- written to {out}")
        if rc != 0:
            failures += 1
            print(f"warning: campaign auditor exited {rc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
