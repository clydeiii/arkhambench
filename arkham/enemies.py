"""Enemy movement and attack placeholders for phase B."""
from __future__ import annotations

from collections import deque
from typing import Any

from . import data as card_data
from .cards import player as player_cards
from .effects import discover_clue, log_event, place_doom, start_damage_assignment
from .model import GATHERING_FAMILY, MIDNIGHT_MASKS_FAMILY, DecisionOption, EnemyInstance, GameState, PendingDecision


def enemy_card(state: GameState, enemy_id: str) -> dict[str, Any]:
    return card_data.cards_by_code().get(state.enemies[enemy_id].card_code, {})


def enemy_name(state: GameState, enemy_id: str) -> str:
    return str(enemy_card(state, enemy_id).get("name", enemy_id))


def is_hunter(state: GameState, enemy_id: str) -> bool:
    return "Hunter" in str(enemy_card(state, enemy_id).get("text", ""))


def has_retaliate(state: GameState, enemy_id: str) -> bool:
    if "Retaliate" in str(enemy_card(state, enemy_id).get("text", "")):
        return True
    enemy = state.enemies[enemy_id]
    if card_data.get_card(enemy.card_code).get("is_unique") and any(
        state.card_instances[attachment].card_code == "50043" for attachment in enemy.attachments
    ):
        return True
    return False


def is_elite(state: GameState, enemy_id: str) -> bool:
    return "Elite" in str(enemy_card(state, enemy_id).get("traits", ""))


def can_attack_investigator(state: GameState, enemy_id: str) -> bool:
    if any(str(key).startswith("on_the_lam:") and value for key, value in state.limits.items()):
        return is_elite(state, enemy_id)
    return True


def can_be_evaded(state: GameState, enemy_id: str) -> bool:
    # Acolyte of Umôrdhoth: cannot be evaded while the engaged investigator has
    # no cards in hand. "Cannot" is absolute — it also blocks automatic evades.
    if enemy_card(state, enemy_id).get("code") == "50039" and not state.investigator.hand:
        return False
    return True


def enemy_health(state: GameState, enemy_id: str) -> int:
    code = state.enemies[enemy_id].card_code
    if code == "01121b":
        base = 6
    elif code == "50026b":
        base = 7
    else:
        base = int(enemy_card(state, enemy_id).get("enemy_health") or enemy_card(state, enemy_id).get("health") or 1)
    masks = sum(1 for attachment in state.enemies[enemy_id].attachments if state.card_instances[attachment].card_code == "50043")
    return base + 2 * masks


def is_aloof(state: GameState, enemy_id: str) -> bool:
    if "Aloof" in str(enemy_card(state, enemy_id).get("text", "")):
        return True
    enemy = state.enemies[enemy_id]
    if card_data.get_card(enemy.card_code).get("is_unique"):
        return False
    return any(state.card_instances[attachment].card_code == "50043" for attachment in enemy.attachments)


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
    if engaged is True or (engaged is None and target == state.investigator.location_id and not enemy.exhausted and not is_aloof(state, instance_id)):
        engage_enemy(state, events, instance_id)
    return instance_id


