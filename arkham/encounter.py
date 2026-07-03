"""Encounter draw and revelation placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import data as card_data
from .effects import log_event, place_doom, start_damage_assignment
from .enemies import spawn_enemy
from .model import GameState
from .rng import ArkhamRng
from . import skill_test


def draw_encounter(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> str | None:
    if not state.encounter_deck:
        reshuffle(state, rng, events)
    if not state.encounter_deck:
        return None
    instance_id = state.encounter_deck.pop(0)
    instance = state.card_instances[instance_id]
    card = card_data.cards_by_code().get(instance.card_code, {})
    log_event(events, "encounter_drawn", f"Roland drew encounter card {card.get('name', instance.card_code)}.", card=instance_id)
    resolve_revelation(state, rng, events, instance_id)
    return instance_id


def reshuffle(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> None:
    if not state.encounter_discard:
        return
    state.encounter_deck = list(state.encounter_discard)
    state.encounter_discard = []
    for instance_id in state.encounter_deck:
        state.card_instances[instance_id].zone = "encounter_deck"
    rng.shuffle(state.encounter_deck)
    log_event(events, "encounter_reshuffled", "Encounter discard was shuffled into the encounter deck.")


def resolve_revelation(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]], instance_id: str) -> None:
    instance = state.card_instances[instance_id]
    card = card_data.cards_by_code().get(instance.card_code, {})
    type_code = card.get("type_code")
    if type_code == "enemy":
        spawn_enemy(state, events, instance_id=instance_id)
        return
    code = instance.card_code
    if code == "01166" or code == "phaseb_ancient_evils":
        discard_encounter(state, instance_id)
        place_doom(state, 1, events, source=card.get("name", "Ancient Evils"))
    elif code == "01163" or code == "phaseb_rotting_remains":
        discard_encounter(state, instance_id)
        skill_test.start(
            state,
            events,
            skill="willpower",
            difficulty=3,
            source=card.get("name", "Rotting Remains"),
            on_failure={"kind": "horror_per_fail", "source": card.get("name", "Rotting Remains")},
        )
    elif code == "phaseb_direct_damage":
        discard_encounter(state, instance_id)
        start_damage_assignment(state, events, source="Direct Damage", damage=1, horror=0)
    elif code == "01164":
        state.investigator.threat_area.append(instance_id)
        instance.zone = "threat"
        log_event(events, "treachery_threat", "Frozen in Fear entered Roland's threat area.", card=instance_id)
    else:
        discard_encounter(state, instance_id)
        log_event(events, "treachery_discarded", f"{card.get('name', code)} had no placeholder effect.", card=instance_id)


def discard_encounter(state: GameState, instance_id: str) -> None:
    state.card_instances[instance_id].zone = "encounter_discard"
    if instance_id not in state.encounter_discard:
        state.encounter_discard.append(instance_id)
