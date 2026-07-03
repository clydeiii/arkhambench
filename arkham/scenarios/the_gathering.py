"""The Gathering scenario implementation will be added in later phases."""
from __future__ import annotations

from typing import Any

from .. import data as card_data
from ..model import ActState, AgendaState, CardInstance, ChaosBag, GameState, Investigator, Location, PendingDecision, TurnState
from ..rng import ArkhamRng


CHAOS_BAGS: dict[str, list[str]] = {
    "easy": ["+1", "+1", "0", "0", "0", "-1", "-1", "-1", "-2", "-2", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
    "standard": ["+1", "0", "0", "-1", "-1", "-1", "-2", "-2", "-3", "-4", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
    "hard": ["0", "0", "0", "-1", "-1", "-2", "-2", "-3", "-3", "-4", "-5", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
    "expert": ["0", "-1", "-1", "-2", "-2", "-3", "-3", "-4", "-4", "-5", "-6", "-8", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
}


ENGINE_TEST_PLAYER_CODES = [
    "01016",
    "01020",
    "01018",
    "01019",
    "01021",
    "01022",
    "01023",
    "01030",
    "01087",
    "01088",
]

ENGINE_TEST_ENCOUNTER_CODES = [
    "01163",
    "01166",
    "01180",
    "01172",
    "01163",
]


def build_engine_test_state(*, difficulty: str, rng: ArkhamRng) -> GameState:
    cards = card_data.cards_by_code()
    investigator_card = cards["01001"]
    instances: dict[str, CardInstance] = {}
    deck_ids: list[str] = []
    for index, code in enumerate(ENGINE_TEST_PLAYER_CODES, start=1):
        instance_id = f"pc{index:04d}"
        instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="player_deck")
        deck_ids.append(instance_id)
    rng.shuffle(deck_ids)
    hand = deck_ids[:5]
    player_deck = deck_ids[5:]
    for instance_id in hand:
        instances[instance_id].zone = "hand"

    encounter_ids: list[str] = []
    for index, code in enumerate(ENGINE_TEST_ENCOUNTER_CODES, start=1):
        instance_id = f"ec{index:04d}"
        instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="encounter_deck")
        encounter_ids.append(instance_id)
    rng.shuffle(encounter_ids)

    investigator = Investigator(
        id="roland",
        name=str(investigator_card["name"]),
        card_code=str(investigator_card["code"]),
        location_id="study",
        willpower=int(investigator_card["skill_willpower"]),
        intellect=int(investigator_card["skill_intellect"]),
        combat=int(investigator_card["skill_combat"]),
        agility=int(investigator_card["skill_agility"]),
        health=int(investigator_card["health"]),
        sanity=int(investigator_card["sanity"]),
        resources=5,
        actions_remaining=3,
        hand=hand,
        deck=player_deck,
    )
    return GameState(
        schema_version=2,
        scenario="engine_test",
        difficulty=difficulty,
        status="in_progress",
        round=1,
        phase="Investigation",
        turn=TurnState(investigator_id="roland", action_index=0),
        investigator=investigator,
        card_instances=instances,
        locations={
            "study": Location(id="study", code="01111", name="Study", revealed=True, shroud=2, clues=2, connections=["hallway"], investigator_ids=["roland"]),
            "hallway": Location(id="hallway", code="01112", name="Hallway", revealed=True, shroud=1, clues=0, connections=["study", "attic", "cellar"]),
            "attic": Location(id="attic", code="01113", name="Attic", revealed=True, shroud=1, clues=2, connections=["hallway"]),
            "cellar": Location(id="cellar", code="01114", name="Cellar", revealed=True, shroud=4, clues=2, connections=["hallway"]),
        },
        agenda=AgendaState(code="phaseb_agenda_1", name="What's Going On?!", stage=1, threshold=3),
        act=ActState(code="phaseb_act_1", name="Trapped", stage=1, clues_required=2),
        chaos_bag=ChaosBag(tokens=list(CHAOS_BAGS[difficulty])),
        encounter_deck=encounter_ids,
        decision_queue=[],
    )
