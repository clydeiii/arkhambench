"""Encounter card registrations and attachment helpers for The Gathering."""
from __future__ import annotations

from ..model import GameState
from .registry import card


ENCOUNTER_CARD_CODES = [
    "01116",
    "01117",
    "01118",
    "01119",
    "01159",
    "01160",
    "01161",
    "01162",
    "01163",
    "01164",
    "01165",
    "01166",
    "01167",
    "01168",
    "01174",
    # Return to The Gathering (return set + Ghouls of Umôrdhoth)
    "50022",
    "50023",
    "50024",
    "50038",
    "50039",
    "50040",
]


class EncounterCard:
    """Marker base class for registered encounter card implementations."""


for _code in ENCOUNTER_CARD_CODES:
    card(_code)(type(f"EncounterCard{_code}", (EncounterCard,), {"code": _code}))


def attached_to_location(state: GameState, location_id: str, code: str) -> list[str]:
    return [
        instance_id
        for instance_id in state.locations[location_id].attached_instance_ids
        if state.card_instances[instance_id].card_code == code
    ]


def location_has_attachment(state: GameState, location_id: str, code: str) -> bool:
    return bool(attached_to_location(state, location_id, code))


def attachment_location(state: GameState, instance_id: str) -> str | None:
    for location_id, location in state.locations.items():
        if instance_id in location.attached_instance_ids:
            return location_id
    return None
