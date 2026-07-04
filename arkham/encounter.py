"""Encounter draw and revelation placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import data as card_data
from .cards import encounter_cards, player as player_cards
from .effects import log_event, place_doom, start_damage_assignment
from .enemies import spawn_enemy
from .model import DecisionOption, GameState, PendingDecision
from .rng import ArkhamRng
from . import skill_test


def draw_encounter(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> str | None:
    if not state.encounter_deck:
        reshuffle(state, rng, events)
    if not state.encounter_deck:
        return None
    instance_id = state.encounter_deck.pop(0)
    instance = state.card_instances[instance_id]
    instance.zone = "encounter_drawn"
    card = card_data.cards_by_code().get(instance.card_code, {})
    log_event(events, "encounter_drawn", f"Roland drew encounter card {card.get('name', instance.card_code)}.", card=instance_id)
    state.limits["encounter_cards_drawn"] = int(state.limits.get("encounter_cards_drawn", 0)) + 1
    if present_revelation_cancel(state, instance_id):
        return instance_id
    resolve_revelation(state, rng, events, instance_id)
    return instance_id


def present_revelation_cancel(state: GameState, instance_id: str) -> bool:
    instance = state.card_instances[instance_id]
    card = card_data.get_card(instance.card_code)
    if card.get("type_code") != "treachery" or card.get("subtype_code") in {"weakness", "basicweakness"}:
        return False
    wards = player_cards.hand_ids(state, "01065")
    if not wards or state.investigator.resources < 1:
        return False
    state.decision_queue = [
        PendingDecision(
            id="revelation-cancel",
            kind="revelation_cancel",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Cancel {card.get('name', instance.card_code)}'s revelation?",
            options=[
                DecisionOption(
                    "Play Ward of Protection",
                    {"kind": "ward_revelation", "choice": "cancel", "ward": wards[0], "treachery": instance_id},
                ),
                DecisionOption(
                    "Resolve revelation",
                    {"kind": "ward_revelation", "choice": "pass", "treachery": instance_id},
                ),
            ],
        )
    ]
    return True


def resolve_ward_revelation(
    state: GameState,
    payload: dict[str, Any],
    events: list[dict[str, Any]],
    rng: ArkhamRng,
) -> None:
    treachery = str(payload.get("treachery", ""))
    if treachery not in state.card_instances:
        return
    state.decision_queue = [decision for decision in state.decision_queue if decision.id != "revelation-cancel"]
    if payload.get("choice") == "cancel":
        ward = str(payload.get("ward", ""))
        if ward in state.investigator.hand and state.investigator.resources >= 1:
            state.investigator.resources -= 1
            player_cards.discard_from_hand(state, ward)
            discard_encounter(state, treachery)
            log_event(events, "revelation_canceled", "Ward of Protection canceled the revelation effect.", card=treachery, ward=ward)
            start_damage_assignment(state, events, source="Ward of Protection", damage=0, horror=1)
            return
    resolve_revelation(state, rng, events, treachery)


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
    code = instance.card_code
    type_code = card.get("type_code")
    if type_code == "enemy":
        if code == "01118":
            spawn_enemy(state, events, instance_id=instance_id, location_id="attic")
            return
        if code == "01119":
            spawn_enemy(state, events, instance_id=instance_id, location_id="cellar")
            return
        spawn_enemy(state, events, instance_id=instance_id)
        return
    if code == "01166" or code == "phaseb_ancient_evils":
        discard_encounter(state, instance_id)
        place_doom(state, 1, events, source=card.get("name", "Ancient Evils"), rng=rng, can_advance=True)
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
    elif code == "01162":
        discard_encounter(state, instance_id)
        skill_test.start(
            state,
            events,
            skill="agility",
            difficulty=3,
            source=card.get("name", "Grasping Hands"),
            on_failure={"kind": "damage_per_fail", "source": card.get("name", "Grasping Hands")},
        )
    elif code == "phaseb_direct_damage":
        discard_encounter(state, instance_id)
        start_damage_assignment(state, events, source="Direct Damage", damage=1, horror=0)
    elif code == "01164":
        state.investigator.threat_area.append(instance_id)
        instance.zone = "threat"
        log_event(events, "treachery_threat", "Frozen in Fear entered Roland's threat area.", card=instance_id)
    elif code == "01165":
        state.investigator.threat_area.append(instance_id)
        instance.zone = "threat"
        log_event(events, "treachery_threat", "Dissonant Voices entered Roland's threat area.", card=instance_id)
    elif code == "01167":
        discard_encounter(state, instance_id)
        skill_test.start(
            state,
            events,
            skill="willpower",
            difficulty=4,
            source=card.get("name", "Crypt Chill"),
            on_failure={"kind": "crypt_chill"},
        )
    elif code == "01168":
        attach_to_location_or_discard(state, events, instance_id, state.investigator.location_id, limit_code="01168")
    elif code == "01174":
        location_id = locked_door_target(state)
        if location_id is None:
            discard_encounter(state, instance_id)
            log_event(events, "treachery_discarded", "Locked Door had no legal location.", card=instance_id)
        else:
            attach_to_location_or_discard(state, events, instance_id, location_id)
    else:
        discard_encounter(state, instance_id)
        log_event(events, "treachery_discarded", f"{card.get('name', code)} had no placeholder effect.", card=instance_id)


def discard_encounter(state: GameState, instance_id: str) -> None:
    state.card_instances[instance_id].zone = "encounter_discard"
    if instance_id not in state.encounter_discard:
        state.encounter_discard.append(instance_id)


def attach_to_location_or_discard(
    state: GameState,
    events: list[dict[str, Any]],
    instance_id: str,
    location_id: str,
    *,
    limit_code: str | None = None,
) -> None:
    if limit_code and encounter_cards.location_has_attachment(state, location_id, limit_code):
        discard_encounter(state, instance_id)
        log_event(events, "treachery_discarded", f"{card_data.get_card(state.card_instances[instance_id].card_code)['name']} had no legal attachment target.", card=instance_id)
        return
    state.card_instances[instance_id].zone = "attachment"
    state.locations[location_id].attached_instance_ids.append(instance_id)
    log_event(events, "treachery_attached", f"{card_data.get_card(state.card_instances[instance_id].card_code)['name']} attached to {state.locations[location_id].name}.", card=instance_id, location=location_id)


def locked_door_target(state: GameState) -> str | None:
    candidates = [
        location
        for location in state.locations.values()
        if location.revealed and not encounter_cards.location_has_attachment(state, location.id, "01174")
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda loc: (-loc.clues, loc.code, loc.id))
    return candidates[0].id
