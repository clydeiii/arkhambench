"""Phase structure placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import actions, encounter
from .cards import player as player_cards
from .effects import draw_player_card, gain_resource, log_event
from .enemies import attack, engage_ready_enemies_at_roland, move_hunters
from .model import DecisionOption, GameState, PendingDecision
from .rng import ArkhamRng


def advance_until_decision(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> None:
    guard = 0
    while state.status == "in_progress" and not state.decision_queue:
        guard += 1
        if guard > 100:
            raise RuntimeError("phase loop did not reach a decision")
        if state.active_skill_test or state.pending_damage:
            return
        if state.phase == "Investigation":
            if state.investigator.actions_remaining > 0:
                actions.present_action_decision(state)
            else:
                if start_frozen_end_turn_test(state, events):
                    return
                state.phase = "Enemy"
                log_event(events, "phase_started", "Enemy phase began.")
        elif state.phase == "Enemy":
            run_enemy_phase(state, events)
            if not state.decision_queue and state.status == "in_progress":
                if state.scenario == "the_gathering":
                    from .scenarios import the_gathering

                    the_gathering.end_enemy_phase(state, events)
                if state.decision_queue or state.status != "in_progress":
                    return
                state.phase = "Upkeep"
                log_event(events, "phase_started", "Upkeep phase began.")
        elif state.phase == "Upkeep":
            run_upkeep_phase(state, events)
            if not state.decision_queue and state.status == "in_progress":
                if state.scenario == "the_gathering":
                    from .scenarios import the_gathering

                    the_gathering.end_round(state, events)
                if state.decision_queue or state.status != "in_progress":
                    return
                state.round += 1
                state.phase = "Mythos"
                state.limits = {
                    key: value
                    for key, value in state.limits.items()
                    if not str(key).startswith("frozen:")
                    and not str(key).startswith("enemy_phase_attacked:")
                    and not str(key).startswith("mind_over_matter:")
                    and not str(key).startswith("frozen_end_turn:")
                    and not str(key).startswith("mythos_")
                }
                log_event(events, "round_started", f"Round {state.round} began.")
        elif state.phase == "Mythos":
            run_mythos_phase(state, rng, events)
            if not state.decision_queue and state.status == "in_progress":
                state.phase = "Investigation"
                state.investigator.actions_remaining = 3
                state.turn.action_index = 0
                log_event(events, "phase_started", "Investigation phase began.")
        else:
            state.phase = "Investigation"


def run_enemy_phase(state: GameState, events: list[dict[str, Any]]) -> None:
    move_hunters(state, events)
    attacked_key = f"enemy_phase_attacked:{state.round}"
    attacked = set(state.limits.get(attacked_key, []))
    for enemy_id in list(state.investigator.engaged_enemies):
        if enemy_id in attacked:
            continue
        enemy = state.enemies.get(enemy_id)
        if enemy and not enemy.exhausted:
            attack(state, events, enemy_id, source="enemy phase")
            attacked.add(enemy_id)
            state.limits[attacked_key] = sorted(attacked)
            if state.decision_queue:
                return


def run_upkeep_phase(state: GameState, events: list[dict[str, Any]]) -> None:
    state.investigator.exhausted = False
    for instance in state.card_instances.values():
        instance.exhausted = False
    for enemy in state.enemies.values():
        enemy.exhausted = False
    log_event(events, "ready_step", "All exhausted cards readied.")
    draw_player_card(state, events)
    gain_resource(state, 1, events)
    discard_dissonant_voices(state, events)
    if len(state.investigator.hand) > 8:
        present_discard_to_size(state)


def present_discard_to_size(state: GameState) -> None:
    cards = __import__("arkham.data", fromlist=["cards_by_code"]).cards_by_code()
    options = []
    for instance_id in state.investigator.hand:
        card = cards.get(state.card_instances[instance_id].card_code, {})
        options.append(DecisionOption(f"Discard {card.get('name', instance_id)}", {"kind": "discard_to_size", "card": instance_id}))
    state.decision_queue = [
        PendingDecision(
            id="discard-to-size",
            kind="choose_option",
            prompt=f"[Round {state.round} · Upkeep · Roland Banks] Discard to hand size 8.",
            options=options,
        )
    ]


def discard_to_size(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    instance_id = str(payload["card"])
    if instance_id in state.investigator.hand:
        state.investigator.hand.remove(instance_id)
        state.investigator.discard.append(instance_id)
        state.card_instances[instance_id].zone = "discard"
        log_event(events, "card_discarded", f"Discarded {instance_id} to hand size.", card=instance_id)
    if len(state.investigator.hand) > 8:
        present_discard_to_size(state)


def run_mythos_phase(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> None:
    if state.round == 1:
        key = f"mythos_skipped:{state.round}"
        if not state.limits.get(key):
            state.limits[key] = True
            log_event(events, "mythos_skipped", "Mythos phase skipped in round 1.")
        return
    from .effects import place_doom

    doom_key = f"mythos_doom_placed:{state.round}"
    if not state.limits.get(doom_key):
        state.limits[doom_key] = True
        place_doom(state, 1, events, source="mythos")
    if state.status != "in_progress" or state.decision_queue:
        return
    encounter_key = f"mythos_encounter_drawn:{state.round}"
    if not state.limits.get(encounter_key):
        state.limits[encounter_key] = True
        encounter.draw_encounter(state, rng, events)
    if state.status != "in_progress" or state.decision_queue:
        return
    engage_ready_enemies_at_roland(state, events)


def start_frozen_end_turn_test(state: GameState, events: list[dict[str, Any]]) -> bool:
    if state.limits.get(f"frozen_end_turn:{state.round}"):
        return False
    frozen = player_cards.threat_ids(state, "01164")
    if not frozen:
        return False
    state.limits[f"frozen_end_turn:{state.round}"] = True
    from . import skill_test

    skill_test.start(
        state,
        events,
        skill="willpower",
        difficulty=3,
        source="Frozen in Fear",
        on_success={"kind": "discard_threat_on_success", "card_code": "01164"},
    )
    return True


def discard_dissonant_voices(state: GameState, events: list[dict[str, Any]]) -> None:
    for instance_id in list(player_cards.threat_ids(state, "01165")):
        player_cards.discard_from_threat(state, instance_id)
        log_event(events, "treachery_discarded", "Dissonant Voices was discarded at end of round.", card=instance_id)
