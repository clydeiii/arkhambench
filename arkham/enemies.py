"""Enemy movement and attack placeholders for phase B."""
from __future__ import annotations

from collections import deque
from typing import Any

from . import data as card_data
from .effects import log_event, start_damage_assignment
from .model import EnemyInstance, GameState


def enemy_card(state: GameState, enemy_id: str) -> dict[str, Any]:
    return card_data.cards_by_code().get(state.enemies[enemy_id].card_code, {})


def enemy_name(state: GameState, enemy_id: str) -> str:
    return str(enemy_card(state, enemy_id).get("name", enemy_id))


def is_hunter(state: GameState, enemy_id: str) -> bool:
    return "Hunter" in str(enemy_card(state, enemy_id).get("text", ""))


def has_retaliate(state: GameState, enemy_id: str) -> bool:
    return "Retaliate" in str(enemy_card(state, enemy_id).get("text", ""))


def enemy_health(state: GameState, enemy_id: str) -> int:
    return int(enemy_card(state, enemy_id).get("enemy_health") or enemy_card(state, enemy_id).get("health") or 1)


def enemy_damage_horror(state: GameState, enemy_id: str) -> tuple[int, int]:
    card = enemy_card(state, enemy_id)
    return int(card.get("enemy_damage") or 0), int(card.get("enemy_horror") or 0)


def spawn_enemy(
    state: GameState,
    events: list[dict[str, Any]],
    *,
    instance_id: str,
    location_id: str | None = None,
    engaged: bool | None = None,
) -> str | None:
    instance = state.card_instances[instance_id]
    target = location_id or state.investigator.location_id
    if target not in state.locations:
        instance.zone = "encounter_discard"
        state.encounter_discard.append(instance_id)
        log_event(events, "enemy_spawn_discarded", f"{instance.card_code} had no legal spawn location.")
        return None
    enemy = EnemyInstance(id=instance_id, card_code=instance.card_code, location_id=target)
    state.enemies[instance_id] = enemy
    instance.zone = "enemy"
    state.locations[target].enemy_ids.append(instance_id)
    log_event(events, "enemy_spawned", f"{enemy_name(state, instance_id)} spawned at {state.locations[target].name}.", enemy=instance_id)
    if engaged is True or (engaged is None and target == state.investigator.location_id and not enemy.exhausted):
        engage_enemy(state, events, instance_id)
    return instance_id


