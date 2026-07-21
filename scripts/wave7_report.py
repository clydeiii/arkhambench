#!/usr/bin/env python3
"""Aggregate wave-7 telemetry (logs/show3-telemetry.jsonl) into per-lane and
per-campaign stats: tokens, wall time, and cost — both the claude CLI's own
figure and an API-list-price recompute. Prints a summary and writes
results/wave7_summary.json.

List prices (July 2026, USD per Mtok in/out). Anthropic cache: write 1.25x
input, read 0.1x input. OpenAI cached input: 0.1x input; reasoning tokens
bill as output.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PRICES = {  # (input, output) USD per 1M tokens
    "claude-fable-5": (10.0, 50.0),
    "claude-sonnet-5": (2.0, 10.0),      # intro pricing through 2026-08-31
    "claude-opus-4-8": (5.0, 25.0),
    "gpt-5.6-sol": (5.0, 30.0),
    "gpt-5.6-terra": (2.5, 15.0),
    "gpt-5.6-luna": (1.0, 6.0),
    "openrouter/tencent/hy3": (0.2, 0.8),
    "openrouter/moonshotai/kimi-k3": (3.0, 15.0),
}


def list_price_cost(row: dict) -> float | None:
    rates = PRICES.get(row.get("model", ""))
    if not rates:
        return None
    rate_in, rate_out = rates[0] / 1e6, rates[1] / 1e6
    if row.get("harness") == "claude":
        return (row.get("input_tokens", 0) * rate_in
                + row.get("cache_creation_input_tokens", 0) * rate_in * 1.25
                + row.get("cache_read_input_tokens", 0) * rate_in * 0.10
                + row.get("output_tokens", 0) * rate_out)
    if row.get("harness") == "codex":
        fresh = max(0, row.get("input_tokens", 0) - row.get("cached_input_tokens", 0))
        return (fresh * rate_in
                + row.get("cached_input_tokens", 0) * rate_in * 0.10
                + (row.get("output_tokens", 0) + row.get("reasoning_output_tokens", 0)) * rate_out)
    if row.get("harness") == "opencode":
        # opencode already computes provider cost per message
        return row.get("opencode_cost_usd")
    return None


def main() -> int:
    rows = [json.loads(line) for line in
            (ROOT / "logs/show3-telemetry.jsonl").read_text().splitlines() if line.strip()]
    rows = [r for r in rows if not r.get("error") and r.get("lane") not in ("hy3", "k3")]
    lanes: dict[str, dict] = {}
    campaigns: dict[str, dict] = {}
    for r in rows:
        for key, bucket in ((r["lane"], lanes), (r["campaign"], campaigns)):
            b = bucket.setdefault(key, {
                "lane": r["lane"], "model": r.get("model"), "harness": r.get("harness"),
                "reasoning": r.get("reasoning"), "sessions": 0, "seconds": 0,
                "total_tokens": 0, "output_tokens": 0, "cli_cost_usd": 0.0,
                "list_cost_usd": 0.0, "list_cost_known": True,
            })
            b["sessions"] += 1
            b["seconds"] += int(r.get("seconds", 0))
            if r.get("harness") == "codex":
                # input_tokens already includes cached reads; reasoning bills as output
                b["total_tokens"] += (int(r.get("input_tokens") or 0)
                                      + int(r.get("output_tokens") or 0)
                                      + int(r.get("reasoning_output_tokens") or 0))
            else:
                b["total_tokens"] += int(r.get("total_tokens") or 0)
            b["output_tokens"] += int(r.get("output_tokens") or 0) + int(r.get("reasoning_output_tokens") or 0)
            if r.get("cli_cost_usd") is not None:
                b["cli_cost_usd"] += float(r["cli_cost_usd"])
            lp = list_price_cost(r)
            if lp is None:
                b["list_cost_known"] = False
            else:
                b["list_cost_usd"] += lp

    # campaign scores
    for name, b in campaigns.items():
        path = ROOT / "campaigns" / name / "campaign.json"
        if path.exists():
            c = json.loads(path.read_text())
            b["score"] = sum(s.get("score", 0) for s in c.get("scenarios", []))
    for lane, b in lanes.items():
        b["campaign_scores"] = {
            name: c.get("score") for name, c in campaigns.items()
            if c["lane"] == lane
        }
        b["score_total"] = sum(v for v in b["campaign_scores"].values() if v is not None)

    out = {"lanes": lanes, "campaigns": campaigns}
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/wave7_summary.json").write_text(json.dumps(out, indent=1))

    print(f"{'lane':7} {'score':>5} {'sessions':>8} {'hours':>6} {'Mtok':>8} {'out-Mtok':>8} {'CLI $':>8} {'list $':>8}")
    for lane, b in sorted(lanes.items(), key=lambda kv: -kv[1]["score_total"]):
        print(f"{lane:7} {b['score_total']:>5} {b['sessions']:>8} {b['seconds']/3600:>6.1f} "
              f"{b['total_tokens']/1e6:>8.1f} {b['output_tokens']/1e6:>8.2f} "
              f"{b['cli_cost_usd']:>8.2f} {b['list_cost_usd']:>8.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
