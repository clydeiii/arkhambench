"""Random legal-action fuzzer with semantic invariants.

The fuzzer asserts invariants at every decision point, not just at game end.
Use ``--invariants-only`` when the outcome distribution is irrelevant and the
run is only being used as a crash/invariant smoke check.
"""
from __future__ import annotations

import argparse
import random
import re
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .game import Game
from .model import DecisionOption, PendingDecision


TEST_LABEL_RE = re.compile(r"test\s+(?P<skill>[A-Z][A-Za-z]*)\((?P<base>\d+)\)\s+vs\s+(?P<difficulty>\d+)")
STARTED_TEST_RE = re.compile(r"Started\s+(?P<skill>[a-z_]+)\s+test\s+(?P<base>\d+)\s+vs\s+(?P<difficulty>\d+)")


@dataclass
class InvariantContext:
    seed: int
    difficulty: str
    investigator: str
    scenario: str
    decision_step: int = 0
    victory_seen: set[str] = field(default_factory=set)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=200)
    parser.add_argument("--investigator", default="roland")
    parser.add_argument("--scenario", default="the_gathering")
    parser.add_argument(
        "--invariants-only",
        action="store_true",
        help="run games only to exercise invariant checks; suppress the outcome table",
    )
    args = parser.parse_args(argv)
    outcomes = run_fuzz(args.games, investigator=args.investigator, scenario=args.scenario)
    if args.invariants_only:
        print(f"invariants ok: {sum(outcomes.values())} games")
        return 0
    for outcome, count in sorted(outcomes.items()):
        print(f"{outcome}: {count}")
    return 0


def run_fuzz(games: int, *, investigator: str = "roland", scenario: str = "the_gathering") -> Counter[str]:
    difficulties = ["easy", "standard", "hard", "expert"]
    outcomes: Counter[str] = Counter()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for index in range(games):
            difficulty = difficulties[index % len(difficulties)]
            seed = index + 1
            chooser = random.Random(seed * 7919)
            game = Game.new(seed=seed, difficulty=difficulty, deck_path=None, run_dir=root / f"game-{index}", investigator=investigator, scenario=scenario)
            context = InvariantContext(seed=seed, difficulty=difficulty, investigator=investigator, scenario=scenario)
            context.victory_seen = set(game.state.victory_display)
            steps = 0
            while game.state.status == "in_progress":
                check_invariants(game, context)
                if game.state.round > 100:
                    raise AssertionError(f"game exceeded 100 rounds: seed={seed} difficulty={difficulty}")
                decision = game.current_decision()
                if decision is None or not decision.options:
                    raise AssertionError(f"in-progress game has no legal decision: seed={seed}")
                check_decision_invariants(game, decision, context)
                choice = chooser.randrange(1, len(decision.options) + 1)
                chosen_option = decision.options[choice - 1]
                expected_test = parse_test_label(chosen_option.label)
                events = game.apply(choice)
                check_step_invariants(game, events, expected_test, chosen_option, context)
                context.decision_step += 1
                steps += 1
                if steps > 3000:
                    raise AssertionError(f"game exceeded 3000 decisions: seed={seed}")
            check_invariants(game, context)
            outcome = "ended"
            if game.state.result:
                outcome = str(game.state.result.get("outcome", "ended"))
            outcomes[outcome] += 1
    return outcomes


def check_invariants(game: Game, context: InvariantContext | None = None) -> None:
    state = game.state
    investigator = state.investigator
    fail = invariant_failer(game, context)
    fail(investigator.damage >= 0, "investigator damage is negative")
    fail(investigator.horror >= 0, "investigator horror is negative")
    fail(investigator.resources >= 0, "investigator resources are negative")
    fail(investigator.clues >= 0, "investigator clues are negative")
    fail(investigator.actions_remaining >= 0, "actions_remaining is negative")
    fail(investigator.actions_remaining <= 6, "actions_remaining exceeded 6")
    fail(state.turn.action_index <= 6, "per-round actions spent exceeded 6")
    if state.agenda:
        fail(state.agenda.doom >= 0, "agenda doom is negative")
    for location in state.locations.values():
        fail(location.clues >= 0, f"{location.name} clues are negative")
    for instance in state.card_instances.values():
        fail(instance.damage >= 0, f"{instance.id} damage is negative")
        fail(instance.horror >= 0, f"{instance.id} horror is negative")
        fail(instance.clues >= 0, f"{instance.id} clues are negative")
        fail(instance.doom >= 0, f"{instance.id} doom is negative")
    for enemy in state.enemies.values():
        fail(enemy.damage >= 0, f"{enemy.id} damage is negative")
        fail(enemy.horror >= 0, f"{enemy.id} horror is negative")
        fail(enemy.clues >= 0, f"{enemy.id} clues are negative")
        fail(enemy.doom >= 0, f"{enemy.id} doom is negative")
    if context is not None:
        current_victory = set(state.victory_display)
        fail(context.victory_seen.issubset(current_victory), "victory display shrank")
        context.victory_seen = current_victory
    assert_unique_cards(state, fail=fail)


def check_decision_invariants(game: Game, decision: PendingDecision, context: InvariantContext) -> None:
    fail = invariant_failer(game, context)
    labels = [option.label for option in decision.options]
    duplicates = [label for label, count in Counter(labels).items() if count > 1]
    fail(not duplicates, f"duplicate option labels: {duplicates}")
    for option in decision.options:
        move_target = move_target_for_option(option)
        if move_target:
            fail(
                move_target != game.state.investigator.location_id,
                f"self-move option offered: {option.label!r}",
            )


