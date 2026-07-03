"""Effect primitive placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import data as card_data
from .model import CardInstance, DecisionOption, GameState, PendingDecision


def log_event(events: list[dict[str, Any]], event_type: str, message: str, **data: Any) -> None:
    events.append({"type": event_type, "message": message, "data": data})


def draw_player_card(state: GameState, events: list[dict[str, Any]]) -> str | None:
    investigator = state.investigator
    if not investigator.deck:
        log_event(events, "deck_empty", "Roland attempted to draw from an empty deck.")
        return None
    instance_id = investigator.deck.pop(0)
    investigator.hand.append(instance_id)
    state.card_instances[instance_id].zone = "hand"
    card = card_data.get_card(state.card_instances[instance_id].card_code)
    log_event(events, "card_drawn", f"Roland drew {card['name']}.", card=instance_id)
    return instance_id


def gain_resource(state: GameState, amount: int, events: list[dict[str, Any]]) -> None:
    state.investigator.resources += amount
    log_event(events, "resource_gained", f"Roland gained {amount} resource.", amount=amount)


def discover_clue(state: GameState, amount: int, events: list[dict[str, Any]]) -> int:
    location = state.locations[state.investigator.location_id]
    count = min(amount, location.clues)
    if count <= 0:
        return 0
    location.clues -= count
    state.investigator.clues += count
    log_event(events, "clue_discovered", f"Roland discovered {count} clue.", amount=count)
    return count


def spend_clues(state: GameState, amount: int, events: list[dict[str, Any]]) -> bool:
    if state.investigator.clues < amount:
        return False
    state.investigator.clues -= amount
    log_event(events, "clues_spent", f"Roland spent {amount} clue.", amount=amount)
    return True


def place_doom(state: GameState, amount: int, events: list[dict[str, Any]], *, source: str) -> None:
    if state.agenda is None:
        return
    state.agenda.doom += amount
    log_event(events, "doom_placed", f"Placed {amount} doom on the agenda.", source=source)
    check_agenda_advance(state, events)


def check_agenda_advance(state: GameState, events: list[dict[str, Any]]) -> None:
    if state.agenda is None or state.agenda.threshold <= 0:
        return
    while state.agenda.doom >= state.agenda.threshold and state.status == "in_progress":
        state.agenda.doom -= state.agenda.threshold
        state.agenda.stage += 1
        if state.agenda.stage == 2:
            state.agenda.code = "phaseb_agenda_2"
            state.agenda.name = "The House Stirs"
            state.agenda.threshold = 5
            log_event(events, "agenda_advanced", "Agenda advanced to The House Stirs.")
        else:
            end_game(state, events, "agenda advanced beyond the fixture deck")


def advance_act(state: GameState, events: list[dict[str, Any]]) -> None:
    if state.act is None:
        return
    state.act.stage += 1
    if state.act.stage == 2:
        state.act.code = "phaseb_act_2"
        state.act.name = "Find a Way Out"
        state.act.clues_required = 3
        log_event(events, "act_advanced", "Act advanced to Find a Way Out.")
    else:
        end_game(state, events, "act deck completed")


def start_damage_assignment(
    state: GameState,
    events: list[dict[str, Any]],
    *,
    source: str,
    damage: int,
    horror: int,
    direct: bool = False,
    resume: dict[str, Any] | None = None,
) -> None:
    if damage <= 0 and horror <= 0:
        return
    allies = legal_soak_targets(state) if not direct else []
    if not allies:
        state.investigator.damage += damage
        state.investigator.horror += horror
        log_event(events, "damage_assigned", f"Roland took {damage} damage and {horror} horror.", source=source)
        check_investigator_defeat(state, events)
        return
    state.pending_damage = {
        "source": source,
        "remaining_damage": damage,
        "remaining_horror": horror,
        "direct": direct,
        "resume": resume or {},
    }
    present_damage_decision(state)


def legal_soak_targets(state: GameState) -> list[str]:
    targets: list[str] = []
    cards = card_data.cards_by_code()
    for instance_id in state.investigator.play_area:
        card = cards.get(state.card_instances[instance_id].card_code, {})
        if card.get("slot") == "Ally" and (card.get("health") or card.get("sanity")):
            targets.append(instance_id)
    return targets


def present_damage_decision(state: GameState) -> None:
    pending = state.pending_damage
    if not pending:
        return
    cards = card_data.cards_by_code()
    options = []
    if pending["remaining_damage"] > 0:
        options.append(DecisionOption("Assign 1 damage to Roland", {"kind": "assign_damage", "type": "damage", "target": "roland"}))
        for target in legal_soak_targets(state):
            instance = state.card_instances[target]
            card = cards.get(instance.card_code, {})
            if instance.damage < int(card.get("health") or 0):
                options.append(DecisionOption(f"Assign 1 damage to {card.get('name', target)}", {"kind": "assign_damage", "type": "damage", "target": target}))
    if pending["remaining_horror"] > 0:
        options.append(DecisionOption("Assign 1 horror to Roland", {"kind": "assign_damage", "type": "horror", "target": "roland"}))
        for target in legal_soak_targets(state):
            instance = state.card_instances[target]
            card = cards.get(instance.card_code, {})
            if instance.horror < int(card.get("sanity") or 0):
                options.append(DecisionOption(f"Assign 1 horror to {card.get('name', target)}", {"kind": "assign_damage", "type": "horror", "target": target}))
    state.decision_queue = [
        PendingDecision(
            id="assign-damage",
            kind="assign_damage",
            prompt=f"[Round {state.round} · {state.phase} · Roland Banks] Assign damage/horror from {pending['source']}.",
            options=options,
        )
    ]


def assign_damage_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    pending = state.pending_damage
    if pending is None:
        return
    point_type = str(payload["type"])
    target = str(payload["target"])
    if point_type == "damage":
        pending["remaining_damage"] -= 1
    else:
        pending["remaining_horror"] -= 1
    if target == "roland":
        if point_type == "damage":
            state.investigator.damage += 1
        else:
            state.investigator.horror += 1
    else:
        instance = state.card_instances[target]
        if point_type == "damage":
            instance.damage += 1
        else:
            instance.horror += 1
    log_event(events, "damage_assigned", f"Assigned 1 {point_type} to {target}.", target=target)
    destroy_defeated_assets(state, events)
    check_investigator_defeat(state, events)
    if state.status != "in_progress":
        state.pending_damage = None
        return
    if pending["remaining_damage"] > 0 or pending["remaining_horror"] > 0:
        present_damage_decision(state)
    else:
        state.pending_damage = None


def destroy_defeated_assets(state: GameState, events: list[dict[str, Any]]) -> None:
    cards = card_data.cards_by_code()
    for instance_id in list(state.investigator.play_area):
        instance = state.card_instances[instance_id]
        card = cards.get(instance.card_code, {})
        health = int(card.get("health") or 0)
        sanity = int(card.get("sanity") or 0)
        if (health and instance.damage >= health) or (sanity and instance.horror >= sanity):
            state.investigator.play_area.remove(instance_id)
            state.investigator.discard.append(instance_id)
            instance.zone = "discard"
            log_event(events, "asset_discarded", f"{card.get('name', instance_id)} was discarded.", card=instance_id)


def check_investigator_defeat(state: GameState, events: list[dict[str, Any]]) -> None:
    physical = state.investigator.damage >= state.investigator.health
    mental = state.investigator.horror >= state.investigator.sanity
    if physical or mental:
        state.trauma["physical"] = int(state.trauma.get("physical", 0)) + (1 if physical else 0)
        state.trauma["mental"] = int(state.trauma.get("mental", 0)) + (1 if mental else 0)
        end_game(state, events, "Roland was defeated")


def end_game(state: GameState, events: list[dict[str, Any]], summary: str) -> None:
    state.status = "ended"
    state.decision_queue = []
    state.result = {"outcome": summary, "round": state.round, "trauma": dict(state.trauma)}
    log_event(events, "game_end", summary)
