from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from . import data as card_data
from .errors import EngineError
from .upgrade import (
    card_level,
    card_title,
    counted_deck_size,
    legal_card_for_investigator,
    protected_code,
    title_counts,
    validate_deck,
)


@dataclass(frozen=True)
class DeckbuildOption:
    code: str
    name: str
    faction: str
    current_copies: int
    available: bool


def require_deckbuild_phase(campaign: dict[str, Any]) -> None:
    if campaign.get("phase") != "deckbuild":
        raise EngineError(f"campaign is in {campaign.get('phase')} phase, not deckbuild")


def deckbuild_options(campaign: dict[str, Any]) -> list[DeckbuildOption]:
    require_deckbuild_phase(campaign)
    investigator = str(campaign["investigator"])
    counts = title_counts(campaign["deck"], investigator)
    options: list[DeckbuildOption] = []
    for code in sorted(card_data.cards_by_code()):
        if card_level(code) != 0:
            continue
        if not legal_card_for_investigator(investigator, code):
            continue
        card = card_data.get_card(code)
        title = card_title(code)
        copies = int(counts[title])
        options.append(
            DeckbuildOption(
                code=code,
                name=title,
                faction=str(card.get("faction_code", "")),
                current_copies=copies,
                available=copies < 2,
            )
        )
    return options


def swap(campaign: dict[str, Any], *, in_code: str, out_code: str) -> None:
    require_deckbuild_phase(campaign)
    in_code = str(in_code)
    out_code = str(out_code)
    cards = card_data.cards_by_code()
    if in_code not in cards:
        raise EngineError(f"unknown card code: {in_code}")
    if out_code not in cards:
        raise EngineError(f"unknown card code: {out_code}")
    investigator = str(campaign["investigator"])
    if card_level(in_code) != 0:
        raise EngineError(f"{in_code} is not a level-0 card")
    if not legal_card_for_investigator(investigator, in_code):
        raise EngineError(f"{in_code} is not legal for {investigator}")
    deck = campaign["deck"]
    if protected_code(out_code, deck, investigator):
        raise EngineError(f"cannot remove protected card {out_code}")
    if card_level(out_code) != 0:
        raise EngineError(f"cannot remove level-{card_level(out_code)} card {out_code} during deckbuild")
    if int(deck.get("slots", {}).get(out_code, 0)) <= 0:
        raise EngineError(f"deck does not contain {out_code}")

    candidate = deepcopy(campaign)
    slots = candidate["deck"]["slots"]
    slots[out_code] = int(slots[out_code]) - 1
    if slots[out_code] <= 0:
        del slots[out_code]
    slots[in_code] = int(slots.get(in_code, 0)) + 1
    validate_deck(candidate, final=False)

    campaign["deck"] = candidate["deck"]
    campaign.setdefault("deckbuild_swaps", []).append({"in": in_code, "out": out_code})


def finish_deckbuild(campaign: dict[str, Any]) -> None:
    require_deckbuild_phase(campaign)
    validate_deck(campaign, final=True)
    campaign["phase"] = "scenario"


def deck_summary(campaign: dict[str, Any]) -> list[tuple[str, str, int, bool]]:
    investigator = str(campaign["investigator"])
    rows: list[tuple[str, str, int, bool]] = []
    for code, count in sorted(campaign["deck"].get("slots", {}).items()):
        code = str(code)
        rows.append((code, card_title(code), int(count), protected_code(code, campaign["deck"], investigator)))
    for code in campaign["deck"].get("story_assets", []):
        code = str(code)
        rows.append((code, card_title(code), 1, True))
    for code in campaign["deck"].get("weaknesses", []):
        code = str(code)
        rows.append((code, card_title(code), 1, True))
    return rows


def deck_size(campaign: dict[str, Any]) -> int:
    return counted_deck_size(campaign["deck"], str(campaign["investigator"]))
