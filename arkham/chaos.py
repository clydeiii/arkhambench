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
        code = state.investigator.card_code
        if code == "01001":
            location = state.locations[state.investigator.location_id]
            return (location.clues, False)
        if code == "01003":
            return (2, False)
        if code == "01004":
            return (state.investigator.horror, False)
        return (0, False)
    if state.scenario == "the_gathering":
        if token == "skull":
            if state.difficulty in {"easy", "standard"}:
                from .scenarios import the_gathering

                return (-the_gathering.ghouls_at_roland_location(state), False)
            return (-2, False)
        if token == "cultist":
            return (-1 if state.difficulty in {"easy", "standard"} else 0, False)
        if token == "tablet":
            return (-2 if state.difficulty in {"easy", "standard"} else -4, False)
    if token in {"skull", "cultist", "tablet", "elderthing"}:
        modifiers = {"skull": -1, "cultist": -2, "tablet": -3, "elderthing": -4}
        return (modifiers[token], False)
    return (int(token), False)
