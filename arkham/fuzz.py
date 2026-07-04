from __future__ import annotations

import argparse
import random
import tempfile
from collections import Counter
from pathlib import Path

from .game import Game


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=200)
    parser.add_argument("--investigator", default="roland")
    args = parser.parse_args(argv)
    outcomes = run_fuzz(args.games, investigator=args.investigator)
    for outcome, count in sorted(outcomes.items()):
        print(f"{outcome}: {count}")
    return 0


def run_fuzz(games: int, *, investigator: str = "roland") -> Counter[str]:
    difficulties = ["easy", "standard", "hard", "expert"]
    outcomes: Counter[str] = Counter()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for index in range(games):
            difficulty = difficulties[index % len(difficulties)]
            seed = index + 1
            chooser = random.Random(seed * 7919)
            game = Game.new(seed=seed, difficulty=difficulty, deck_path=None, run_dir=root / f"game-{index}", investigator=investigator)
            steps = 0
            while game.state.status == "in_progress":
                check_invariants(game)
                if game.state.round > 100:
                    raise AssertionError(f"game exceeded 100 rounds: seed={seed} difficulty={difficulty}")
                decision = game.current_decision()
                if decision is None or not decision.options:
                    raise AssertionError(f"in-progress game has no legal decision: seed={seed}")
                choice = chooser.randrange(1, len(decision.options) + 1)
                game.apply(choice)
                steps += 1
                if steps > 3000:
                    raise AssertionError(f"game exceeded 3000 decisions: seed={seed}")
            check_invariants(game)
            outcome = "ended"
            if game.state.result:
                outcome = str(game.state.result.get("outcome", "ended"))
            outcomes[outcome] += 1
    return outcomes


def check_invariants(game: Game) -> None:
    state = game.state
    investigator = state.investigator
    assert investigator.damage >= 0
    assert investigator.horror >= 0
    assert investigator.resources >= 0
    assert investigator.clues >= 0
    assert investigator.actions_remaining <= 6
    if state.agenda:
        assert state.agenda.doom >= 0
    for location in state.locations.values():
        assert location.clues >= 0
    for instance in state.card_instances.values():
        assert instance.damage >= 0
        assert instance.horror >= 0
        assert instance.clues >= 0
        assert instance.doom >= 0
    assert_unique_cards(state)


def assert_unique_cards(state) -> None:
    seen: dict[str, str] = {}

    def add(card_id: str, zone: str) -> None:
        if card_id not in state.card_instances:
            return
        if card_id in seen:
            raise AssertionError(f"{card_id} appears in both {seen[card_id]} and {zone}")
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
        raise AssertionError(f"cards missing from zones: {sorted(missing - allowed_missing)[:5]}")


if __name__ == "__main__":
    raise SystemExit(main())
