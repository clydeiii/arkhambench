"""Player card helpers and registrations for the Roland starter deck."""
from __future__ import annotations

from typing import Any

from .. import data as card_data
from ..model import CardInstance, DecisionOption, GameState
from .registry import card


PLAYER_CARD_CODES = [
    "01001",
    "01002",
    "01003",
    "01004",
    "01005",
    "01008",
    "01009",
    "01012",
    "01013",
    "01006",
    "01007",
    "01102",
    "01016",
    "01017",
    "01018",
    "01019",
    "01020",
    "01021",
    "01022",
    "01023",
    "01024",
    "01025",
    "01030",
    "01031",
    "01032",
    "01033",
    "01034",
    "01035",
    "01036",
    "01037",
    "01038",
    "01039",
    "01010",
    "01011",
    "01044",
    "01045",
    "01047",
    "01049",
    "01050",
    "01052",
    "01053",
    "01058",
    "01059",
    "01060",
    "01061",
    "01062",
    "01063",
    "01064",
    "01065",
    "01066",
    "01067",
    "01072",
    "01074",
    "01076",
    "01080",
    "01086",
    "01087",
    "01088",
    "01089",
    "01090",
    "01091",
    "01092",
    "01093",
    "01096",
    "01097",
    "01098",
    "01101",
]


class PlayerCard:
    """Marker base class for registered player card implementations."""


for _code in PLAYER_CARD_CODES:
    card(_code)(type(f"PlayerCard{_code}", (PlayerCard,), {"code": _code}))


def card_name(state: GameState, instance_id: str) -> str:
    instance = state.card_instances[instance_id]
    return str(card_data.get_card(instance.card_code).get("name", instance.card_code))


def ids_with_code(state: GameState, code: str, zones: set[str] | None = None) -> list[str]:
    result: list[str] = []
    for instance_id, instance in state.card_instances.items():
        if instance.card_code != code:
            continue
        if zones is not None and instance.zone not in zones:
            continue
        result.append(instance_id)
    return sorted(result)


def play_area_ids(state: GameState, code: str) -> list[str]:
    return [
        instance_id
        for instance_id in state.investigator.play_area
        if state.card_instances[instance_id].card_code == code
    ]


def threat_ids(state: GameState, code: str) -> list[str]:
    return [
        instance_id
        for instance_id in state.investigator.threat_area
        if state.card_instances[instance_id].card_code == code
    ]


def hand_ids(state: GameState, code: str) -> list[str]:
    return [
        instance_id
        for instance_id in state.investigator.hand
        if state.card_instances[instance_id].card_code == code
    ]


def controls_code(state: GameState, code: str) -> bool:
    return bool(play_area_ids(state, code))


def setup_uses(instance: CardInstance) -> None:
    if instance.card_code in {"01006", "01016"}:
        instance.uses["ammo"] = 4
    elif instance.card_code == "01047":
        instance.uses["ammo"] = 3
    elif instance.card_code == "01087":
        instance.uses["supplies"] = 3
    elif instance.card_code == "01019":
        instance.uses["supplies"] = 3
    elif instance.card_code == "01058":
        instance.uses["secrets"] = 4
    elif instance.card_code == "01060":
        instance.uses["charges"] = 4
    elif instance.card_code == "01061":
        instance.uses["charges"] = 3


def discard_from_play(state: GameState, instance_id: str) -> None:
    if instance_id in state.investigator.play_area:
        state.investigator.play_area.remove(instance_id)
    instance = state.card_instances[instance_id]
    instance.zone = "discard"
    if instance_id not in state.investigator.discard:
        state.investigator.discard.append(instance_id)


def discard_from_threat(state: GameState, instance_id: str) -> None:
    if instance_id in state.investigator.threat_area:
        state.investigator.threat_area.remove(instance_id)
    instance = state.card_instances[instance_id]
    instance.zone = "discard"
    if instance_id not in state.investigator.discard:
        state.investigator.discard.append(instance_id)


def discard_from_hand(state: GameState, instance_id: str) -> None:
    if instance_id in state.investigator.hand:
        state.investigator.hand.remove(instance_id)
    state.card_instances[instance_id].zone = "discard"
    if instance_id not in state.investigator.discard:
        state.investigator.discard.append(instance_id)


def static_skill_bonus(state: GameState, skill: str, source: str) -> int:
    bonus = 0
    if any(state.card_instances[instance_id].card_code == "01098" for instance_id in state.investigator.threat_area):
        bonus -= 1
    if skill == "combat":
        if controls_code(state, "01018"):
            bonus += 1
        if lita_controlled_at_roland_location(state):
            bonus += 1
    if skill == "willpower":
        if controls_code(state, "01059"):
            bonus += 1
    if skill == "intellect":
        if controls_code(state, "01033"):
            bonus += 1
        if source.startswith("Investigate") and controls_code(state, "01030"):
            bonus += 1
    return bonus


