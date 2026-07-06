from __future__ import annotations

from typing import Any

from ..errors import EngineError
from ..model import GameState
from ..rng import ArkhamRng


def build_state(**kwargs: Any) -> GameState:
    raise EngineError("The Devourer Below is not implemented until phase C3")


def resolve_scenario_choice(
    state: GameState,
    payload: dict[str, Any],
    events: list[dict[str, Any]],
    rng: ArkhamRng,
) -> None:
    raise EngineError("The Devourer Below is not implemented until phase C3")