def check_step_invariants(
    game: Game,
    events: list[dict[str, Any]],
    expected_test: tuple[str, int, int] | None,
    chosen_option: DecisionOption,
    context: InvariantContext,
) -> None:
    fail = invariant_failer(game, context, chosen_option=chosen_option.label)
    if expected_test is not None:
        started = first_started_test(events)
        if started is not None:
            fail(
                started == expected_test,
                f"label test math {expected_test} did not match started test {started}",
            )
    if any(event.get("type") == "action_spent" for event in events):
        spent_index = next(index for index, event in enumerate(events) if event.get("type") == "action_spent")
        trailing = events[spent_index + 1 :]
        has_trace = any(event.get("type") != "action_spent" for event in trailing)
        decision_pending = game.current_decision() is not None
        actions_refunded = game.state.investigator.actions_remaining > actions_remaining_after_spend(events)
        fail(
            has_trace or decision_pending or actions_refunded,
            "action_spent had no subsequent trace, pending decision, or action refund",
        )
    check_invariants(game, context)


def parse_test_label(label: str) -> tuple[str, int, int] | None:
    match = TEST_LABEL_RE.search(label)
    if not match:
        return None
    return (match.group("skill").lower(), int(match.group("base")), int(match.group("difficulty")))


def first_started_test(events: list[dict[str, Any]]) -> tuple[str, int, int] | None:
    for event in events:
        if event.get("type") != "skill_test_started":
            continue
        data = event.get("data", {})
        message = str(data.get("message", "")) if isinstance(data, dict) else ""
        match = STARTED_TEST_RE.search(message)
        if match:
            return (match.group("skill"), int(match.group("base")), int(match.group("difficulty")))
    return None


def actions_remaining_after_spend(events: list[dict[str, Any]]) -> int:
    # Event rows do not carry public state snapshots. This helper only exists to
    # recognize explicit action-grant events in the loose trace heuristic.
    grants = {"skids_ability", "card_played"}
    return -1 if any(event.get("type") in grants for event in events) else 99


def move_target_for_option(option: DecisionOption) -> str | None:
    payload = option.payload
    kind = str(payload.get("kind", ""))
    action = str(payload.get("action", ""))
    ability = str(payload.get("ability", ""))
    location = str(payload.get("location", ""))
    if kind == "action" and action == "move":
        return location or None
    if kind == "action" and action == "fast_ability" and ability == "elusive" and location:
        return location
    if kind == "survival_instinct" and location:
        return location
    return None


def invariant_failer(game: Game, context: InvariantContext | None, *, chosen_option: str | None = None):
    def fail(condition: bool, message: str) -> None:
        if condition:
            return
        seed = context.seed if context else "?"
        difficulty = context.difficulty if context else game.state.difficulty
        step = context.decision_step if context else "?"
        decision = game.current_decision()
        prompt = decision.prompt if decision else "<no decision>"
        extra = f" chosen={chosen_option!r}" if chosen_option is not None else ""
        raise AssertionError(
            f"invariant failed: {message}; seed={seed} difficulty={difficulty} "
            f"scenario={game.state.scenario} investigator={game.state.investigator.id} "
            f"step={step} round={game.state.round} phase={game.state.phase} "
            f"prompt={prompt!r}{extra}"
        )

    return fail


def assert_unique_cards(state, *, fail=None) -> None:
    if fail is None:
        fail = lambda condition, message: (_ for _ in ()).throw(AssertionError(message)) if not condition else None
    seen: dict[str, str] = {}

    def add(card_id: str, zone: str) -> None:
        if card_id not in state.card_instances:
            return
        if card_id in seen:
            fail(False, f"{card_id} appears in both {seen[card_id]} and {zone}")
        seen[card_id] = zone

    for zone_name, card_ids in (
        ("hand", state.investigator.hand),
        ("player_deck", state.investigator.deck),
        ("player_discard", state.investigator.discard),
        ("play", state.investigator.play_area),
        ("threat", state.investigator.threat_area),
        ("encounter_deck", state.encounter_deck),
        ("encounter_discard", state.encounter_discard),
        ("victory", state.victory_display),
    ):
        for card_id in card_ids:
            add(card_id, zone_name)
    for test_card in (state.active_skill_test or {}).get("committed", []):
        add(test_card, "committed")
    played_event = (state.active_skill_test or {}).get("played_event")
    if played_event:
        add(str(played_event), "limbo")
    for enemy_id in state.enemies:
        add(enemy_id, "enemy")
    for location in state.locations.values():
        for attachment in location.attached_instance_ids:
            add(attachment, f"attachment:{location.id}")
    for card_id, instance in state.card_instances.items():
        if instance.zone in {"set_aside", "removed", "aside"}:
            seen.setdefault(card_id, instance.zone)
    for card_id in state.limits.get("mulliganed_aside", []):
        seen.setdefault(str(card_id), "mulliganed_aside")
    missing = set(state.card_instances) - set(seen)
    allowed_missing = {
        card_id
        for card_id, instance in state.card_instances.items()
        if instance.zone in {"story", "attachment", "enemy", "set_aside", "aside", "encounter_drawn"}
    }
    if missing - allowed_missing:
        fail(False, f"cards missing from zones: {sorted(missing - allowed_missing)[:5]}")


if __name__ == "__main__":
    raise SystemExit(main())