def effective_base_skill(state: GameState, skill: str, source: str) -> int:
    base_skill = skill
    if (
        skill in {"combat", "agility"}
        and state.limits.get(f"mind_over_matter:{state.round}")
    ):
        base_skill = "intellect"
    return int(getattr(state.investigator, base_skill)) + static_skill_bonus(
        state, base_skill, source
    )


def boost_options(state: GameState) -> list[DecisionOption]:
    test = state.active_skill_test
    if not test or state.investigator.resources <= 0:
        return []
    skill = str(test["skill"])
    options: list[DecisionOption] = []
    if controls_code(state, "01017") and skill in {"willpower", "combat"}:
        options.append(
            DecisionOption(
                f"Spend 1 resource with Physical Training (+1 {skill})",
                {"kind": "skill_boost", "card_code": "01017", "skill": skill},
            )
        )
    if controls_code(state, "01062") and skill in {"willpower", "intellect"}:
        options.append(
            DecisionOption(
                f"Spend 1 resource with Arcane Studies (+1 {skill})",
                {"kind": "skill_boost", "card_code": "01062", "skill": skill},
            )
        )
    if controls_code(state, "01034") and skill in {"intellect", "agility"}:
        options.append(
            DecisionOption(
                f"Spend 1 resource with Hyperawareness (+1 {skill})",
                {"kind": "skill_boost", "card_code": "01034", "skill": skill},
            )
        )
    if controls_code(state, "01049") and skill in {"combat", "agility"}:
        options.append(
            DecisionOption(
                f"Spend 1 resource with Hard Knocks (+1 {skill})",
                {"kind": "skill_boost", "card_code": "01049", "skill": skill},
            )
        )
    return options


def apply_boost(state: GameState, card_code: str, skill: str) -> bool:
    test = state.active_skill_test
    if not test or state.investigator.resources <= 0:
        return False
    if str(test["skill"]) != skill:
        return False
    if card_code == "01017" and skill not in {"willpower", "combat"}:
        return False
    if card_code == "01062" and skill not in {"willpower", "intellect"}:
        return False
    if card_code == "01034" and skill not in {"intellect", "agility"}:
        return False
    if card_code == "01049" and skill not in {"combat", "agility"}:
        return False
    if not controls_code(state, card_code):
        return False
    state.investigator.resources -= 1
    boosts = test.setdefault("boosts", [])
    boosts.append({"card_code": card_code, "skill": skill, "amount": 1})
    return True


def boost_total(test: dict[str, Any]) -> int:
    return sum(int(item.get("amount", 0)) for item in test.get("boosts", []))


def committed_codes(state: GameState) -> list[str]:
    test = state.active_skill_test or {}
    return [
        state.card_instances[instance_id].card_code
        for instance_id in test.get("committed", [])
        if instance_id in state.card_instances
    ]


def max_one_committed_already(state: GameState, code: str) -> bool:
    return code in {"01089", "01090", "01091", "01092", "01093"} and code in committed_codes(state)


def lita_controlled_at_roland_location(state: GameState) -> bool:
    for instance_id in play_area_ids(state, "01117"):
        instance = state.card_instances[instance_id]
        if instance.owner == state.investigator.id:
            return True
    return False


def lita_uncontrolled_at_location(state: GameState, location_id: str) -> str | None:
    for instance_id, instance in sorted(state.card_instances.items()):
        if instance.card_code != "01117" or instance.zone != "story":
            continue
        if instance_id in state.locations[location_id].attached_instance_ids:
            return instance_id
    return None


def roland_location_has_clues(state: GameState) -> bool:
    return state.locations[state.investigator.location_id].clues > 0


def controlled_tome_count(state: GameState) -> int:
    count = 0
    for instance_id in state.investigator.play_area:
        card = card_data.get_card(state.card_instances[instance_id].card_code)
        if card.get("type_code") == "asset" and "Tome" in str(card.get("traits", "")):
            count += 1
    return count


def is_tome_asset_code(card_code: str) -> bool:
    card = card_data.get_card(card_code)
    return card.get("type_code") == "asset" and "Tome" in str(card.get("traits", ""))


def has_cultist_at_roland_location(state: GameState) -> bool:
    location = state.locations[state.investigator.location_id]
    for enemy_id in location.enemy_ids:
        enemy = state.enemies.get(enemy_id)
        if not enemy:
            continue
        traits = str(card_data.get_card(enemy.card_code).get("traits", ""))
        if "Cultist" in traits:
            return True
    return False


def monster_enemy(state: GameState, enemy_id: str) -> bool:
    enemy = state.enemies.get(enemy_id)
    if not enemy:
        return False
    return "Monster" in str(card_data.get_card(enemy.card_code).get("traits", ""))
