from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from . import data as card_data
from .cards.registry import REGISTRY
from .errors import EngineError


XP_CARD_CODES = {
    "01026",
    "01027",
    "01028",
    "01029",
    "01040",
    "01041",
    "01042",
    "01043",
    "01054",
    "01055",
    "01056",
    "01057",
    "01068",
    "01069",
    "01070",
    "01071",
    "01082",
    "01083",
    "01084",
    "01085",
    "01094",
    "01095",
    "50001",
    "50002",
    "50003",
    "50004",
    "50005",
    "50006",
    "50007",
    "50008",
    "50009",
    "50010",
}

SIGNATURE_CODES = {
    "roland": {"01006", "01007"},
    "daisy": {"01008", "01009"},
    "skids": {"01010", "01011"},
    "agnes": {"01012", "01013"},
    "wendy": {"01014", "01015"},
}
ALL_SIGNATURE_CODES = set().union(*SIGNATURE_CODES.values())

CLASS_ACCESS = {
    "roland": {"guardian": 5, "seeker": 2, "neutral": 5},
    "daisy": {"seeker": 5, "mystic": 2, "neutral": 5},
    "skids": {"rogue": 5, "guardian": 2, "neutral": 5},
    "agnes": {"mystic": 5, "survivor": 2, "neutral": 5},
    "wendy": {"survivor": 5, "rogue": 2, "neutral": 5},
}


@dataclass(frozen=True)
class PurchaseOption:
    code: str
    name: str
    level: int
    faction: str
    cost: int
    kind: str
    removal_required: bool
    affordable: bool


def split_starting_deck(investigator: str) -> dict[str, Any]:
    deck = card_data.load_deck(card_data.default_deck_for_investigator(investigator))
    signatures = SIGNATURE_CODES[investigator]
    slots: dict[str, int] = {}
    weaknesses: list[str] = []
    for code, count in deck["slots"].items():
        code = str(code)
        card = card_data.get_card(code)
        subtype = str(card.get("subtype_code", ""))
        if subtype in {"weakness", "basicweakness"} and code not in signatures:
            weaknesses.extend([code] * int(count))
        else:
            slots[code] = int(count)
    return {"slots": slots, "story_assets": [], "weaknesses": weaknesses}


def full_deck_slots(campaign_deck: dict[str, Any]) -> dict[str, int]:
    counts = Counter({str(code): int(count) for code, count in campaign_deck.get("slots", {}).items()})
    counts.update(str(code) for code in campaign_deck.get("story_assets", []))
    counts.update(str(code) for code in campaign_deck.get("weaknesses", []))
    return dict(sorted(counts.items()))


def counted_slots(campaign_deck: dict[str, Any], investigator: str) -> dict[str, int]:
    signatures = SIGNATURE_CODES[investigator]
    result: dict[str, int] = {}
    for code, count in campaign_deck.get("slots", {}).items():
        code = str(code)
        if code in signatures:
            continue
        card = card_data.get_card(code)
        if str(card.get("subtype_code", "")) in {"weakness", "basicweakness"}:
            continue
        result[code] = int(count)
    return result


def counted_deck_size(campaign_deck: dict[str, Any], investigator: str) -> int:
    return sum(counted_slots(campaign_deck, investigator).values())


def protected_code(code: str, campaign_deck: dict[str, Any], investigator: str) -> bool:
    if code in SIGNATURE_CODES[investigator]:
        return True
    if code in set(str(item) for item in campaign_deck.get("story_assets", [])):
        return True
    card = card_data.get_card(code)
    return str(card.get("subtype_code", "")) in {"weakness", "basicweakness"}


def card_level(code: str) -> int:
    return int(card_data.get_card(code).get("xp") or 0)


def card_title(code: str) -> str:
    return str(card_data.get_card(code).get("name", code))


def legal_card_for_investigator(investigator: str, code: str) -> bool:
    if code not in REGISTRY:
        return False
    card = card_data.get_card(code)
    if card.get("type_code") not in {"asset", "event", "skill"}:
        return False
    if str(card.get("subtype_code", "")) in {"weakness", "basicweakness"}:
        return False
    if code in ALL_SIGNATURE_CODES:
        return False
    if code == "01117":
        return False
    faction = str(card.get("faction_code", "neutral"))
    level = card_level(code)
    return level <= CLASS_ACCESS[investigator].get(faction, -1)


def purchasable_codes(investigator: str) -> list[str]:
    codes = set(XP_CARD_CODES)
    for code in REGISTRY:
        if code not in card_data.cards_by_code():
            continue
        card = card_data.get_card(code)
        if int(card.get("xp") or 0) == 0:
            codes.add(code)
    return sorted(code for code in codes if legal_card_for_investigator(investigator, code))


