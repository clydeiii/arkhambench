"""Skill test state machine placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import data as card_data
from .cards import encounter_cards, player as player_cards
from .chaos import draw_token, token_modifier
from .effects import (
    add_player_card_to_hand,
    discard_asset_choice,
    discover_clue,
    draw_player_card,
    heal_roland,
    log_event,
    start_damage_assignment,
)
from .enemies import damage_enemy, disengage_enemy, has_retaliate, attack
from .model import DEVOURER_FAMILY, GATHERING_FAMILY, MIDNIGHT_MASKS_FAMILY, DecisionOption, GameState, PendingDecision
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
    base_boost: int = 0,
) -> None:
    # base_boost carries ability modifiers (Machete's +1, Baseball Bat's +2...)
    # so the started-test log shows the true value, not the pre-boost base.
    base = player_cards.effective_base_skill(state, skill, source) + base_boost
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
        "base_boost": base_boost,
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
    present_pre_reveal_reaction(state)
    if state.decision_queue:
        return
    reveal_token_for_test(state, rng, events)
    present_token_reveal_reaction(state, rng, events)
    if state.decision_queue:
        return
    resolve(state, events, rng)


def reveal_token_for_test(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> None:
    test = state.active_skill_test
    if not test:
        return
    if state.limits.get(f"will_to_survive:{state.round}"):
        test["token"] = None
        test["extra_tokens"] = []
        test["modifier"] = 0
        test["autofail"] = False
        test["revealless"] = True
        log_event(events, "chaos_token_skipped", "Will to Survive prevented revealing a chaos token.", modifier=0)
        return
    token = draw_token(state, rng)
    modifier, autofail = adjusted_token_modifier(state, token)
    extra_tokens: list[str] = []
    current = token
    while (
        state.scenario in GATHERING_FAMILY
        and state.difficulty in {"hard", "expert"}
        and current == "cultist"
    ) or (
        state.scenario in MIDNIGHT_MASKS_FAMILY
        and state.difficulty in {"hard", "expert"}
        and current == "cultist"
        and not midnight_cultists_in_play(state)
    ) or (
        state.scenario in DEVOURER_FAMILY
        and current == "elderthing"
        and devourer_ancient_one_in_play(state)
    ) or devourer_location_extra_token(state, test, extra_tokens):
        extra = draw_token(state, rng)
        extra_modifier, extra_autofail = adjusted_token_modifier(state, extra)
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


def adjusted_token_modifier(state: GameState, token: str) -> tuple[int, bool]:
    modifier, autofail = token_modifier(state, token)
    test = state.active_skill_test or {}
    if autofail or modifier >= 0:
        return modifier, autofail
    if test.get("on_success", {}).get("kind") != "evade" and test.get("on_failure", {}).get("kind") != "evade":
        return modifier, autofail
    enemy_id = str(test.get("on_success", {}).get("enemy") or test.get("on_failure", {}).get("enemy") or "")
    if enemy_id in state.enemies and state.enemies[enemy_id].card_code == "01172":
        return modifier * 2, autofail
    return modifier, autofail


def present_pre_reveal_reaction(state: GameState) -> None:
    test = state.active_skill_test
    if not test:
        return
    statues = [
        card_id
        for card_id in player_cards.play_area_ids(state, "01071")
        if state.card_instances[card_id].uses.get("charges", 0) > 0
    ]
    if not statues:
        return
    state.decision_queue = [
        PendingDecision(
            id="grotesque-reaction",
            kind="token_reveal_reaction",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Use Grotesque Statue before revealing a chaos token?",
            options=[
                DecisionOption("Spend 1 charge on Grotesque Statue", {"kind": "grotesque_reaction", "choice": "use", "card": statues[0]}),
                DecisionOption("Pass", {"kind": "grotesque_reaction", "choice": "pass"}),
            ],
        )
    ]


def resolve_grotesque_reaction(
    state: GameState,
    payload: dict[str, Any],
    events: list[dict[str, Any]],
    rng: ArkhamRng,
) -> None:
    state.decision_queue = [decision for decision in state.decision_queue if decision.id != "grotesque-reaction"]
    if payload.get("choice") != "use":
        reveal_token_for_test(state, rng, events)
        present_token_reveal_reaction(state, rng, events)
        if not state.decision_queue:
            resolve(state, events, rng)
        return
    card_id = str(payload.get("card", ""))
    if card_id not in state.investigator.play_area or state.card_instances[card_id].uses.get("charges", 0) <= 0:
        reveal_token_for_test(state, rng, events)
        present_token_reveal_reaction(state, rng, events)
        if not state.decision_queue:
            resolve(state, events, rng)
        return
    state.card_instances[card_id].uses["charges"] -= 1
    tokens = [draw_token(state, rng), draw_token(state, rng)]
    state.limits["grotesque_tokens"] = tokens
    options = []
    for token in tokens:
        modifier, autofail = adjusted_token_modifier(state, token)
        options.append(DecisionOption(f"Resolve {token} ({modifier})", {"kind": "grotesque_choice", "token": token, "modifier": modifier, "autofail": autofail}))
    state.decision_queue = [
        PendingDecision(
            id="grotesque-choice",
            kind="token_reveal_reaction",
            prompt="Grotesque Statue revealed 2 chaos tokens. Choose 1 to resolve.",
            options=options,
        )
    ]
    log_event(events, "grotesque_statue", f"Grotesque Statue revealed {tokens[0]} and {tokens[1]}.", card=card_id, tokens=tokens)


def resolve_grotesque_choice(
    state: GameState,
    payload: dict[str, Any],
    events: list[dict[str, Any]],
    rng: ArkhamRng,
) -> None:
    test = state.active_skill_test
    if not test:
        return
    state.decision_queue = [decision for decision in state.decision_queue if decision.id != "grotesque-choice"]
    token = str(payload.get("token"))
    tokens = [str(item) for item in state.limits.pop("grotesque_tokens", [])]
    if token not in tokens:
        token = tokens[0] if tokens else token
    modifier, autofail = adjusted_token_modifier(state, token)
    test["token"] = token
    test["extra_tokens"] = []
    test["modifier"] = modifier
    test["autofail"] = autofail
    ignored = [item for item in tokens if item != token]
    log_event(events, "chaos_token", f"Resolved {token}; ignored {', '.join(ignored) or 'nothing'}.", token=token, modifier=modifier, ignored=ignored)
    present_token_reveal_reaction(state, rng, events)
    if not state.decision_queue:
        resolve(state, events, rng)


def present_token_reveal_reaction(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> None:
    test = state.active_skill_test
    if not test:
        return
    options: list[DecisionOption] = []
    if state.investigator.card_code == "01005" and not player_cards.investigator_text_blank(state) and not test.get("wendy_used") and state.investigator.hand:
        options.extend(
            DecisionOption(
                f"Discard {card_data.get_card(state.card_instances[card_id].card_code)['name']} to cancel and redraw",
                {"kind": "wendy_token_reaction", "choice": "redraw", "discard": card_id},
            )
            for card_id in state.investigator.hand
            if not player_cards.is_weakness(state, card_id)
        )
    if int(test.get("modifier", 0)) < 0 and state.investigator.resources >= 2:
        for card_id in player_cards.hand_ids(state, "01056"):
            options.append(DecisionOption("Play Sure Gamble", {"kind": "sure_gamble_reaction", "choice": "play", "card": card_id}))
    if not options:
        return
    options.append(DecisionOption("Pass", {"kind": "wendy_token_reaction", "choice": "pass"}))
    state.decision_queue = [
        PendingDecision(
            id="wendy-token-reaction",
            kind="token_reveal_reaction",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Use a reaction after revealing {test.get('token')}?",
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
    state.decision_queue = [decision for decision in state.decision_queue if decision.id not in {"wendy-token-reaction", "token-reveal-reaction"}]
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


def resolve_sure_gamble_reaction(
    state: GameState,
    payload: dict[str, Any],
    events: list[dict[str, Any]],
    rng: ArkhamRng,
) -> None:
    test = state.active_skill_test
    if not test:
        return
    state.decision_queue = [decision for decision in state.decision_queue if decision.id not in {"wendy-token-reaction", "token-reveal-reaction"}]
    card_id = str(payload.get("card", ""))
    if payload.get("choice") == "play" and card_id in state.investigator.hand and state.investigator.resources >= 2 and int(test.get("modifier", 0)) < 0:
        state.investigator.resources -= 2
        player_cards.discard_from_hand(state, card_id)
        before = int(test.get("modifier", 0))
        test["modifier"] = abs(before)
        log_event(events, "sure_gamble", f"Sure Gamble switched the modifier from {before} to {test['modifier']}.", card=card_id)
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
    apply_scenario_token_reveal_effects(state, events, rng)
    if state.status != "in_progress":
        state.active_skill_test = None
        return
    if state.pending_damage or state.decision_queue:
        state.limits["deferred_skill_test_resolution"] = True
        return
    result = compute_result(state, test)
    if not result["success"] and legal_lucky_cards(state) and not test.get("resolving_lucky"):
        present_lucky_decision(state, result)
        return
    finalize_resolution(state, events, rng, result)


def resume_deferred_resolution(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    if state.pending_damage or state.decision_queue or not state.active_skill_test:
        return
    state.limits.pop("deferred_skill_test_resolution", None)
    resolve(state, events, rng)


def compute_result(state: GameState, test: dict[str, Any]) -> dict[str, Any]:
    cards = card_data.cards_by_code()
    skill = str(test["skill"])
    committed = sum(icon_count(cards[state.card_instances[instance_id].card_code], skill) for instance_id in test["committed"])
    boosts = player_cards.boost_total(test)
    base = player_cards.effective_base_skill(state, skill, str(test["source"])) + int(test.get("base_boost", 0))
    test["base"] = base
    value = max(0, base + committed + boosts + int(test["modifier"]))
    if bool(test["autofail"]):
        value = 0
    difficulty = int(test["difficulty"])
    auto_success = (
        test.get("token") == "eldersign"
        and state.investigator.card_code == "01005"
        and not player_cards.investigator_text_blank(state)
        and player_cards.controls_code(state, "01014")
    )
    success = (value >= difficulty and not bool(test["autofail"])) or auto_success
    margin = value - difficulty if success else max(0, difficulty - value)
    return {
        "source": test["source"],
        "skill": skill,
        "difficulty": difficulty,
        "base": base,
        "committed_icons": committed,
        "boosts": boosts,
        "token": test["token"],
        "extra_tokens": list(test.get("extra_tokens", [])),
        "modifier": test["modifier"],
        "value": value,
        "success": success,
        "auto_success": auto_success,
        "margin": margin,
        "reveal_effects_applied": bool(test.get("scenario_reveal_effects_applied")),
    }


def skill_test_result_message(test: dict[str, Any], result: dict[str, Any], label: str, margin: int) -> str:
    difficulty = int(result["difficulty"])
    if bool(test.get("autofail")):
        return f"{result['source']}: {label} by {margin} - autofail (skill value 0) vs {difficulty}."
    skill = str(result["skill"])
    base = int(result["base"])
    committed = int(result["committed_icons"])
    boosts = int(result["boosts"])
    modifier = int(result["modifier"])
    value = int(result["value"])
    token_part = f"+ token {modifier}"
    return (
        f"{result['source']}: {label} by {margin} - "
        f"{skill} {base} + committed {committed} + boosts {boosts} {token_part} = {value} vs {difficulty}."
    )


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
    ids = player_cards.hand_ids(state, "01080") + player_cards.hand_ids(state, "01084")
    top = player_cards.topmost_discard_event_id(state)
    if top is not None and player_cards.can_play_from_discard_with_amulet(state, top) and state.card_instances[top].card_code in {"01080", "01084"}:
        ids.append(top)
    return ids


def resolve_lucky_would_fail(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    test = state.active_skill_test
    if not test:
        return
    state.decision_queue = [decision for decision in state.decision_queue if decision.id != "would-fail"]
    if payload.get("choice") == "play":
        card_id = str(payload.get("card", ""))
        if card_id in legal_lucky_cards(state):
            state.investigator.resources -= 1
            if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
                state.investigator.resources += 1
                return
            code = state.card_instances[card_id].card_code
            test.setdefault("boosts", []).append({"card_code": code, "skill": test["skill"], "amount": 2})
            player_cards.place_played_event(state, card_id, events)
            log_event(events, "event_played", "Played Lucky! for +2 skill value.", card=card_id)
            if code == "01084":
                draw_player_card(state, events, rng)
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
    log_event(events, "skill_test_result", skill_test_result_message(test, result, label, margin), **result)
    apply_blinding_light_symbol_loss(state, events, test, result)
    apply_elder_sign_success(state, events, result, rng)
    callback = test["on_success"] if success else test["on_failure"]
    result["callback_kind"] = callback.get("kind")
    committed_ids = list(test["committed"])
    played_event = str(test.get("played_event", ""))
    for instance_id in test["committed"]:
        code = state.card_instances[instance_id].card_code
        if success and code == "01053" and margin >= 3:
            add_player_card_to_hand(
                state,
                events,
                instance_id,
                event_type="opportunist_returned",
                message="Opportunist returned to hand.",
            )
        else:
            state.investigator.discard.append(instance_id)
            state.card_instances[instance_id].zone = "discard"
    state.active_skill_test = None
    apply_callback(state, events, callback, success=success, margin=margin, committed=committed_ids, rng=rng)
    if state.scenario in DEVOURER_FAMILY:
        from .scenarios import the_devourer_below

        the_devourer_below.after_skill_test(state, events, test, result, rng)
    apply_post_attack_symbol_effects(state, events, test, result)
    apply_scenario_token_aftermath(state, events, result, rng)
    if played_event:
        player_cards.place_played_event(state, played_event, events)
    present_skill_test_aftermath_reactions(state, result, committed_ids)


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
            discovered = discover_clue(state, clue_count, events)
            if clue_count > 1 and discovered > 1:
                log_event(events, "deduction", f"Deduction discovered {discovered - 1} additional clue.")
            discard_obscuring_fog_at_roland(state, events)
            if player_cards.controls_code(state, "01033"):
                state.investigator.resources += 1
                log_event(events, "milan_reaction", f"Dr. Milan Christopher gained {state.investigator.name} 1 resource.")
    elif kind == "fight":
        enemy_id = str(callback["enemy"])
        if success and enemy_id in state.enemies:
            damage = int(callback.get("damage", 1))
            if callback.get("shotgun"):
                damage = min(5, max(1, margin))
            if callback.get("succeed_by") is not None and margin >= int(callback.get("succeed_by", 0)):
                bonus = int(callback.get("bonus_damage", 0))
                damage += bonus
                if bonus:
                    log_event(events, "succeed_by_bonus", f"Succeed-by bonus added {bonus} damage.")
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
            from .enemies import evade_enemy

            evade_enemy(state, events, enemy_id)
            from . import actions

            actions.queue_pickpocketing_reaction(state, enemy_id)
            actions.queue_close_call_reaction(state, enemy_id)
    elif kind == "blinding_light":
        enemy_id = str(callback["enemy"])
        if success and enemy_id in state.enemies:
            from .enemies import evade_enemy

            evade_enemy(state, events, enemy_id)
            from . import actions

            actions.queue_pickpocketing_reaction(state, enemy_id)
            actions.queue_close_call_reaction(state, enemy_id)
            if enemy_id in state.enemies:
                damage_enemy(state, events, enemy_id, int(callback.get("damage", 1)))
    elif kind == "burglary":
        if success:
            state.investigator.resources += 3
            log_event(events, "burglary", "Burglary gained 3 resources instead of discovering clues.", amount=3)
            discard_obscuring_fog_at_roland(state, events)
    elif kind == "horror_per_fail":
        if not success and margin > 0:
            start_damage_assignment(state, events, source=str(callback.get("source", "treachery")), damage=0, horror=margin)
    elif kind == "damage_per_fail":
        if not success and margin > 0:
            start_damage_assignment(state, events, source=str(callback.get("source", "treachery")), damage=margin, horror=0)
    elif kind == "discard_random_per_fail":
        if not success and margin > 0 and rng is not None:
            source = str(callback.get("source", "treachery"))
            for _ in range(margin):
                if not state.investigator.hand:
                    break
                card_id = rng.choice(state.investigator.hand)
                player_cards.discard_from_hand(state, card_id)
                log_event(events, "card_discarded", f"{source} forced a random discard of {player_cards.card_name(state, card_id)}.", card=card_id)
    elif kind == "zealots_seal_discard":
        if not success and rng is not None:
            for _ in range(2):
                if not state.investigator.hand:
                    break
                card_id = rng.choice(state.investigator.hand)
                player_cards.discard_from_hand(state, card_id)
                log_event(events, "card_discarded", f"The Zealot's Seal forced a random discard of {player_cards.card_name(state, card_id)}.", card=card_id)
    elif kind == "chill_from_below":
        if not success and margin > 0 and rng is not None:
            discarded = 0
            for _ in range(margin):
                if not state.investigator.hand:
                    break
                card_id = rng.choice(state.investigator.hand)
                player_cards.discard_from_hand(state, card_id)
                log_event(events, "card_discarded", f"Chill from Below forced a random discard of {player_cards.card_name(state, card_id)}.", card=card_id)
                discarded += 1
            shortfall = margin - discarded
            if shortfall > 0:
                start_damage_assignment(state, events, source="Chill from Below", damage=shortfall, horror=0)
    elif kind == "ghoul_pits_rats":
        if not success and margin > 0 and rng is not None:
            from .scenarios import the_gathering

            the_gathering.ghoul_pits_draw_rats(state, events, rng, margin)
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
    elif kind == "false_lead":
        if not success and margin > 0:
            from .scenarios import the_midnight_masks

            the_midnight_masks.false_lead_aftermath(state, events, margin)
    elif kind == "on_wings":
        if state.scenario in MIDNIGHT_MASKS_FAMILY:
            from .scenarios import the_midnight_masks

            the_midnight_masks.on_wings_aftermath(state, events, failed=not success)
    elif kind == "jeremiah_doom":
        if not success:
            from .scenarios import the_midnight_masks

            the_midnight_masks.jeremiah_doom(state, events, margin, rng)
    elif kind == "graveyard":
        if not success:
            from .scenarios import the_midnight_masks

            the_midnight_masks.graveyard_failure(state)
    elif kind == "devourer_unhallowed":
        if not success:
            start_damage_assignment(state, events, source="Unhallowed Ground", damage=1, horror=1)
    elif kind == "devourer_twisting":
        from .scenarios import the_devourer_below

        the_devourer_below.finish_twisting_paths_move(state, events, success=success, rng=rng)
    elif kind == "devourer_disrupt":
        if success:
            from .scenarios import the_devourer_below

            the_devourer_below.place_clue_on_act(state, events)
    elif kind == "devourer_agenda2":
        if not success:
            from .scenarios import the_devourer_below

            the_devourer_below.gain_madness_weakness(state, events, rng, to_hand=True)
        from .scenarios import the_devourer_below

        the_devourer_below.advance_to_agenda3(state, events)
    elif kind == "umordhoths_wrath":
        if not success and margin > 0:
            from .scenarios import the_devourer_below

            the_devourer_below.present_wrath_choices(state, margin)
    elif kind == "lita_parley":
        if success:
            lita = str(callback.get("lita"))
            location_id = encounter_cards.attachment_location(state, lita)
            if location_id and lita in state.locations[location_id].attached_instance_ids:
                state.locations[location_id].attached_instance_ids.remove(lita)
            state.card_instances[lita].zone = "play"
            state.card_instances[lita].owner = state.investigator.id
            state.investigator.play_area.append(lita)
            log_event(events, "lita_recruited", f"{state.investigator.name} took control of Lita Chantler.", card=lita)
    for instance_id in committed:
        code = state.card_instances[instance_id].card_code
        if success and code in {"01089", "01090", "01091", "01092"}:
            draw_player_card(state, events, rng)
        if success and code == "01067":
            heal_roland(state, events, horror=1)
    if success and any(state.card_instances[instance_id].card_code == "01081" for instance_id in committed) and kind in {"evade", "blinding_light"}:
        present_survival_instinct_decision(state)


def present_skill_test_aftermath_reactions(state: GameState, result: dict[str, Any], committed: list[str]) -> None:
    state.limits["last_skill_test"] = result
    if result.get("success"):
        if result.get("callback_kind") == "investigate" and int(result.get("margin", 0)) >= 2:
            present_scavenging_decision(state)
        return
    options: list[DecisionOption] = []
    rabbit = next(
        (
            card_id
            for card_id in player_cards.play_area_ids(state, "01075")
            if not state.card_instances[card_id].exhausted
        ),
        None,
    )
    if rabbit:
        options.append(DecisionOption("Exhaust Rabbit's Foot to draw 1 card", {"kind": "after_fail_reaction", "reaction": "rabbit", "card": rabbit}))
    rabbit3 = next(
        (
            card_id
            for card_id in player_cards.play_area_ids(state, "50010")
            if not state.card_instances[card_id].exhausted and state.investigator.deck
        ),
        None,
    )
    if rabbit3:
        options.append(DecisionOption("Exhaust Rabbit's Foot(3) to search failed-by cards", {"kind": "after_fail_reaction", "reaction": "rabbit3", "card": rabbit3, "count": int(result.get("margin", 1))}))
    if (
        result.get("callback_kind") == "investigate"
        and int(result.get("margin", 0)) <= 2
        and state.investigator.resources >= 2
        and state.locations[state.investigator.location_id].clues > 0
    ):
        for card_id in legal_look_what_i_found_cards(state):
            suffix = " from discard" if card_id not in state.investigator.hand else ""
            options.append(DecisionOption(f'Play "Look what I found!"{suffix}', {"kind": "after_fail_reaction", "reaction": "look", "card": card_id}))
    if not options:
        return
    options.append(DecisionOption("Done", {"kind": "after_fail_reaction", "reaction": "done"}))
    state.decision_queue.append(
        PendingDecision(
            id="after-fail-reactions",
            kind="after_fail_reaction",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Choose reactions after failing {result.get('source', 'the test')}.",
            options=options,
        )
    )


def legal_look_what_i_found_cards(state: GameState) -> list[str]:
    ids = player_cards.hand_ids(state, "01079")
    top = player_cards.topmost_discard_event_id(state)
    if top is not None and player_cards.can_play_from_discard_with_amulet(state, top) and state.card_instances[top].card_code == "01079":
        ids.append(top)
    return ids


def resolve_after_fail_reaction(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    reaction = str(payload.get("reaction", ""))
    if reaction == "rabbit":
        card_id = str(payload.get("card", ""))
        if card_id in state.investigator.play_area and not state.card_instances[card_id].exhausted:
            state.card_instances[card_id].exhausted = True
            draw_player_card(state, events, rng)
            log_event(events, "rabbits_foot", "Rabbit's Foot drew 1 card.", card=card_id)
    elif reaction == "rabbit3":
        card_id = str(payload.get("card", ""))
        if card_id in state.investigator.play_area and not state.card_instances[card_id].exhausted:
            state.card_instances[card_id].exhausted = True
            count = max(1, int(payload.get("count", 1)))
            candidates = list(state.investigator.deck[:count])
            if candidates:
                state.decision_queue.append(
                    PendingDecision(
                        id="rabbits-foot-3-choice",
                        kind="rabbits_foot_3",
                        prompt="Choose a card to draw with Rabbit's Foot.",
                        options=[
                            DecisionOption(
                                f"Draw {player_cards.card_name(state, cid)}",
                                {"kind": "rabbits_foot_3", "card": cid, "candidates": candidates},
                            )
                            for cid in candidates
                        ],
                    )
                )
            log_event(events, "rabbits_foot", f"Rabbit's Foot searched the top {len(candidates)} cards.", card=card_id)
    elif reaction == "look":
        card_id = str(payload.get("card", ""))
        if card_id in legal_look_what_i_found_cards(state) and state.investigator.resources >= 2:
            state.investigator.resources -= 2
            if not player_cards.remove_from_hand_or_discard_for_play(state, card_id):
                state.investigator.resources += 2
                return
            discover_clue(state, 2, events)
            player_cards.place_played_event(state, card_id, events)
            log_event(events, "event_played", 'Played "Look what I found!".', card=card_id)
    if reaction in {"rabbit", "rabbit3", "look"} and state.status == "in_progress":
        result = dict(state.limits.get("last_skill_test", {}))
        if result:
            present_skill_test_aftermath_reactions(state, result, [])


def resolve_rabbits_foot_3(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng | None) -> None:
    chosen = str(payload.get("card", ""))
    candidates = [str(card_id) for card_id in payload.get("candidates", [])]
    candidates = [card_id for card_id in candidates if card_id in state.investigator.deck]
    if chosen not in candidates:
        return
    for card_id in candidates:
        state.investigator.deck.remove(card_id)
    rest = [card_id for card_id in candidates if card_id != chosen]
    state.investigator.deck.extend(rest)
    if rng is not None:
        rng.shuffle(state.investigator.deck)
    add_player_card_to_hand(state, events, chosen, event_type="card_drawn", message=f"{state.investigator.name} drew {player_cards.card_name(state, chosen)}.")


def present_scavenging_decision(state: GameState) -> None:
    scavenging = next(
        (
            card_id
            for card_id in player_cards.play_area_ids(state, "01073")
            if not state.card_instances[card_id].exhausted
        ),
        None,
    )
    if not scavenging:
        return
    item_ids = [
        card_id
        for card_id in state.investigator.discard
        if "Item" in str(card_data.get_card(state.card_instances[card_id].card_code).get("traits", ""))
    ]
    if not item_ids:
        return
    options = [
        DecisionOption(
            f"Return {player_cards.card_name(state, card_id)} to hand",
            {"kind": "scavenging_reaction", "choice": "take", "card": card_id, "asset": scavenging},
        )
        for card_id in item_ids
    ]
    options.append(DecisionOption("Pass", {"kind": "scavenging_reaction", "choice": "pass", "asset": scavenging}))
    state.decision_queue.append(
        PendingDecision(
            id="scavenging-reaction",
            kind="scavenging_reaction",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Use Scavenging?",
            options=options,
        )
    )


def resolve_scavenging_reaction(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    asset = str(payload.get("asset", ""))
    if payload.get("choice") != "take" or asset not in state.investigator.play_area:
        return
    card_id = str(payload.get("card", ""))
    if card_id not in state.investigator.discard:
        return
    if "Item" not in str(card_data.get_card(state.card_instances[card_id].card_code).get("traits", "")):
        return
    state.card_instances[asset].exhausted = True
    state.investigator.discard.remove(card_id)
    add_player_card_to_hand(
        state,
        events,
        card_id,
        event_type="scavenging",
        message=f"Scavenging returned {player_cards.card_name(state, card_id)} to hand.",
    )


def present_survival_instinct_decision(state: GameState) -> None:
    others = [enemy_id for enemy_id in state.investigator.engaged_enemies if enemy_id in state.enemies]
    destinations = list(state.locations[state.investigator.location_id].connections)
    if not others and not destinations:
        return
    options: list[DecisionOption] = []
    if others:
        options.append(DecisionOption("Disengage each other engaged enemy", {"kind": "survival_instinct", "disengage": True, "location": ""}))
    for location_id in destinations:
        options.append(DecisionOption(f"Move to {state.locations[location_id].name}", {"kind": "survival_instinct", "disengage": False, "location": location_id}))
        if others:
            options.append(DecisionOption(f"Disengage other enemies and move to {state.locations[location_id].name}", {"kind": "survival_instinct", "disengage": True, "location": location_id}))
    options.append(DecisionOption("Do neither", {"kind": "survival_instinct", "disengage": False, "location": ""}))
    state.decision_queue.append(
        PendingDecision(
            id="survival-instinct",
            kind="survival_instinct",
            prompt="Resolve Survival Instinct.",
            options=options,
        )
    )


def resolve_survival_instinct(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    if payload.get("disengage"):
        for enemy_id in list(state.investigator.engaged_enemies):
            if enemy_id in state.enemies:
                disengage_enemy(state, events, enemy_id, exhaust=False)
    location_id = str(payload.get("location", ""))
    if location_id:
        from . import actions

        actions.move(state, location_id, events)


def apply_blinding_light_symbol_loss(
    state: GameState,
    events: list[dict[str, Any]],
    test: dict[str, Any],
    result: dict[str, Any],
) -> None:
    if not test.get("blinding_light"):
        return
    tokens = [str(result.get("token"))] + [str(token) for token in result.get("extra_tokens", [])]
    if not any(token in {"skull", "cultist", "tablet", "elderthing", "elder_thing", "autofail"} for token in tokens):
        return
    before = state.investigator.actions_remaining
    state.investigator.actions_remaining = max(0, before - 1)
    log_event(events, "action_lost", "Blinding Light caused Daisy to lose 1 action.", before=before, after=state.investigator.actions_remaining)


def revealed_symbol(result: dict[str, Any], symbols: set[str]) -> bool:
    tokens = [str(result.get("token"))] + [str(token) for token in result.get("extra_tokens", [])]
    normalized = {"elderthing" if token == "elder_thing" else token for token in tokens}
    wanted = {"elderthing" if token == "elder_thing" else token for token in symbols}
    return any(token in wanted for token in normalized)


def apply_post_attack_symbol_effects(
    state: GameState,
    events: list[dict[str, Any]],
    test: dict[str, Any],
    result: dict[str, Any],
) -> None:
    if test.get("symbol_horror") and revealed_symbol(result, {"skull", "cultist", "tablet", "elderthing", "elder_thing", "autofail"}):
        start_damage_assignment(state, events, source="Shrivelling", damage=0, horror=1)
    bat = dict(test.get("bat_discard_symbols", {}))
    if bat and revealed_symbol(result, {"skull", "autofail"}):
        asset_id = str(bat.get("asset", ""))
        if asset_id in state.investigator.play_area:
            player_cards.discard_from_play(state, asset_id)
            log_event(events, "asset_discarded", "Baseball Bat was discarded after the attack.", card=asset_id)


def apply_elder_sign_success(
    state: GameState,
    events: list[dict[str, Any]],
    result: dict[str, Any],
    rng: ArkhamRng | None,
) -> None:
    if result.get("token") != "eldersign" or not result.get("success"):
        return
    if player_cards.investigator_text_blank(state):
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
    if state.status != "in_progress":
        return
    if state.decision_queue or state.pending_damage:
        queue_scenario_token_aftermath(state, result)
        return
    if state.scenario in GATHERING_FAMILY:
        from .scenarios import the_gathering

        the_gathering.apply_token_aftermath(state, events, result, rng)
    elif state.scenario in MIDNIGHT_MASKS_FAMILY:
        from .scenarios import the_midnight_masks

        the_midnight_masks.apply_token_aftermath(state, events, result, rng)
    elif state.scenario in DEVOURER_FAMILY:
        from .scenarios import the_devourer_below

        the_devourer_below.apply_token_aftermath(state, events, result, rng)


def queue_scenario_token_aftermath(state: GameState, result: dict[str, Any]) -> None:
    pending = list(state.limits.get("pending_scenario_token_aftermath", []))
    pending.append(dict(result))
    state.limits["pending_scenario_token_aftermath"] = pending


def process_deferred_scenario_token_aftermath(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    if state.status != "in_progress" or state.decision_queue or state.pending_damage or state.active_skill_test:
        return
    pending = list(state.limits.pop("pending_scenario_token_aftermath", []))
    while pending and state.status == "in_progress" and not state.decision_queue and not state.pending_damage and not state.active_skill_test:
        result = dict(pending.pop(0))
        apply_scenario_token_aftermath(state, events, result, rng)
    if pending:
        state.limits["pending_scenario_token_aftermath"] = pending


def apply_scenario_token_reveal_effects(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    test = state.active_skill_test
    if not test or test.get("scenario_reveal_effects_applied"):
        return
    test["scenario_reveal_effects_applied"] = True
    if state.scenario in GATHERING_FAMILY:
        from .scenarios import the_gathering

        the_gathering.apply_token_reveal_effects(state, events, test, rng)
    elif state.scenario in MIDNIGHT_MASKS_FAMILY:
        from .scenarios import the_midnight_masks

        the_midnight_masks.apply_token_reveal_effects(state, events, test, rng)
    elif state.scenario in DEVOURER_FAMILY:
        from .scenarios import the_devourer_below

        the_devourer_below.apply_token_reveal_effects(state, events, test, rng)


def midnight_cultists_in_play(state: GameState) -> bool:
    if state.scenario not in MIDNIGHT_MASKS_FAMILY:
        return False
    from .scenarios import the_midnight_masks

    return bool(the_midnight_masks.cultist_enemy_ids(state))


def devourer_ancient_one_in_play(state: GameState) -> bool:
    if state.scenario not in DEVOURER_FAMILY:
        return False
    return any("Ancient One" in str(card_data.get_card(enemy.card_code).get("traits", "")) for enemy in state.enemies.values())


def devourer_location_extra_token(state: GameState, test: dict[str, Any], extra_tokens: list[str]) -> bool:
    if state.scenario not in DEVOURER_FAMILY or extra_tokens:
        return False
    from .scenarios import the_devourer_below

    return the_devourer_below.location_extra_token_applies(state, test)


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
    player_cards.discard_to_owner_pile(state, instance_id)
    log_event(events, "attachment_discarded", f"{card_data.get_card(state.card_instances[instance_id].card_code)['name']} was discarded.", card=instance_id)
