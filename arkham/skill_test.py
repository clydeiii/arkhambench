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
            prompt=f"[Round {state.round} · {state.phase} · Roland Banks] Commit cards to {test['source']} ({skill} vs {test['difficulty']}).",
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
    if player_cards.apply_boost(state, str(payload["card_code"]), str(payload["skill"])):
        log_event(events, "skill_boost", f"Spent 1 resource for +1 {payload['skill']}.", card_code=payload["card_code"])
    if state.active_skill_test.get("token") is None:
        present_commit_decision(state)
    else:
        present_post_reveal_decision(state)


def finish_commit(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> None:
    test = state.active_skill_test
    if not test:
        return
    token = draw_token(state, rng)
    modifier, autofail = token_modifier(state, token)
    test["token"] = token
    test["modifier"] = modifier
    test["autofail"] = autofail
    log_event(events, "chaos_token", f"Revealed {token}.", token=token, modifier=modifier)
    if player_cards.boost_options(state):
        present_post_reveal_decision(state)
    else:
        resolve(state, events)


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
            prompt=f"[Round {state.round} · {state.phase} · Roland Banks] Use fast abilities after revealing {test.get('token')}.",
            options=options,
        )
    ]


def resolve(state: GameState, events: list[dict[str, Any]]) -> None:
    test = state.active_skill_test
    if not test:
        return
    cards = card_data.cards_by_code()
    skill = str(test["skill"])
    committed = sum(icon_count(cards[state.card_instances[instance_id].card_code], skill) for instance_id in test["committed"])
    boosts = player_cards.boost_total(test)
    value = max(0, int(test["base"]) + committed + boosts + int(test["modifier"]))
    difficulty = int(test["difficulty"])
    success = value >= difficulty and not bool(test["autofail"])
    margin = value - difficulty if success else difficulty - value
    result = {
        "source": test["source"],
        "skill": skill,
        "difficulty": difficulty,
        "base": test["base"],
        "committed_icons": committed,
        "boosts": boosts,
        "token": test["token"],
        "modifier": test["modifier"],
        "value": value,
        "success": success,
        "margin": margin,
    }
    state.limits["last_skill_test"] = result
    log_event(events, "skill_test_result", f"{test['source']}: {'success' if success else 'failure'} by {margin}.", **result)
    callback = test["on_success"] if success else test["on_failure"]
    committed_ids = list(test["committed"])
    for instance_id in test["committed"]:
        state.investigator.discard.append(instance_id)
        state.card_instances[instance_id].zone = "discard"
    state.active_skill_test = None
    apply_callback(state, events, callback, success=success, margin=margin, committed=committed_ids)


def apply_callback(
    state: GameState,
    events: list[dict[str, Any]],
    callback: dict[str, Any],
    *,
    success: bool,
    margin: int,
    committed: list[str] | None = None,
) -> None:
    committed = committed or []
    kind = callback.get("kind")
    if kind == "investigate":
        if success:
            discover_clue(state, 1, events)
            if any(state.card_instances[instance_id].card_code == "01039" for instance_id in committed):
                discover_clue(state, 1, events)
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
            attack(state, events, enemy_id, source="retaliate")
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
        if success and code in {"01089", "01092"}:
            draw_player_card(state, events)


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