def title_counts(campaign_deck: dict[str, Any], investigator: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for code, count in counted_slots(campaign_deck, investigator).items():
        counts[card_title(code)] += int(count)
    return counts


def lower_versions_in_deck(campaign_deck: dict[str, Any], investigator: str, new_code: str) -> list[str]:
    new_title = card_title(new_code)
    new_level = card_level(new_code)
    result = []
    for code, count in counted_slots(campaign_deck, investigator).items():
        if count > 0 and card_title(code) == new_title and card_level(code) < new_level:
            result.append(code)
    return sorted(result, key=lambda c: (card_level(c), c))


def purchase_options(campaign: dict[str, Any]) -> list[PurchaseOption]:
    investigator = str(campaign["investigator"])
    deck = dict(campaign["deck"])
    size = counted_deck_size(deck, investigator)
    counts = title_counts(deck, investigator)
    options: list[PurchaseOption] = []
    for code in purchasable_codes(investigator):
        card = card_data.get_card(code)
        level = card_level(code)
        title = card_title(code)
        lowers = lower_versions_in_deck(deck, investigator, code)
        if counts[title] >= 2 and not lowers:
            continue
        cost = max(1, level)
        kind = "new"
        if lowers:
            old = lowers[0]
            cost = max(1, level - card_level(old))
            kind = f"upgrade of {old}"
        affordable = cost <= int(campaign.get("xp_unspent", 0))
        options.append(
            PurchaseOption(
                code=code,
                name=title,
                level=level,
                faction=str(card.get("faction_code", "")),
                cost=cost,
                kind=kind,
                removal_required=(not lowers and size >= 30),
                affordable=affordable,
            )
        )
    return options


def validate_deck(campaign: dict[str, Any], *, final: bool) -> None:
    investigator = str(campaign["investigator"])
    deck = campaign["deck"]
    size = counted_deck_size(deck, investigator)
    if final and size != 30:
        raise EngineError(f"deck must contain exactly 30 counted cards; currently {size}")
    counts = title_counts(deck, investigator)
    over = sorted(title for title, count in counts.items() if count > 2)
    if over:
        raise EngineError(f"deck exceeds 2 copies by title: {', '.join(over)}")
    signatures = SIGNATURE_CODES[investigator]
    for code in signatures:
        if int(deck.get("slots", {}).get(code, 0)) != 1:
            raise EngineError(f"deck must contain signature card {code}")
    for code, count in deck.get("slots", {}).items():
        code = str(code)
        if code in signatures:
            continue
        if protected_code(code, deck, investigator):
            continue
        if not legal_card_for_investigator(investigator, code):
            card = card_data.get_card(code)
            raise EngineError(
                f"{code} {card.get('name', code)} is illegal for {investigator} "
                f"(class {card.get('faction_code')}, level {card_level(code)})"
            )
        if int(count) < 0:
            raise EngineError(f"negative deck count for {code}")


def remove_card(campaign: dict[str, Any], code: str) -> None:
    investigator = str(campaign["investigator"])
    code = str(code)
    if protected_code(code, campaign["deck"], investigator):
        raise EngineError(f"cannot remove protected card {code}")
    slots = campaign["deck"]["slots"]
    if int(slots.get(code, 0)) <= 0:
        raise EngineError(f"deck does not contain {code}")
    slots[code] = int(slots[code]) - 1
    if slots[code] <= 0:
        del slots[code]


def buy_card(campaign: dict[str, Any], code: str, *, remove: str | None = None, replace: str | None = None) -> None:
    investigator = str(campaign["investigator"])
    deck = campaign["deck"]
    code = str(code)
    if not legal_card_for_investigator(investigator, code):
        raise EngineError(f"{code} is not legal for {investigator}")
    if code not in purchasable_codes(investigator):
        raise EngineError(f"{code} is not in the purchasable pool")
    title = card_title(code)
    counts = title_counts(deck, investigator)
    replacing = replace is not None
    if replacing:
        replace = str(replace)
        if int(deck["slots"].get(replace, 0)) <= 0:
            raise EngineError(f"deck does not contain replacement source {replace}")
        if card_title(replace) != title:
            raise EngineError(f"{code} is not an upgrade of {replace}: titles differ")
        if card_level(code) <= card_level(replace):
            raise EngineError(f"{code} is not a higher-level upgrade of {replace}")
        cost = max(1, card_level(code) - card_level(replace))
    else:
        if counts[title] >= 2:
            raise EngineError(f"would exceed 2 copies of {title}")
        cost = max(1, card_level(code))
    if int(campaign.get("xp_unspent", 0)) < cost:
        raise EngineError(f"not enough XP: {code} costs {cost}, have {campaign.get('xp_unspent', 0)}")
    if not replacing and counted_deck_size(deck, investigator) >= 30:
        if remove is None:
            raise EngineError("must remove a card to keep deck size at 30")
        remove_card(campaign, remove)
    if replacing:
        remove_card(campaign, replace or "")
    deck["slots"][code] = int(deck["slots"].get(code, 0)) + 1
    campaign["xp_unspent"] = int(campaign.get("xp_unspent", 0)) - cost
    campaign["xp_spent_total"] = int(campaign.get("xp_spent_total", 0)) + cost
    validate_deck(campaign, final=False)
    campaign.setdefault("purchases", []).append(
        {
            "window": len(campaign.get("scenarios", [])) + 1,
            "code": code,
            "replaced": replace,
            "removed": str(remove) if remove is not None and not replacing else None,
            "price": cost,
        }
    )
