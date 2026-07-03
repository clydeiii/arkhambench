"""Action generation and execution placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import data as card_data
from .cards import encounter_cards, player as player_cards
from .effects import advance_act, discover_clue, draw_player_card, gain_resource, heal_roland, legal_soak_targets, log_event, spend_clues, start_damage_assignment
from .enemies import attack, damage_enemy, enemy_damage_horror, engage_enemy, engage_ready_enemies_at_roland, enemy_card, enemy_name, legal_dodge_card, move_engaged_enemies_with_roland
from .errors import EngineError
from .model import DecisionOption, GameState, PendingDecision
from . import skill_test


SAFE_FROM_AOO = {"resign", "pass", "advance_act"}
FREE_ACTIONS = {"fast_ability"}
NON_ACTIONS = {"advance_act", "pass"}


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
    if (
        state.act
        and state.act.clues_required is not None
        and investigator.clues >= state.act.clues_required
        and not (state.scenario == "the_gathering" and state.act.stage == 2)
    ):
        options.append(DecisionOption(f"Advance act by spending {state.act.clues_required} clues", {"kind": "action", "action": "advance_act"}))
    if location.revealed and location.shroud is not None and not location_locked(state, location.id):
        shroud = modified_shroud(state, location.id)
        intellect = player_cards.effective_base_skill(state, "intellect", f"Investigate {location.name}")
        options.append(DecisionOption(f"Investigate {location.name} (shroud {shroud}) — test Intellect({intellect}) vs {shroud}", {"kind": "action", "action": "investigate"}))
    for target in sorted(location.connections, key=lambda loc: (state.locations[loc].code, loc)):
        if state.scenario == "the_gathering" and target == "parlor" and not state.locations[target].revealed:
            continue
        options.append(DecisionOption(f"Move to {state.locations[target].name}", {"kind": "action", "action": "move", "location": target}))
    for enemy_id in fight_targets(state):
        card = enemy_card(state, enemy_id)
        combat = player_cards.effective_base_skill(state, "combat", f"Fight {enemy_name(state, enemy_id)}")
        options.append(DecisionOption(f"Fight {enemy_name(state, enemy_id)} (fight {card.get('enemy_fight', 1)}, 1 dmg) — test Combat({combat})", {"kind": "action", "action": "fight", "enemy": enemy_id}))
    for enemy_id in list(investigator.engaged_enemies):
        card = enemy_card(state, enemy_id)
        agility = player_cards.effective_base_skill(state, "agility", f"Evade {enemy_name(state, enemy_id)}")
        options.append(DecisionOption(f"Evade {enemy_name(state, enemy_id)} (evade {card.get('enemy_evade', 1)}) — test Agility({agility})", {"kind": "action", "action": "evade", "enemy": enemy_id}))
    for enemy_id in sorted(location.enemy_ids):
        if enemy_id not in investigator.engaged_enemies and state.enemies[enemy_id].engaged_with is None:
            options.append(DecisionOption(f"Engage {enemy_name(state, enemy_id)}", {"kind": "action", "action": "engage", "enemy": enemy_id}))
    options.append(DecisionOption("Draw 1 card", {"kind": "action", "action": "draw"}))
    options.append(DecisionOption("Take resource (gain 1)", {"kind": "action", "action": "resource"}))
    add_asset_action_options(state, options)
    add_locked_door_options(state, options)
    add_lita_parley_option(state, options)
    add_resign_option(state, options)
    add_fast_options(state, options)
    for instance_id in investigator.hand:
        instance = state.card_instances[instance_id]
        card = card_data.cards_by_code().get(instance.card_code, {})
        cost = int(card.get("cost") or 0)
        if (
            card.get("type_code") in {"asset", "event"}
            and investigator.resources >= cost
            and not dissonant_blocks(state, instance.card_code)
            and not is_fast_turn_card(instance.card_code)
            and instance.card_code != "01024"
        ):
            options.append(DecisionOption(f"Play {card.get('name', instance.card_code)} ({cost} res)", {"kind": "action", "action": "play", "card": instance_id}))
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
        if action in FREE_ACTIONS or action in NON_ACTIONS or effective_action_cost(state, action) <= state.investigator.actions_remaining:
            affordable.append(option)
    return affordable


def fight_targets(state: GameState) -> list[str]:
    ids = set(state.investigator.engaged_enemies)
    ids.update(state.locations[state.investigator.location_id].enemy_ids)
    return sorted(enemy_id for enemy_id in ids if enemy_id in state.enemies)


def execute(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: Any = None) -> None:
    action = str(payload["action"])
    if action not in NON_ACTIONS | FREE_ACTIONS:
        if not payload.get("skip_aoo"):
            attacks_of_opportunity(state, events, action, payload, rng=rng)
        if state.decision_queue or state.status != "in_progress":
            return
        spend_action(state, events, action)
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
        difficulty = int(enemy_card(state, enemy_id).get("enemy_evade") or 1)
        skill_test.start(state, events, skill="agility", difficulty=difficulty, source=f"Evade {enemy_name(state, enemy_id)}", on_success={"kind": "evade", "enemy": enemy_id})
    elif action == "engage":
        engage_enemy(state, events, str(payload["enemy"]))
    elif action == "draw":
        draw_player_card(state, events, rng)
    elif action == "resource":
        gain_resource(state, 1, events)
    elif action == "play":
        play_card(state, str(payload["card"]), events)
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
    elif action == "locked_door":
        skill = str(payload["skill"])
        skill_test.start(state, events, skill=skill, difficulty=4, source="Locked Door", on_success={"kind": "locked_door", "door": payload["door"]})
    elif action == "parley_lita":
        skill_test.start(state, events, skill="intellect", difficulty=4, source="Parley with Lita Chantler", on_success={"kind": "lita_parley", "lita": payload["lita"]})
    elif action == "dynamite":
        dynamite_blast(state, payload, events)
    elif action == "fast_ability":
        resolve_fast_ability(state, payload, events)
    elif action == "advance_act":
        if state.act and state.act.clues_required is not None and spend_clues(state, state.act.clues_required, events):
            advance_act(state, events)
    elif action == "pass":
        state.investigator.actions_remaining = 0
        log_event(events, "turn_passed", "Roland ended his turn.")
    elif action == "resign":
        from .scenarios import the_gathering

        the_gathering.resign(state, events)


def spend_action(state: GameState, events: list[dict[str, Any]], action: str) -> None:
    cost = effective_action_cost(state, action)
    if cost > state.investigator.actions_remaining:
        raise EngineError(f"cannot spend {cost} actions with only {state.investigator.actions_remaining} remaining")
    mark_action_cost_paid(state, action, cost)
    state.investigator.actions_remaining -= cost
    state.turn.action_index += cost
    state.limits["actions_taken"] = int(state.limits.get("actions_taken", 0)) + cost
    log_event(events, "action_spent", f"Spent {cost} action on {action}.", action=action, cost=cost)


def effective_action_cost(state: GameState, action: str) -> int:
    cost = 1
    designator = action_designator(action)
    key = f"frozen:{state.round}:move_fight_evade"
    if designator in {"move", "fight", "evade"} and has_threat(state, "01164") and not state.limits.get(key):
        cost += 1
    return cost


def mark_action_cost_paid(state: GameState, action: str, cost: int) -> None:
    designator = action_designator(action)
    key = f"frozen:{state.round}:move_fight_evade"
    if cost > 1 and designator in {"move", "fight", "evade"}:
        state.limits[key] = True


def action_designator(action: str) -> str:
    if action == "asset_fight":
        return "fight"
    if action == "parley_lita":
        return "parley"
    return action


def attacks_of_opportunity(state: GameState, events: list[dict[str, Any]], action: str, payload: dict[str, Any], rng: Any = None) -> None:
    if action in SAFE_FROM_AOO:
        return
    exempt_enemy = targeted_aoo_exempt_enemy(action, payload)
    for enemy_id in list(state.investigator.engaged_enemies):
        if enemy_id == exempt_enemy:
            continue
        enemy = state.enemies.get(enemy_id)
        if enemy and not enemy.exhausted:
            resume_payload = dict(payload)
            resume_payload["skip_aoo"] = True
            resume = {"kind": "action", "payload": resume_payload} if aoo_needs_resume(state, enemy_id) else None
            attack(
                state,
                events,
                enemy_id,
                source="attack of opportunity",
                resume=resume,
                rng=rng,
            )
            if state.decision_queue:
                return


def targeted_aoo_exempt_enemy(action: str, payload: dict[str, Any]) -> str | None:
    designator = action_designator(action)
    if designator in {"fight", "evade"}:
        return str(payload.get("enemy")) if payload.get("enemy") else None
    if designator == "parley" and payload.get("enemy"):
        return str(payload.get("enemy"))
    return None


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
    log_event(events, "investigator_moved", f"Roland moved to {state.locations[location_id].name}.", location=location_id)
    if state.scenario == "the_gathering":
        from .scenarios import the_gathering

        the_gathering.after_enter_location(state, events, location_id)
    engage_ready_enemies_at_roland(state, events)


def play_card(state: GameState, instance_id: str, events: list[dict[str, Any]]) -> None:
    if instance_id not in state.investigator.hand:
        return
    instance = state.card_instances[instance_id]
    card = card_data.cards_by_code().get(instance.card_code, {})
    if dissonant_blocks(state, instance.card_code):
        return
    cost = int(card.get("cost") or 0)
    if state.investigator.resources < cost:
        return
    state.investigator.resources -= cost
    state.investigator.hand.remove(instance_id)
    if card.get("type_code") == "asset":
        instance.zone = "play"
        state.investigator.play_area.append(instance_id)
        player_cards.setup_uses(instance)
        if instance.card_code == "01032":
            research_librarian_search(state, events)
    else:
        if instance.card_code == "01088":
            gain_resource(state, 3, events)
        elif instance.card_code == "01038":
            instance.zone = "attachment"
            state.locations[state.investigator.location_id].attached_instance_ids.append(instance_id)
            log_event(events, "event_attached", "Barricade attached to Roland's location.", card=instance_id, location=state.investigator.location_id)
            return
        instance.zone = "discard"
        state.investigator.discard.append(instance_id)
    log_event(events, "card_played", f"Roland played {card.get('name', instance.card_code)}.", card=instance_id)


def has_threat(state: GameState, code: str) -> bool:
    return any(state.card_instances[instance_id].card_code == code for instance_id in state.investigator.threat_area)


def dissonant_blocks(state: GameState, card_code: str) -> bool:
    if not has_threat(state, "01165"):
        return False
    card = card_data.get_card(card_code)
    return card.get("type_code") in {"asset", "event"}


def is_fast_turn_card(card_code: str) -> bool:
    return card_code in {"01022", "01023", "01030", "01036", "01037"}


def add_fast_options(state: GameState, options: list[DecisionOption], *, during_turn: bool = True) -> None:
    # Fast card PLAYS are only legal during the investigator's own turn;
    # triggered fast abilities on in-play cards (Beat Cop) work in any window.
    if during_turn:
        for card_id in list(state.investigator.hand):
            instance = state.card_instances[card_id]
            code = instance.card_code
            card = card_data.get_card(code)
            cost = int(card.get("cost") or 0)
            if state.investigator.resources < cost or dissonant_blocks(state, code):
                continue
            if code == "01030":
                options.append(DecisionOption("Play Magnifying Glass (fast)", {"kind": "action", "action": "fast_ability", "ability": "play_fast_asset", "card": card_id}))
            elif code == "01036":
                options.append(DecisionOption("Play Mind over Matter", {"kind": "action", "action": "fast_ability", "ability": "mind_over_matter", "card": card_id}))
            elif code == "01037" and state.locations[state.investigator.location_id].clues > 0:
                options.append(DecisionOption("Play Working a Hunch", {"kind": "action", "action": "fast_ability", "ability": "working_hunch", "card": card_id}))
    for beat_cop in player_cards.play_area_ids(state, "01018"):
        enemies = fight_targets(state)
        if enemies:
            options.append(DecisionOption("Discard Beat Cop to deal 1 damage", {"kind": "action", "action": "fast_ability", "ability": "beat_cop", "card": beat_cop, "enemy": enemies[0]}))


def add_asset_action_options(state: GameState, options: list[DecisionOption]) -> None:
    for asset_id in list(state.investigator.play_area):
        instance = state.card_instances[asset_id]
        code = instance.card_code
        if code in {"01006", "01016"} and instance.uses.get("ammo", 0) > 0:
            for enemy_id in fight_targets(state):
                boost = 3 if code == "01006" and player_cards.roland_location_has_clues(state) else 1
                label = _weapon_fight_label(state, enemy_id, player_cards.card_name(state, asset_id), boost, 2, extra=f"{instance.uses['ammo']} ammo")
                options.append(DecisionOption(label, {"kind": "action", "action": "asset_fight", "asset": asset_id, "enemy": enemy_id, "boost": boost, "damage": 2}))
        elif code == "01020":
            for enemy_id in fight_targets(state):
                only = len([eid for eid in state.investigator.engaged_enemies if eid in state.enemies]) == 1 and enemy_id in state.investigator.engaged_enemies
                damage = 2 if only else 1
                options.append(DecisionOption(_weapon_fight_label(state, enemy_id, "Machete", 1, damage), {"kind": "action", "action": "asset_fight", "asset": asset_id, "enemy": enemy_id, "boost": 1, "damage": damage}))
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
    for card_id in list(state.investigator.hand):
        if state.card_instances[card_id].card_code == "01024" and state.investigator.resources >= 5 and not dissonant_blocks(state, "01024"):
            for location_id in [state.investigator.location_id, *state.locations[state.investigator.location_id].connections]:
                label = f"Play Dynamite Blast at {state.locations[location_id].name}"
                if location_id == state.investigator.location_id:
                    label += " (hits Roland)"
                options.append(DecisionOption(label, {"kind": "action", "action": "dynamite", "card": card_id, "location": location_id}))


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


def add_lita_parley_option(state: GameState, options: list[DecisionOption]) -> None:
    lita = player_cards.lita_uncontrolled_at_location(state, state.investigator.location_id)
    if lita:
        options.append(DecisionOption("Parley with Lita Chantler (Intellect 4)", {"kind": "action", "action": "parley_lita", "lita": lita}))


def add_resign_option(state: GameState, options: list[DecisionOption]) -> None:
    if state.scenario != "the_gathering":
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
    if asset.card_code in {"01006", "01016"}:
        if asset.uses.get("ammo", 0) <= 0:
            return
        asset.uses["ammo"] -= 1
    difficulty = int(enemy_card(state, enemy_id).get("enemy_fight") or 1)
    boost = int(payload.get("boost", 0))
    state.limits[f"temp_skill_boost:{asset_id}"] = boost
    skill_test.start(state, events, skill="combat", difficulty=difficulty, source=f"Fight with {player_cards.card_name(state, asset_id)}", on_success={"kind": "fight", "enemy": enemy_id, "damage": int(payload.get("damage", 1))}, on_failure={"kind": "fight", "enemy": enemy_id})
    if state.active_skill_test:
        state.active_skill_test["base"] += boost
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
    log_event(events, "card_drawn", f"Roland drew {card['name']}.", card=chosen)


def dynamite_blast(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    card_id = str(payload["card"])
    location_id = str(payload["location"])
    if card_id not in state.investigator.hand or state.investigator.resources < 5:
        return
    state.investigator.resources -= 5
    player_cards.discard_from_hand(state, card_id)
    for enemy_id in list(state.locations[location_id].enemy_ids):
        if enemy_id in state.enemies:
            damage_enemy(state, events, enemy_id, 3)
    if state.investigator.location_id == location_id:
        start_damage_assignment(state, events, source="Dynamite Blast", damage=3, horror=0)
    log_event(events, "event_played", f"Dynamite Blast dealt 3 damage at {state.locations[location_id].name}.", card=card_id, location=location_id)


def resolve_fast_ability(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    ability = str(payload.get("ability"))
    card_id = str(payload.get("card"))
    if ability == "play_fast_asset":
        play_card(state, card_id, events)
    elif ability == "mind_over_matter" and card_id in state.investigator.hand and state.investigator.resources >= 1:
        state.investigator.resources -= 1
        player_cards.discard_from_hand(state, card_id)
        state.limits[f"mind_over_matter:{state.round}"] = True
        log_event(events, "event_played", "Roland played Mind over Matter.", card=card_id)
    elif ability == "working_hunch" and card_id in state.investigator.hand and state.investigator.resources >= 2:
        state.investigator.resources -= 2
        player_cards.discard_from_hand(state, card_id)
        discover_clue(state, 1, events)
        log_event(events, "event_played", "Roland played Working a Hunch.", card=card_id)
    elif ability == "beat_cop":
        enemy_id = str(payload.get("enemy"))
        if card_id in state.investigator.play_area and enemy_id in state.enemies:
            player_cards.discard_from_play(state, card_id)
            damage_enemy(state, events, enemy_id, 1)
            log_event(events, "beat_cop_ability", "Beat Cop dealt 1 damage.", enemy=enemy_id)


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
            state.card_instances[attachment].zone = "discard"
            state.investigator.discard.append(attachment)
            log_event(events, "barricade_discarded", "Barricade was discarded when Roland left.", card=attachment)
