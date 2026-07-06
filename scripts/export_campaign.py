#!/usr/bin/env python3
"""Export a full campaign (all scenario legs + upgrade phases) for the viewer.

    python3 scripts/export_campaign.py campaigns/<name> [more...] [--out viewer/data]

Each leg exports as a normal run (<campaign>-<k>-<scenario-short>); the campaign
manifest (upgrade phases reconstructed from the per-scenario deck snapshots and the
XP ledger) is appended to <out>/campaigns.json, which the viewer reads to render the
campaign strip and upgrade modals.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from arkham import data as card_data  # noqa: E402
from arkham.export import export_run, rebuild_index  # noqa: E402

SHORT = {
    "return_to_the_gathering": "gathering",
    "return_to_the_midnight_masks": "midnight-masks",
    "return_to_the_devourer_below": "devourer",
    "the_gathering": "gathering",
    "the_midnight_masks": "midnight-masks",
    "the_devourer_below": "devourer",
}


def card_info(code: str) -> dict:
    card = card_data.get_card(code)
    return {
        "code": code,
        "name": str(card.get("name", code)),
        "level": int(card.get("xp") or 0),
        "faction": str(card.get("faction_code", "")),
        "weakness": str(card.get("subtype_code", "")) in {"weakness", "basicweakness"},
    }


def diff_upgrade_phase(before: dict[str, int], after: dict[str, int]) -> dict:
    added: list[str] = []
    removed: list[str] = []
    for code in sorted(set(before) | set(after)):
        delta = int(after.get(code, 0)) - int(before.get(code, 0))
        added.extend([code] * max(0, delta))
        removed.extend([code] * max(0, -delta))
    purchases = []
    spent = 0
    removed_pool = list(removed)
    for code in added:
        info = card_info(code)
        if code == "01117":
            purchases.append({**info, "kind": "story", "cost": 0})
            continue
        if info["weakness"]:
            purchases.append({**info, "kind": "weakness-gained", "cost": 0})
            continue
        upgrade_source = next(
            (
                r
                for r in removed_pool
                if card_info(r)["name"] == info["name"] and card_info(r)["level"] < info["level"]
            ),
            None,
        )
        if upgrade_source:
            removed_pool.remove(upgrade_source)
            cost = max(1, info["level"] - card_info(upgrade_source)["level"])
            purchases.append({**info, "kind": f"upgrade of {upgrade_source}", "cost": cost,
                              "replaced": card_info(upgrade_source)})
        else:
            cost = max(1, info["level"])
            purchases.append({**info, "kind": "new", "cost": cost})
        spent += purchases[-1]["cost"]
    removals = [card_info(code) for code in removed_pool]
    return {"purchases": purchases, "removals": removals, "xp_spent": spent}


def export_campaign(campaign_dir: Path, out_dir: Path) -> dict:
    campaign = json.loads((campaign_dir / "campaign.json").read_text(encoding="utf-8"))
    name = campaign_dir.name
    legs = []
    deck_slots = []
    for k, row in enumerate(campaign.get("scenarios", []), start=1):
        run_dir = Path(row["run"])
        export_name = f"{name}-{k}-{SHORT.get(row['scenario'], row['scenario'])}"
        export_run(run_dir, out_dir, name=export_name, rebuild=False)
        legs.append(
            {
                "leg": k,
                "run": export_name,
                "scenario": row["scenario"],
                "resolution": row.get("resolution"),
                "xp_earned": row.get("xp_earned", 0),
                "score": row.get("score", 0),
                "trauma_delta": row.get("trauma_delta", {}),
            }
        )
        deck_path = campaign_dir / "decks" / f"deck-{k}.json"
        deck = json.loads(deck_path.read_text()) if deck_path.exists() else None
        deck_slots.append(deck["slots"] if deck else None)
        legs[-1]["investigator_code"] = (deck or {}).get("investigator_code")
    upgrades = []
    xp_bank = 0
    for k in range(len(legs)):
        xp_bank += int(legs[k]["xp_earned"])
        if k + 1 >= len(legs) or deck_slots[k] is None or deck_slots[k + 1] is None:
            continue
        if legs[k]["investigator_code"] != legs[k + 1]["investigator_code"]:
            # investigator was killed/insane; fresh replacement deck, XP reset
            upgrades.append({
                "after_leg": k + 1,
                "replacement": True,
                "purchases": [], "removals": [], "xp_spent": 0,
                "xp_before": xp_bank, "xp_after": 0,
            })
            xp_bank = 0
            continue
        phase = diff_upgrade_phase(deck_slots[k], deck_slots[k + 1])
        phase["after_leg"] = k + 1
        phase["xp_before"] = xp_bank
        xp_bank -= phase["xp_spent"]
        phase["xp_after"] = xp_bank
        upgrades.append(phase)
    manifest = {
        "name": name,
        "campaign": campaign.get("campaign"),
        "investigator": campaign.get("investigator"),
        "difficulty": campaign.get("difficulty"),
        "seed": campaign.get("seed"),
        "legs": legs,
        "upgrades": upgrades,
        "outcomes": {
            "killed_investigators": campaign.get("killed_investigators", []),
            **{k: campaign.get("log", {}).get(k) for k in
               ("arkham_succumbed", "ritual_broken", "umordhoth_repelled", "lita_sacrificed")},
        },
        "campaign_score": sum(int(l.get("score") or 0) for l in legs),
    }
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaigns", nargs="+")
    parser.add_argument("--out", default="viewer/data")
    args = parser.parse_args(argv)
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "campaigns.json"
    existing = json.loads(index_path.read_text()) if index_path.exists() else []
    by_name = {c["name"]: c for c in existing}
    for arg in args.campaigns:
        manifest = export_campaign(Path(arg), out_dir)
        by_name[manifest["name"]] = manifest
        print(f"exported campaign {manifest['name']}: {len(manifest['legs'])} legs, "
              f"{len(manifest['upgrades'])} upgrade phases")
    index_path.write_text(json.dumps(sorted(by_name.values(), key=lambda c: c["name"]), indent=2) + "\n",
                          encoding="utf-8")
    rebuild_index(out_dir)
    print(f"campaign index: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
