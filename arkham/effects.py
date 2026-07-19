"""Effect primitive placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import data as card_data
from .cards import player as player_cards
from .errors import EngineError
from .model import DEVOURER_FAMILY, GATHERING_FAMILY, MIDNIGHT_MASKS_FAMILY, CardInstance, DecisionOption, GameState, PendingDecision


class RuleEventList(list[dict[str, Any]]):
    def __init__(self, state: GameState) -> None:
        super().__init__()
        self.state = state


def log_event(events: list[dict[str, Any]], event_type: str, message: str, **data: Any) -> None:
    event = {"type": event_type, "message": message, "data": data}
    state = getattr(events, "state", None)
    if state is not None:
        event["round"] = state.round
        event["phase"] = state.phase
    events.append(event)


def draw_player_card(
    state: GameState,
    events: list[dict[str, Any]],
    rng: Any = None,
    *,
    log_draw: bool = True,
) -> str | None:
    investigator = state.investigator
    reshuffled = False
    if not investigator.deck:
        # RR: an investigator who must draw from an empty deck shuffles his
        # discard pile into his deck, draws, and takes 1 horror after the draw.
        if not investigator.discard:
            log_event(events, "deck_empty", f"{investigator.name}'s deck and discard are both empty; no card drawn.")
            return None
        if rng is None:
            raise EngineError("deck reshuffle requires the game RNG")
        investigator.deck = list(investigator.discard)
        investigator.discard = []
        for instance_id in investigator.deck:
            state.card_instances[instance_id].zone = "deck"
        rng.shuffle(investigator.deck)
        reshuffled = True
        log_event(events, "deck_reshuffled", f"{investigator.name} shuffled their discard pile into their deck (they will take 1 horror).")
    instance_id = investigator.deck.pop(0)
    investigator.hand.append(instance_id)
    state.card_instances[instance_id].zone = "hand"
    card = card_data.get_card(state.card_instances[instance_id].card_code)
    if log_draw:
        log_event(events, "card_drawn", f"{investigator.name} drew {card['name']}.", card=instance_id)
    resolve_player_weakness_draw(state, events, instance_id)
    if reshuffled and state.status == "in_progress":
        start_damage_assignment(state, events, source="empty-deck reshuffle", damage=0, horror=1)
    return instance_id


def add_player_card_to_hand(
    state: GameState,
    events: list[dict[str, Any]],
    instance_id: str,
    *,
    event_type: str = "card_added_to_hand",
    message: str | None = None,
) -> None:
    if instance_id not in state.investigator.hand:
        state.investigator.hand.append(instance_id)
    state.card_instances[instance_id].zone = "hand"
    if message is not None:
        log_event(events, event_type, message, card=instance_id)
    resolve_player_weakness_draw(state, events, instance_id)


def resolve_player_weakness_draw(state: GameState, events: list[dict[str, Any]], instance_id: str) -> None:
    instance = state.card_instances[instance_id]
    if instance.card_code == "01007":
        if instance_id in state.investigator.hand:
            state.investigator.hand.remove(instance_id)
        instance.zone = "threat"
        instance.clues = 3
        state.investigator.threat_area.append(instance_id)
        log_event(events, "weakness_revealed", f"Cover Up entered {state.investigator.name}'s threat area with 3 clues.", card=instance_id)
    elif instance.card_code == "01102":
        if instance_id in state.investigator.hand:
            state.investigator.hand.remove(instance_id)
        from .enemies import spawn_enemy

        spawn_enemy(state, events, instance_id=instance_id, location_id=state.investigator.location_id, engaged=True)
    elif instance.card_code == "01096":
        if instance_id in state.investigator.hand:
            state.investigator.hand.remove(instance_id)
        instance.zone = "discard"
        state.investigator.discard.append(instance_id)
        present_amnesia_decision(state)
        log_event(events, "weakness_revealed", "Amnesia was revealed.", card=instance_id)
    elif instance.card_code == "01097":
        if instance_id in state.investigator.hand:
            state.investigator.hand.remove(instance_id)
        instance.zone = "discard"
        state.investigator.discard.append(instance_id)
        state.investigator.resources = 0
        log_event(events, "weakness_revealed", "Paranoia discarded all resources.", card=instance_id)
    elif instance.card_code in {"01098", "01099", "01100"}:
        if instance_id in state.investigator.hand:
            state.investigator.hand.remove(instance_id)
        instance.zone = "threat"
        state.investigator.threat_area.append(instance_id)
        name = str(card_data.get_card(instance.card_code).get("name", instance.card_code))
        log_event(events, "weakness_revealed", f"{name} entered the threat area.", card=instance_id)
    elif instance.card_code == "01015":
        if instance_id in state.investigator.hand:
            state.investigator.hand.remove(instance_id)
        log_event(events, "weakness_revealed", "Abandoned and Alone was revealed.", card=instance_id)
        start_damage_assignment(state, events, source="Abandoned and Alone", damage=0, horror=2, direct=True)
        if state.status != "in_progress":
            return
        removed = list(state.investigator.discard)
        state.investigator.discard = []
        for discard_id in removed:
            state.card_instances[discard_id].zone = "removed"
            if discard_id not in state.removed_from_game:
                state.removed_from_game.append(discard_id)
        if removed:
            log_event(events, "cards_removed", "Abandoned and Alone removed the discard pile from the game.", cards=removed)
        instance.zone = "discard"
        state.investigator.discard.append(instance_id)
    elif instance.card_code == "01009":
        if instance_id in state.investigator.hand:
            state.investigator.hand.remove(instance_id)
        instance.zone = "threat"
        instance.horror = 3
        state.investigator.threat_area.append(instance_id)
        log_event(events, "weakness_revealed", "The Necronomicon entered Daisy's threat area with 3 horror.", card=instance_id)
        from . import actions

        actions.enforce_slot_capacity(state, events)
    elif instance.card_code == "01011":
        if instance_id in state.investigator.hand:
            state.investigator.hand.remove(instance_id)
        instance.zone = "threat"
        state.investigator.threat_area.append(instance_id)
        log_event(events, "weakness_revealed", "Hospital Debts entered the threat area.", card=instance_id)
    elif card_data.get_card(instance.card_code).get("type_code") == "enemy" and str(card_data.get_card(instance.card_code).get("subtype_code", "")) in {"weakness", "basicweakness"}:
        if instance_id in state.investigator.hand:
            state.investigator.hand.remove(instance_id)
        from .enemies import spawn_enemy

        spawn_enemy(state, events, instance_id=instance_id, location_id=state.investigator.location_id, engaged=True)


def present_amnesia_decision(state: GameState) -> None:
    if len(state.investigator.hand) <= 1:
        return
    cards = card_data.cards_by_code()
    state.decision_queue = [
        PendingDecision(
            id="amnesia-keep",
            kind="amnesia_keep",
            prompt="Choose 1 card to keep for Amnesia.",
            options=[
                DecisionOption(
                    f"Keep {cards[state.card_instances[card_id].card_code].get('name', card_id)}",
                    {"kind": "amnesia_keep", "keep": card_id},
                )
                for card_id in state.investigator.hand
            ],
        )
    ]


def resolve_amnesia_keep(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    state.decision_queue = [decision for decision in state.decision_queue if decision.id != "amnesia-keep"]
    keep = str(payload.get("keep", ""))
    for card_id in list(state.investigator.hand):
        if card_id == keep:
            continue
        player_cards.discard_from_hand(state, card_id)
        log_event(events, "card_discarded", f"Discarded {card_name_for_id(state, card_id)} for Amnesia.", card=card_id)


def card_name_for_id(state: GameState, instance_id: str) -> str:
    return str(card_data.get_card(state.card_instances[instance_id].card_code).get("name", instance_id))


def gain_resource(state: GameState, amount: int, events: list[dict[str, Any]]) -> None:
    state.investigator.resources += amount
    log_event(events, "resource_gained", f"{state.investigator.name} gained {amount} resource.", amount=amount)


def discover_clue(
    state: GameState,
    amount: int,
    events: list[dict[str, Any]],
    *,
    event_type: str = "clue_discovered",
    message: str | None = None,
) -> int:
    if state.scenario in MIDNIGHT_MASKS_FAMILY:
        from .scenarios import the_midnight_masks

        if the_midnight_masks.masked_hunter_blocks_clues(state):
            log_event(events, "clue_discovery_blocked", "The Masked Hunter prevented clue discovery.")
            return 0
    location = state.locations[state.investigator.location_id]
    count = min(amount, location.clues)
    if count <= 0:
        return 0
    cover = active_cover_up(state)
    if cover is not None:
        present_cover_up_decision(
            state,
            count,
            cover,
            event_type=event_type,
            message=message,
        )
        return 0
    return actually_discover_clues(state, count, events, event_type=event_type, message=message)


def actually_discover_clues(
    state: GameState,
    count: int,
    events: list[dict[str, Any]],
    *,
    event_type: str = "clue_discovered",
    message: str | None = None,
) -> int:
    location = state.locations[state.investigator.location_id]
    count = min(count, location.clues)
    if count <= 0:
        return 0
    location.clues -= count
    state.investigator.clues += count
    log_event(
        events,
        event_type,
        message or f"{state.investigator.name} discovered {count} clue.",
        amount=count,
    )
    return count


def active_cover_up(state: GameState) -> str | None:
    for instance_id in list(state.investigator.threat_area):
        instance = state.card_instances[instance_id]
        if instance.card_code == "01007" and instance.clues > 0:
            return instance_id
    return None


def present_cover_up_decision(
    state: GameState,
    amount: int,
    cover: str,
    *,
    event_type: str = "clue_discovered",
    message: str | None = None,
) -> None:
    remove = min(amount, state.card_instances[cover].clues)
    discovery_log = (
        {"event_type": event_type, "message": message}
        if event_type != "clue_discovered" or message is not None
        else {}
    )
    state.decision_queue = [
        PendingDecision(
            id="cover-up-reaction",
            kind="cover_up",
            prompt=f"Cover Up may replace discovering {amount} clue.",
            options=[
                DecisionOption(
                    f"Discard {remove} clue from Cover Up instead",
                    {
                        "kind": "cover_up_choice",
                        "choice": "redirect",
                        "amount": amount,
                        "cover": cover,
                        **discovery_log,
                    },
                ),
                DecisionOption(
                    f"Discover {amount} clue",
                    {
                        "kind": "cover_up_choice",
                        "choice": "discover",
                        "amount": amount,
                        "cover": cover,
                        **discovery_log,
                    },
                ),
            ],
        )
    ]


def resolve_cover_up_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    amount = int(payload.get("amount", 0))
    cover = str(payload.get("cover", ""))
    if payload.get("choice") == "redirect" and cover in state.investigator.threat_area:
        instance = state.card_instances[cover]
        remove = min(amount, instance.clues)
        instance.clues -= remove
        log_event(
            events,
            "cover_up_redirect",
            f"Cover Up redirected {remove} clue discovery.",
            card=cover,
            amount=remove,
            remaining=instance.clues,
        )
        if instance.clues == 0:
            player_cards.discard_from_threat(state, cover)
            log_event(events, "card_discarded", "Cover Up was discarded.", card=cover)
    else:
        actually_discover_clues(
            state,
            amount,
            events,
            event_type=str(payload.get("event_type", "clue_discovered")),
            message=str(payload["message"]) if payload.get("message") else None,
        )


def spend_clues(state: GameState, amount: int, events: list[dict[str, Any]]) -> bool:
    if state.scenario in MIDNIGHT_MASKS_FAMILY:
        from .scenarios import the_midnight_masks

        if the_midnight_masks.masked_hunter_blocks_clues(state):
            log_event(events, "clue_spend_blocked", "The Masked Hunter prevented spending clues.")
            return False
    if state.investigator.clues < amount:
        return False
    state.investigator.clues -= amount
    log_event(events, "clues_spent", f"{state.investigator.name} spent {amount} clue.", amount=amount)
    return True


def place_doom(
    state: GameState,
    amount: int,
    events: list[dict[str, Any]],
    *,
    source: str,
    rng: Any = None,
    can_advance: bool = False,
) -> None:
    if state.agenda is None:
        return
    state.agenda.doom += amount
    log_event(events, "doom_placed", f"Placed {amount} doom on the agenda.", source=source)
    if can_advance:
        check_agenda_advance(state, events, rng=rng)


def check_agenda_advance(state: GameState, events: list[dict[str, Any]], *, rng: Any = None) -> None:
    if state.agenda is None or state.agenda.threshold <= 0:
        return
    if state.active_skill_test:
        state.limits["deferred_agenda_advance"] = True
        return
    if state.scenario in GATHERING_FAMILY:
        from .scenarios import the_gathering

        the_gathering.check_agenda_advance(state, events, rng=rng)
        return
    if state.scenario in MIDNIGHT_MASKS_FAMILY:
        from .scenarios import the_midnight_masks

        the_midnight_masks.check_agenda_advance(state, events, rng=rng)
        return
    if state.scenario in DEVOURER_FAMILY:
        from .scenarios import the_devourer_below

        the_devourer_below.check_agenda_advance(state, events, rng=rng)
        return
    while state.agenda.doom >= state.agenda.threshold and state.status == "in_progress":
        clear_all_doom(state)
        state.agenda.stage += 1
        if state.agenda.stage == 2:
            state.agenda.code = "phaseb_agenda_2"
            state.agenda.name = "The House Stirs"
            state.agenda.threshold = 5
            log_event(events, "agenda_advanced", "Agenda advanced to The House Stirs.")
        else:
            end_game(state, events, "agenda advanced beyond the fixture deck")


def process_deferred_agenda_advance(state: GameState, events: list[dict[str, Any]], *, rng: Any = None) -> None:
    if not state.limits.get("deferred_agenda_advance"):
        return
    if state.active_skill_test or state.pending_damage or state.decision_queue or state.status != "in_progress":
        return
    state.limits.pop("deferred_agenda_advance", None)
    check_agenda_advance(state, events, rng=rng)


def check_act_objective(state: GameState, events: list[dict[str, Any]]) -> None:
    if state.scenario in MIDNIGHT_MASKS_FAMILY:
        from .scenarios import the_midnight_masks

        the_midnight_masks.check_act_objective(state, events)


def finalize_result(state: GameState, events: list[dict[str, Any]], **kwargs: Any) -> None:
    if state.scenario in GATHERING_FAMILY:
        from .scenarios import the_gathering

        the_gathering.finalize_result(state, events, **kwargs)
    elif state.scenario in MIDNIGHT_MASKS_FAMILY:
        from .scenarios import the_midnight_masks

        the_midnight_masks.finalize_result(state, events, **kwargs)
    elif state.scenario in DEVOURER_FAMILY:
        from .scenarios import the_devourer_below

        the_devourer_below.finalize_result(state, events, **kwargs)
    else:
        end_game(state, events, str(kwargs.get("summary", "scenario ended")))


def clear_all_doom(state: GameState) -> None:
    if state.agenda is not None:
        state.agenda.doom = 0
    for enemy in state.enemies.values():
        enemy.doom = 0
    for instance in state.card_instances.values():
        instance.doom = 0


def advance_act(state: GameState, events: list[dict[str, Any]], rng: Any = None) -> None:
    if state.act is None:
        return
    if state.scenario in GATHERING_FAMILY:
        from .scenarios import the_gathering

        the_gathering.advance_act(state, events)
        return
    if state.scenario in DEVOURER_FAMILY:
        from .scenarios import the_devourer_below

        the_devourer_below.advance_act(state, events, rng=rng)
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
    rng: Any = None,
) -> None:
    if damage <= 0 and horror <= 0:
        return
    assignment = {
        "source": source,
        "remaining_damage": damage,
        "remaining_horror": horror,
        "direct": direct,
        "resume": resume or {},
        "assigned": [],
    }
    if resume and resume.get("kind") == "after_attack":
        assignment["attack_enemy_id"] = resume.get("enemy")
    if state.pending_damage is not None:
        state.pending_damage.setdefault("queue", []).append(assignment)
        return
    begin_damage_assignment(state, events, assignment, rng=rng)


def begin_damage_assignment(
    state: GameState,
    events: list[dict[str, Any]],
    assignment: dict[str, Any],
    *,
    rng: Any = None,
) -> None:
    damage = int(assignment.get("remaining_damage", 0))
    horror = int(assignment.get("remaining_horror", 0))
    direct = bool(assignment.get("direct"))
    allies = legal_soak_targets(state) if not direct else []
    if not allies:
        state.investigator.damage += damage
        state.investigator.horror += horror
        log_event(
            events,
            "damage_assigned",
            f"{state.investigator.name} took {damage} damage and {horror} horror.",
            source=str(assignment.get("source", "")),
        )
        check_investigator_defeat(state, events)
        if state.decision_queue:
            defer_damage_continuation(state, assignment)
            return
        if state.status == "in_progress":
            resolve_damage_horror_forced_weaknesses(state, events, damage=damage, horror=horror)
        if state.status == "in_progress" and horror > 0:
            present_after_horror_reaction(state, events)
        if state.decision_queue:
            defer_damage_continuation(state, assignment)
            return
        continue_damage_assignments(state, events, assignment, rng=rng)
        return
    state.pending_damage = assignment
    present_damage_decision(state)


def damage_resumes(assignment: dict[str, Any]) -> list[dict[str, Any]]:
    resumes = []
    resume = dict(assignment.get("resume", {}))
    if resume:
        resumes.append(resume)
    resumes.extend(dict(item) for item in assignment.get("post_resumes", []) if item)
    return resumes


def defer_damage_continuation(state: GameState, assignment: dict[str, Any]) -> None:
    state.limits["deferred_damage_continuation"] = {
        "queue": [dict(item) for item in assignment.get("queue", [])],
        "resumes": damage_resumes(assignment),
    }


def continue_damage_assignments(
    state: GameState,
    events: list[dict[str, Any]],
    assignment: dict[str, Any],
    *,
    rng: Any = None,
) -> None:
    if state.status != "in_progress":
        return
    queue = [dict(item) for item in assignment.get("queue", [])]
    resumes = damage_resumes(assignment)
    if queue:
        next_assignment = queue.pop(0)
        next_assignment["queue"] = queue
        next_assignment["post_resumes"] = resumes
        begin_damage_assignment(state, events, next_assignment, rng=rng)
        return
    resolve_damage_resumes(state, events, resumes, rng=rng)


def resolve_damage_resumes(
    state: GameState,
    events: list[dict[str, Any]],
    resumes: list[dict[str, Any]],
    *,
    rng: Any = None,
) -> None:
    remaining = [dict(resume) for resume in resumes if resume]
    while remaining and state.status == "in_progress" and not state.decision_queue and not state.pending_damage:
        resolve_damage_resume(state, events, remaining.pop(0), rng=rng)
    if remaining and state.status == "in_progress":
        state.limits["deferred_damage_continuation"] = {
            "queue": [],
            "resumes": remaining,
        }


def resume_damage_continuation(state: GameState, events: list[dict[str, Any]], rng: Any = None) -> None:
    if state.status != "in_progress" or state.decision_queue or state.pending_damage:
        return
    continuation = dict(state.limits.pop("deferred_damage_continuation", {}))
    queue = [dict(item) for item in continuation.get("queue", [])]
    resumes = [dict(item) for item in continuation.get("resumes", [])]
    if queue:
        next_assignment = queue.pop(0)
        next_assignment["queue"] = queue
        next_assignment["post_resumes"] = resumes
        begin_damage_assignment(state, events, next_assignment, rng=rng)
        return
    resolve_damage_resumes(state, events, resumes, rng=rng)


def legal_soak_targets(state: GameState) -> list[str]:
    targets: list[str] = []
    cards = card_data.cards_by_code()
    for instance_id in state.investigator.play_area:
        card = cards.get(state.card_instances[instance_id].card_code, {})
        if card.get("type_code") == "asset" and (card.get("health") or card.get("sanity")):
            targets.append(instance_id)
    return targets


def present_damage_decision(state: GameState) -> None:
    pending = state.pending_damage
    if not pending:
        return
    cards = card_data.cards_by_code()
    options = []
    if pending["remaining_damage"] > 0:
        options.append(DecisionOption(f"Assign 1 damage to {state.investigator.name}", {"kind": "assign_damage", "type": "damage", "target": "roland"}))
        for target in legal_soak_targets(state):
            instance = state.card_instances[target]
            card = cards.get(instance.card_code, {})
            assigned = assigned_damage_count(pending, target, "damage")
            if instance.damage + assigned < int(card.get("health") or 0):
                options.append(DecisionOption(f"Assign 1 damage to {card.get('name', target)}", {"kind": "assign_damage", "type": "damage", "target": target}))
    if pending["remaining_horror"] > 0:
        options.append(DecisionOption(f"Assign 1 horror to {state.investigator.name}", {"kind": "assign_damage", "type": "horror", "target": "roland"}))
        for target in legal_soak_targets(state):
            instance = state.card_instances[target]
            card = cards.get(instance.card_code, {})
            assigned = assigned_damage_count(pending, target, "horror")
            if instance.horror + assigned < int(card.get("sanity") or 0):
                options.append(DecisionOption(f"Assign 1 horror to {card.get('name', target)}", {"kind": "assign_damage", "type": "horror", "target": target}))
    # Keep any other queued decisions (e.g. defeat reactions queued when Guard
    # Dog's counter kills the attacker mid-assignment) behind the assignment.
    others = [d for d in state.decision_queue if d.id != "assign-damage"]
    state.decision_queue = [
        PendingDecision(
            id="assign-damage",
            kind="assign_damage",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Assign damage/horror from {pending['source']}.",
            options=options,
        )
    ] + others


def assigned_damage_count(pending: dict[str, Any], target: str, point_type: str) -> int:
    return sum(
        1
        for assignment in pending.get("assigned", [])
        if assignment.get("target") == target and assignment.get("type") == point_type
    )


def assign_damage_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: Any = None) -> None:
    pending = state.pending_damage
    if pending is None:
        return
    point_type = str(payload["type"])
    target = str(payload["target"])
    if point_type not in {"damage", "horror"}:
        return
    if point_type == "damage":
        if int(pending.get("remaining_damage", 0)) <= 0:
            return
        pending["remaining_damage"] -= 1
    else:
        if int(pending.get("remaining_horror", 0)) <= 0:
            return
        pending["remaining_horror"] -= 1
    pending.setdefault("assigned", []).append({"type": point_type, "target": target})
    if target == "roland":
        target_name = state.investigator.name
    else:
        target_card = card_data.cards_by_code().get(state.card_instances[target].card_code, {})
        target_name = str(target_card.get("name", target))
    log_event(events, "damage_assigned", f"Assigned 1 {point_type} to {target_name}.", target=target)
    if pending["remaining_damage"] > 0 or pending["remaining_horror"] > 0:
        present_damage_decision(state)
    else:
        state.pending_damage = None
        damage_to_investigator, horror_to_investigator = apply_assigned_damage(state, pending, events)
        if state.status != "in_progress":
            return
        if state.decision_queue:
            defer_damage_continuation(state, pending)
            return
        resolve_damage_horror_forced_weaknesses(state, events, damage=damage_to_investigator, horror=horror_to_investigator)
        if state.status != "in_progress":
            return
        if horror_to_investigator > 0:
            present_after_horror_reaction(state, events)
            if state.decision_queue:
                defer_damage_continuation(state, pending)
                return
        continue_damage_assignments(state, events, pending, rng=rng)


def resolve_damage_resume(state: GameState, events: list[dict[str, Any]], resume: dict[str, Any], rng: Any = None) -> None:
    if not resume or state.status != "in_progress":
        return
    kind = resume.get("kind")
    if kind == "after_attack":
        from .enemies import after_attack

        after_attack(
            state,
            events,
            str(resume.get("enemy", "")),
            dict(resume.get("resume", {})),
            source=str(resume.get("source", "")),
            rng=rng,
        )
    elif kind == "action":
        from . import actions

        actions.execute(state, dict(resume.get("payload", {})), events, rng)
    elif kind == "scenario":
        from .scenarios import SCENARIOS

        scenario = SCENARIOS.get(state.scenario)
        if scenario is not None:
            scenario.resolve_choice(state, dict(resume), events, rng)
    elif kind == "skill_test_reveal":
        from . import skill_test

        skill_test.resume_deferred_resolution(state, events, rng)


def apply_assigned_damage(state: GameState, pending: dict[str, Any], events: list[dict[str, Any]]) -> tuple[int, int]:
    assignments = list(pending.get("assigned", []))
    damage_to_investigator = 0
    horror_to_investigator = 0
    guard_dog_damage = 0
    for assignment in assignments:
        point_type = str(assignment.get("type", ""))
        target = str(assignment.get("target", ""))
        if target == "roland":
            if point_type == "damage":
                state.investigator.damage += 1
                damage_to_investigator += 1
            elif point_type == "horror":
                state.investigator.horror += 1
                horror_to_investigator += 1
            continue
        if target not in state.card_instances:
            continue
        instance = state.card_instances[target]
        if point_type == "damage":
            instance.damage += 1
            if instance.card_code == "01021" and pending.get("attack_enemy_id"):
                guard_dog_damage += 1
        elif point_type == "horror":
            instance.horror += 1
    if guard_dog_damage and pending.get("attack_enemy_id"):
        from .enemies import damage_enemy

        enemy_id = str(pending["attack_enemy_id"])
        for _ in range(guard_dog_damage):
            if enemy_id in state.enemies:
                damage_enemy(state, events, enemy_id, 1)
                log_event(events, "guard_dog_reaction", "Guard Dog dealt 1 damage to the attacking enemy.", enemy=enemy_id)
    destroy_defeated_assets(state, events)
    check_investigator_defeat(state, events)
    return damage_to_investigator, horror_to_investigator


def resolve_damage_horror_forced_weaknesses(state: GameState, events: list[dict[str, Any]], *, damage: int, horror: int) -> None:
    if state.status != "in_progress":
        return
    if horror > 0 and player_cards.threat_ids(state, "01099"):
        state.investigator.damage += 1
        log_event(events, "weakness_forced", "Psychosis dealt 1 direct damage.", card=player_cards.threat_ids(state, "01099")[0])
        check_investigator_defeat(state, events)
        if state.status == "in_progress":
            resolve_damage_horror_forced_weaknesses(state, events, damage=1, horror=0)
    if state.status != "in_progress":
        return
    if damage > 0 and player_cards.threat_ids(state, "01100"):
        state.investigator.horror += 1
        log_event(events, "weakness_forced", "Hypochondria dealt 1 direct horror.", card=player_cards.threat_ids(state, "01100")[0])
        check_investigator_defeat(state, events)
        if state.status == "in_progress":
            resolve_damage_horror_forced_weaknesses(state, events, damage=0, horror=1)


def destroy_defeated_assets(state: GameState, events: list[dict[str, Any]]) -> None:
    cards = card_data.cards_by_code()
    for instance_id in list(state.investigator.play_area):
        instance = state.card_instances[instance_id]
        card = cards.get(instance.card_code, {})
        health = int(card.get("health") or 0)
        sanity = int(card.get("sanity") or 0)
        if (health and instance.damage >= health) or (sanity and instance.horror >= sanity):
            player_cards.discard_from_play(state, instance_id)
            log_event(events, "asset_discarded", f"{card.get('name', instance_id)} was discarded.", card=instance_id)


def check_investigator_defeat(state: GameState, events: list[dict[str, Any]]) -> None:
    # Guarded: this is called from every damage/horror sink; the defeat trauma
    # must apply exactly once (it double-counted in the opus48/sonnet5 demos).
    if state.status != "in_progress" or state.limits.get("defeat_trauma_applied"):
        return
    physical = state.investigator.damage >= state.investigator.health
    mental = state.investigator.horror >= state.investigator.sanity
    if physical or mental:
        state.limits["defeat_trauma_applied"] = True
        if physical and mental:
            state.limits["pending_defeat_summary"] = f"{state.investigator.name} was defeated"
            state.decision_queue = [
                PendingDecision(
                    id="defeat-trauma-choice",
                    kind="defeat_trauma",
                    prompt="Choose trauma for simultaneous defeat.",
                    options=[
                        DecisionOption("Suffer 1 physical trauma", {"kind": "defeat_trauma", "type": "physical"}),
                        DecisionOption("Suffer 1 mental trauma", {"kind": "defeat_trauma", "type": "mental"}),
                    ],
                )
            ]
            return
        state.trauma["physical"] = int(state.trauma.get("physical", 0)) + (1 if physical else 0)
        state.trauma["mental"] = int(state.trauma.get("mental", 0)) + (1 if mental else 0)
        end_game(state, events, f"{state.investigator.name} was defeated")


def resolve_defeat_trauma_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    trauma_type = str(payload.get("type", ""))
    if trauma_type not in {"physical", "mental"} or state.status != "in_progress":
        return
    state.decision_queue = [decision for decision in state.decision_queue if decision.id != "defeat-trauma-choice"]
    state.trauma[trauma_type] = int(state.trauma.get(trauma_type, 0)) + 1
    summary = str(state.limits.pop("pending_defeat_summary", f"{state.investigator.name} was defeated"))
    end_game(state, events, summary)


def end_game(state: GameState, events: list[dict[str, Any]], summary: str) -> None:
    apply_cover_up_trauma(state, events)
    state.status = "ended"
    state.decision_queue = []
    state.result = {"outcome": summary, "round": state.round, "trauma": dict(state.trauma)}
    dispatched_event_count = len(events)
    if state.scenario in GATHERING_FAMILY:
        from .scenarios import the_gathering

        the_gathering.finalize_result(state, events, outcome="no_resolution", summary=summary)
    elif state.scenario in MIDNIGHT_MASKS_FAMILY:
        from .scenarios import the_midnight_masks

        the_midnight_masks.finalize_result(state, events, outcome="R1", resolution="R1", summary=summary)
    elif state.scenario in DEVOURER_FAMILY:
        from .scenarios import the_devourer_below

        the_devourer_below.finalize_result(state, events, outcome="no_resolution", resolution="no_resolution", summary=summary)
    if not any(event.get("type") == "game_end" for event in events[dispatched_event_count:]):
        log_event(events, "game_end", summary)


def apply_cover_up_trauma(state: GameState, events: list[dict[str, Any]]) -> None:
    key = "cover_up_trauma_applied"
    if state.limits.get(key):
        return
    remaining = 0
    for instance_id in state.investigator.threat_area:
        instance = state.card_instances[instance_id]
        if instance.card_code == "01007":
            remaining += instance.clues
    if remaining > 0:
        state.trauma["mental"] = int(state.trauma.get("mental", 0)) + 1
        state.limits[key] = True
        log_event(events, "cover_up_trauma", "Cover Up caused 1 mental trauma.", remaining=remaining)


def heal_roland(state: GameState, events: list[dict[str, Any]], *, damage: int = 0, horror: int = 0) -> None:
    if damage > 0 and state.investigator.damage > 0:
        healed = min(damage, state.investigator.damage)
        state.investigator.damage = max(0, state.investigator.damage - damage)
        log_event(events, "damage_healed", f"{state.investigator.name} healed {healed} damage.", amount=healed)
    if horror > 0 and state.investigator.horror > 0:
        healed = min(horror, state.investigator.horror)
        state.investigator.horror = max(0, state.investigator.horror - horror)
        log_event(events, "horror_healed", f"{state.investigator.name} healed {healed} horror.", amount=healed)


def present_after_horror_reaction(state: GameState, events: list[dict[str, Any]]) -> None:
    if state.investigator.card_code != "01004" or player_cards.investigator_text_blank(state):
        return
    key = f"agnes_horror:{state.phase}:{state.round}"
    if state.limits.get(key):
        return
    enemies = [
        enemy_id
        for enemy_id in state.locations[state.investigator.location_id].enemy_ids
        if enemy_id in state.enemies
    ]
    if not enemies:
        return
    from .enemies import enemy_name

    options = [
        DecisionOption(
            f"Deal 1 damage to {enemy_name(state, enemy_id)}",
            {"kind": "agnes_horror_reaction", "enemy": enemy_id, "key": key},
        )
        for enemy_id in enemies
    ]
    options.append(DecisionOption("Pass", {"kind": "agnes_horror_reaction", "enemy": "", "key": key, "pass": True}))
    state.decision_queue.append(
        PendingDecision(
            id="agnes-after-horror",
            kind="after_horror",
            prompt=f"[Round {state.round} · {state.phase} · Agnes Baker] Use Agnes Baker reaction after horror was placed?",
            options=options,
        )
    )


def resolve_agnes_horror_reaction(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    key = str(payload.get("key", f"agnes_horror:{state.phase}:{state.round}"))
    state.limits[key] = True
    if payload.get("pass"):
        return
    enemy_id = str(payload.get("enemy", ""))
    if enemy_id in state.enemies:
        from .enemies import damage_enemy

        damage_enemy(state, events, enemy_id, 1)
        log_event(events, "agnes_reaction", "Agnes dealt 1 damage after horror was placed.", enemy=enemy_id)


def discard_asset_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    instance_id = str(payload["card"])
    if instance_id not in state.investigator.play_area:
        return
    name = player_cards.card_name(state, instance_id)
    player_cards.discard_from_play(state, instance_id)
    log_event(events, "asset_discarded", f"{name} was discarded.", card=instance_id)
    from . import actions

    actions.enforce_slot_capacity(state, events)
