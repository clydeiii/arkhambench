"""Action generation and execution placeholders for phase B."""
from __future__ import annotations

from itertools import permutations
from typing import Any

from . import data as card_data
from .cards import encounter_cards, player as player_cards
from .effects import advance_act, discover_clue, draw_player_card, gain_resource, heal_roland, legal_soak_targets, log_event, place_doom, resolve_player_weakness_draw, spend_clues, start_damage_assignment
from .log import action_count_text
from .enemies import attack, can_attack_investigator, can_be_evaded, damage_enemy, disengage_enemy, enemy_damage_horror, engage_enemy, engage_ready_enemies_at_roland, enemy_card, enemy_name, is_elite, legal_dodge_card, move_engaged_enemies_with_roland
from .errors import EngineError
from .model import GATHERING_FAMILY, DecisionOption, GameState, PendingDecision
from . import skill_test


SAFE_FROM_AOO = {"fight", "asset_fight", "evade", "backstab", "cunning_distraction", "blinding_light", "parley_lita", "parley_mob", "resign", "pass", "advance_act"}
FREE_ACTIONS = {"fast_ability"}
NON_ACTIONS = {"advance_act", "pass"}

# Events playable only through their own dedicated windows/actions, never as a
# generic "Play X" action: Dynamite Blast (01024), Backstab (01051), Sneak
# Attack (01052), Ward of Protection (01065, revelation-cancel window only),
# Blinding Light (01066), Cunning Distraction (01078), "Look what I found!"
# (01079, after-fail window only), Lucky! (01080, would-fail window only).
SPECIAL_WINDOW_PLAYS = {"01024", "01051", "01052", "01065", "01066", "01078", "01079", "01080"}


def present_action_decision(state: GameState) -> None:
    state.decision_queue = [
        PendingDecision(
            id="choose-action",
            kind="choose_action",
            prompt=f"[Round {state.round} · Investigation · {state.investigator.name} · {action_count_text(state)}] Choose an action:",
            options=legal_actions(state),
        )
    ]


def legal_actions(state: GameState) -> list[DecisionOption]:
    investigator = state.investigator
    location = state.locations[investigator.location_id]
    options: list[DecisionOption] = []
    if act_advance_available(state):
        options.append(DecisionOption(f"Advance act by spending {state.act.clues_required} clues", {"kind": "action", "action": "advance_act"}))
    if location.revealed and location.shroud is not None and not location_locked(state, location.id):
        shroud = modified_shroud(state, location.id)
        intellect = player_cards.effective_base_skill(state, "intellect", f"Investigate {location.name}")
        options.append(DecisionOption(f"Investigate {location.name} (shroud {shroud}) — test Intellect({intellect}) vs {shroud}", {"kind": "action", "action": "investigate"}))
    for target in sorted(location.connections, key=lambda loc: (state.locations[loc].code, loc)):
        if state.scenario in GATHERING_FAMILY and target == "parlor" and not state.locations[target].revealed:
            continue
        options.append(DecisionOption(f"Move to {state.locations[target].name}", {"kind": "action", "action": "move", "location": target}))
    for enemy_id in fight_targets(state):
        card = enemy_card(state, enemy_id)
        combat = player_cards.effective_base_skill(state, "combat", f"Fight {enemy_name(state, enemy_id)}")
        options.append(DecisionOption(f"Fight {enemy_name(state, enemy_id)} (fight {card.get('enemy_fight', 1)}, 1 dmg) — test Combat({combat})", {"kind": "action", "action": "fight", "enemy": enemy_id}))
    for enemy_id in list(investigator.engaged_enemies):
        if not can_be_evaded(state, enemy_id):
            continue
        card = enemy_card(state, enemy_id)
        agility = player_cards.effective_base_skill(state, "agility", f"Evade {enemy_name(state, enemy_id)}")
        options.append(DecisionOption(f"Evade {enemy_name(state, enemy_id)} (evade {card.get('enemy_evade', 1)}) — test Agility({agility})", {"kind": "action", "action": "evade", "enemy": enemy_id}))
    for enemy_id in sorted(location.enemy_ids):
        if enemy_id not in investigator.engaged_enemies and state.enemies[enemy_id].engaged_with is None:
            options.append(DecisionOption(f"Engage {enemy_name(state, enemy_id)}", {"kind": "action", "action": "engage", "enemy": enemy_id}))
    if not (the_gathering_module().is_return(state) and investigator.location_id == "guest_hall"):
        options.append(DecisionOption("Draw 1 card", {"kind": "action", "action": "draw"}))
    options.append(DecisionOption("Take resource (gain 1)", {"kind": "action", "action": "resource"}))
    add_study_gateway_option(state, options)
    add_asset_action_options(state, options)
    add_locked_door_options(state, options)
    add_threat_action_options(state, options)
    add_lita_parley_option(state, options)
    add_mob_enforcer_options(state, options)
    add_resign_option(state, options)
    add_fast_options(state, options)
    playable_ids = list(investigator.hand)
    top_discard_event = player_cards.topmost_discard_event_id(state)
    if top_discard_event is not None and player_cards.can_play_from_discard_with_amulet(state, top_discard_event):
        playable_ids.append(top_discard_event)
    seen_play_codes: set[tuple[str, bool]] = set()
    for instance_id in playable_ids:
        instance = state.card_instances[instance_id]
        card = card_data.cards_by_code().get(instance.card_code, {})
        cost = int(card.get("cost") or 0)
        from_discard = instance_id not in investigator.hand
        # Two identical copies in hand are the same play — offer it once.
        if (instance.card_code, from_discard) in seen_play_codes:
            continue
        seen_play_codes.add((instance.card_code, from_discard))
        if (
            card.get("type_code") in {"asset", "event"}
            and investigator.resources >= cost
            and not dissonant_blocks(state, instance.card_code)
            and not is_fast_turn_card(instance.card_code)
            and instance.card_code not in SPECIAL_WINDOW_PLAYS
            and can_enter_play_unique(state, instance.card_code)
            and (not from_discard or player_cards.can_play_from_discard_with_amulet(state, instance_id))
        ):
            suffix = " from discard" if from_discard else ""
            options.append(DecisionOption(f"Play {card.get('name', instance.card_code)}{suffix} ({cost} res)", {"kind": "action", "action": "play", "card": instance_id}))
    options.append(DecisionOption("Pass (end turn)", {"kind": "action", "action": "pass"}))
    return affordable_actions(state, options)


def affordable_actions(state: GameState, options: list[DecisionOption]) -> list[DecisionOption]:
    affordable: list[DecisionOption] = []
    for option in options:
        payload = option.payload
        if payload.get("kind") != "action":
            affordable.append(option)
            continue
        action = str(payload.get("action", ""))
        if only_daisy_tome_action_remains(state) and action not in FREE_ACTIONS | NON_ACTIONS and not is_tome_action(state, payload):
            continue
        if action in FREE_ACTIONS or action in NON_ACTIONS or effective_action_cost(state, action) <= state.investigator.actions_remaining:
            affordable.append(option)
    return affordable


def fight_targets(state: GameState) -> list[str]:
    ids = set(state.investigator.engaged_enemies)
    ids.update(state.locations[state.investigator.location_id].enemy_ids)
    return sorted(enemy_id for enemy_id in ids if enemy_id in state.enemies)


def enemies_at_location(state: GameState) -> list[str]:
    return sorted(
        enemy_id
        for enemy_id in state.locations[state.investigator.location_id].enemy_ids
        if enemy_id in state.enemies
    )


def exhausted_enemies_at_location(state: GameState) -> list[str]:
    location = state.locations[state.investigator.location_id]
    return sorted(
        enemy_id
        for enemy_id in location.enemy_ids
        if enemy_id in state.enemies and state.enemies[enemy_id].exhausted
    )


def elusive_destinations(state: GameState) -> list[str]:
    # RR "Move": an entity cannot move to its current placement — the
    # investigator's own location is never a legal Elusive destination.
    return [
        location.id
        for location in sorted(state.locations.values(), key=lambda loc: (loc.code, loc.id))
        if location.revealed and not location.enemy_ids and location.id != state.investigator.location_id
    ]


def the_gathering_module():
    from .scenarios import the_gathering

    return the_gathering


def act_advance_available(state: GameState) -> bool:
    # Advancing via the act Objective is a free triggered ability, legal in any
    # player window during the investigators' turns (RR "Objective").
    return bool(
        state.act
        and state.act.clues_required is not None
        and state.investigator.clues >= state.act.clues_required
        and not (state.scenario in GATHERING_FAMILY and state.act.stage == 2)
        and act_advance_location_ok(state)
    )


def act_advance_location_ok(state: GameState) -> bool:
    # Return to The Gathering Act 1 (Mysterious Gateway): only investigators in
    # the Guest Hall may spend the requisite clues to advance.
    if the_gathering_module().is_return(state) and state.act and state.act.stage == 1:
        return state.investigator.location_id == "guest_hall"
    return True


def add_study_gateway_option(state: GameState, options: list[DecisionOption]) -> None:
    # Study (Aberrant Gateway): "[action] [action]: Draw 3 cards." (lead
    # investigator only — the solo investigator qualifies).
    if not the_gathering_module().is_return(state):
        return
    if state.investigator.location_id != "study":
        return
    if state.investigator.actions_remaining >= effective_action_cost(state, "study_draw"):
        options.append(
            DecisionOption("Study (Aberrant Gateway): spend 2 actions to draw 3 cards", {"kind": "action", "action": "study_draw"})
        )


