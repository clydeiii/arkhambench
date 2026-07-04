from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import data as card_data
from .errors import EngineError
from .game import Game
from .log import read_jsonl, read_markdown, render_event, status_line
from .model import GameState
from .notebook import add_note, compact, resolve_notebook, show


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except EngineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ahlcg")
    parser.add_argument("--run", help="run directory")
    parser.add_argument("--notebook", help="notebook path")
    sub = parser.add_subparsers(required=True)

    new = sub.add_parser("new")
    new.add_argument("--seed", type=int, default=1)
    new.add_argument("--difficulty", choices=("easy", "standard", "hard", "expert"), default="standard")
    new.add_argument("--scenario", choices=("the_gathering", "return_to_the_gathering"), default="the_gathering")
    new.add_argument("--investigator", choices=tuple(card_data.INVESTIGATOR_CODES), default="roland")
    new.add_argument("--deck", default=None)
    new.add_argument("--run", dest="run", default=None)
    new.add_argument("--notebook", dest="notebook", default=None, help="persistent notebook bound to this run (recorded in meta.json)")
    new.set_defaults(func=cmd_new)

    state = sub.add_parser("state")
    state.add_argument("--run", dest="run", default=None)
    state.add_argument("--full", action="store_true")
    state.set_defaults(func=cmd_state)

    actions = sub.add_parser("actions")
    actions.add_argument("--run", dest="run", default=None)
    actions.set_defaults(func=cmd_actions)

    do = sub.add_parser("do")
    do.add_argument("option", type=int)
    do.add_argument("--run", dest="run", default=None)
    do.set_defaults(func=cmd_do)

    log = sub.add_parser("log")
    log.add_argument("--run", dest="run", default=None)
    log.add_argument("--tail", type=int, default=20)
    log.add_argument("--md", action="store_true")
    log.set_defaults(func=cmd_log)

    card = sub.add_parser("card")
    card.add_argument("query")
    card.set_defaults(func=cmd_card)

    score = sub.add_parser("score")
    score.add_argument("--run", dest="run", default=None)
    score.set_defaults(func=cmd_score)

    note = sub.add_parser("note")
    note_sub = note.add_subparsers(required=True)
    note_add = note_sub.add_parser("add")
    note_add.add_argument("text")
    note_add.add_argument("--run", dest="run", default=None)
    note_add.add_argument("--notebook", dest="notebook", default=None)
    note_add.set_defaults(func=cmd_note_add)
    note_show = note_sub.add_parser("show")
    note_show.add_argument("--notebook", dest="notebook", default=None)
    note_show.set_defaults(func=cmd_note_show)
    note_compact = note_sub.add_parser("compact")
    note_compact.add_argument("--file", "-f", required=True)
    note_compact.add_argument("--notebook", dest="notebook", default=None)
    note_compact.set_defaults(func=cmd_note_compact)
    return parser


def resolve_run_dir(run_arg: str | None, *, for_new: bool = False) -> Path:
    if run_arg:
        return Path(run_arg)
    if os.environ.get("AHLCG_RUN"):
        return Path(os.environ["AHLCG_RUN"])
    current = Path.cwd() / ".current_run"
    if current.exists():
        text = current.read_text(encoding="utf-8").strip()
        if text:
            return Path(text)
    if for_new:
        return Path("runs") / "current"
    raise EngineError("run directory not specified; use --run, AHLCG_RUN, or .current_run")


def cmd_new(args: argparse.Namespace) -> int:
    run_dir = resolve_run_dir(args.run, for_new=True)
    game = Game.new(
        seed=args.seed,
        difficulty=args.difficulty,
        deck_path=args.deck,
        run_dir=run_dir,
        scenario=args.scenario,
        investigator=args.investigator,
        notebook=args.notebook,
    )
    (Path.cwd() / ".current_run").write_text(str(run_dir), encoding="utf-8")
    print(f"Created run: {run_dir}")
    print(render_state(game.state))
    print(render_decision(game.current_decision(), game.state))
    return 0


def cmd_state(args: argparse.Namespace) -> int:
    game = Game.load(resolve_run_dir(args.run))
    print(render_state(game.state, full=args.full))
    return 0


def cmd_actions(args: argparse.Namespace) -> int:
    game = Game.load(resolve_run_dir(args.run))
    print(render_decision(game.current_decision(), game.state))
    return 0


