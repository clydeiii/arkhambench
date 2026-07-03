"""Action generation and execution placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import data as card_data
from .effects import advance_act, discover_clue, draw_player_card, gain_resource, log_event, spend_clues
from .enemies import attack, engage_enemy, engage_ready_enemies_at_roland, enemy_card, enemy_name, move_engaged_enemies_with_roland
from .model import DecisionOption, GameState, PendingDecision
from . import skill_test


SAFE_FROM_AOO = {"fight", "evade", "engage", "parley", "resign", "pass", "advance_act"}


def present_action_decision(state: GameState) -> None:
    state.decision_queue = [
        PendingDecision(
            id="choose-action",
            kind="choose_action",
            prompt=f"[Round {state.round} · Investigation · Roland Banks · {state.investigator.actions_remaining} actions left] Choose an action:",
            options=legal_actions(state),
        )
    ]


def legal_actions(state: GameState) -> list[DecisionOption]:
    investigator = state.investigator
    location = state.locations[investigator.location_id]
    options: list[DecisionOption] = []
    if state.act and state.act.clues_required is not None and investigator.clues >= state.act.clues_required:
        options.append(DecisionOption(f"Advance act by spending {state.act.clues_required} clues", {"kind": "action", "action": "advance_act"}))
    if location.revealed and location.shroud is not None:
        options.append(DecisionOption(f"Investigate {location.name} (shroud {location.shroud}) — test Intellect({investigator.intellect}) vs {location.shroud}", {"kind": "action", "action": "investigate"}))
    for target in sorted(location.connections, key=lambda loc: (state.locations[loc].code, loc)):
        options.append(DecisionOption(f"Move to {state.locations[target].name}", {"kind": "action", "action": "move", "location": target}))
    for enemy_id in fight_targets(state):
        card = enemy_card(state, enemy_id)
        options.append(DecisionOption(f"Fight {enemy_name(state, enemy_id)} (fight {card.get('enemy_fight', 1)}, 1 dmg) — test Combat({investigator.combat})", {"kind": "action", "action": "fight", "enemy": enemy_id}))
    for enemy_id in list(investigator.engaged_enemies):
        card = enemy_card(state, enemy_id)
        options.append(DecisionOption(f"Evade {enemy_name(state, enemy_id)} (evade {card.get('enemy_evade', 1)}) — test Agility({investigator.agility})", {"kind": "action", "action": "evade", "enemy": enemy_id}))
    for enemy_id in sorted(location.enemy_ids):
        if enemy_id not in investigator.engaged_enemies and state.enemies[enemy_id].engaged_with is None:
            options.append(DecisionOption(f"Engage {enemy_name(state, enemy_id)}", {"kind": "action", "action": "engage", "enemy": enemy_id}))
    options.append(DecisionOption("Draw 1 card", {"kind": "action", "action": "draw"}))
    options.append(DecisionOption("Take resource (gain 1)", {"kind": "action", "action": "resource"}))
    for instance_id in investigator.hand:
        instance = state.card_instances[instance_id]
        card = card_data.cards_by_code().get(instance.card_code, {})
        cost = int(card.get("cost") or 0)
        if card.get("type_code") in {"asset", "event"} and investigator.resources >= cost:
            options.append(DecisionOption(f"Play {card.get('name', instance.card_code)} ({cost} res)", {"kind": "action", "action": "play", "card": instance_id}))
    options.append(DecisionOption("Pass (end turn)", {"kind": "action", "action": "pass"}))
    return options


def fight_targets(state: GameState) -> list[str]:
    ids = set(state.investigator.engaged_enemies)
    ids.update(state.locations[state.investigator.location_id].enemy_ids)
    return sorted(enemy_id for enemy_id in ids if enemy_id in state.enemies)


def execute(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    action = str(payload["action"])
    if action != "advance_act":
        if not payload.get("skip_aoo"):
            attacks_of_opportunity(state, events, action, payload)
        if state.decision_queue or state.status != "in_progress":
            return
        spend_action(state, events, action)
    if action == "investigate":
        loc = state.locations[state.investigator.location_id]
        skill_test.start(state, events, skill="intellect", difficulty=int(loc.shroud or 0), source=f"Investigate {loc.name}", on_success={"kind": "investigate"})
    elif action == "move":
        move(state, str(payload["location"]), events)
    elif action == "fight":
        enemy_id = str(payload["enemy"])
        difficulty = int(enemy_card(state, enemy_id).get("enemy_fight") or 1)
        skill_test.start(state, events, skill="combat", difficulty=difficulty, source=f"Fight {enemy_name(state, enemy_id)}", on_success={"kind": "fight", "enemy": enemy_id, "damage": 1}, on_failure={"kind": "fight", "enemy": enemy_id})
    elif action == "evade":
        enemy_id = str(payload["enemy"])
        difficulty = int(enemy_card(state, enemy_id).get("enemy_evade") or 1)
        skill_test.start(state, events, skill="agility", difficulty=difficulty, source=f"Evade {enemy_name(state, enemy_id)}", on_success={"kind": "evade", "enemy": enemy_id})
    elif action == "engage":
        engage_enemy(state, events, str(payload["enemy"]))
    elif action == "draw":
        draw_player_card(state, events)
    elif action == "resource":
        gain_resource(state, 1, events)
    elif action == "play":
        play_card(state, str(payload["card"]), events)
    elif action == "advance_act":
        if state.act and state.act.clues_required is not None and spend_clues(state, state.act.clues_required, events):
            advance_act(state, events)
    elif action == "pass":
        state.investigator.actions_remaining = 0
        log_event(events, "turn_passed", "Roland ended his turn.")


def spend_action(state: GameState, events: list[dict[str, Any]], action: str) -> None:
    cost = 1
    key = f"frozen:{state.round}:{action}"
    if action in {"move", "fight", "evade"} and has_threat(state, "01164") and not state.limits.get(key):
        cost += 1
        state.limits[key] = True
    state.investigator.actions_remaining = max(0, state.investigator.actions_remaining - cost)
    state.turn.action_index += cost
    log_event(events, "action_spent", f"Spent {cost} action on {action}.", action=action, cost=cost)


def attacks_of_opportunity(state: GameState, events: list[dict[str, Any]], action: str, payload: dict[str, Any]) -> None:
    if action in SAFE_FROM_AOO:
        return
    for enemy_id in list(state.investigator.engaged_enemies):
        enemy = state.enemies.get(enemy_id)
        if enemy and not enemy.exhausted:
            resume_payload = dict(payload)
            resume_payload["skip_aoo"] = True
            attack(
                state,
                events,
                enemy_id,
                source="attack of opportunity",
                resume={"kind": "action", "payload": resume_payload},
            )
            if state.decision_queue:
                return


def move(state: GameState, location_id: str, events: list[dict[str, Any]]) -> None:
    current = state.investigator.location_id
    if location_id not in state.locations[current].connections:
        return
    state.locations[current].investigator_ids.remove(state.investigator.id)
    state.investigator.location_id = location_id
    state.locations[location_id].investigator_ids.append(state.investigator.id)
    move_engaged_enemies_with_roland(state, events, location_id)
    log_event(events, "investigator_moved", f"Roland moved to {state.locations[location_id].name}.", location=location_id)
    engage_ready_enemies_at_roland(state, events)


def play_card(state: GameState, instance_id: str, events: list[dict[str, Any]]) -> None:
    if instance_id not in state.investigator.hand:
        return
    instance = state.card_instances[instance_id]
    card = card_data.cards_by_code().get(instance.card_code, {})
    cost = int(card.get("cost") or 0)
    if state.investigator.resources < cost:
        return
    state.investigator.resources -= cost
    state.investigator.hand.remove(instance_id)
    if card.get("type_code") == "asset":
        instance.zone = "play"
        state.investigator.play_area.append(instance_id)
        if "Uses (4 ammo)" in str(card.get("text", "")):
            instance.uses["ammo"] = 4
    else:
        instance.zone = "discard"
        state.investigator.discard.append(instance_id)
    log_event(events, "card_played", f"Roland played {card.get('name', instance.card_code)}.", card=instance_id)


def has_threat(state: GameState, code: str) -> bool:
    return any(state.card_instances[instance_id].card_code == code for instance_id in state.investigator.threat_area)
