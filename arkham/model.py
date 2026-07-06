from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


# Scenarios sharing The Gathering engine hooks (agenda/act/token/resolution logic).
GATHERING_FAMILY = {"the_gathering", "return_to_the_gathering"}
MIDNIGHT_MASKS_FAMILY = {"the_midnight_masks", "return_to_the_midnight_masks"}
DEVOURER_FAMILY = {"the_devourer_below", "return_to_the_devourer_below"}

JsonDict = dict[str, Any]


@dataclass
class DecisionOption:
    label: str
    payload: JsonDict = field(default_factory=dict)

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "DecisionOption":
        return cls(label=str(data["label"]), payload=dict(data.get("payload", {})))


@dataclass
class PendingDecision:
    id: str
    prompt: str
    options: list[DecisionOption] = field(default_factory=list)
    kind: str = "choose_option"

    def to_dict(self) -> JsonDict:
        return {
            "id": self.id,
            "kind": self.kind,
            "prompt": self.prompt,
            "options": [option.to_dict() for option in self.options],
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "PendingDecision":
        return cls(
            id=str(data["id"]),
            kind=str(data.get("kind", "choose_option")),
            prompt=str(data["prompt"]),
            options=[DecisionOption.from_dict(item) for item in data.get("options", [])],
        )


@dataclass
class Investigator:
    id: str
    name: str
    card_code: str
    location_id: str
    willpower: int
    intellect: int
    combat: int
    agility: int
    health: int
    sanity: int
    damage: int = 0
    horror: int = 0
    resources: int = 0
    clues: int = 0
    actions_remaining: int = 0
    exhausted: bool = False
    hand: list[str] = field(default_factory=list)
    deck: list[str] = field(default_factory=list)
    discard: list[str] = field(default_factory=list)
    play_area: list[str] = field(default_factory=list)
    threat_area: list[str] = field(default_factory=list)
    engaged_enemies: list[str] = field(default_factory=list)

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "Investigator":
        return cls(**data)


@dataclass
class CardInstance:
    id: str
    card_code: str
    zone: str
    owner: str = "roland"
    exhausted: bool = False
    uses: dict[str, int] = field(default_factory=dict)
    damage: int = 0
    horror: int = 0
    clues: int = 0
    doom: int = 0
    attachments: list[str] = field(default_factory=list)

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "CardInstance":
        return cls(**data)


@dataclass
class Location:
    id: str
    code: str
    name: str
    revealed: bool = False
    shroud: int | None = None
    clues: int = 0
    connections: list[str] = field(default_factory=list)
    attached_instance_ids: list[str] = field(default_factory=list)
    investigator_ids: list[str] = field(default_factory=list)
    enemy_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "Location":
        return cls(**data)


@dataclass
class EnemyInstance:
    id: str
    card_code: str
    location_id: str
    engaged_with: str | None = None
    exhausted: bool = False
    damage: int = 0
    horror: int = 0
    clues: int = 0
    doom: int = 0
    attachments: list[str] = field(default_factory=list)

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "EnemyInstance":
        return cls(**data)


@dataclass
class AgendaState:
    code: str
    name: str
    stage: int
    doom: int = 0
    threshold: int = 0

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "AgendaState":
        return cls(**data)


@dataclass
class ActState:
    code: str
    name: str
    stage: int
    clues_required: int | None = None

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "ActState":
        return cls(**data)


@dataclass
class ChaosBag:
    tokens: list[str] = field(default_factory=list)

    def to_dict(self) -> JsonDict:
        return {"tokens": list(self.tokens)}

    @classmethod
    def from_dict(cls, data: JsonDict) -> "ChaosBag":
        return cls(tokens=list(data.get("tokens", [])))


@dataclass
class TurnState:
    investigator_id: str = "roland"
    action_index: int = 0

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "TurnState":
        return cls(**data)


@dataclass
class GameState:
    schema_version: int
    scenario: str
    difficulty: str
    status: str
    round: int
    phase: str
    turn: TurnState
    investigator: Investigator
    card_instances: dict[str, CardInstance] = field(default_factory=dict)
    locations: dict[str, Location] = field(default_factory=dict)
    enemies: dict[str, EnemyInstance] = field(default_factory=dict)
    agenda: AgendaState | None = None
    act: ActState | None = None
    chaos_bag: ChaosBag = field(default_factory=ChaosBag)
    victory_display: list[str] = field(default_factory=list)
    decision_queue: list[PendingDecision] = field(default_factory=list)
    encounter_deck: list[str] = field(default_factory=list)
    encounter_discard: list[str] = field(default_factory=list)
    removed_from_game: list[str] = field(default_factory=list)
    active_skill_test: JsonDict | None = None
    pending_damage: JsonDict | None = None
    limits: JsonDict = field(default_factory=dict)
    trauma: JsonDict = field(default_factory=dict)
    result: JsonDict | None = None

    def to_dict(self) -> JsonDict:
        return {
            "schema_version": self.schema_version,
            "scenario": self.scenario,
            "difficulty": self.difficulty,
            "status": self.status,
            "round": self.round,
            "phase": self.phase,
            "turn": self.turn.to_dict(),
            "investigator": self.investigator.to_dict(),
            "card_instances": {
                key: value.to_dict() for key, value in sorted(self.card_instances.items())
            },
            "locations": {
                key: value.to_dict() for key, value in sorted(self.locations.items())
            },
            "enemies": {key: value.to_dict() for key, value in sorted(self.enemies.items())},
            "agenda": self.agenda.to_dict() if self.agenda else None,
            "act": self.act.to_dict() if self.act else None,
            "chaos_bag": self.chaos_bag.to_dict(),
            "victory_display": list(self.victory_display),
            "decision_queue": [decision.to_dict() for decision in self.decision_queue],
            "encounter_deck": list(self.encounter_deck),
            "encounter_discard": list(self.encounter_discard),
            "removed_from_game": list(self.removed_from_game),
            "active_skill_test": self.active_skill_test,
            "pending_damage": self.pending_damage,
            "limits": dict(self.limits),
            "trauma": dict(self.trauma),
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "GameState":
        return cls(
            schema_version=int(data["schema_version"]),
            scenario=str(data["scenario"]),
            difficulty=str(data["difficulty"]),
            status=str(data["status"]),
            round=int(data["round"]),
            phase=str(data["phase"]),
            turn=TurnState.from_dict(data["turn"]),
            investigator=Investigator.from_dict(data["investigator"]),
            card_instances={
                key: CardInstance.from_dict(value)
                for key, value in data.get("card_instances", {}).items()
            },
            locations={
                key: Location.from_dict(value)
                for key, value in data.get("locations", {}).items()
            },
            enemies={
                key: EnemyInstance.from_dict(value)
                for key, value in data.get("enemies", {}).items()
            },
            agenda=AgendaState.from_dict(data["agenda"]) if data.get("agenda") else None,
            act=ActState.from_dict(data["act"]) if data.get("act") else None,
            chaos_bag=ChaosBag.from_dict(data.get("chaos_bag", {})),
            victory_display=list(data.get("victory_display", [])),
            decision_queue=[
                PendingDecision.from_dict(item) for item in data.get("decision_queue", [])
            ],
            encounter_deck=list(data.get("encounter_deck", [])),
            encounter_discard=list(data.get("encounter_discard", [])),
            removed_from_game=list(data.get("removed_from_game", [])),
            active_skill_test=data.get("active_skill_test"),
            pending_damage=data.get("pending_damage"),
            limits=dict(data.get("limits", {})),
            trauma=dict(data.get("trauma", {})),
            result=data.get("result"),
        )

    def public_dict(self) -> JsonDict:
        data = self.to_dict()
        investigator = dict(data["investigator"])
        investigator.pop("deck", None)
        investigator["deck_count"] = len(self.investigator.deck)
        data["encounter_deck"] = []
        data["encounter_deck_count"] = len(self.encounter_deck)
        visible_ids = set(investigator["hand"])
        visible_ids.update(investigator["discard"])
        visible_ids.update(investigator["play_area"])
        visible_ids.update(investigator["threat_area"])
        visible_ids.update(self.victory_display)
        visible_ids.update(self.encounter_discard)
        visible_ids.update(self.removed_from_game)
        for location in self.locations.values():
            visible_ids.update(location.attached_instance_ids)
        for enemy in self.enemies.values():
            visible_ids.update(enemy.attachments)
        data["investigator"] = investigator
        data["card_instances"] = {
            key: value.to_dict()
            for key, value in sorted(self.card_instances.items())
            if key in visible_ids
        }
        return data