def execute(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: Any = None) -> None:
    action = str(payload["action"])
    if action not in NON_ACTIONS | FREE_ACTIONS:
        if not payload.get("cost_paid"):
            spend_action(state, events, action, payload)
        if not payload.get("skip_aoo"):
            attacks_of_opportunity(state, events, action, payload, rng=rng)
            if state.decision_queue or state.status != "in_progress":
                return
    if action == "investigate":
        loc = state.locations[state.investigator.location_id]
        skill_test.start(state, events, skill="intellect", difficulty=modified_shroud(state, loc.id), source=f"Investigate {loc.name}", on_success={"kind": "investigate"})
    elif action == "move":
        move(state, str(payload["location"]), events)
    elif action == "fight":
        enemy_id = str(payload["enemy"])
        difficulty = int(enemy_card(state, enemy_id).get("enemy_fight") or 1)
        skill_test.start(state, events, skill="combat", difficulty=difficulty, source=f"Fight {enemy_name(state, enemy_id)}", on_success={"kind": "fight", "enemy": enemy_id, "damage": 1}, on_failure={"kind": "fight", "enemy": enemy_id})
    elif action == "evade":
        enemy_id = str(payload["enemy"])
        if not can_be_evaded(state, enemy_id):
            raise EngineError(f"{enemy_name(state, enemy_id)} cannot be evaded right now")
        difficulty = int(enemy_card(state, enemy_id).get("enemy_evade") or 1)
        skill_test.start(state, events, skill="agility", difficulty=difficulty, source=f"Evade {enemy_name(state, enemy_id)}", on_success={"kind": "evade", "enemy": enemy_id})
    elif action == "engage":
        engage_enemy(state, events, str(payload["enemy"]))
    elif action == "draw":
        if the_gathering_module().is_return(state) and state.investigator.location_id == "guest_hall":
            raise EngineError("Investigators in the Guest Hall cannot take draw actions")
        draw_player_card(state, events, rng)
    elif action == "study_draw":
        for _ in range(3):
            if state.status != "in_progress":
                break
            draw_player_card(state, events, rng)
        log_event(events, "study_draw", "The Study's gateway ability drew 3 cards.")
    elif action == "resource":
        gain_resource(state, 1, events)
    elif action == "play":
        play_card(state, str(payload["card"]), events, rng)
    elif action == "asset_fight":
        asset_fight(state, payload, events)
    elif action == "flashlight":
        flashlight_investigate(state, payload, events)
    elif action == "first_aid":
        first_aid(state, payload, events)
    elif action == "old_book":
        old_book_of_lore(state, payload, events)
    elif action == "medical_texts":
        skill_test.start(state, events, skill="intellect", difficulty=2, source="Medical Texts", on_success={"kind": "medical_texts"}, on_failure={"kind": "medical_texts"})
    elif action == "necronomicon":
        necronomicon_action(state, payload, events)
    elif action == "scrying":
        scrying_action(state, payload, events)
    elif action == "burglary":
        burglary_action(state, payload, events)
    elif action == "blinding_light":
        blinding_light(state, payload, events)
    elif action == "backstab":
        backstab(state, payload, events)
    elif action == "cunning_distraction":
        cunning_distraction(state, payload, events)
    elif action == "discard_haunted":
        discard_haunted(state, payload, events)
    elif action == "locked_door":
        skill = str(payload["skill"])
        skill_test.start(state, events, skill=skill, difficulty=4, source="Locked Door", on_success={"kind": "locked_door", "door": payload["door"]})
    elif action == "parley_lita":
        skill_test.start(state, events, skill="intellect", difficulty=4, source="Parley with Lita Chantler", on_success={"kind": "lita_parley", "lita": payload["lita"]})
    elif action == "parley_mob":
        parley_mob_enforcer(state, payload, events)
    elif action == "dynamite":
        dynamite_blast(state, payload, events)
    elif action == "sneak_attack":
        sneak_attack(state, payload, events)
    elif action == "fast_ability":
        resolve_fast_ability(state, payload, events)
    elif action == "advance_act":
        if state.act and state.act.clues_required is not None and spend_clues(state, state.act.clues_required, events):
            advance_act(state, events)
    elif action == "pass":
        state.investigator.actions_remaining = 0
        log_event(events, "turn_passed", f"{state.investigator.name} ended their turn.")
    elif action == "resign":
        from .scenarios import the_gathering

        the_gathering.resign(state, events)


def spend_action(state: GameState, events: list[dict[str, Any]], action: str, payload: dict[str, Any] | None = None) -> None:
    cost = effective_action_cost(state, action)
    if cost > state.investigator.actions_remaining:
        raise EngineError(f"cannot spend {cost} actions with only {state.investigator.actions_remaining} remaining")
    mark_action_cost_paid(state, action, cost)
    state.investigator.actions_remaining -= cost
    state.turn.action_index += cost
    state.limits["actions_taken"] = int(state.limits.get("actions_taken", 0)) + cost
    label = describe_action(state, action, payload or {})
    plural = "action" if cost == 1 else "actions"
    log_event(events, "action_spent", f"Spent {cost} {plural}: {label}.", action=action, cost=cost)


def describe_action(state: GameState, action: str, payload: dict[str, Any]) -> str:
    if action == "investigate":
        return f"Investigate {state.locations[state.investigator.location_id].name}"
    if action == "move":
        location_id = str(payload.get("location", ""))
        return f"Move to {state.locations[location_id].name}" if location_id in state.locations else "Move"
    if action == "fight":
        enemy_id = str(payload.get("enemy", ""))
        return f"Fight {enemy_name(state, enemy_id)}" if enemy_id in state.enemies else "Fight"
    if action == "evade":
        enemy_id = str(payload.get("enemy", ""))
        return f"Evade {enemy_name(state, enemy_id)}" if enemy_id in state.enemies else "Evade"
    if action == "engage":
        enemy_id = str(payload.get("enemy", ""))
        return f"Engage {enemy_name(state, enemy_id)}" if enemy_id in state.enemies else "Engage"
    if action == "draw":
        return "Draw 1 card"
    if action == "resource":
        return "Take resource"
    if action == "play":
        card_id = str(payload.get("card", ""))
        name = player_cards.card_name(state, card_id) if card_id in state.card_instances else "card"
        return f"Play {name}"
    if action == "asset_fight":
        asset_id = str(payload.get("asset", ""))
        enemy_id = str(payload.get("enemy", ""))
        asset = player_cards.card_name(state, asset_id) if asset_id in state.card_instances else "asset"
        if enemy_id in state.enemies:
            return f"Fight with {asset} (target: {enemy_name(state, enemy_id)})"
        return f"Fight with {asset}"
    if action == "flashlight":
        return f"Investigate {state.locations[state.investigator.location_id].name} with Flashlight"
    if action == "first_aid":
        heal = str(payload.get("heal", "damage"))
        return f"Use First Aid to heal 1 {heal}"
    if action == "old_book":
        return "Use Old Book of Lore"
    if action == "medical_texts":
        return "Use Medical Texts"
    if action == "necronomicon":
        return "Use The Necronomicon"
    if action == "scrying":
        return "Use Scrying"
    if action == "burglary":
        return f"Use Burglary at {state.locations[state.investigator.location_id].name}"
    if action == "blinding_light":
        enemy_id = str(payload.get("enemy", ""))
        return f"Play Blinding Light on {enemy_name(state, enemy_id)}" if enemy_id in state.enemies else "Play Blinding Light"
    if action == "backstab":
        enemy_id = str(payload.get("enemy", ""))
        return f"Play Backstab on {enemy_name(state, enemy_id)}" if enemy_id in state.enemies else "Play Backstab"
    if action == "cunning_distraction":
        return "Play Cunning Distraction"
    if action == "discard_haunted":
        return "Discard Haunted"
    if action == "locked_door":
        skill = str(payload.get("skill", "combat")).capitalize()
        return f"Test {skill} to discard Locked Door"
    if action == "parley_lita":
        return "Parley with Lita Chantler"
    if action == "parley_mob":
        return "Parley with Mob Enforcer"
    if action == "dynamite":
        location_id = str(payload.get("location", ""))
        return f"Play Dynamite Blast at {state.locations[location_id].name}" if location_id in state.locations else "Play Dynamite Blast"
    if action == "sneak_attack":
        enemy_id = str(payload.get("enemy", ""))
        return f"Play Sneak Attack on {enemy_name(state, enemy_id)}" if enemy_id in state.enemies else "Play Sneak Attack"
    if action == "study_draw":
        return "Study (Aberrant Gateway) - draw 3 cards"
    if action == "advance_act":
        return "Advance act"
    if action == "resign":
        return "Resign"
    return action.replace("_", " ").title()


def effective_action_cost(state: GameState, action: str) -> int:
    cost = 2 if action in {"discard_haunted", "study_draw"} else 1
    designator = action_designator(action)
    key = f"frozen:{state.round}:move_fight_evade"
    if designator in {"move", "fight", "evade"} and not state.limits.get(key):
        # Each Frozen in Fear copy is an independent Forced effect on the same
        # "first move/fight/evade each round" — multiple copies stack.
        cost += sum(
            1
            for instance_id in state.investigator.threat_area
            if state.card_instances[instance_id].card_code == "01164"
        )
    return cost


def mark_action_cost_paid(state: GameState, action: str, cost: int) -> None:
    designator = action_designator(action)
    key = f"frozen:{state.round}:move_fight_evade"
    if cost > 1 and designator in {"move", "fight", "evade"}:
        state.limits[key] = True
    if state.investigator.card_code == "01002" and action in {"old_book", "medical_texts", "necronomicon"}:
        state.limits[f"daisy_tome:{state.round}"] = True