def cmd_do(args: argparse.Namespace) -> int:
    game = Game.load(resolve_run_dir(args.run))
    decision = game.current_decision()
    if decision is None:
        if game.state.status == "ended":
            print(status_line(game.state))
            print("GAME OVER")
            return 0
        print("GAME OVER" if game.state.status == "ended" else "No available actions.")
        return 0
    if args.option < 1 or args.option > len(decision.options):
        print("error: invalid option", file=sys.stderr)
        print(render_decision(decision, game.state), file=sys.stderr)
        return 2
    events = game.apply(args.option)
    for event in events:
        print(render_event(event))
    if game.state.status == "ended":
        summary = game.state.result.get("outcome", "game ended") if game.state.result else "game ended"
        print(status_line(game.state))
        print(f"GAME OVER — {summary}")
    else:
        print(render_decision(game.current_decision(), game.state))
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    run_dir = resolve_run_dir(args.run)
    text = read_markdown(run_dir, args.tail) if args.md else read_jsonl(run_dir, args.tail)
    print(text)
    return 0


def cmd_card(args: argparse.Namespace) -> int:
    matches = card_data.search_cards(args.query)
    if not matches:
        raise EngineError(f"no card found for {args.query!r}")
    for index, card in enumerate(matches, start=1):
        if index > 1:
            print()
        print(card_data.format_card(card))
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    game = Game.load(resolve_run_dir(args.run))
    if game.state.result:
        result = game.state.result
        print(f"outcome: {result.get('outcome', 'game ended')}")
        print(f"resolution: {result.get('resolution', '-')}")
        print(f"xp: {result.get('xp', 0)}")
        print(f"score: {result.get('score', 0)}")
        print(f"trauma: {result.get('trauma', {})}")
    else:
        print("game in progress")
    return 0


def cmd_note_add(args: argparse.Namespace) -> int:
    run_name = None
    round_number = None
    run_dir = None
    try:
        run_dir = resolve_run_dir(args.run)
        game = Game.load(run_dir)
        run_name = run_dir.name
        round_number = game.state.round
    except EngineError:
        pass
    notebook_path = resolve_notebook(args.notebook, run_dir=run_dir)
    add_note(notebook_path, args.text, run_name=run_name, round_number=round_number)
    if run_name is not None and run_dir is not None:
        from .log import EventLog

        EventLog(run_dir).append(
            round=game.state.round,
            phase=game.state.phase,
            type="note_added",
            data={},
        )
    print(f"added note: {notebook_path}")
    return 0


def _notebook_run_dir(run_arg: str | None) -> Path | None:
    try:
        return resolve_run_dir(run_arg)
    except EngineError:
        return None


def cmd_note_show(args: argparse.Namespace) -> int:
    print(show(resolve_notebook(args.notebook, run_dir=_notebook_run_dir(None))), end="")
    return 0


def cmd_note_compact(args: argparse.Namespace) -> int:
    if args.file == "-":
        body = sys.stdin.read()
    else:
        body = Path(args.file).read_text(encoding="utf-8")
    archive = compact(resolve_notebook(args.notebook, run_dir=_notebook_run_dir(None)), body)
    print(f"archived previous notebook: {archive}")
    return 0


def render_decision(decision: object | None, state: GameState | None = None) -> str:
    if decision is None:
        return "No current decision."
    prompt = decision.prompt  # type: ignore[attr-defined]
    lines = []
    if state is not None:
        lines.append(status_line(state))
    lines.append(prompt)
    for index, option in enumerate(decision.options, start=1):  # type: ignore[attr-defined]
        lines.append(f"{index}. {option.label}")
    return "\n".join(lines)


