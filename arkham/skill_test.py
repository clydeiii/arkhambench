"""Skill test state machine placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import data as card_data
from .chaos import draw_token, token_modifier
from .effects import discover_clue, log_event, start_damage_assignment
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
    base = int(getattr(state.investigator, skill))
    state.active_skill_test = {
        "skill": skill,
        "difficulty": difficulty,
        "source": source,
        "base": base,
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
        icons = icon_count(card, skill)
        if icons > 0:
            options.append(
                DecisionOption(
                    f"Commit {card.get('name', instance.card_code)} (+{icons})",
                    {"kind": "commit_card", "card": instance_id},
                )
            )
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
    state.investigator.hand.remove(instance_id)
    test["committed"].append(instance_id)
    state.card_instances[instance_id].zone = "committed"
    card = card_data.get_card(state.card_instances[instance_id].card_code)
    log_event(events, "card_committed", f"Committed {card['name']}.", card=instance_id)
    present_commit_decision(state)


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
    resolve(state, events)


def resolve(state: GameState, events: list[dict[str, Any]]) -> None:
    test = state.active_skill_test
    if not test:
        return
    cards = card_data.cards_by_code()
    skill = str(test["skill"])
    committed = sum(icon_count(cards[state.card_instances[instance_id].card_code], skill) for instance_id in test["committed"])
    value = max(0, int(test["base"]) + committed + int(test["modifier"]))
    difficulty = int(test["difficulty"])
    success = value >= difficulty and not bool(test["autofail"])
    margin = value - difficulty if success else difficulty - value
    result = {
        "source": test["source"],
        "skill": skill,
        "difficulty": difficulty,
        "base": test["base"],
        "committed_icons": committed,
        "token": test["token"],
        "modifier": test["modifier"],
        "value": value,
        "success": success,
        "margin": margin,
    }
    state.limits["last_skill_test"] = result
    log_event(events, "skill_test_result", f"{test['source']}: {'success' if success else 'failure'} by {margin}.", **result)
    callback = test["on_success"] if success else test["on_failure"]
    for instance_id in test["committed"]:
        state.investigator.discard.append(instance_id)
        state.card_instances[instance_id].zone = "discard"
    state.active_skill_test = None
    apply_callback(state, events, callback, success=success, margin=margin)


def apply_callback(
    state: GameState,
    events: list[dict[str, Any]],
    callback: dict[str, Any],
    *,
    success: bool,
    margin: int,
) -> None:
    kind = callback.get("kind")
    if kind == "investigate":
        if success:
            discover_clue(state, 1, events)
    elif kind == "fight":
        enemy_id = str(callback["enemy"])
        if success and enemy_id in state.enemies:
            damage_enemy(state, events, enemy_id, int(callback.get("damage", 1)))
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