def engage_enemy(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> None:
    enemy = state.enemies[enemy_id]
    if enemy.exhausted:
        return
    enemy.engaged_with = state.investigator.id
    if enemy_id not in state.investigator.engaged_enemies:
        state.investigator.engaged_enemies.append(enemy_id)
    log_event(events, "enemy_engaged", f"{enemy_name(state, enemy_id)} engaged Roland.", enemy=enemy_id)


def disengage_enemy(state: GameState, events: list[dict[str, Any]], enemy_id: str, *, exhaust: bool) -> None:
    enemy = state.enemies[enemy_id]
    enemy.engaged_with = None
    if enemy_id in state.investigator.engaged_enemies:
        state.investigator.engaged_enemies.remove(enemy_id)
    if exhaust:
        enemy.exhausted = True
    log_event(events, "enemy_disengaged", f"{enemy_name(state, enemy_id)} disengaged.", enemy=enemy_id)


def engage_ready_enemies_at_roland(state: GameState, events: list[dict[str, Any]]) -> None:
    location = state.locations[state.investigator.location_id]
    for enemy_id in sorted(location.enemy_ids):
        enemy = state.enemies[enemy_id]
        if enemy.engaged_with is None and not enemy.exhausted:
            engage_enemy(state, events, enemy_id)


def move_enemy_to(state: GameState, events: list[dict[str, Any]], enemy_id: str, location_id: str) -> None:
    enemy = state.enemies[enemy_id]
    if enemy.location_id in state.locations and enemy_id in state.locations[enemy.location_id].enemy_ids:
        state.locations[enemy.location_id].enemy_ids.remove(enemy_id)
    enemy.location_id = location_id
    state.locations[location_id].enemy_ids.append(enemy_id)
    log_event(events, "enemy_moved", f"{enemy_name(state, enemy_id)} moved to {state.locations[location_id].name}.", enemy=enemy_id)
    if location_id == state.investigator.location_id and enemy.engaged_with is None and not enemy.exhausted:
        engage_enemy(state, events, enemy_id)


def move_engaged_enemies_with_roland(state: GameState, events: list[dict[str, Any]], location_id: str) -> None:
    for enemy_id in list(state.investigator.engaged_enemies):
        move_enemy_to(state, events, enemy_id, location_id)
        state.enemies[enemy_id].engaged_with = state.investigator.id


def move_hunters(state: GameState, events: list[dict[str, Any]]) -> None:
    for enemy_id in sorted(state.enemies):
        enemy = state.enemies[enemy_id]
        if enemy.exhausted or enemy.engaged_with is not None or not is_hunter(state, enemy_id):
            continue
        step = next_step_toward(state, enemy.location_id, state.investigator.location_id, enemy_id)
        if step:
            move_enemy_to(state, events, enemy_id, step)


def next_step_toward(state: GameState, start: str, goal: str, enemy_id: str | None = None) -> str | None:
    if start == goal:
        return None
    queue: deque[tuple[str, list[str]]] = deque([(start, [])])
    seen = {start}
    while queue:
        current, path = queue.popleft()
        for neighbor in sorted(state.locations[current].connections, key=lambda loc: (state.locations[loc].code, loc)):
            if neighbor in seen or move_blocked(state, enemy_id, neighbor):
                continue
            next_path = path + [neighbor]
            if neighbor == goal:
                return next_path[0]
            seen.add(neighbor)
            queue.append((neighbor, next_path))
    return None


def move_blocked(state: GameState, enemy_id: str | None, destination: str) -> bool:
    if enemy_id is None:
        return False
    traits = str(enemy_card(state, enemy_id).get("traits", ""))
    if "Elite" in traits:
        return False
    cards = card_data.cards_by_code()
    for attachment in state.locations[destination].attached_instance_ids:
        name = str(cards.get(state.card_instances[attachment].card_code, {}).get("name", ""))
        if name == "Barricade" or state.card_instances[attachment].card_code == "phaseb_barricade":
            return True
    return False


def attack(
    state: GameState,
    events: list[dict[str, Any]],
    enemy_id: str,
    *,
    source: str,
    resume: dict[str, Any] | None = None,
) -> None:
    if enemy_id not in state.enemies or state.enemies[enemy_id].exhausted:
        return
    damage, horror = enemy_damage_horror(state, enemy_id)
    log_event(events, "enemy_attack", f"{enemy_name(state, enemy_id)} attacked Roland.", enemy=enemy_id, source=source)
    start_damage_assignment(state, events, source=enemy_name(state, enemy_id), damage=damage, horror=horror, resume=resume)


def defeat_enemy(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> None:
    if enemy_id not in state.enemies:
        return
    card = enemy_card(state, enemy_id)
    enemy = state.enemies.pop(enemy_id)
    if enemy.location_id in state.locations and enemy_id in state.locations[enemy.location_id].enemy_ids:
        state.locations[enemy.location_id].enemy_ids.remove(enemy_id)
    if enemy_id in state.investigator.engaged_enemies:
        state.investigator.engaged_enemies.remove(enemy_id)
    if int(card.get("victory") or 0) > 0:
        state.victory_display.append(enemy_id)
        state.card_instances[enemy_id].zone = "victory"
    else:
        state.encounter_discard.append(enemy_id)
        state.card_instances[enemy_id].zone = "encounter_discard"
    log_event(events, "enemy_defeated", f"{card.get('name', enemy_id)} was defeated.", enemy=enemy_id)


def damage_enemy(state: GameState, events: list[dict[str, Any]], enemy_id: str, amount: int) -> None:
    enemy = state.enemies[enemy_id]
    enemy.damage += amount
    log_event(events, "enemy_damaged", f"{enemy_name(state, enemy_id)} took {amount} damage.", enemy=enemy_id)
    if enemy.damage >= enemy_health(state, enemy_id):
        defeat_enemy(state, events, enemy_id)