def render_state(state: GameState, *, full: bool = False) -> str:
    investigator = state.investigator
    agenda = state.agenda
    act = state.act
    lines = [
        f"Scenario: {state.scenario} ({state.difficulty})",
        f"Round {state.round} · {state.phase} · {investigator.name} · {investigator.actions_remaining} actions left",
    ]
    if agenda:
        lines.append(f"Agenda: {agenda.name} — doom {agenda.doom}/{agenda.threshold}")
    if act:
        needed = "?" if act.clues_required is None else str(act.clues_required)
        lines.append(f"Act: {act.name} — clues {investigator.clues}/{needed}")
    lines.append("Locations:")
    for location in state.locations.values():
        reveal = "revealed" if location.revealed else "unrevealed"
        shroud = "?" if location.shroud is None else str(location.shroud)
        details = [
            f"{location.name} ({reveal}) shroud {shroud}",
            f"clues {location.clues}",
            f"connections {', '.join(location.connections) or '-'}",
        ]
        if location.attached_instance_ids:
            details.append("attachments " + ", ".join(card_label(state, card_id) for card_id in location.attached_instance_ids))
        if location.enemy_ids:
            details.append("enemies " + ", ".join(enemy_label(state, enemy_id) for enemy_id in location.enemy_ids if enemy_id in state.enemies))
        lines.append("- " + "; ".join(details))
    lines.append(
        f"{investigator.name}: {investigator.damage}/{investigator.health} damage, {investigator.horror}/{investigator.sanity} horror, "
        f"{investigator.resources} resources, {investigator.clues} clues, hand {len(investigator.hand)}, deck {len(investigator.deck)}"
    )
    if investigator.engaged_enemies:
        lines.append("Engaged enemies: " + ", ".join(enemy_label(state, enemy_id) for enemy_id in investigator.engaged_enemies if enemy_id in state.enemies))
    lines.append("Play area: " + (", ".join(play_area_label(state, card_id) for card_id in investigator.play_area) or "-"))
    lines.append("Threat area: " + (", ".join(threat_label(state, card_id) for card_id in investigator.threat_area) or "-"))
    lines.append("Hand:")
    if investigator.hand:
        cards = card_data.cards_by_code()
        for instance_id in investigator.hand:
            instance = state.card_instances[instance_id]
            card = cards.get(instance.card_code, {})
            cost = card.get("cost", "-")
            lines.append(f"- {card_label(state, instance_id)} (cost {cost})")
    else:
        lines.append("- empty")
    lines.append("Chaos bag: " + ", ".join(state.chaos_bag.tokens))
    lines.append("Victory display: " + (", ".join(zone_label(state, item_id) for item_id in state.victory_display) or "-"))
    lines.append(f"Discards: player {len(investigator.discard)}, encounter {len(state.encounter_discard)}")
    if full:
        cards = card_data.cards_by_code()
        if investigator.discard:
            lines.append("Player discard:")
            for instance_id in investigator.discard:
                instance = state.card_instances[instance_id]
                card = cards.get(instance.card_code, {})
                lines.append(f"- {card_label(state, instance_id)}")
        if state.encounter_discard:
            lines.append("Encounter discard:")
            for instance_id in state.encounter_discard:
                instance = state.card_instances.get(instance_id)
                code = instance.card_code if instance else instance_id
                card = cards.get(code, {})
                lines.append(f"- {card.get('name', code)} ({instance_id})")
    lines.append(f"Deck counts: player {len(investigator.deck)}")
    return "\n".join(lines)


def card_label(state: GameState, instance_id: str) -> str:
    instance = state.card_instances.get(instance_id)
    if instance is None:
        return instance_id
    card = card_data.cards_by_code().get(instance.card_code, {})
    return f"{card.get('name', instance.card_code)} ({instance_id})"


def zone_label(state: GameState, item_id: str) -> str:
    if item_id in state.card_instances:
        return card_label(state, item_id)
    if item_id in state.locations:
        return state.locations[item_id].name
    return item_id


def play_area_label(state: GameState, instance_id: str) -> str:
    label = card_label(state, instance_id)
    instance = state.card_instances.get(instance_id)
    if instance is None:
        return label
    card = card_data.cards_by_code().get(instance.card_code, {})
    parts: list[str] = []
    if instance.uses:
        parts.extend(f"{key} {value}" for key, value in sorted(instance.uses.items()))
    if card.get("slot") == "Ally" or instance.card_code == "01117":
        health = int(card.get("health") or 0)
        sanity = int(card.get("sanity") or 0)
        if health or sanity:
            parts.append(f"{instance.damage}/{health} dmg")
            parts.append(f"{instance.horror}/{sanity} horror")
    if instance.exhausted:
        parts.append("exhausted")
    if instance.attachments:
        parts.append("attachments " + ", ".join(card_label(state, card_id) for card_id in instance.attachments))
    return f"{label} [{', '.join(parts)}]" if parts else label


def threat_label(state: GameState, instance_id: str) -> str:
    label = card_label(state, instance_id)
    instance = state.card_instances.get(instance_id)
    if instance is None:
        return label
    parts: list[str] = []
    if instance.clues:
        parts.append(f"{instance.clues} clues")
    if instance.doom:
        parts.append(f"{instance.doom} doom")
    if instance.damage:
        parts.append(f"{instance.damage} damage")
    if instance.horror:
        parts.append(f"{instance.horror} horror")
    return f"{label} [{', '.join(parts)}]" if parts else label


def enemy_label(state: GameState, enemy_id: str) -> str:
    enemy = state.enemies[enemy_id]
    card = card_data.cards_by_code().get(enemy.card_code, {})
    health = int(card.get("enemy_health") or card.get("health") or 0)
    parts = [f"{enemy.damage}/{health} dmg" if health else f"{enemy.damage} dmg"]
    if enemy.doom:
        parts.append(f"{enemy.doom} doom")
    if enemy.exhausted:
        parts.append("exhausted")
    if enemy.engaged_with:
        parts.append("engaged")
    if enemy.attachments:
        parts.append("attachments " + ", ".join(card_label(state, card_id) for card_id in enemy.attachments))
    return f"{card.get('name', enemy.card_code)} [{', '.join(parts)}]"
