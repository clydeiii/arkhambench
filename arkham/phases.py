"""Phase structure placeholders for phase B."""
from __future__ import annotations

from typing import Any

from . import actions, encounter
from .cards import player as player_cards
from .effects import draw_player_card, gain_resource, log_event, process_deferred_agenda_advance, resolve_damage_resume, resume_damage_continuation
from .enemies import attack, can_attack_investigator, engage_ready_enemies_at_roland, enemy_name, move_hunters
from .model import DEVOURER_FAMILY, GATHERING_FAMILY, MIDNIGHT_MASKS_FAMILY, DecisionOption, GameState, PendingDecision
from .rng import ArkhamRng


def advance_until_decision(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]]) -> None:
    guard = 0
    while state.status == "in_progress" and not state.decision_queue:
        guard += 1
        if guard > 100:
            raise RuntimeError("phase loop did not reach a decision")
        if state.active_skill_test or state.pending_damage:
            if state.active_skill_test and state.limits.get("deferred_skill_test_resolution") and not state.pending_damage:
                from . import skill_test

                skill_test.resume_deferred_resolution(state, events, rng)
                continue
            if state.active_skill_test and not state.pending_damage and state.active_skill_test.get("token") is None:
                # A reaction queued at play time (e.g. Heirloom of Hyperborea)
                # interleaved with the commit window and finish_commit bailed
                # believing its own pre-reveal prompt was pending. The queue is
                # empty here, so drive the test forward: reveal and resolve.
                from . import skill_test

                skill_test.finish_commit(state, rng, events)
                continue
            return
        if state.limits.get("pending_scenario_token_aftermath"):
            from . import skill_test

            skill_test.process_deferred_scenario_token_aftermath(state, events, rng)
            continue
        if state.limits.get("deferred_damage_continuation"):
            resume_damage_continuation(state, events, rng)
            continue
        if state.limits.get("deferred_skill_callback"):
            from . import skill_test

            skill_test.resume_deferred_callback(state, events, rng)
            continue
        if state.limits.get("deferred_agenda_advance"):
            process_deferred_agenda_advance(state, events, rng=rng)
            continue
        if state.limits.get("pending_devourer_agenda3"):
            from .scenarios import the_devourer_below

            state.limits.pop("pending_devourer_agenda3", None)
            the_devourer_below.advance_to_agenda3(state, events)
            continue
        if state.limits.get("pending_alma_parley"):
            from .scenarios import the_midnight_masks

            the_midnight_masks.resume_alma_parley(state, events, rng)
            continue
        if state.limits.get("after_encounter_draw"):
            encounter.resolve_after_encounter_draw(state, events)
            continue
        deferred = state.limits.pop("deferred_resume", None)
        if deferred:
            if deferred.get("kind") == "aoo_order":
                actions.continue_aoo_order(state, events, dict(deferred), rng)
            elif deferred.get("kind") == "after_attack":
                from .enemies import after_attack

                after_attack(
                    state,
                    events,
                    str(deferred.get("enemy", "")),
                    dict(deferred.get("resume", {})),
                    source=str(deferred.get("source", "")),
                    rng=rng,
                )
            elif deferred.get("kind") == "scenario":
                resolve_damage_resume(state, events, dict(deferred), rng)
            elif deferred.get("kind") == "skill_test_reveal":
                from . import skill_test

                skill_test.resume_deferred_resolution(state, events, rng)
            else:
                actions.execute(state, dict(deferred.get("payload", {})), events, rng)
            continue
        if state.phase == "Investigation":
            if state.investigator.actions_remaining > 0:
                actions.present_action_decision(state)
            else:
                turn_ended = state.limits.get(f"turn_ended:{state.round}") or state.limits.get(
                    f"turn_forcibly_ended:{state.round}"
                )
                if not turn_ended and present_fast_window(state, "inv_end", during_turn=True):
                    return
                if resolve_dark_memory_end_turn(state, events):
                    return
                if start_frozen_end_turn_test(state, events):
                    return
                if state.scenario in DEVOURER_FAMILY:
                    from .scenarios import the_devourer_below

                    the_devourer_below.end_investigator_turn(state, events)
                # Will to Survive lasts "until the end of your turn", not the round.
                state.limits.pop(f"will_to_survive:{state.round}", None)
                state.phase = "Enemy"
                log_event(events, "phase_started", "Enemy phase began.")
        elif state.phase == "Enemy":
            run_enemy_phase(state, events, rng)
            if not state.decision_queue and state.status == "in_progress":
                if state.scenario in GATHERING_FAMILY:
                    from .scenarios import the_gathering

                    the_gathering.end_enemy_phase(state, events)
                elif state.scenario in MIDNIGHT_MASKS_FAMILY:
                    from .scenarios import the_midnight_masks

                    the_midnight_masks.end_enemy_phase(state, events, rng)
                elif state.scenario in DEVOURER_FAMILY:
                    from .scenarios import the_devourer_below

                    the_devourer_below.end_enemy_phase(state, events, rng)
                if state.decision_queue or state.status != "in_progress":
                    return
                state.phase = "Upkeep"
                log_event(events, "phase_started", "Upkeep phase began.")
        elif state.phase == "Upkeep":
            run_upkeep_phase(state, events, rng)
            if not state.decision_queue and state.status == "in_progress":
                if state.scenario in GATHERING_FAMILY:
                    from .scenarios import the_gathering

                    the_gathering.end_round(state, events)
                elif state.scenario in DEVOURER_FAMILY:
                    from .scenarios import the_devourer_below

                    the_devourer_below.end_round(state, events)
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
                    and not str(key).startswith("daisy_tome:")
                    and not str(key).startswith("skids_action:")
                    and not str(key).startswith("agnes_horror:")
                    and not str(key).startswith("frozen_end_turn:")
                    and not str(key).startswith("mythos_")
                    and not str(key).startswith("upkeep_done:")
                    and not str(key).startswith("fastwin:")
                    and not str(key).startswith("hunters_moved:")
                    and not str(key).startswith("on_the_lam:")
                    and not str(key).startswith("hospital_debts:")
                    and not str(key).startswith("dark_memory_end_turn:")
                    and not str(key).startswith("turn_ended:")
                    and not str(key).startswith("turn_forcibly_ended:")
                }
                log_event(events, "round_started", f"Round {state.round} began.")
        elif state.phase == "Mythos":
            run_mythos_phase(state, rng, events)
            if not state.decision_queue and state.status == "in_progress":
                if present_fast_window(state, "mythos_end", during_turn=False):
                    return
                if state.scenario in MIDNIGHT_MASKS_FAMILY:
                    from .scenarios import the_midnight_masks

                    the_midnight_masks.end_mythos_phase(state, events, rng)
                elif state.scenario in DEVOURER_FAMILY:
                    from .scenarios import the_devourer_below

                    the_devourer_below.end_mythos_phase(state, events, rng)
                if state.decision_queue or state.status != "in_progress":
                    return
                state.phase = "Investigation"
                state.investigator.actions_remaining = starting_actions(state)
                state.turn.action_index = 0
                log_event(events, "phase_started", "Investigation phase began.")
        else:
            state.phase = "Investigation"


