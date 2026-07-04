"""Scenario implementation package."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..model import GameState
from ..rng import ArkhamRng


@dataclass(frozen=True)
class ScenarioDef:
    id: str
    build_state: Callable[..., GameState]
    resolve_choice: Callable[..., None]


from . import the_gathering


SCENARIOS: dict[str, ScenarioDef] = {
    "the_gathering": ScenarioDef(
        id="the_gathering",
        build_state=the_gathering.build_gathering_state,
        resolve_choice=the_gathering.resolve_scenario_choice,
    )
}