def action_designator(action: str) -> str:
    if action == "asset_fight":
        return "fight"
    if action == "blinding_light":
        return "evade"
    if action in {"parley_lita", "parley_mob"}:
        return "parley"
    if action in {"discard_haunted", "necronomicon", "scrying", "study_draw"}:
        return "activate"
    return action


def only_daisy_tome_action_remains(state: GameState) -> bool:
    return (
        state.investigator.card_code == "01002"
        and state.investigator.actions_remaining == 1
        and not state.limits.get(f"daisy_tome:{state.round}")
    )


def is_tome_action(state: GameState, payload: dict[str, Any]) -> bool:
    asset_id = str(payload.get("asset", ""))
    if asset_id not in state.investigator.play_area and asset_id not in state.investigator.threat_area:
        return False
    return player_cards.is_tome_asset_code(state.card_instances[asset_id].card_code)


def attacks_of_opportunity(state: GameState, events: list[dict[str, Any]], action: str, payload: dict[str, Any], rng: Any = None) -> None:
    if action in SAFE_FROM_AOO:
        return
    attackers = [
        enemy_id
        for enemy_id in list(state.investigator.engaged_enemies)
        if (enemy := state.enemies.get(enemy_id)) is not None and not enemy.exhausted
        and can_attack_investigator(state, enemy_id)
    ]
    if not attackers:
        return
    resume_payload = dict(payload)
    resume_payload["skip_aoo"] = True
    resume_payload["cost_paid"] = True
    if len(attackers) > 1:
        present_aoo_order_decision(state, attackers, resume_payload)
        return
    resolve_ordered_aoo(state, events, attackers[0], [], resume_payload, rng=rng)


def present_aoo_order_decision(state: GameState, attackers: list[str], action_payload: dict[str, Any]) -> None:
    live = [enemy_id for enemy_id in attackers if enemy_id in state.enemies and not state.enemies[enemy_id].exhausted]
    if not live:
        return
    state.decision_queue = [
        PendingDecision(
            id="aoo-attack-order",
            kind="aoo_attack_order",
            prompt="Choose the next enemy to make an attack of opportunity.",
            options=[
                DecisionOption(
                    f"Attack next: {enemy_name(state, enemy_id)}",
                    {
                        "kind": "aoo_attack_order",
                        "enemy": enemy_id,
                        "remaining": [other for other in live if other != enemy_id],
                        "action_payload": action_payload,
                    },
                )
                for enemy_id in live
            ],
        )
    ]


def resolve_ordered_aoo(
    state: GameState,
    events: list[dict[str, Any]],
    enemy_id: str,
    remaining: list[str],
    action_payload: dict[str, Any],
    rng: Any = None,
) -> None:
    remaining = [eid for eid in remaining if eid in state.enemies and not state.enemies[eid].exhausted]
    resume: dict[str, Any] = {}
    if aoo_needs_resume(state, enemy_id):
        if remaining:
            resume = {"kind": "aoo_order", "remaining": remaining, "action_payload": dict(action_payload)}
        else:
            resume = {"kind": "action", "payload": dict(action_payload)}
    attack(state, events, enemy_id, source="attack of opportunity", resume=resume, rng=rng)
    if state.status != "in_progress" or state.decision_queue:
        return
    if remaining:
        present_aoo_order_decision(state, remaining, action_payload)
    else:
        execute(state, dict(action_payload), events, rng)


def continue_aoo_order(state: GameState, events: list[dict[str, Any]], resume: dict[str, Any], rng: Any = None) -> None:
    remaining = [str(enemy_id) for enemy_id in resume.get("remaining", [])]
    action_payload = dict(resume.get("action_payload", {}))
    if not remaining:
        execute(state, action_payload, events, rng)
    elif len(remaining) == 1:
        resolve_ordered_aoo(state, events, remaining[0], [], action_payload, rng=rng)
    else:
        present_aoo_order_decision(state, remaining, action_payload)


def aoo_needs_resume(state: GameState, enemy_id: str) -> bool:
    if legal_dodge_card(state) is not None:
        return True
    damage, horror = enemy_damage_horror(state, enemy_id)
    return (damage > 0 or horror > 0) and bool(legal_soak_targets(state))


def move(state: GameState, location_id: str, events: list[dict[str, Any]]) -> None:
    current = state.investigator.location_id
    if location_id not in state.locations[current].connections:
        return
    state.locations[current].investigator_ids.remove(state.investigator.id)
    discard_barricades_at_location(state, current, events)
    state.investigator.location_id = location_id
    state.locations[location_id].investigator_ids.append(state.investigator.id)
    move_engaged_enemies_with_roland(state, events, location_id)
    log_event(events, "investigator_moved", f"{state.investigator.name} moved to {state.locations[location_id].name}.", location=location_id)
    if state.scenario in GATHERING_FAMILY:
        from .scenarios import the_gathering

        the_gathering.after_enter_location(state, events, location_id)
    engage_ready_enemies_at_roland(state, events)


def play_card(state: GameState, instance_id: str, events: list[dict[str, Any]], rng: Any = None) -> None:
    in_hand = instance_id in state.investigator.hand
    from_discard = player_cards.can_play_from_discard_with_amulet(state, instance_id)
    if not in_hand and not from_discard:
        return
    instance = state.card_instances[instance_id]
    card = card_data.cards_by_code().get(instance.card_code, {})
    if dissonant_blocks(state, instance.card_code):
        return
    if card.get("type_code") == "asset":
        if not can_enter_play_unique(state, instance.card_code):
            log_event(events, "play_blocked", f"{card.get('name', instance.card_code)} is unique and already in play.", card=instance_id)
            return
        slot_discards = required_slot_discards(state, instance_id)
        if slot_discards:
            present_slot_discard_decision(state, instance_id, slot_discards)
            return
    cost = int(card.get("cost") or 0)
    if state.investigator.resources < cost:
        return
    state.investigator.resources -= cost
    if not player_cards.remove_from_hand_or_discard_for_play(state, instance_id):
        state.investigator.resources += cost
        return
    if card.get("type_code") == "asset":
        instance.zone = "play"
        state.investigator.play_area.append(instance_id)
        player_cards.setup_uses(instance)
        if instance.card_code == "01048" and state.phase == "Investigation":
            state.investigator.actions_remaining += 1
        if instance.card_code == "01032":
            research_librarian_search(state, events)
        elif instance.card_code == "01063":
            instance.doom += 1
            log_event(events, "doom_placed", "Placed 1 doom on Arcane Initiate.", card=instance_id)
    else:
        if instance.card_code == "01088":
            gain_resource(state, 3, events)
        elif instance.card_code == "01013":
            place_doom(state, 1, events, source="Dark Memory", rng=rng, can_advance=True)
        elif instance.card_code == "01038":
            instance.zone = "attachment"
            state.locations[state.investigator.location_id].attached_instance_ids.append(instance_id)
            log_event(events, "event_attached", f"Barricade attached to {state.investigator.name}'s location.", card=instance_id, location=state.investigator.location_id)
            queue_heirloom_reaction(state, instance_id)
            return
        elif instance.card_code == "01064":
            if rng is None:
                raise EngineError("Drawn to the Flame requires the game RNG")
            from . import encounter

            state.limits["after_encounter_draw"] = {"kind": "drawn_to_the_flame"}
            encounter.draw_encounter(state, rng, events)
        player_cards.place_played_event(state, instance_id, events)
    log_event(events, "card_played", f"{state.investigator.name} played {card.get('name', instance.card_code)}.", card=instance_id)
    if card.get("type_code") == "asset":
        enforce_slot_capacity(state, events)
    queue_heirloom_reaction(state, instance_id)
    if state.limits.get("after_encounter_draw") and not state.decision_queue and not state.active_skill_test and not state.pending_damage:
        from . import encounter

        encounter.resolve_after_encounter_draw(state, events)


def can_enter_play_unique(state: GameState, card_code: str) -> bool:
    card = card_data.get_card(card_code)
    if not card.get("is_unique"):
        return True
    title = str(card.get("name", card_code))
    for instance_id in state.investigator.play_area:
        other = card_data.get_card(state.card_instances[instance_id].card_code)
        if other.get("is_unique") and str(other.get("name", "")) == title:
            return False
    return True


def required_slot_discards(state: GameState, card_id: str) -> list[str]:
    card_code = state.card_instances[card_id].card_code
    if card_code == "01117":
        return []
    card = card_data.get_card(card_code)
    slot = slot_type(card)
    if slot is None:
        return []
    occupants = slotted_asset_ids(state, slot, include=card_id)
    if slot_fits(state, slot, occupants):
        return []
    choices = discard_choices_for_slot_overflow(state, slot, occupants, candidate_id=card_id)
    if choices:
        return choices
    return []


def present_slot_discard_decision(state: GameState, card_id: str, occupants: list[str]) -> None:
    state.decision_queue = [
        PendingDecision(
            id="slot-discard-for-play",
            kind="slot_discard",
            prompt=f"Choose a card to discard for {player_cards.card_name(state, card_id)}.",
            options=[
                DecisionOption(
                    f"Discard {player_cards.card_name(state, occupant)}",
                    {"kind": "slot_discard", "discard": occupant, "play": card_id},
                )
                for occupant in occupants
            ],
        )
    ]