def present_fast_window(state: GameState, boundary: str, *, during_turn: bool) -> bool:
    """Offer legal fast abilities at a phase boundary. Returns True if a decision
    was queued. The window closes when the player passes (guard key set) and is
    re-offered after each use while more fast abilities remain legal."""
    key = f"fastwin:{boundary}:{state.round}"
    if state.limits.get(key):
        return False
    options: list[DecisionOption] = []
    actions.add_fast_options(state, options, during_turn=during_turn, include_objective=during_turn)
    if not options:
        state.limits[key] = True
        return False
    options.append(DecisionOption("Pass (continue)", {"kind": "fast_window_pass", "key": key}))
    state.decision_queue = [
        PendingDecision(
            id=f"fast-window-{boundary}",
            kind="fast_window",
            prompt=f"[Round {state.round} · {state.phase} · {state.investigator.name}] Fast-ability window — use a fast ability or pass:",
            options=options,
        )
    ]
    return True


def run_enemy_phase(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    # Hunters move once per round even if the phase is interrupted by decisions.
    hunters_key = f"hunters_moved:{state.round}"
    if not state.limits.get(hunters_key):
        state.limits[hunters_key] = True
        move_hunters(state, events)
    if present_fast_window(state, "enemy_pre", during_turn=False):
        return
    attacked_key = f"enemy_phase_attacked:{state.round}"
    attacked = set(state.limits.get(attacked_key, []))
    ready_attackers = [
        enemy_id
        for enemy_id in list(state.investigator.engaged_enemies)
        if enemy_id not in attacked
        and (enemy := state.enemies.get(enemy_id)) is not None
        and not enemy.exhausted
        and can_attack_investigator(state, enemy_id)
    ]
    if state.scenario in DEVOURER_FAMILY:
        from .scenarios import the_devourer_below

        ready_attackers.extend(the_devourer_below.massive_attackers(state, attacked))
    if len(ready_attackers) > 1:
        present_enemy_attack_order(state, ready_attackers)
        return
    for enemy_id in ready_attackers:
        if enemy_id in attacked:
            continue
        enemy = state.enemies.get(enemy_id)
        if enemy and not enemy.exhausted:
            attack(state, events, enemy_id, source="enemy phase", rng=rng)
            attacked.add(enemy_id)
            state.limits[attacked_key] = sorted(attacked)
            if state.decision_queue:
                return
    if present_fast_window(state, "enemy_post", during_turn=False):
        return


def present_enemy_attack_order(state: GameState, attackers: list[str]) -> None:
    state.decision_queue = [
        PendingDecision(
            id="enemy-attack-order",
            kind="enemy_attack_order",
            prompt="Choose the next enemy-phase attack.",
            options=[
                DecisionOption(
                    f"Attack next: {enemy_name(state, enemy_id)}",
                    {"kind": "enemy_attack_order", "enemy": enemy_id},
                )
                for enemy_id in attackers
            ],
        )
    ]


def resolve_enemy_attack_order(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    enemy_id = str(payload.get("enemy", ""))
    attacked_key = f"enemy_phase_attacked:{state.round}"
    attacked = set(state.limits.get(attacked_key, []))
    if enemy_id in state.enemies and not state.enemies[enemy_id].exhausted and enemy_id not in attacked and can_attack_investigator(state, enemy_id):
        attacked.add(enemy_id)
        state.limits[attacked_key] = sorted(attacked)
        attack(state, events, enemy_id, source="enemy phase", rng=rng)


def run_upkeep_phase(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    if state.status != "in_progress":
        return
    if present_fast_window(state, "upkeep_start", during_turn=False):
        return
    # Idempotency guard: the phase loop re-enters this function after the
    # hand-size discard decision resolves; the ready/draw/resource steps must
    # only happen once per round (they are not re-run while discarding).
    key = f"upkeep_done:{state.round}"
    if not state.limits.get(key):
        state.limits[key] = True
        state.investigator.exhausted = False
        for instance in state.card_instances.values():
            instance.exhausted = False
        for enemy in state.enemies.values():
            enemy.exhausted = False
        log_event(events, "ready_step", "All exhausted cards readied.")
        engage_ready_enemies_at_roland(state, events)
        if state.status != "in_progress":
            return
        draw_player_card(state, events, rng)
        if state.status != "in_progress":
            return
        gain_resource(state, 1, events)
        if state.status != "in_progress":
            return
        discard_dissonant_voices(state, events)
        if state.status != "in_progress":
            return
    if state.status != "in_progress":
        return
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
            prompt=f"[Round {state.round} · Upkeep · {state.investigator.name}] Discard to hand size 8.",
            options=options,
        )
    ]


def discard_to_size(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    instance_id = str(payload["card"])
    if instance_id in state.investigator.hand:
        state.investigator.hand.remove(instance_id)
        state.investigator.discard.append(instance_id)
        state.card_instances[instance_id].zone = "discard"
        from . import data as card_data

        card_name = card_data.cards_by_code().get(state.card_instances[instance_id].card_code, {}).get("name", instance_id)
        log_event(events, "card_discarded", f"Discarded {card_name} to hand size.", card=instance_id)
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
        place_doom(state, 1, events, source="mythos", rng=rng, can_advance=True)
    if state.status != "in_progress" or state.decision_queue:
        return
    encounter_key = f"mythos_encounter_drawn:{state.round}"
    if not state.limits.get(encounter_key):
        state.limits[encounter_key] = True
        encounter.draw_encounter(state, rng, events)
    if state.status != "in_progress" or state.decision_queue:
        return
    engage_ready_enemies_at_roland(state, events)


def starting_actions(state: GameState) -> int:
    total = 4 if state.investigator.card_code == "01002" and not player_cards.investigator_text_blank(state) else 3
    if player_cards.controls_code(state, "01048") or player_cards.controls_code(state, "01054"):
        total += 1
    return total


def resolve_dark_memory_end_turn(state: GameState, events: list[dict[str, Any]]) -> bool:
    key = f"dark_memory_end_turn:{state.round}"
    if state.limits.get(key):
        return False
    memories = player_cards.hand_ids(state, "01013")
    if not memories:
        return False
    state.limits[key] = True
    from .effects import log_event, start_damage_assignment

    log_event(events, "dark_memory_revealed", "Dark Memory was revealed from hand at end of turn.", card=memories[0])
    start_damage_assignment(state, events, source="Dark Memory", damage=0, horror=2)
    return bool(state.decision_queue or state.pending_damage or state.status != "in_progress")


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
