from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CARD_FILES = (ROOT / "data/cards/core.json", ROOT / "data/cards/core_encounter.json")
DEFAULT_DECK = ROOT / "data/decks/roland_ltp.json"


@lru_cache(maxsize=1)
def all_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for path in CARD_FILES:
        with path.open("r", encoding="utf-8") as handle:
            cards.extend(json.load(handle))
    return cards


@lru_cache(maxsize=1)
def cards_by_code() -> dict[str, dict[str, Any]]:
    return {str(card["code"]): card for card in all_cards()}


def get_card(code: str) -> dict[str, Any]:
    return cards_by_code()[code]


def load_deck(path: str | Path | None = None) -> dict[str, Any]:
    deck_path = Path(path) if path else DEFAULT_DECK
    with deck_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def search_cards(query: str) -> list[dict[str, Any]]:
    needle = query.strip().lower()
    if not needle:
        return []
    by_code = cards_by_code()
    if query in by_code:
        return [by_code[query]]
    return [card for card in all_cards() if needle in str(card.get("name", "")).lower()]


def format_card(card: dict[str, Any]) -> str:
    lines = [f"{card.get('code', '')} — {card.get('name', '')}"]
    if card.get("subname"):
        lines.append(str(card["subname"]))
    fields = [
        ("type", "type_code"),
        ("faction", "faction_code"),
        ("cost", "cost"),
        ("traits", "traits"),
        ("skill icons", None),
        ("health", "health"),
        ("sanity", "sanity"),
        ("fight", "enemy_fight"),
        ("health", "enemy_health"),
        ("evade", "enemy_evade"),
        ("damage", "enemy_damage"),
        ("horror", "enemy_horror"),
        ("shroud", "shroud"),
        ("clues", "clues"),
        ("doom threshold", "doom"),
        ("victory", "victory"),
    ]
    for label, key in fields:
        if key is None:
            icons = []
            for icon_key, icon_label in (
                ("skill_willpower", "willpower"),
                ("skill_intellect", "intellect"),
                ("skill_combat", "combat"),
                ("skill_agility", "agility"),
                ("skill_wild", "wild"),
            ):
                if card.get(icon_key):
                    icons.append(f"{icon_label} {card[icon_key]}")
            if icons:
                lines.append(f"{label}: {', '.join(icons)}")
        elif key in card and card[key] is not None:
            lines.append(f"{label}: {card[key]}")
    for text_key, label in (("text", "Text"), ("back_text", "Back")):
        if card.get(text_key):
            lines.append(f"{label}: {card[text_key]}")
    return "\n".join(lines)
