"""Chaos bag helpers will be implemented in phase B."""
from __future__ import annotations

from .model import GameState
from .rng import ArkhamRng


def draw_token(state: GameState, rng: ArkhamRng) -> str:
    """Draw a chaos token with replacement."""
    if not state.chaos_bag.tokens:
        raise ValueError("chaos bag is empty")
    return rng.choice(state.chaos_bag.tokens)


def token_modifier(state: GameState, token: str) -> tuple[int, bool]:
    if token == "autofail":
        return (0, True)
    if token == "eldersign":
        location = state.locations[state.investigator.location_id]
        return (location.clues, False)
    if token in {"skull", "cultist", "tablet", "elderthing"}:
        modifiers = {"skull": -1, "cultist": -2, "tablet": -3, "elderthing": -4}
        return (modifiers[token], False)
    return (int(token), False)
