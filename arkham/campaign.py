from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import data as card_data
from .errors import EngineError
from .game import Game
from .serialize import atomic_write_json
from .upgrade import full_deck_slots, split_starting_deck, validate_deck


RETURN_SEQUENCE = ["return_to_the_gathering", "return_to_the_midnight_masks", "return_to_the_devourer_below"]
ORIGINAL_SEQUENCE = ["the_gathering", "the_midnight_masks", "the_devourer_below"]


def current_campaign_file() -> Path:
    return Path.cwd() / ".current_campaign"


def resolve_campaign_dir(path: str | None) -> Path:
    if path:
        return Path(path)
    pointer = current_campaign_file()
    if pointer.exists():
        text = pointer.read_text(encoding="utf-8").strip()
        if text:
            return Path(text)
    raise EngineError("campaign directory not specified; use --dir or .current_campaign")


def campaign_path(campaign_dir: Path) -> Path:
    return campaign_dir / "campaign.json"


def load_campaign(campaign_dir: str | Path) -> dict[str, Any]:
    path = campaign_path(Path(campaign_dir))
    if not path.exists():
        raise EngineError(f"missing campaign file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_campaign(campaign_dir: str | Path, campaign: dict[str, Any]) -> None:
    atomic_write_json(campaign_path(Path(campaign_dir)), campaign)


def create_campaign(
    campaign_dir: str | Path,
    *,
    investigator: str,
    difficulty: str,
    seed: int,
    original: bool = False,
) -> dict[str, Any]:
    campaign_dir = Path(campaign_dir)
    if campaign_path(campaign_dir).exists():
        raise EngineError(f"campaign already exists: {campaign_path(campaign_dir)}")
    if investigator not in card_data.INVESTIGATOR_CODES:
        raise EngineError(f"unknown investigator: {investigator}")
    sequence = ORIGINAL_SEQUENCE if original else RETURN_SEQUENCE
    campaign = {
        "campaign": "night_of_the_zealot" if original else "return_to_night_of_the_zealot",
        "difficulty": difficulty,
        "seed": int(seed),
        "investigator": investigator,
        "killed_investigators": [],
        "trauma": {"physical": 0, "mental": 0},
        "xp_unspent": 0,
        "xp_earned_total": 0,
        "xp_spent_total": 0,
        "deck": split_starting_deck(investigator),
        "chaos_bag_additions": [],
        "log": {
            "your_house_standing": True,
            "ghoul_priest_alive": True,
            "lita_was_forced_to_find_others": False,
            "lita_earned": False,
            "lita_in_deck": False,
            "cultists_interrogated": [],
            "cultists_got_away": [],
            "past_midnight": False,
            "arkham_succumbed": None,
            "ritual_broken": None,
            "umordhoth_repelled": None,
            "lita_sacrificed": None,
            "notes": [],
        },
        "scenarios": [],
        "next": sequence[0],
        "phase": "scenario",
    }
    validate_deck(campaign, final=True)
    campaign_dir.mkdir(parents=True, exist_ok=True)
    save_campaign(campaign_dir, campaign)
    current_campaign_file().write_text(str(campaign_dir), encoding="utf-8")
    return campaign


def campaign_sequence(campaign: dict[str, Any]) -> list[str]:
    return ORIGINAL_SEQUENCE if campaign.get("campaign") == "night_of_the_zealot" else RETURN_SEQUENCE


def scenario_index(campaign: dict[str, Any]) -> int:
    return len(campaign.get("scenarios", [])) + 1


def scenario_seed(campaign: dict[str, Any]) -> int:
    return int(campaign.get("seed", 1)) * 100 + scenario_index(campaign)


def materialize_deck(campaign_dir: Path, campaign: dict[str, Any], run_dir: Path) -> Path:
    deck_dir = campaign_dir / "decks"
    deck_dir.mkdir(parents=True, exist_ok=True)
    path = deck_dir / f"deck-{len(campaign.get('scenarios', [])) + 1}.json"
    atomic_write_json(
        path,
        {
            "name": f"{campaign['investigator']} campaign deck",
            "campaign_deck": True,
            "investigator_code": card_data.INVESTIGATOR_CODES[str(campaign["investigator"])],
            "slots": full_deck_slots(campaign["deck"]),
        },
    )
    return path


def start_next_scenario(campaign_dir: str | Path) -> tuple[Path, Game]:
    campaign_dir = Path(campaign_dir)
    campaign = load_campaign(campaign_dir)
    if campaign.get("phase") != "scenario":
        raise EngineError(f"campaign is in {campaign.get('phase')} phase; finish that phase first")
    scenario = str(campaign.get("next") or "")
    if not scenario:
        raise EngineError("campaign has no next scenario")
    idx = scenario_index(campaign)
    run_dir = campaign_dir / "runs" / f"c-{campaign_dir.name}-{idx}"
    deck_path = materialize_deck(campaign_dir, campaign, run_dir)
    kwargs: dict[str, Any] = {}
    log = campaign.get("log", {})
    if scenario in {"the_midnight_masks", "return_to_the_midnight_masks"}:
        kwargs.update(
            {
                "house_burned": not bool(log.get("your_house_standing", True)),
                "ghoul_priest_alive": bool(log.get("ghoul_priest_alive", True)),
                "lita_forced_to_find_others": bool(log.get("lita_was_forced_to_find_others", False)),
            }
        )
    if scenario in {"the_devourer_below", "return_to_the_devourer_below"}:
        kwargs.update(
            {
                "cultists_got_away": list(log.get("cultists_got_away", [])),
                "past_midnight": bool(log.get("past_midnight", False)),
                "ghoul_priest_alive": bool(log.get("ghoul_priest_alive", False)),
                "lita_in_deck": bool(log.get("lita_in_deck", False)),
            }
        )
    game = Game.new(
        seed=scenario_seed(campaign),
        difficulty=str(campaign["difficulty"]),
        deck_path=deck_path,
        run_dir=run_dir,
        scenario=scenario,
        investigator=str(campaign["investigator"]),
        trauma=dict(campaign.get("trauma", {})),
        campaign_context=mission_context(campaign),
        **kwargs,
    )
    (Path.cwd() / ".current_run").write_text(str(run_dir), encoding="utf-8")
    return run_dir, game


def mission_context(campaign: dict[str, Any]) -> dict[str, Any]:
    return {
        "campaign": campaign.get("campaign"),
        "scenario_number": scenario_index(campaign),
        "scenario_total": len(campaign_sequence(campaign)),
        "trauma": dict(campaign.get("trauma", {})),
        "xp_unspent": int(campaign.get("xp_unspent", 0)),
        "log": dict(campaign.get("log", {})),
    }


def record_current_run(campaign_dir: str | Path, run_arg: str | None = None) -> dict[str, Any]:
    campaign_dir = Path(campaign_dir)
    campaign = load_campaign(campaign_dir)
    if campaign.get("phase") != "scenario":
        raise EngineError(f"campaign is in {campaign.get('phase')} phase; cannot record a scenario now")
    run_dir = Path(run_arg) if run_arg else _current_run_dir()
    result_path = run_dir / "result.json"
    if not result_path.exists():
        raise EngineError(f"run is not complete; missing {result_path}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    expected_scenario = str(campaign.get("next") or "")
    result_scenario = result.get("scenario")
    if result_scenario is None and isinstance(result.get("campaign"), dict):
        result_scenario = result["campaign"].get("scenario")
    if result_scenario is not None and str(result_scenario) != expected_scenario:
        raise EngineError(f"run scenario {result_scenario} does not match campaign next scenario {expected_scenario}")
    scenario = str(result_scenario or expected_scenario)
    xp = int(result.get("xp", 0))
    trauma = dict(result.get("trauma", {}))
    physical_delta = int(trauma.get("physical", 0))
    mental_delta = int(trauma.get("mental", 0))
    campaign["xp_unspent"] = int(campaign.get("xp_unspent", 0)) + xp
    campaign["xp_earned_total"] = int(campaign.get("xp_earned_total", 0)) + xp
    campaign["trauma"]["physical"] = int(campaign["trauma"].get("physical", 0)) + physical_delta
    campaign["trauma"]["mental"] = int(campaign["trauma"].get("mental", 0)) + mental_delta
    apply_campaign_log(campaign, result)
    campaign["scenarios"].append(
        {
            "scenario": scenario,
            "run": str(run_dir),
            "status": "complete",
            "resolution": result.get("resolution", result.get("outcome")),
            "xp_earned": xp,
            "score": int(result.get("score", 0)),
            "trauma_delta": {"physical": physical_delta, "mental": mental_delta},
        }
    )
    sequence = campaign_sequence(campaign)
    finished = len(campaign["scenarios"]) >= len(sequence)
    killed = investigator_killed_or_insane(campaign, result)
    if killed:
        if str(campaign["investigator"]) not in campaign["killed_investigators"]:
            campaign["killed_investigators"].append(str(campaign["investigator"]))
        campaign["xp_unspent"] = 0
    if finished:
        campaign["phase"] = "complete"
        campaign["next"] = None
        write_summary(campaign_dir, campaign)
    elif killed:
        campaign["phase"] = "replace"
        campaign["next"] = sequence[len(campaign["scenarios"])]
    else:
        campaign["phase"] = "upgrade"
        campaign["next"] = sequence[len(campaign["scenarios"])]
    save_campaign(campaign_dir, campaign)
    return campaign


def _current_run_dir() -> Path:
    path = Path.cwd() / ".current_run"
    if not path.exists():
        raise EngineError("run directory not specified and .current_run is missing")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise EngineError(".current_run is empty")
    return Path(text)


def apply_campaign_log(campaign: dict[str, Any], result: dict[str, Any]) -> None:
    log = campaign["log"]
    gathering = result.get("campaign_log") or {}
    if gathering:
        house = gathering.get("house")
        if house == "burned_down":
            log["your_house_standing"] = False
        elif house == "standing":
            log["your_house_standing"] = True
        if gathering.get("ghoul_priest_still_alive") is not None:
            log["ghoul_priest_alive"] = bool(gathering.get("ghoul_priest_still_alive"))
        lita = gathering.get("lita")
        if lita == "earned" or result.get("lita_earned"):
            log["lita_earned"] = True
        if lita == "forced_to_find_others":
            log["lita_was_forced_to_find_others"] = True
    block = result.get("campaign") or {}
    if block:
        scenario = str(block.get("scenario") or result.get("scenario") or "")
        if scenario in {"the_midnight_masks", "return_to_the_midnight_masks"}:
            log["cultists_interrogated"] = sorted(
                set(log.get("cultists_interrogated", [])) | set(block.get("cultists_interrogated", []))
            )
            if "cultists_got_away" in block:
                log["cultists_got_away"] = sorted(set(block.get("cultists_got_away", [])))
            if "past_midnight" in block:
                log["past_midnight"] = bool(block.get("past_midnight", False))
            if block.get("ghoul_priest_defeated_here"):
                log["ghoul_priest_alive"] = False
        if scenario in {"the_devourer_below", "return_to_the_devourer_below"}:
            for key in ("arkham_succumbed", "ritual_broken", "umordhoth_repelled", "lita_sacrificed"):
                if key in block:
                    log[key] = bool(block.get(key))
            if block.get("elderthing_added") and "elderthing" not in campaign.setdefault("chaos_bag_additions", []):
                campaign["chaos_bag_additions"].append("elderthing")
    weaknesses = result.get("weaknesses_added", []) or block.get("weaknesses_added", []) or block.get("weakness_gained", [])
    for weakness in weaknesses:
        campaign["deck"].setdefault("weaknesses", []).append(str(weakness))


def investigator_killed_or_insane(campaign: dict[str, Any], result: dict[str, Any]) -> bool:
    if bool(result.get("investigator_killed")) or bool(result.get("investigator_insane")):
        return True
    investigator_code = card_data.INVESTIGATOR_CODES[str(campaign["investigator"])]
    card = card_data.get_card(investigator_code)
    trauma = campaign.get("trauma", {})
    return int(trauma.get("physical", 0)) >= int(card.get("health", 99)) or int(trauma.get("mental", 0)) >= int(card.get("sanity", 99))


def choose_lita(campaign_dir: str | Path, *, include: bool) -> dict[str, Any]:
    campaign = load_campaign(campaign_dir)
    if not campaign["log"].get("lita_earned"):
        raise EngineError("Lita Chantler has not been earned")
    assets = campaign["deck"].setdefault("story_assets", [])
    if include:
        if "01117" not in assets:
            assets.append("01117")
        campaign["log"]["lita_in_deck"] = True
    else:
        campaign["deck"]["story_assets"] = [code for code in assets if code != "01117"]
        campaign["log"]["lita_in_deck"] = False
    save_campaign(campaign_dir, campaign)
    return campaign


def replace_investigator(campaign_dir: str | Path, *, investigator: str) -> dict[str, Any]:
    campaign = load_campaign(campaign_dir)
    if campaign.get("phase") != "replace":
        raise EngineError("replacement is only allowed after an investigator is killed or driven insane")
    if investigator not in card_data.INVESTIGATOR_CODES:
        raise EngineError(f"unknown investigator: {investigator}")
    if investigator == campaign.get("investigator"):
        raise EngineError(f"{investigator} is already the current investigator")
    if investigator in set(str(item) for item in campaign.get("killed_investigators", [])):
        raise EngineError(f"{investigator} was killed and cannot return")
    campaign["investigator"] = investigator
    old_story = list(campaign.get("deck", {}).get("story_assets", []))
    campaign["deck"] = split_starting_deck(investigator)
    campaign["deck"]["story_assets"] = old_story
    campaign["trauma"] = {"physical": 0, "mental": 0}
    campaign["xp_unspent"] = 0
    campaign["phase"] = "scenario"
    validate_deck(campaign, final=True)
    save_campaign(campaign_dir, campaign)
    return campaign


def finish_upgrade(campaign_dir: str | Path) -> dict[str, Any]:
    campaign = load_campaign(campaign_dir)
    if campaign.get("phase") != "upgrade":
        raise EngineError(f"campaign is in {campaign.get('phase')} phase, not upgrade")
    validate_deck(campaign, final=True)
    campaign["phase"] = "scenario"
    save_campaign(campaign_dir, campaign)
    return campaign


def write_summary(campaign_dir: Path, campaign: dict[str, Any]) -> None:
    rows = list(campaign.get("scenarios", []))
    summary = {
        "campaign": campaign.get("campaign"),
        "investigator": campaign.get("investigator"),
        "scenarios": rows,
        "xp_earned_total": int(campaign.get("xp_earned_total", 0)),
        "xp_spent_total": int(campaign.get("xp_spent_total", 0)),
        "campaign_score": sum(int(row.get("score", 0)) for row in rows),
        "outcomes": {
            "arkham_succumbed": campaign["log"].get("arkham_succumbed"),
            "ritual_broken": campaign["log"].get("ritual_broken"),
            "umordhoth_repelled": campaign["log"].get("umordhoth_repelled"),
            "lita_sacrificed": campaign["log"].get("lita_sacrificed"),
            "killed_investigators": list(campaign.get("killed_investigators", [])),
        },
    }
    atomic_write_json(campaign_dir / "campaign_summary.json", summary)


def render_status(campaign: dict[str, Any]) -> str:
    lines = [
        f"campaign: {campaign.get('campaign')}",
        f"investigator: {campaign.get('investigator')}  difficulty: {campaign.get('difficulty')}  phase: {campaign.get('phase')}",
        f"next: {campaign.get('next') or '-'}  xp: {campaign.get('xp_unspent', 0)} unspent / {campaign.get('xp_earned_total', 0)} earned",
        f"trauma: physical {campaign.get('trauma', {}).get('physical', 0)}, mental {campaign.get('trauma', {}).get('mental', 0)}",
        "",
        "scenario | resolution | xp | trauma | score",
    ]
    for row in campaign.get("scenarios", []):
        trauma = row.get("trauma_delta", {})
        lines.append(
            f"{row.get('scenario')} | {row.get('resolution')} | {row.get('xp_earned', 0)} | "
            f"{trauma.get('physical', 0)}/{trauma.get('mental', 0)} | {row.get('score', 0)}"
        )
    if not campaign.get("scenarios"):
        lines.append("(none)")
    log = campaign.get("log", {})
    lines.extend(
        [
            "",
            f"house standing: {log.get('your_house_standing')}  ghoul priest alive: {log.get('ghoul_priest_alive')}",
            f"lita earned: {log.get('lita_earned')}  in deck: {log.get('lita_in_deck')}",
            f"cultists interrogated: {', '.join(log.get('cultists_interrogated', [])) or '-'}",
            f"cultists got away: {', '.join(log.get('cultists_got_away', [])) or '-'}",
        ]
    )
    return "\n".join(lines)
