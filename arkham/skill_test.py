"""Skill test state machine placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import data as card_data
from .cards import encounter_cards, player as player_cards
from .chaos import draw_token, token_modifier
from .effects import (
    discard_asset_choice,
    discover_clue,
    draw_player_card,
    heal_roland,
    log_event,
    start_damage_assignment,
)
from .enemies import damage_enemy, disengage_enemy, has_retaliate, attack
from .model import DecisionOption, GameState, PendingDecision
from .rng import ArkhamRng


SKILL_ICON_KEYS = {
    "willpower": "skill_willpower",
    "intellect": "skill_intellect",
    "combat": "skill_combat",
    "agility": "skill_agility",
}


def start(
    state: GameState,
    events: list[dict[str, Any]],
    *,
    skill: str,
    difficulty: int,
    source: str,
    on_success: dict[str, Any] | None = None,
    on_failure: dict[str, Any] | None = None,
) -> None:
    base = player_cards.effective_base_skill(state, skill, source)
    state.active_skill_test = {
        "skill": skill,
        "difficulty": difficulty,
        "source": source,
        "base": base,
        "boosts": [],
        "committed": [],
        "token": None,
        "modifier": 0,
        "autofail": False,
        "on_success": on_success or {},
        "on_failure": on_failure or {},
    }
    log_event(events, "skill_test_started", f"Started {skill} test {base} vs {difficulty}.", source=source)
    present_commit_decision(state)


def present_commit_decision(state: GameState) -> None:
    test = state.active_skill_test
    if not test:
        return
    options: list[DecisionOption] = []
    cards = card_data.cards_by_code()
    skill = str(test["skill"])
    for instance_id in state.investigator.hand:
        instance = state.card_instances[instance_id]
        card = cards.get(instance.card_code, {})
        if player_cards.max_one_committed_already(state, instance.card_code):
            continue
        icons = icon_count(card, skill)
        if icons > 0:
            options.append(
                DecisionOption(
                    f"Commit {card.get('name', instance.card_code)} (+{icons})",
                    {"kind": "commit_card", "card": instance_id},
                )
            )
    options.extend(player_cards.boost_options(state))
    options.append(DecisionOption("Done", {"kind": "commit_done"}))
    state.decision_queue = [
        PendingDecision(
            id="commit-cards",
            kind="commit_cards",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Commit cards to {test['source']} ({skill} vs {test['difficulty']}).",
            options=options,
        )
    ]


def icon_count(card: dict[str, Any], skill: str) -> int:
    return int(card.get(SKILL_ICON_KEYS[skill]) or 0) + int(card.get("skill_wild") or 0)


def commit_card(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    test = state.active_skill_test
    if not test:
        return
    instance_id = str(payload["card"])
    if instance_id not in state.investigator.hand:
        return
    if player_cards.max_one_committed_already(state, state.card_instances[instance_id].card_code):
        return
    state.investigator.hand.remove(instance_id)
    test["committed"].append(instance_id)
    state.card_instances[instance_id].zone = "committed"
    card = card_data.get_card(state.card_instances[instance_id].card_code)
    log_event(events, "card_committed", f"Committed {card['name']}.", card=instance_id)
    present_commit_decision(state)


def apply_skill_boost(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    if not state.active_skill_test:
        return
    if state.active_skill_test.get("token") is not None:
        return
    if player_cards.apply_boost(state, str(payload["card_code"]), str(payload["skill"])):
        log_event(events, "skill_boost", f"Spent 1 resource for +1 {payload['skill']}.", card_code=payload["card_code"])
    present_commit_decision(state)


def finish_commit(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> None:
    test = state.active_skill_test
    if not test:
        return
    state.decision_queue = [decision for decision in state.decision_queue if decision.id != "commit-cards"]
    reveal_token_for_test(state, rng, events)
    present_token_reveal_reaction(state, rng, events)
    if state.decision_queue:
        return
    resolve(state, events, rng)


def reveal_token_for_test(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> None:
    test = state.active_skill_test
    if not test:
        return
    token = draw_token(state, rng)
    modifier, autofail = token_modifier(state, token)
    extra_tokens: list[str] = []
    current = token
    while state.scenario == "the_gathering" and state.difficulty in {"hard", "expert"} and current == "cultist":
        extra = draw_token(state, rng)
        extra_modifier, extra_autofail = token_modifier(state, extra)
        modifier += extra_modifier
        autofail = autofail or extra_autofail
        extra_tokens.append(extra)
        current = extra
    test["token"] = token
    test["extra_tokens"] = extra_tokens
    test["modifier"] = modifier
    test["autofail"] = autofail
    suffix = f" then {', '.join(extra_tokens)}" if extra_tokens else ""
    log_event(events, "chaos_token", f"Revealed {token}{suffix}.", token=token, modifier=modifier, extra_tokens=extra_tokens)


def present_token_reveal_reaction(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> None:
    test = state.active_skill_test
    if not test or state.investigator.card_code != "01005":
        return
    if test.get("wendy_used") or not state.investigator.hand:
        return
    options = [
        DecisionOption(
            f"Discard {card_data.get_card(state.card_instances[card_id].card_code)['name']} to cancel and redraw",
            {"kind": "wendy_token_reaction", "choice": "redraw", "discard": card_id},
        )
        for card_id in state.investigator.hand
    ]
    options.append(DecisionOption("Pass", {"kind": "wendy_token_reaction", "choice": "pass"}))
    state.decision_queue = [
        PendingDecision(
            id="wendy-token-reaction",
            kind="token_reveal_reaction",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Use Wendy Adams reaction after revealing {test.get('token')}?",
            options=options,
        )
    ]


def resolve_wendy_token_reaction(
    state: GameState,
    payload: dict[str, Any],
    events: list[dict[str, Any]],
    rng: ArkhamRng,
) -> None:
    test = state.active_skill_test
    if not test:
        return
    state.decision_queue = [decision for decision in state.decision_queue if decision.id != "wendy-token-reaction"]
    if payload.get("choice") == "redraw" and not test.get("wendy_used"):
        discard_id = str(payload.get("discard", ""))
        if discard_id in state.investigator.hand:
            state.investigator.hand.remove(discard_id)
            state.investigator.discard.append(discard_id)
            state.card_instances[discard_id].zone = "discard"
            test["wendy_used"] = True
            log_event(events, "wendy_reaction", "Wendy canceled the chaos token and redrew.", card=discard_id)
            reveal_token_for_test(state, rng, events)
    else:
        test["wendy_passed"] = True
    resolve(state, events, rng)


def present_post_reveal_decision(state: GameState) -> None:
    test = state.active_skill_test
    if not test:
        return
    options = player_cards.boost_options(state)
    options.append(DecisionOption("Resolve test", {"kind": "post_reveal_done"}))
    state.decision_queue = [
        PendingDecision(
            id="post-reveal-boosts",
            kind="post_reveal_boosts",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Use fast abilities after revealing {test.get('token')}.",
            options=options,
        )
    ]


def resolve(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    test = state.active_skill_test
    if not test:
        return
    result = compute_result(state, test)
    if not result["success"] and legal_lucky_cards(state) and not test.get("resolving_lucky"):
        present_lucky_decision(state, result)
        return
    finalize_resolution(state, events, rng, result)


def compute_result(state: GameState, test: dict[str, Any]) -> dict[str, Any]:
    cards = card_data.cards_by_code()
    skill = str(test["skill"])
    committed = sum(icon_count(cards[state.card_instances[instance_id].card_code], skill) for instance_id in test["committed"])
    boosts = player_cards.boost_total(test)
    value = max(0, int(test["base"]) + committed + boosts + int(test["modifier"]))
    if bool(test["autofail"]):
        value = 0
    difficulty = int(test["difficulty"])
    auto_success = (
        test.get("token") == "eldersign"
        and state.investigator.card_code == "01005"
        and player_cards.controls_code(state, "01014")
    )
    success = (value >= difficulty and not bool(test["autofail"])) or auto_success
    margin = value - difficulty if success else max(0, difficulty - value)
    return {
        "source": test["source"],
        "skill": skill,
        "difficulty": difficulty,
        "base": test["base"],
        "committed_icons": committed,
        "boosts": boosts,
        "token": test["token"],
        "extra_tokens": list(test.get("extra_tokens", [])),
        "modifier": test["modifier"],
        "value": value,
        "success": success,
        "auto_success": auto_success,
        "margin": margin,
    }


def present_lucky_decision(state: GameState, result: dict[str, Any]) -> None:
    options = [
        DecisionOption(
            f"Play Lucky! ({card_data.get_card(state.card_instances[card_id].card_code)['name']})",
            {"kind": "lucky_would_fail", "choice": "play", "card": card_id},
        )
        for card_id in legal_lucky_cards(state)
    ]
    options.append(DecisionOption("Fail the test", {"kind": "lucky_would_fail", "choice": "pass"}))
    state.decision_queue = [
        PendingDecision(
            id="would-fail",
            kind="would_fail",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] {result['source']} would fail by {result['margin']}.",
            options=options,
        )
    ]


def legal_lucky_cards(state: GameState) -> list[str]:
    if state.investigator.resources < 1:
        return []
    return player_cards.hand_ids(state, "01080")


def resolve_lucky_would_fail(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    test = state.active_skill_test
    if not test:
        return
    state.decision_queue = [decision for decision in state.decision_queue if decision.id != "would-fail"]
    if payload.get("choice") == "play":
        card_id = str(payload.get("card", ""))
        if card_id in legal_lucky_cards(state):
            state.investigator.resources -= 1
            player_cards.discard_from_hand(state, card_id)
            test.setdefault("boosts", []).append({"card_code": "01080", "skill": test["skill"], "amount": 2})
            log_event(events, "event_played", "Played Lucky! for +2 skill value.", card=card_id)
            result = compute_result(state, test)
            if not result["success"] and legal_lucky_cards(state):
                present_lucky_decision(state, result)
                return
            finalize_resolution(state, events, rng, result)
            return
    result = compute_result(state, test)
    finalize_resolution(state, events, rng, result)


def finalize_resolution(
    state: GameState,
    events: list[dict[str, Any]],
    rng: ArkhamRng | None,
    result: dict[str, Any],
) -> None:
    test = state.active_skill_test
    if not test:
        return
    state.limits["last_skill_test"] = result
    success = bool(result["success"])
    margin = int(result["margin"])
    label = "failure (autofail)" if test["autofail"] and not success else ("success" if success else "failure")
    log_event(events, "skill_test_result", f"{test['source']}: {label} by {margin}.", **result)
    apply_elder_sign_success(state, events, result, rng)
    callback = test["on_success"] if success else test["on_failure"]
    committed_ids = list(test["committed"])
    for instance_id in test["committed"]:
        state.investigator.discard.append(instance_id)
        state.card_instances[instance_id].zone = "discard"
    state.active_skill_test = None
    apply_callback(state, events, callback, success=success, margin=margin, committed=committed_ids, rng=rng)
    apply_scenario_token_aftermath(state, events, result, rng)


def apply_callback(
    state: GameState,
    events: list[dict[str, Any]],
    callback: dict[str, Any],
    *,
    success: bool,
    margin: int,
    committed: list[str] | None = None,
    rng: ArkhamRng | None = None,
) -> None:
    committed = committed or []
    kind = callback.get("kind")
    if kind == "investigate":
        if success:
            clue_count = 1
            if any(state.card_instances[instance_id].card_code == "01039" for instance_id in committed):
                clue_count += 1
            discover_clue(state, clue_count, events)
            if clue_count > 1:
                log_event(events, "deduction", "Deduction discovered 1 additional clue.")
            discard_obscuring_fog_at_roland(state, events)
            if player_cards.controls_code(state, "01033"):
                state.investigator.resources += 1
                log_event(events, "milan_reaction", "Dr. Milan Christopher gained Roland 1 resource.")
    elif kind == "fight":
        enemy_id = str(callback["enemy"])
        if success and enemy_id in state.enemies:
            damage = int(callback.get("damage", 1))
            if any(state.card_instances[instance_id].card_code == "01025" for instance_id in committed):
                damage += 1
                log_event(events, "vicious_blow", "Vicious Blow added 1 damage.")
            if (
                callback.get("lita", True)
                and player_cards.lita_controlled_at_roland_location(state)
                and player_cards.monster_enemy(state, enemy_id)
            ):
                damage += 1
                log_event(events, "lita_reaction", "Lita Chantler added 1 damage against a Monster.")
            damage_enemy(state, events, enemy_id, damage)
        elif not success and enemy_id in state.enemies and has_retaliate(state, enemy_id) and not state.enemies[enemy_id].exhausted:
            attack(state, events, enemy_id, source="retaliate", rng=rng)
    elif kind == "evade":
        enemy_id = str(callback["enemy"])
        if success and enemy_id in state.enemies:
            disengage_enemy(state, events, enemy_id, exhaust=True)
    elif kind == "horror_per_fail":
        if not success and margin > 0:
            start_damage_assignment(state, events, source=str(callback.get("source", "treachery")), damage=0, horror=margin)
    elif kind == "damage_per_fail":
        if not success and margin > 0:
            start_damage_assignment(state, events, source=str(callback.get("source", "treachery")), damage=margin, horror=0)
    elif kind == "discard_threat_on_success":
        if success:
            code = str(callback.get("card_code", ""))
            for instance_id in list(state.investigator.threat_area):
                if state.card_instances[instance_id].card_code == code:
                    player_cards.discard_from_threat(state, instance_id)
                    log_event(events, "treachery_discarded", f"{card_data.get_card(code)['name']} was discarded.", card=instance_id)
                    break
    elif kind == "medical_texts":
        if success:
            heal_roland(state, events, damage=1)
        else:
            start_damage_assignment(state, events, source="Medical Texts", damage=1, horror=0)
    elif kind == "crypt_chill":
        if not success:
            assets = list(state.investigator.play_area)
            if not assets:
                start_damage_assignment(state, events, source="Crypt Chill", damage=2, horror=0)
            else:
                options = [
                    DecisionOption(
                        f"Discard {player_cards.card_name(state, instance_id)}",
                        {"kind": "discard_asset", "card": instance_id},
                    )
                    for instance_id in assets
                ]
                state.decision_queue = [
                    PendingDecision(
                        id="crypt-chill-discard",
                        kind="discard_asset",
                        prompt="Choose an asset to discard for Crypt Chill.",
                        options=options,
                    )
                ]
    elif kind == "locked_door":
        if success:
            door = str(callback.get("door"))
            discard_location_attachment(state, events, door)
    elif kind == "lita_parley":
        if success:
            lita = str(callback.get("lita"))
            location_id = encounter_cards.attachment_location(state, lita)
            if location_id and lita in state.locations[location_id].attached_instance_ids:
                state.locations[location_id].attached_instance_ids.remove(lita)
            state.card_instances[lita].zone = "play"
            state.card_instances[lita].owner = state.investigator.id
            state.investigator.play_area.append(lita)
            log_event(events, "lita_recruited", "Roland took control of Lita Chantler.", card=lita)
    for instance_id in committed:
        code = state.card_instances[instance_id].card_code
        if success and code in {"01089", "01090", "01091", "01092"}:
            draw_player_card(state, events, rng)


def apply_elder_sign_success(
    state: GameState,
    events: list[dict[str, Any]],
    result: dict[str, Any],
    rng: ArkhamRng | None,
) -> None:
    if result.get("token") != "eldersign" or not result.get("success"):
        return
    if state.investigator.card_code == "01002":
        count = player_cards.controlled_tome_count(state)
        for _ in range(count):
            draw_player_card(state, events, rng)
        if count:
            log_event(events, "elder_sign", f"Daisy drew {count} card from her elder sign.", amount=count)
    elif state.investigator.card_code == "01003":
        state.investigator.resources += 2
        log_event(events, "elder_sign", '"Skids" gained 2 resources from his elder sign.', amount=2)


def apply_scenario_token_aftermath(state: GameState, events: list[dict[str, Any]], result: dict[str, Any], rng: ArkhamRng | None = None) -> None:
    if state.scenario != "the_gathering" or state.status != "in_progress" or state.decision_queue:
        return
    from .scenarios import the_gathering

    the_gathering.apply_token_aftermath(state, events, result, rng)


def discard_obscuring_fog_at_roland(state: GameState, events: list[dict[str, Any]]) -> None:
    location = state.locations[state.investigator.location_id]
    for attachment in list(location.attached_instance_ids):
        if state.card_instances[attachment].card_code == "01168":
            discard_location_attachment(state, events, attachment)
            log_event(events, "obscuring_fog_discarded", "Obscuring Fog was discarded after a successful investigation.", card=attachment)
            return


def discard_location_attachment(state: GameState, events: list[dict[str, Any]], instance_id: str) -> None:
    for location in state.locations.values():
        if instance_id in location.attached_instance_ids:
            location.attached_instance_ids.remove(instance_id)
            break
    state.card_instances[instance_id].zone = "encounter_discard"
    if instance_id not in state.encounter_discard:
        state.encounter_discard.append(instance_id)
    log_event(events, "attachment_discarded", f"{card_data.get_card(state.card_instances[instance_id].card_code)['name']} was discarded.", card=instance_id)