def resolve_slot_discard(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    discard = str(payload.get("discard", ""))
    play = str(payload.get("play", ""))
    if discard in state.investigator.play_area:
        name = player_cards.card_name(state, discard)
        player_cards.discard_from_play(state, discard)
        log_event(events, "asset_discarded", f"{name} was discarded for slot capacity.", card=discard)
    elif discard in state.investigator.threat_area and can_discard_for_slots(state, discard):
        name = player_cards.card_name(state, discard)
        player_cards.discard_from_threat(state, discard)
        log_event(events, "asset_discarded", f"{name} was discarded for slot capacity.", card=discard)
    if play in state.investigator.hand:
        play_card(state, play, events)
    elif not state.decision_queue:
        enforce_slot_capacity(state, events)


def enforce_slot_capacity(state: GameState, events: list[dict[str, Any]]) -> bool:
    for slot in ("Ally", "Hand", "Arcane", "Accessory", "Body"):
        occupants = slotted_asset_ids(state, slot)
        if slot_fits(state, slot, occupants):
            continue
        choices = discard_choices_for_slot_overflow(state, slot, occupants)
        if not choices:
            log_event(events, "slot_overflow_blocked", f"No legal discard can resolve {slot} slot overflow.")
            return False
        state.decision_queue = [
            PendingDecision(
                id="slot-overflow-discard",
                kind="slot_discard",
                prompt=f"Choose a {slot} asset to discard for slot capacity.",
                options=[
                    DecisionOption(
                        f"Discard {player_cards.card_name(state, occupant)}",
                        {"kind": "slot_discard", "discard": occupant},
                    )
                    for occupant in choices
                ],
            )
        ]
        return True
    return False


def slot_type(card: dict[str, Any]) -> str | None:
    slot = str(card.get("slot") or "")
    if "Hand" in slot:
        return "Hand"
    if "Ally" in slot:
        return "Ally"
    if "Arcane" in slot:
        return "Arcane"
    if "Accessory" in slot:
        return "Accessory"
    if "Body" in slot:
        return "Body"
    return None


def slotted_asset_ids(state: GameState, slot: str, *, include: str | None = None) -> list[str]:
    ids = list(state.investigator.play_area) + list(state.investigator.threat_area)
    if include is not None:
        ids.append(include)
    result: list[str] = []
    for instance_id in ids:
        if instance_id not in state.card_instances:
            continue
        if instance_id == include or instance_id in state.investigator.play_area or instance_id in state.investigator.threat_area:
            card = card_data.get_card(state.card_instances[instance_id].card_code)
            if state.card_instances[instance_id].card_code == "01117":
                continue
            if card.get("type_code") == "asset" and slot_type(card) == slot:
                result.append(instance_id)
    return result


def slot_fits(state: GameState, slot: str, occupants: list[str]) -> bool:
    if slot == "Ally":
        return len(occupants) <= 1
    if slot == "Arcane":
        return len(occupants) <= 2
    if slot == "Accessory":
        return len(occupants) <= 1
    if slot == "Body":
        return len(occupants) <= 1
    if slot != "Hand":
        return True
    tome_slots = 2 if any(state.card_instances[asset_id].card_code == "01008" for asset_id in state.investigator.play_area) else 0
    tomes = [asset_id for asset_id in occupants if player_cards.is_tome_asset_code(state.card_instances[asset_id].card_code)]
    non_tomes = [asset_id for asset_id in occupants if asset_id not in tomes]
    tome_regular_width = sum(slot_width(state, asset_id) for asset_id in tomes[max(0, tome_slots):])
    non_tome_width = sum(slot_width(state, asset_id) for asset_id in non_tomes)
    return non_tome_width <= 2 and non_tome_width + tome_regular_width <= 2


def slot_width(state: GameState, asset_id: str) -> int:
    card = card_data.get_card(state.card_instances[asset_id].card_code)
    slot = str(card.get("slot") or "")
    if "x2" in slot:
        return 2
    return 1


def discard_choices_for_slot_overflow(
    state: GameState,
    slot: str,
    occupants: list[str],
    *,
    candidate_id: str | None = None,
) -> list[str]:
    candidates = [
        asset_id
        for asset_id in occupants
        if asset_id != candidate_id and can_discard_for_slots(state, asset_id)
    ]
    valid = [
        asset_id
        for asset_id in candidates
        if slot_fits(state, slot, [other for other in occupants if other != asset_id])
    ]
    return valid or candidates


def can_discard_for_slots(state: GameState, asset_id: str) -> bool:
    instance = state.card_instances.get(asset_id)
    if not instance:
        return False
    return not (instance.card_code == "01009" and instance.horror > 0)


def has_threat(state: GameState, code: str) -> bool:
    return any(state.card_instances[instance_id].card_code == code for instance_id in state.investigator.threat_area)


def dissonant_blocks(state: GameState, card_code: str) -> bool:
    if not has_threat(state, "01165"):
        return False
    card = card_data.get_card(card_code)
    return card.get("type_code") in {"asset", "event"}


def is_fast_turn_card(card_code: str) -> bool:
    return card_code in {"01010", "01022", "01023", "01030", "01036", "01037", "01044", "01050"}


def add_fast_options(state: GameState, options: list[DecisionOption], *, during_turn: bool = True, include_objective: bool = False) -> None:
    # Fast card PLAYS are only legal during the investigator's own turn;
    # triggered fast abilities on in-play cards (Beat Cop) work in any window.
    if during_turn:
        # The action menu adds the objective itself; only standalone fast
        # windows (present_fast_window) ask for it here.
        if include_objective and act_advance_available(state):
            options.append(
                DecisionOption(
                    f"Advance act by spending {state.act.clues_required} clues",
                    {"kind": "action", "action": "advance_act"},
                )
            )
        if (
            state.investigator.card_code == "01003"
            and state.investigator.resources >= 2
            and not state.limits.get(f"skids_action:{state.round}")
        ):
            options.append(
                DecisionOption(
                    'Use "Skids" O\'Toole ability (spend 2 resources for +1 action)',
                    {"kind": "action", "action": "fast_ability", "ability": "skids_action"},
                )
            )
        fast_ids = list(state.investigator.hand)
        top_discard_event = player_cards.topmost_discard_event_id(state)
        if top_discard_event is not None and player_cards.can_play_from_discard_with_amulet(state, top_discard_event):
            fast_ids.append(top_discard_event)
        seen_fast_codes: set[tuple[str, bool]] = set()
        for card_id in fast_ids:
            instance = state.card_instances[card_id]
            code = instance.card_code
            card = card_data.get_card(code)
            cost = int(card.get("cost") or 0)
            if state.investigator.resources < cost or dissonant_blocks(state, code):
                continue
            from_discard = card_id not in state.investigator.hand
            if from_discard and card.get("type_code") != "event":
                continue
            if (code, from_discard) in seen_fast_codes:
                continue
            seen_fast_codes.add((code, from_discard))
            if code == "01030":
                if from_discard:
                    continue
                if not can_enter_play_unique(state, code):
                    continue
                options.append(DecisionOption("Play Magnifying Glass (fast)", {"kind": "action", "action": "fast_ability", "ability": "play_fast_asset", "card": card_id}))
            elif code == "01044":
                if from_discard:
                    continue
                if not can_enter_play_unique(state, code):
                    continue
                options.append(DecisionOption("Play Switchblade (fast)", {"kind": "action", "action": "fast_ability", "ability": "play_fast_asset", "card": card_id}))
            elif code == "01010":
                options.append(DecisionOption("Play On the Lam", {"kind": "action", "action": "fast_ability", "ability": "on_the_lam", "card": card_id}))
            elif code == "01036":
                options.append(DecisionOption("Play Mind over Matter", {"kind": "action", "action": "fast_ability", "ability": "mind_over_matter", "card": card_id}))
            elif code == "01037" and state.locations[state.investigator.location_id].clues > 0:
                options.append(DecisionOption("Play Working a Hunch", {"kind": "action", "action": "fast_ability", "ability": "working_hunch", "card": card_id}))
            elif code == "01050":
                # Only offer Elusive when it can change the game state (RR play
                # rules): a legal move destination or an enemy to disengage from.
                destinations = elusive_destinations(state)
                for location_id in destinations:
                    options.append(DecisionOption(f"Play Elusive and move to {state.locations[location_id].name}", {"kind": "action", "action": "fast_ability", "ability": "elusive", "card": card_id, "location": location_id}))
                if not destinations and state.investigator.engaged_enemies:
                    options.append(DecisionOption("Play Elusive (disengage; no eligible move)", {"kind": "action", "action": "fast_ability", "ability": "elusive", "card": card_id, "location": ""}))
    for debt in player_cards.threat_ids(state, "01011"):
        count = int(state.limits.get(f"hospital_debts:{state.round}", 0))
        if state.investigator.resources > 0 and count < 2:
            banked = state.card_instances[debt].uses.get("resources", 0)
            options.append(DecisionOption(f"Move 1 resource to Hospital Debts ({banked}/6)", {"kind": "action", "action": "fast_ability", "ability": "hospital_debts", "card": debt}))
    for beat_cop in player_cards.play_area_ids(state, "01018"):
        enemies = fight_targets(state)
        if enemies:
            options.append(DecisionOption("Discard Beat Cop to deal 1 damage", {"kind": "action", "action": "fast_ability", "ability": "beat_cop", "card": beat_cop, "enemy": enemies[0]}))
    for knowledge in player_cards.play_area_ids(state, "01058"):
        instance = state.card_instances[knowledge]
        if not instance.exhausted and instance.uses.get("secrets", 0) > 0:
            options.append(
                DecisionOption(
                    f"Use Forbidden Knowledge ({instance.uses['secrets']} secrets)",
                    {"kind": "action", "action": "fast_ability", "ability": "forbidden_knowledge", "card": knowledge},
                )
            )
    for initiate in player_cards.play_area_ids(state, "01063"):
        if not state.card_instances[initiate].exhausted and state.investigator.deck:
            options.append(
                DecisionOption(
                    "Use Arcane Initiate",
                    {"kind": "action", "action": "fast_ability", "ability": "arcane_initiate", "card": initiate},
                )
            )
    for cat in player_cards.play_area_ids(state, "01076"):
        for enemy_id in enemies_at_location(state):
            if not is_elite(state, enemy_id) and can_be_evaded(state, enemy_id):
                options.append(
                    DecisionOption(
                        f"Discard Stray Cat to evade {enemy_name(state, enemy_id)}",
                        {"kind": "action", "action": "fast_ability", "ability": "stray_cat", "card": cat, "enemy": enemy_id},
                    )
                )


def add_asset_action_options(state: GameState, options: list[DecisionOption]) -> None:
    for asset_id in list(state.investigator.play_area):
        instance = state.card_instances[asset_id]
        code = instance.card_code
        if code in {"01006", "01016"} and instance.uses.get("ammo", 0) > 0:
            for enemy_id in fight_targets(state):
                boost = 3 if code == "01006" and player_cards.roland_location_has_clues(state) else 1
                label = _weapon_fight_label(state, enemy_id, player_cards.card_name(state, asset_id), boost, 2, extra=f"{instance.uses['ammo']} ammo")
                options.append(DecisionOption(label, {"kind": "action", "action": "asset_fight", "asset": asset_id, "enemy": enemy_id, "boost": boost, "damage": 2}))
        elif code == "01047" and instance.uses.get("ammo", 0) > 0:
            for enemy_id in fight_targets(state):
                label = _weapon_fight_label(state, enemy_id, player_cards.card_name(state, asset_id), 2, 1, extra=f"{instance.uses['ammo']} ammo; +1 dmg on succeed by 2")
                options.append(DecisionOption(label, {"kind": "action", "action": "asset_fight", "asset": asset_id, "enemy": enemy_id, "boost": 2, "damage": 1, "succeed_by": 2, "bonus_damage": 1}))
        elif code == "01044":
            for enemy_id in fight_targets(state):
                label = _weapon_fight_label(state, enemy_id, "Switchblade", 0, 1, extra="+1 dmg on succeed by 2")
                options.append(DecisionOption(label, {"kind": "action", "action": "asset_fight", "asset": asset_id, "enemy": enemy_id, "boost": 0, "damage": 1, "succeed_by": 2, "bonus_damage": 1}))
        elif code == "01020":
            for enemy_id in fight_targets(state):
                only = len([eid for eid in state.investigator.engaged_enemies if eid in state.enemies]) == 1 and enemy_id in state.investigator.engaged_enemies
                damage = 2 if only else 1
                options.append(DecisionOption(_weapon_fight_label(state, enemy_id, "Machete", 1, damage), {"kind": "action", "action": "asset_fight", "asset": asset_id, "enemy": enemy_id, "boost": 1, "damage": damage}))
        elif code == "01060" and instance.uses.get("charges", 0) > 0:
            for enemy_id in fight_targets(state):
                willpower = player_cards.effective_base_skill(state, "willpower", f"Shrivelling {enemy_name(state, enemy_id)}")
                fight = int(enemy_card(state, enemy_id).get("enemy_fight") or 1)
                options.append(
                    DecisionOption(
                        f"Fight {enemy_name(state, enemy_id)} with Shrivelling ({instance.uses['charges']} charges) — test Willpower({willpower}) vs {fight}, 2 dmg",
                        {"kind": "action", "action": "asset_fight", "asset": asset_id, "enemy": enemy_id, "damage": 2, "skill": "willpower", "spend_use": "charges", "symbol_horror": True},
                    )
                )
        elif code == "01074":
            for enemy_id in fight_targets(state):
                label = _weapon_fight_label(state, enemy_id, "Baseball Bat", 2, 2)
                options.append(DecisionOption(label, {"kind": "action", "action": "asset_fight", "asset": asset_id, "enemy": enemy_id, "boost": 2, "damage": 2, "bat_discard_symbols": True}))
        elif code == "01086":
            for enemy_id in fight_targets(state):
                options.append(DecisionOption(_weapon_fight_label(state, enemy_id, "Knife", 1, 1), {"kind": "action", "action": "asset_fight", "asset": asset_id, "enemy": enemy_id, "boost": 1, "damage": 1}))
                options.append(DecisionOption(_weapon_fight_label(state, enemy_id, "Knife (throw, discards it)", 2, 2), {"kind": "action", "action": "asset_fight", "asset": asset_id, "enemy": enemy_id, "boost": 2, "damage": 2, "discard_asset": True}))
        elif code == "01087" and instance.uses.get("supplies", 0) > 0 and not location_locked(state, state.investigator.location_id):
            options.append(DecisionOption(f"Investigate with Flashlight ({instance.uses['supplies']} supplies, shroud -2)", {"kind": "action", "action": "flashlight", "asset": asset_id}))
        elif code == "01019" and instance.uses.get("supplies", 0) > 0:
            if state.investigator.damage > 0:
                options.append(DecisionOption("Use First Aid to heal 1 damage", {"kind": "action", "action": "first_aid", "asset": asset_id, "heal": "damage"}))
            if state.investigator.horror > 0:
                options.append(DecisionOption("Use First Aid to heal 1 horror", {"kind": "action", "action": "first_aid", "asset": asset_id, "heal": "horror"}))
        elif code == "01031" and not instance.exhausted:
            options.append(DecisionOption("Use Old Book of Lore", {"kind": "action", "action": "old_book", "asset": asset_id}))
        elif code == "01035":
            options.append(DecisionOption("Use Medical Texts", {"kind": "action", "action": "medical_texts", "asset": asset_id}))
        elif code == "01061" and not instance.exhausted and instance.uses.get("charges", 0) > 0:
            if state.investigator.deck:
                options.append(DecisionOption(f"Use Scrying on Daisy's deck ({instance.uses['charges']} charges)", {"kind": "action", "action": "scrying", "asset": asset_id, "target": "investigator"}))
            if state.encounter_deck:
                options.append(DecisionOption(f"Use Scrying on the encounter deck ({instance.uses['charges']} charges)", {"kind": "action", "action": "scrying", "asset": asset_id, "target": "encounter"}))
        elif code == "01045" and not instance.exhausted and not location_locked(state, state.investigator.location_id):
            location = state.locations[state.investigator.location_id]
            if location.revealed and location.shroud is not None:
                shroud = modified_shroud(state, location.id)
                intellect = player_cards.effective_base_skill(state, "intellect", f"Burglary {location.name}")
                options.append(DecisionOption(f"Use Burglary at {location.name} — test Intellect({intellect}) vs {shroud}", {"kind": "action", "action": "burglary", "asset": asset_id}))
    playable_ids = list(state.investigator.hand)
    top_discard_event = player_cards.topmost_discard_event_id(state)
    if top_discard_event is not None:
        playable_ids.append(top_discard_event)
    for card_id in playable_ids:
        from_discard = card_id not in state.investigator.hand
        if from_discard and not player_cards.can_play_from_discard_with_amulet(state, card_id):
            continue
        if state.card_instances[card_id].card_code == "01024" and state.investigator.resources >= 5 and not dissonant_blocks(state, "01024"):
            for location_id in [state.investigator.location_id, *state.locations[state.investigator.location_id].connections]:
                label = f"Play Dynamite Blast at {state.locations[location_id].name}"
                if location_id == state.investigator.location_id:
                    label += f" (hits {state.investigator.name})"
                options.append(DecisionOption(label, {"kind": "action", "action": "dynamite", "card": card_id, "location": location_id}))
        if state.card_instances[card_id].card_code == "01051" and state.investigator.resources >= 3 and not dissonant_blocks(state, "01051"):
            for enemy_id in fight_targets(state):
                agility = player_cards.effective_base_skill(state, "agility", f"Backstab {enemy_name(state, enemy_id)}")
                fight = int(enemy_card(state, enemy_id).get("enemy_fight") or 1)
                suffix = " from discard" if from_discard else ""
                options.append(DecisionOption(f"Play Backstab{suffix} on {enemy_name(state, enemy_id)} — test Agility({agility}) vs {fight}, 3 dmg", {"kind": "action", "action": "backstab", "card": card_id, "enemy": enemy_id}))
        if state.card_instances[card_id].card_code == "01052" and state.investigator.resources >= 2 and not dissonant_blocks(state, "01052"):
            for enemy_id in exhausted_enemies_at_location(state):
                options.append(DecisionOption(f"Play Sneak Attack on {enemy_name(state, enemy_id)}", {"kind": "action", "action": "sneak_attack", "card": card_id, "enemy": enemy_id}))
        if state.card_instances[card_id].card_code == "01066" and state.investigator.resources >= 2 and not dissonant_blocks(state, "01066"):
            for enemy_id in list(state.investigator.engaged_enemies):
                if enemy_id in state.enemies and can_be_evaded(state, enemy_id):
                    willpower = player_cards.effective_base_skill(state, "willpower", f"Blinding Light {enemy_name(state, enemy_id)}")
                    evade = int(enemy_card(state, enemy_id).get("enemy_evade") or 1)
                    options.append(DecisionOption(f"Play Blinding Light to evade {enemy_name(state, enemy_id)} — test Willpower({willpower}) vs {evade}", {"kind": "action", "action": "blinding_light", "card": card_id, "enemy": enemy_id}))
        if state.card_instances[card_id].card_code == "01078" and state.investigator.resources >= 5 and not dissonant_blocks(state, "01078") and enemies_at_location(state):
            suffix = " from discard" if from_discard else ""
            options.append(DecisionOption(f"Play Cunning Distraction{suffix} to evade all enemies at your location", {"kind": "action", "action": "cunning_distraction", "card": card_id}))


def _weapon_fight_label(state: GameState, enemy_id: str, weapon: str, boost: int, damage: int, extra: str | None = None) -> str:
    # Show the effective test math so agents don't have to add the weapon boost
    # themselves: base combat (incl. statics) + weapon boost vs enemy fight.
    effective = player_cards.effective_base_skill(state, "combat", f"Fight {enemy_name(state, enemy_id)}") + boost
    fight = int(enemy_card(state, enemy_id).get("enemy_fight") or 1)
    parts = f"Fight {enemy_name(state, enemy_id)} with {weapon}"
    if extra:
        parts += f" ({extra})"
    return f"{parts} — test Combat({effective}) vs {fight}, {damage} dmg"


def add_locked_door_options(state: GameState, options: list[DecisionOption]) -> None:
    location = state.locations[state.investigator.location_id]
    for attachment in location.attached_instance_ids:
        if state.card_instances[attachment].card_code == "01174":
            options.append(DecisionOption("Break down Locked Door (Combat 4)", {"kind": "action", "action": "locked_door", "door": attachment, "skill": "combat"}))
            options.append(DecisionOption("Pick Locked Door (Agility 4)", {"kind": "action", "action": "locked_door", "door": attachment, "skill": "agility"}))


def add_threat_action_options(state: GameState, options: list[DecisionOption]) -> None:
    for instance_id in player_cards.threat_ids(state, "01098"):
        options.append(
            DecisionOption(
                "Discard Haunted (2 actions)",
                {"kind": "action", "action": "discard_haunted", "card": instance_id},
            )
        )
    for instance_id in player_cards.threat_ids(state, "01009"):
        instance = state.card_instances[instance_id]
        if instance.horror > 0:
            options.append(
                DecisionOption(
                    f"Move 1 horror from The Necronomicon to Daisy ({instance.horror} horror on it)",
                    {"kind": "action", "action": "necronomicon", "asset": instance_id},
                )
            )


def add_mob_enforcer_options(state: GameState, options: list[DecisionOption]) -> None:
    if state.investigator.resources < 4:
        return
    for enemy_id in list(state.investigator.engaged_enemies):
        if enemy_id in state.enemies and state.enemies[enemy_id].card_code == "01101":
            options.append(
                DecisionOption(
                    "Parley with Mob Enforcer (spend 4 resources)",
                    {"kind": "action", "action": "parley_mob", "enemy": enemy_id},
                )
            )


def add_lita_parley_option(state: GameState, options: list[DecisionOption]) -> None:
    lita = player_cards.lita_uncontrolled_at_location(state, state.investigator.location_id)
    if lita:
        options.append(DecisionOption("Parley with Lita Chantler (Intellect 4)", {"kind": "action", "action": "parley_lita", "lita": lita}))


def add_resign_option(state: GameState, options: list[DecisionOption]) -> None:
    if state.scenario not in GATHERING_FAMILY:
        return
    location = state.locations[state.investigator.location_id]
    if location.id == "parlor" and location.revealed:
        options.append(DecisionOption("Resign", {"kind": "action", "action": "resign"}))


def location_locked(state: GameState, location_id: str) -> bool:
    return encounter_cards.location_has_attachment(state, location_id, "01174")


def modified_shroud(state: GameState, location_id: str) -> int:
    location = state.locations[location_id]
    shroud = int(location.shroud or 0)
    if encounter_cards.location_has_attachment(state, location_id, "01168"):
        shroud += 2
    return shroud


def asset_fight(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    asset_id = str(payload["asset"])
    enemy_id = str(payload["enemy"])
    if asset_id not in state.investigator.play_area or enemy_id not in state.enemies:
        return
    asset = state.card_instances[asset_id]
    if asset.card_code in {"01006", "01016", "01047"}:
        if asset.uses.get("ammo", 0) <= 0:
            return
        asset.uses["ammo"] -= 1
    if payload.get("spend_use"):
        use = str(payload.get("spend_use"))
        if asset.uses.get(use, 0) <= 0:
            return
        asset.uses[use] -= 1
    difficulty = int(enemy_card(state, enemy_id).get("enemy_fight") or 1)
    boost = int(payload.get("boost", 0))
    state.limits[f"temp_skill_boost:{asset_id}"] = boost
    on_success = {"kind": "fight", "enemy": enemy_id, "damage": int(payload.get("damage", 1))}
    if payload.get("succeed_by") is not None:
        on_success["succeed_by"] = int(payload.get("succeed_by", 0))
        on_success["bonus_damage"] = int(payload.get("bonus_damage", 0))
    skill = str(payload.get("skill", "combat"))
    skill_test.start(state, events, skill=skill, difficulty=difficulty, source=f"Fight with {player_cards.card_name(state, asset_id)}", on_success=on_success, on_failure={"kind": "fight", "enemy": enemy_id}, base_boost=boost)
    if state.active_skill_test:
        if payload.get("symbol_horror"):
            state.active_skill_test["symbol_horror"] = {"asset": asset_id}
        if payload.get("bat_discard_symbols"):
            state.active_skill_test["bat_discard_symbols"] = {"asset": asset_id}
    if payload.get("discard_asset"):
        player_cards.discard_from_play(state, asset_id)


def flashlight_investigate(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    asset_id = str(payload["asset"])
    asset = state.card_instances[asset_id]
    if asset_id not in state.investigator.play_area or asset.uses.get("supplies", 0) <= 0:
        return
    asset.uses["supplies"] -= 1
    location = state.locations[state.investigator.location_id]
    difficulty = max(0, modified_shroud(state, location.id) - 2)
    skill_test.start(state, events, skill="intellect", difficulty=difficulty, source=f"Investigate with Flashlight {location.name}", on_success={"kind": "investigate"})


def burglary_action(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    asset_id = str(payload.get("asset", ""))
    if asset_id not in state.investigator.play_area:
        return
    asset = state.card_instances[asset_id]
    if asset.card_code != "01045" or asset.exhausted:
        return
    location = state.locations[state.investigator.location_id]
    if not location.revealed or location.shroud is None or location_locked(state, location.id):
        return
    asset.exhausted = True
    skill_test.start(
        state,
        events,
        skill="intellect",
        difficulty=modified_shroud(state, location.id),
        source=f"Burglary {location.name}",
        on_success={"kind": "burglary"},
    )


def first_aid(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    asset_id = str(payload["asset"])
    asset = state.card_instances[asset_id]
    if asset_id not in state.investigator.play_area or asset.uses.get("supplies", 0) <= 0:
        return
    asset.uses["supplies"] -= 1
    if payload.get("heal") == "damage":
        heal_roland(state, events, damage=1)
    else:
        heal_roland(state, events, horror=1)
    if asset.uses.get("supplies", 0) <= 0:
        player_cards.discard_from_play(state, asset_id)
        log_event(events, "asset_discarded", "First Aid was discarded with no supplies.", card=asset_id)


def necronomicon_action(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    from .effects import check_investigator_defeat, present_after_horror_reaction

    asset_id = str(payload.get("asset", ""))
    if asset_id not in state.investigator.threat_area:
        return
    instance = state.card_instances[asset_id]
    if instance.card_code != "01009" or instance.horror <= 0:
        return
    instance.horror -= 1
    state.investigator.horror += 1
    log_event(events, "horror_moved", "Moved 1 horror from The Necronomicon to Daisy Walker.", card=asset_id)
    check_investigator_defeat(state, events)
    if state.status == "in_progress":
        present_after_horror_reaction(state, events)
    if instance.horror <= 0:
        player_cards.discard_from_threat(state, asset_id)
        log_event(events, "weakness_discarded", "The Necronomicon was discarded.", card=asset_id)
        enforce_slot_capacity(state, events)


def scrying_action(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    asset_id = str(payload.get("asset", ""))
    target = str(payload.get("target", ""))
    if asset_id not in state.investigator.play_area:
        return
    instance = state.card_instances[asset_id]
    if instance.card_code != "01061" or instance.exhausted or instance.uses.get("charges", 0) <= 0:
        return
    deck = state.investigator.deck if target == "investigator" else state.encounter_deck
    top = list(deck[:3])
    if not top:
        return
    instance.exhausted = True
    instance.uses["charges"] -= 1
    present_scrying_order_decision(state, target, top)
    log_event(events, "scrying_peek", f"Scrying looked at the top {len(top)} cards of the {target} deck.", card=asset_id, target=target)


def present_scrying_order_decision(state: GameState, target: str, top: list[str]) -> None:
    seen: set[tuple[str, ...]] = set()
    options: list[DecisionOption] = []
    for order_tuple in permutations(top):
        if order_tuple in seen:
            continue
        seen.add(order_tuple)
        labels = [player_cards.card_name(state, card_id) for card_id in order_tuple]
        options.append(
            DecisionOption(
                " / ".join(labels) + " (top first)",
                {"kind": "scrying_order", "target": target, "cards": list(top), "order": list(order_tuple)},
            )
        )
    names = ", ".join(player_cards.card_name(state, card_id) for card_id in top)
    state.decision_queue = [
        PendingDecision(
            id="scrying-order",
            kind="scrying_order",
            prompt=f"Scrying saw: {names}. Choose the return order (first listed is topmost).",
            options=options,
        )
    ]


def resolve_scrying_order(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    target = str(payload.get("target", ""))
    cards = [str(card_id) for card_id in payload.get("cards", [])]
    order = [str(card_id) for card_id in payload.get("order", [])]
    if sorted(cards) != sorted(order):
        return
    deck = state.investigator.deck if target == "investigator" else state.encounter_deck
    if deck[: len(cards)] != cards:
        return
    deck[: len(cards)] = order
    log_event(events, "scrying_ordered", f"Scrying reordered the top {len(order)} cards of the {target} deck.", target=target)


def blinding_light(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    card_id = str(payload.get("card", ""))
    enemy_id = str(payload.get("enemy", ""))
    if not playable_event(state, card_id) or enemy_id not in state.investigator.engaged_enemies:
        return
    if enemy_id not in state.enemies or state.investigator.resources < 2:
        return
    state.investigator.resources -= 2
    if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
        state.investigator.resources += 2
        return
    difficulty = int(enemy_card(state, enemy_id).get("enemy_evade") or 1)
    skill_test.start(
        state,
        events,
        skill="willpower",
        difficulty=difficulty,
        source=f"Blinding Light {enemy_name(state, enemy_id)}",
        on_success={"kind": "blinding_light", "enemy": enemy_id},
        on_failure={"kind": "blinding_light", "enemy": enemy_id},
    )
    if state.active_skill_test:
        state.active_skill_test["blinding_light"] = True
        state.active_skill_test["played_event"] = card_id
    log_event(events, "event_played", "Played Blinding Light.", card=card_id)
    queue_heirloom_reaction(state, card_id)


def playable_event(state: GameState, card_id: str) -> bool:
    if card_id not in state.card_instances:
        return False
    card = card_data.get_card(state.card_instances[card_id].card_code)
    if card.get("type_code") != "event":
        return False
    return card_id in state.investigator.hand or player_cards.can_play_from_discard_with_amulet(state, card_id)


def backstab(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    card_id = str(payload.get("card", ""))
    enemy_id = str(payload.get("enemy", ""))
    if not playable_event(state, card_id) or enemy_id not in fight_targets(state) or state.investigator.resources < 3:
        return
    state.investigator.resources -= 3
    if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
        state.investigator.resources += 3
        return
    difficulty = int(enemy_card(state, enemy_id).get("enemy_fight") or 1)
    skill_test.start(
        state,
        events,
        skill="agility",
        difficulty=difficulty,
        source=f"Backstab {enemy_name(state, enemy_id)}",
        on_success={"kind": "fight", "enemy": enemy_id, "damage": 3},
        on_failure={"kind": "fight", "enemy": enemy_id},
    )
    if state.active_skill_test:
        state.active_skill_test["played_event"] = card_id
    log_event(events, "event_played", "Played Backstab.", card=card_id)


def cunning_distraction(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    card_id = str(payload.get("card", ""))
    if not playable_event(state, card_id) or state.investigator.resources < 5:
        return
    targets = enemies_at_location(state)
    if not targets:
        return
    state.investigator.resources -= 5
    if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
        state.investigator.resources += 5
        return
    evaded = []
    for enemy_id in targets:
        if enemy_id in state.enemies and can_be_evaded(state, enemy_id):
            disengage_enemy(state, events, enemy_id, exhaust=True)
            evaded.append(enemy_id)
    if evaded:
        queue_pickpocketing_reaction(state, evaded[0])
    player_cards.place_played_event(state, card_id, events)
    log_event(events, "event_played", "Played Cunning Distraction.", card=card_id, enemies=evaded)


def discard_haunted(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    card_id = str(payload.get("card", ""))
    if card_id in state.investigator.threat_area and state.card_instances[card_id].card_code == "01098":
        player_cards.discard_from_threat(state, card_id)
        log_event(events, "treachery_discarded", "Haunted was discarded.", card=card_id)


def parley_mob_enforcer(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    enemy_id = str(payload.get("enemy", ""))
    if enemy_id not in state.enemies or state.enemies[enemy_id].card_code != "01101":
        return
    if state.investigator.resources < 4:
        return
    state.investigator.resources -= 4
    enemy = state.enemies.pop(enemy_id)
    if enemy.location_id in state.locations and enemy_id in state.locations[enemy.location_id].enemy_ids:
        state.locations[enemy.location_id].enemy_ids.remove(enemy_id)
    if enemy_id in state.investigator.engaged_enemies:
        state.investigator.engaged_enemies.remove(enemy_id)
    state.card_instances[enemy_id].zone = "discard"
    state.investigator.discard.append(enemy_id)
    log_event(events, "enemy_discarded", "Mob Enforcer was discarded after parley.", enemy=enemy_id)


def old_book_of_lore(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    asset_id = str(payload["asset"])
    if asset_id not in state.investigator.play_area or state.card_instances[asset_id].exhausted:
        return
    state.card_instances[asset_id].exhausted = True
    candidates = list(state.investigator.deck[:3])
    if not candidates:
        log_event(events, "old_book_empty", "Old Book of Lore found no cards.")
        return
    cards = card_data.cards_by_code()
    state.decision_queue = [
        PendingDecision(
            id="old-book-of-lore",
            kind="old_book",
            prompt="Choose 1 card to draw with Old Book of Lore.",
            options=[
                DecisionOption(
                    f"Draw {cards[state.card_instances[card_id].card_code].get('name', card_id)}",
                    {"kind": "old_book_choice", "card": card_id, "candidates": candidates},
                )
                for card_id in candidates
            ],
        )
    ]


def resolve_old_book_choice(
    state: GameState,
    payload: dict[str, Any],
    events: list[dict[str, Any]],
    rng: Any,
) -> None:
    chosen = str(payload["card"])
    candidates = [str(card_id) for card_id in payload.get("candidates", [])]
    candidates = [card_id for card_id in candidates if card_id in state.investigator.deck]
    if chosen not in candidates:
        return
    for card_id in candidates:
        state.investigator.deck.remove(card_id)
    state.investigator.hand.append(chosen)
    state.card_instances[chosen].zone = "hand"
    rest = [card_id for card_id in candidates if card_id != chosen]
    state.investigator.deck.extend(rest)
    rng.shuffle(state.investigator.deck)
    card = card_data.get_card(state.card_instances[chosen].card_code)
    log_event(events, "card_drawn", f"{state.investigator.name} drew {card['name']}.", card=chosen)
    resolve_player_weakness_draw(state, events, chosen)


def dynamite_blast(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    card_id = str(payload["card"])
    location_id = str(payload["location"])
    if not playable_event(state, card_id) or state.investigator.resources < 5:
        return
    state.investigator.resources -= 5
    if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
        state.investigator.resources += 5
        return
    for enemy_id in list(state.locations[location_id].enemy_ids):
        if enemy_id in state.enemies:
            damage_enemy(state, events, enemy_id, 3)
    if state.investigator.location_id == location_id:
        start_damage_assignment(state, events, source="Dynamite Blast", damage=3, horror=0)
    player_cards.place_played_event(state, card_id, events)
    log_event(events, "event_played", f"Dynamite Blast dealt 3 damage at {state.locations[location_id].name}.", card=card_id, location=location_id)


def resolve_fast_ability(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    ability = str(payload.get("ability"))
    card_id = str(payload.get("card"))
    if ability == "play_fast_asset":
        play_card(state, card_id, events)
    elif ability == "mind_over_matter" and playable_event(state, card_id) and state.investigator.resources >= 1:
        state.investigator.resources -= 1
        if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
            state.investigator.resources += 1
            return
        state.limits[f"mind_over_matter:{state.round}"] = True
        player_cards.place_played_event(state, card_id, events)
        log_event(events, "event_played", f"{state.investigator.name} played Mind over Matter.", card=card_id)
    elif ability == "working_hunch" and playable_event(state, card_id) and state.investigator.resources >= 2:
        state.investigator.resources -= 2
        if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
            state.investigator.resources += 2
            return
        discover_clue(state, 1, events)
        player_cards.place_played_event(state, card_id, events)
        log_event(events, "event_played", f"{state.investigator.name} played Working a Hunch.", card=card_id)
    elif ability == "on_the_lam" and playable_event(state, card_id) and state.investigator.resources >= 1:
        state.investigator.resources -= 1
        if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
            state.investigator.resources += 1
            return
        state.limits[f"on_the_lam:{state.round}"] = True
        player_cards.place_played_event(state, card_id, events)
        log_event(events, "event_played", '"Skids" played On the Lam.', card=card_id)
    elif ability == "elusive" and playable_event(state, card_id) and state.investigator.resources >= 2:
        destination = str(payload.get("location", ""))
        if destination and destination not in elusive_destinations(state):
            return
        if not destination and not state.investigator.engaged_enemies:
            return
        state.investigator.resources -= 2
        if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
            state.investigator.resources += 2
            return
        for enemy_id in list(state.investigator.engaged_enemies):
            if enemy_id in state.enemies:
                disengage_enemy(state, events, enemy_id, exhaust=False)
        if destination:
            move_without_engaged_enemies(state, destination, events)
        player_cards.place_played_event(state, card_id, events)
        log_event(events, "event_played", '"Skids" played Elusive.', card=card_id)
    elif ability == "hospital_debts":
        debt_id = card_id
        key = f"hospital_debts:{state.round}"
        count = int(state.limits.get(key, 0))
        if debt_id in state.investigator.threat_area and state.investigator.resources > 0 and count < 2:
            state.investigator.resources -= 1
            debt = state.card_instances[debt_id]
            debt.uses["resources"] = debt.uses.get("resources", 0) + 1
            state.limits[key] = count + 1
            log_event(events, "hospital_debts", "Moved 1 resource to Hospital Debts.", card=debt_id, banked=debt.uses["resources"])
    elif ability == "beat_cop":
        enemy_id = str(payload.get("enemy"))
        if card_id in state.investigator.play_area and enemy_id in state.enemies:
            player_cards.discard_from_play(state, card_id)
            damage_enemy(state, events, enemy_id, 1)
            log_event(events, "beat_cop_ability", "Beat Cop dealt 1 damage.", enemy=enemy_id)
    elif ability == "forbidden_knowledge":
        if card_id in state.investigator.play_area:
            asset = state.card_instances[card_id]
            if asset.card_code == "01058" and not asset.exhausted and asset.uses.get("secrets", 0) > 0:
                asset.exhausted = True
                start_damage_assignment(state, events, source="Forbidden Knowledge", damage=0, horror=1)
                asset.uses["secrets"] -= 1
                state.investigator.resources += 1
                log_event(events, "forbidden_knowledge", "Forbidden Knowledge moved 1 secret to the resource pool.", card=card_id)
                if asset.uses.get("secrets", 0) <= 0:
                    player_cards.discard_from_play(state, card_id)
                    log_event(events, "asset_discarded", "Forbidden Knowledge was discarded with no secrets.", card=card_id)
    elif ability == "arcane_initiate":
        arcane_initiate_action(state, card_id, events)
    elif ability == "stray_cat":
        enemy_id = str(payload.get("enemy", ""))
        if card_id in state.investigator.play_area and state.card_instances[card_id].card_code == "01076":
            if enemy_id in enemies_at_location(state) and not is_elite(state, enemy_id):
                player_cards.discard_from_play(state, card_id)
                disengage_enemy(state, events, enemy_id, exhaust=True)
                queue_pickpocketing_reaction(state, enemy_id)
                log_event(events, "stray_cat", f"Stray Cat automatically evaded {enemy_name(state, enemy_id)}.", enemy=enemy_id)
    elif ability == "skids_action":
        key = f"skids_action:{state.round}"
        if state.investigator.card_code == "01003" and state.investigator.resources >= 2 and not state.limits.get(key):
            state.investigator.resources -= 2
            state.investigator.actions_remaining += 1
            state.limits[key] = True
            log_event(events, "skids_ability", '"Skids" spent 2 resources to gain 1 action.')


def queue_pickpocketing_reaction(state: GameState, enemy_id: str) -> None:
    pickpockets = [
        card_id
        for card_id in player_cards.play_area_ids(state, "01046")
        if not state.card_instances[card_id].exhausted
    ]
    if not pickpockets:
        return
    if any(decision.id == "pickpocketing-reaction" for decision in state.decision_queue):
        return
    state.decision_queue.append(
        PendingDecision(
            id="pickpocketing-reaction",
            kind="pickpocketing_reaction",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Use Pickpocketing after evading {enemy_name(state, enemy_id)}?",
            options=[
                DecisionOption("Exhaust Pickpocketing to draw 1 card", {"kind": "pickpocketing_reaction", "choice": "draw", "card": pickpockets[0]}),
                DecisionOption("Pass", {"kind": "pickpocketing_reaction", "choice": "pass", "card": pickpockets[0]}),
            ],
        )
    )


def resolve_pickpocketing_reaction(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: Any) -> None:
    card_id = str(payload.get("card", ""))
    if payload.get("choice") == "draw" and card_id in state.investigator.play_area and not state.card_instances[card_id].exhausted:
        state.card_instances[card_id].exhausted = True
        draw_player_card(state, events, rng)
        log_event(events, "pickpocketing", "Pickpocketing drew 1 card.", card=card_id)


def arcane_initiate_action(state: GameState, asset_id: str, events: list[dict[str, Any]]) -> None:
    if asset_id not in state.investigator.play_area:
        return
    asset = state.card_instances[asset_id]
    if asset.card_code != "01063" or asset.exhausted:
        return
    candidates = list(state.investigator.deck[:3])
    if not candidates:
        return
    asset.exhausted = True
    cards = card_data.cards_by_code()
    found = [
        card_id
        for card_id in candidates
        if cards[state.card_instances[card_id].card_code].get("type_code") in {"asset", "event"}
        and "Spell" in str(cards[state.card_instances[card_id].card_code].get("traits", ""))
    ]
    names = ", ".join(player_cards.card_name(state, card_id) for card_id in candidates)
    log_event(events, "arcane_initiate_search", f"Arcane Initiate searched: {names}.", card=asset_id)
    options = [
        DecisionOption(
            f"Draw {player_cards.card_name(state, card_id)}",
            {"kind": "arcane_initiate_choice", "card": card_id, "candidates": candidates},
        )
        for card_id in found
    ]
    options.append(
        DecisionOption(
            "Draw no Spell",
            {"kind": "arcane_initiate_choice", "card": "", "candidates": candidates},
        )
    )
    state.decision_queue = [
        PendingDecision(
            id="arcane-initiate-search",
            kind="arcane_initiate",
            prompt=f"Arcane Initiate saw: {names}. Choose a Spell to draw.",
            options=options,
        )
    ]


def resolve_arcane_initiate_choice(
    state: GameState,
    payload: dict[str, Any],
    events: list[dict[str, Any]],
    rng: Any,
) -> None:
    chosen = str(payload.get("card", ""))
    candidates = [str(card_id) for card_id in payload.get("candidates", [])]
    candidates = [card_id for card_id in candidates if card_id in state.investigator.deck]
    if chosen and chosen not in candidates:
        return
    for card_id in candidates:
        state.investigator.deck.remove(card_id)
    if chosen:
        state.investigator.hand.append(chosen)
        state.card_instances[chosen].zone = "hand"
        log_event(events, "card_drawn", f"Arcane Initiate drew {player_cards.card_name(state, chosen)}.", card=chosen)
        resolve_player_weakness_draw(state, events, chosen)
    rest = [card_id for card_id in candidates if card_id != chosen]
    state.investigator.deck.extend(rest)
    rng.shuffle(state.investigator.deck)


def queue_heirloom_reaction(state: GameState, played_id: str) -> None:
    if played_id not in state.card_instances:
        return
    played = state.card_instances[played_id]
    card = card_data.get_card(played.card_code)
    if "Spell" not in str(card.get("traits", "")):
        return
    heirlooms = player_cards.play_area_ids(state, "01012")
    if not heirlooms:
        return
    state.decision_queue.append(
        PendingDecision(
            id="heirloom-reaction",
            kind="heirloom_reaction",
            prompt=f"[Round {state.round} · {state.phase} · Agnes Baker] Use Heirloom of Hyperborea after playing {card.get('name', played.card_code)}?",
            options=[
                DecisionOption(
                    "Draw 1 card",
                    {"kind": "heirloom_reaction", "choice": "draw", "heirloom": heirlooms[0]},
                ),
                DecisionOption(
                    "Pass",
                    {"kind": "heirloom_reaction", "choice": "pass", "heirloom": heirlooms[0]},
                ),
            ],
        )
    )


def resolve_heirloom_reaction(
    state: GameState,
    payload: dict[str, Any],
    events: list[dict[str, Any]],
    rng: Any,
) -> None:
    if payload.get("choice") == "draw" and str(payload.get("heirloom", "")) in state.investigator.play_area:
        draw_player_card(state, events, rng)
        log_event(events, "heirloom_reaction", "Heirloom of Hyperborea drew 1 card.")


def move_without_engaged_enemies(state: GameState, location_id: str, events: list[dict[str, Any]]) -> None:
    current = state.investigator.location_id
    if location_id not in state.locations or location_id == current:
        return
    if current in state.locations and state.investigator.id in state.locations[current].investigator_ids:
        state.locations[current].investigator_ids.remove(state.investigator.id)
    discard_barricades_at_location(state, current, events)
    state.investigator.location_id = location_id
    if state.investigator.id not in state.locations[location_id].investigator_ids:
        state.locations[location_id].investigator_ids.append(state.investigator.id)
    log_event(events, "investigator_moved", f"{state.investigator.name} moved to {state.locations[location_id].name}.", location=location_id)
    if state.scenario in GATHERING_FAMILY:
        from .scenarios import the_gathering

        the_gathering.after_enter_location(state, events, location_id)
    engage_ready_enemies_at_roland(state, events)


def sneak_attack(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    card_id = str(payload.get("card", ""))
    enemy_id = str(payload.get("enemy", ""))
    if not playable_event(state, card_id) or state.investigator.resources < 2:
        return
    if enemy_id not in exhausted_enemies_at_location(state):
        return
    state.investigator.resources -= 2
    if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
        state.investigator.resources += 2
        return
    damage_enemy(state, events, enemy_id, 2)
    player_cards.place_played_event(state, card_id, events)
    log_event(events, "event_played", "Played Sneak Attack.", card=card_id, enemy=enemy_id)


def research_librarian_search(state: GameState, events: list[dict[str, Any]]) -> None:
    cards = card_data.cards_by_code()
    for instance_id in list(state.investigator.deck):
        card = cards[state.card_instances[instance_id].card_code]
        if "Tome" in str(card.get("traits", "")) and card.get("type_code") == "asset":
            state.investigator.deck.remove(instance_id)
            state.investigator.hand.append(instance_id)
            state.card_instances[instance_id].zone = "hand"
            log_event(events, "research_librarian", f"Research Librarian found {card.get('name')}.", card=instance_id)
            break


def discard_barricades_at_location(state: GameState, location_id: str, events: list[dict[str, Any]]) -> None:
    location = state.locations[location_id]
    for attachment in list(location.attached_instance_ids):
        if state.card_instances[attachment].card_code == "01038":
            location.attached_instance_ids.remove(attachment)
            player_cards.discard_event_from_play(state, attachment, events)
            log_event(events, "barricade_discarded", f"Barricade was discarded when {state.investigator.name} left.", card=attachment)
