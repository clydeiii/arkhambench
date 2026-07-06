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


from . import the_devourer_below, the_gathering, the_midnight_masks


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
    "the_midnight_masks": ScenarioDef(
        id="the_midnight_masks",
        build_state=the_midnight_masks.build_state,
        resolve_choice=the_midnight_masks.resolve_scenario_choice,
    ),
    "return_to_the_midnight_masks": ScenarioDef(
        id="return_to_the_midnight_masks",
        build_state=the_midnight_masks.build_return_state,
        resolve_choice=the_midnight_masks.resolve_scenario_choice,
    ),
    "the_devourer_below": ScenarioDef(
        id="the_devourer_below",
        build_state=the_devourer_below.build_state,
        resolve_choice=the_devourer_below.resolve_scenario_choice,
    ),
    "return_to_the_devourer_below": ScenarioDef(
        id="return_to_the_devourer_below",
        build_state=the_devourer_below.build_state,
        resolve_choice=the_devourer_below.resolve_scenario_choice,
    ),
}
