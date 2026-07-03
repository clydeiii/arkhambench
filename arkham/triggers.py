"""Trigger window placeholders for phase B."""
from __future__ import annotations

from typing import Any

from .model import DecisionOption, GameState, PendingDecision


def once_per_round_available(state: GameState, key: str) -> bool:
    return not bool(state.limits.get(f"once:{state.round}:{key}"))


def mark_once_per_round(state: GameState, key: str) -> None:
    state.limits[f"once:{state.round}:{key}"] = True


def expire_round_limits(state: GameState) -> None:
    state.limits = {key: value for key, value in state.limits.items() if not str(key).startswith("once:")}


def present_window(state: GameState, *, window: str, options: list[DecisionOption]) -> bool:
    if not options:
        return False
    state.decision_queue = [
        PendingDecision(
            id=f"window-{window}",
            kind="choose_option",
            prompt=f"[Round {state.round} · {state.phase} · Roland Banks] Choose an optional trigger for {window}.",
            options=options + [DecisionOption("Pass", {"kind": "window_pass", "window": window})],
        )
    ]
    return True