def engage_enemy(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> None:
    enemy = state.enemies[enemy_id]
    if enemy.exhausted:
        return
    enemy.engaged_with = state.investigator.id
    if enemy_id not in state.investigator.engaged_enemies:
        state.investigator.engaged_enemies.append(enemy_id)
    log_event(events, "enemy_engaged", f"{enemy_name(state, enemy_id)} engaged {state.investigator.name}.", enemy=enemy_id)


def disengage_enemy(state: GameState, events: list[dict[str, Any]], enemy_id: str, *, exhaust: bool) -> None:
    enemy = state.enemies[enemy_id]
    enemy.engaged_with = None
    if enemy_id in state.investigator.engaged_enemies:
        state.investigator.engaged_enemies.remove(enemy_id)
    if exhaust:
        enemy.exhausted = True
    log_event(events, "enemy_disengaged", f"{enemy_name(state, enemy_id)} disengaged.", enemy=enemy_id)


def evade_enemy(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> None:
    if enemy_id not in state.enemies or not can_be_evaded(state, enemy_id):
        return
    disengage_enemy(state, events, enemy_id, exhaust=True)
    if state.scenario in MIDNIGHT_MASKS_FAMILY and enemy_id in state.enemies:
        from .scenarios import the_midnight_masks

        the_midnight_masks.after_enemy_evaded(state, events, enemy_id)


def engage_ready_enemies_at_roland(state: GameState, events: list[dict[str, Any]]) -> None:
    location = state.locations[state.investigator.location_id]
    for enemy_id in sorted(location.enemy_ids):
        enemy = state.enemies[enemy_id]
        if enemy.engaged_with is None and not enemy.exhausted and not is_aloof(state, enemy_id):
            engage_enemy(state, events, enemy_id)


def move_enemy_to(state: GameState, events: list[dict[str, Any]], enemy_id: str, location_id: str) -> None:
    enemy = state.enemies[enemy_id]
    if enemy.location_id in state.locations and enemy_id in state.locations[enemy.location_id].enemy_ids:
        state.locations[enemy.location_id].enemy_ids.remove(enemy_id)
    enemy.location_id = location_id
    state.locations[location_id].enemy_ids.append(enemy_id)
    log_event(events, "enemy_moved", f"{enemy_name(state, enemy_id)} moved to {state.locations[location_id].name}.", enemy=enemy_id)
    if location_id == state.investigator.location_id and enemy.engaged_with is None and not enemy.exhausted and not is_aloof(state, enemy_id):
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
    rng: Any = None,
) -> None:
    if enemy_id not in state.enemies or state.enemies[enemy_id].exhausted:
        # The attacker died or exhausted mid-queue (e.g. Agnes's reaction killed
        # the next AoO attacker) — its attack fizzles, but the interrupted
        # action's continuation must still run: AoOs never cancel the action.
        if resume and resume.get("kind") == "action":
            from . import actions

            actions.execute(state, dict(resume.get("payload", {})), events, rng)
        elif resume and resume.get("kind") == "aoo_order":
            from . import actions

            actions.continue_aoo_order(state, events, dict(resume), rng)
        return
    if not can_attack_investigator(state, enemy_id):
        log_event(events, "enemy_attack_suppressed", f"{enemy_name(state, enemy_id)} could not attack.", enemy=enemy_id, source=source)
        if resume and resume.get("kind") == "action":
            from . import actions

            actions.execute(state, dict(resume.get("payload", {})), events, rng)
        elif resume and resume.get("kind") == "aoo_order":
            from . import actions

            actions.continue_aoo_order(state, events, dict(resume), rng)
        return
    dodge = legal_dodge_card(state)
    if dodge:
        state.limits["pending_attack"] = {
            "enemy": enemy_id,
            "source": source,
            "resume": resume or {},
            "dodge": dodge,
        }
        state.decision_queue = [
            PendingDecision(
                id="enemy-attack",
                kind="enemy_attack",
                prompt=f"{enemy_name(state, enemy_id)} is attacking {state.investigator.name}.",
                options=[
                    DecisionOption(
                        f"Play Dodge to cancel {enemy_name(state, enemy_id)}'s attack",
                        {"kind": "dodge_attack", "card": dodge},
                    ),
                    DecisionOption(
                        "Take the attack",
                        {"kind": "take_attack"},
                    ),
                ],
            )
        ]
        return
    resolve_attack(state, events, enemy_id, source=source, resume=resume, rng=rng)


def legal_dodge_card(state: GameState) -> str | None:
    if state.investigator.resources < 1:
        return None
    ids = player_cards.hand_ids(state, "01023")
    return ids[0] if ids else None


def resolve_attack(
    state: GameState,
    events: list[dict[str, Any]],
    enemy_id: str,
    *,
    source: str,
    resume: dict[str, Any] | None = None,
    rng: Any = None,
) -> None:
    if enemy_id not in state.enemies or state.enemies[enemy_id].exhausted:
        return
    damage, horror = enemy_damage_horror(state, enemy_id)
    log_event(events, "enemy_attack", f"{enemy_name(state, enemy_id)} attacked {state.investigator.name}.", enemy=enemy_id, source=source)
    if state.scenario in MIDNIGHT_MASKS_FAMILY:
        from .scenarios import the_midnight_masks

        the_midnight_masks.after_enemy_attacks(state, events, enemy_id)
    after_resume = {"kind": "after_attack", "enemy": enemy_id, "source": source, "resume": resume or {}}
    start_damage_assignment(
        state,
        events,
        source=enemy_name(state, enemy_id),
        damage=damage,
        horror=horror,
        resume=after_resume,
    )
    if not state.pending_damage and state.decision_queue:
        state.limits["deferred_resume"] = after_resume
        return
    if not state.pending_damage and not state.decision_queue:
        after_attack(state, events, enemy_id, resume or {}, source=source, rng=rng)


def cancel_pending_attack(state: GameState, events: list[dict[str, Any]], card_id: str, rng: Any = None) -> None:
    pending = dict(state.limits.pop("pending_attack", {}))
    if not pending:
        return
    if card_id in state.investigator.hand:
        state.investigator.resources -= 1
        player_cards.discard_from_hand(state, card_id)
    enemy_id = str(pending.get("enemy", ""))
    log_event(events, "attack_canceled", f"Dodge canceled {enemy_name(state, enemy_id)}'s attack.", enemy=enemy_id, card=card_id)
    resume = dict(pending.get("resume", {}))
    if resume.get("kind") == "action":
        from . import actions

        actions.execute(state, dict(resume.get("payload", {})), events, rng)
    elif resume.get("kind") == "aoo_order":
        from . import actions

        actions.continue_aoo_order(state, events, dict(resume), rng)


def take_pending_attack(state: GameState, events: list[dict[str, Any]], rng: Any = None) -> None:
    pending = dict(state.limits.pop("pending_attack", {}))
    if not pending:
        return
    resolve_attack(
        state,
        events,
        str(pending["enemy"]),
        source=str(pending.get("source", "attack")),
        resume=dict(pending.get("resume", {})),
        rng=rng,
    )


def after_attack(
    state: GameState,
    events: list[dict[str, Any]],
    enemy_id: str,
    resume: dict[str, Any] | None = None,
    source: str = "",
    rng: Any = None,
) -> None:
    if enemy_id not in state.enemies and enemy_id not in state.card_instances:
        return
    card_code = (
        state.enemies[enemy_id].card_code
        if enemy_id in state.enemies
        else state.card_instances[enemy_id].card_code
    )
    if card_code == "01102":
        place_doom(state, 1, events, source="Silver Twilight Acolyte", rng=rng)
    if card_code == "50038" and state.investigator.hand and rng is not None:
        from .cards import player as player_cards

        card_id = rng.choice(state.investigator.hand)
        player_cards.discard_from_hand(state, card_id)
        log_event(
            events,
            "grave_eater_forced",
            f"Grave-Eater's attack forced a random discard of {player_cards.card_name(state, card_id)}.",
            card=card_id,
        )
    if source == "enemy phase" and enemy_id in state.enemies:
        state.enemies[enemy_id].exhausted = True
        log_event(events, "enemy_exhausted", f"{enemy_name(state, enemy_id)} exhausted after attacking.", enemy=enemy_id)
    if state.status != "in_progress":
        return
    if state.decision_queue:
        # A decision (e.g. defeat reactions) interposed; defer the interrupted
        # action's continuation instead of dropping it — the phase loop resumes
        # it once the queue empties.
        if resume and resume.get("kind") in {"action", "aoo_order"}:
            state.limits["deferred_resume"] = dict(resume)
        return
    if resume and resume.get("kind") == "action":
        from . import actions

        actions.execute(state, dict(resume.get("payload", {})), events, rng)
    elif resume and resume.get("kind") == "aoo_order":
        from . import actions

        actions.continue_aoo_order(state, events, dict(resume), rng)


def defeat_enemy(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> None:
    if enemy_id not in state.enemies:
        return
    card = enemy_card(state, enemy_id)
    enemy = state.enemies.pop(enemy_id)
    state.limits["last_defeated_enemy_location"] = enemy.location_id
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
    if state.scenario in GATHERING_FAMILY:
        from .scenarios import the_gathering

        if the_gathering.after_enemy_defeated(state, events, enemy_id):
            return
    elif state.scenario in MIDNIGHT_MASKS_FAMILY:
        from .scenarios import the_midnight_masks

        if the_midnight_masks.after_enemy_defeated(state, events, enemy_id):
            return
    present_enemy_defeat_reactions(state, events, enemy_id)


def damage_enemy(state: GameState, events: list[dict[str, Any]], enemy_id: str, amount: int) -> None:
    enemy = state.enemies[enemy_id]
    enemy.damage += amount
    log_event(events, "enemy_damaged", f"{enemy_name(state, enemy_id)} took {amount} damage.", enemy=enemy_id)
    if enemy.damage >= enemy_health(state, enemy_id):
        defeat_enemy(state, events, enemy_id)


def present_enemy_defeat_reactions(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> None:
    if state.status != "in_progress":
        return
    options: list[DecisionOption] = []
    location = state.locations[state.investigator.location_id]
    roland_key = f"roland_reaction:{state.round}"
    if state.investigator.card_code == "01001" and location.clues > 0 and not state.limits.get(roland_key):
        options.append(
            DecisionOption(
                "Use Roland Banks reaction to discover 1 clue",
                {"kind": "enemy_defeated_reaction", "reaction": "roland", "enemy": enemy_id},
            )
        )
    evidence = player_cards.hand_ids(state, "01022")
    if evidence and state.investigator.resources >= 1 and location.clues > 0:
        options.append(
            DecisionOption(
                "Play Evidence! to discover 1 clue",
                {"kind": "enemy_defeated_reaction", "reaction": "evidence", "card": evidence[0], "enemy": enemy_id},
            )
        )
    if not options:
        return
    options.append(DecisionOption("Done", {"kind": "enemy_defeated_reaction", "reaction": "done"}))
    decision = PendingDecision(
        id="enemy-defeated-reactions",
        kind="enemy_defeated_reaction",
        prompt="Choose reactions after defeating an enemy.",
        options=options,
    )
    # Append rather than replace: the kill may happen while another decision is
    # in flight (damage assignment, Cover Up choice) — the window waits its turn.
    if any(d.id == "enemy-defeated-reactions" for d in state.decision_queue):
        return
    state.decision_queue.append(decision)


def resolve_enemy_defeated_reaction(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    reaction = str(payload.get("reaction"))
    if reaction == "roland":
        state.limits[f"roland_reaction:{state.round}"] = True
        discover_clue(state, 1, events)
        log_event(events, "roland_reaction", f"{state.investigator.name} discovered 1 clue after defeating an enemy.")
    elif reaction == "evidence":
        card_id = str(payload.get("card"))
        if card_id in state.investigator.hand and state.investigator.resources >= 1:
            state.investigator.resources -= 1
            player_cards.discard_from_hand(state, card_id)
            discover_clue(state, 1, events)
            log_event(events, "event_played", f"{state.investigator.name} played Evidence!.", card=card_id)
    # Multiple reactions may trigger off the same defeat (Roland's ability AND
    # Evidence!) — re-offer whatever is still legal until the player is Done.
    if reaction in ("roland", "evidence") and state.status == "in_progress":
        present_enemy_defeat_reactions(state, events, str(payload.get("enemy", "")))
