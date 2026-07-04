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
    ),
    # Return to The Gathering shares The Gathering's acts 2-3, agendas,
    # resolutions, scoring, and token effects; only setup, the location
    # graph, act 1, and the Ghouls-set swap differ (scenario card 50011).
    "return_to_the_gathering": ScenarioDef(
        id="return_to_the_gathering",
        build_state=the_gathering.build_return_state,
        resolve_choice=the_gathering.resolve_scenario_choice,
    ),
}
