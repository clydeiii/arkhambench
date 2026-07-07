"""The Midnight Masks and Return to The Midnight Masks."""
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any

from .. import data as card_data
from ..cards import player as player_cards
from ..cards.player import card_name
from ..cards.registry import REGISTRY
from ..errors import EngineError
from ..model import (
    ActState,
    AgendaState,
    CardInstance,
    ChaosBag,
    DecisionOption,
    GameState,
    Investigator,
    Location,
    PendingDecision,
    TurnState,
)
from ..rng import ArkhamRng
from .the_gathering import (
    CHAOS_BAGS,
    build_player_deck,
    draw_opening_hand_without_weaknesses,
    hospital_debts_xp_penalty,
    present_mulligan_decision,
    resolve_mulligan_replacements,
    starting_actions,
    toggle_mulligan_card,
    total_trauma,
)


RETURN_SCENARIO = "return_to_the_midnight_masks"
MIDNIGHT_FAMILY = {"the_midnight_masks", RETURN_SCENARIO}

ENCOUNTER_COUNTS = {
    "01135": 3,
    "01136": 2,
    "01169": 3,
    "01170": 1,
    "01171": 2,
    "01172": 2,
    "01173": 2,
    "01167": 2,
    "01168": 2,
    "01174": 2,
}
RETURN_ENCOUNTER_COUNTS = {
    "01135": 3,
    "01136": 2,
    "50041": 3,
    "50042": 1,
    "50043": 2,
    "01172": 2,
    "01173": 2,
    "01167": 2,
    "01168": 2,
    "01174": 2,
    "50031": 2,
}
CORE_CULTISTS = ["01137", "01138", "01139", "01140", "01141"]
RETURN_CULTISTS = ["50044", "50045", "50046"]
UNIQUE_CULTIST_CODES = set(CORE_CULTISTS + RETURN_CULTISTS + ["01121b", "50026b"])

LOCATION_CONNECTIONS = {
    "your_house": ["rivertown"],
    "rivertown": ["your_house", "easttown", "southside", "miskatonic_university", "graveyard"],
    "southside": ["rivertown", "miskatonic_university", "st_marys_hospital"],
    "st_marys_hospital": ["southside", "miskatonic_university"],
    "miskatonic_university": ["rivertown", "southside", "st_marys_hospital", "northside"],
    "downtown": ["easttown", "northside"],
    "easttown": ["rivertown", "downtown"],
    "graveyard": ["rivertown"],
    "northside": ["downtown", "miskatonic_university"],
}
BASE_LOCATION_CODES = {
    "your_house": "01124",
    "rivertown": "01125",
    "southside": "01126",
    "st_marys_hospital": "01128",
    "miskatonic_university": "01129",
    "downtown": "01130",
    "easttown": "01132",
    "graveyard": "01133",
    "northside": "01134",
}
RETURN_LOCATION_CODES = {
    "rivertown": "50030",
    "miskatonic_university": "50029",
    "easttown": "50027",
    "northside": "50028",
}
SOUTHSIDE_CODES = ["01126", "01127"]
DOWNTOWN_CODES = ["01130", "01131"]
CULTIST_SPAWNS = {
    "01137": "downtown",
    "01138": "graveyard",
    "01139": "miskatonic_university",
    "01140": "northside",
    "01141": "st_marys_hospital",
    "50044": "your_house",
    "50045": "easttown",
    "50046": "southside",
}


def is_return(state: GameState) -> bool:
    return state.scenario == RETURN_SCENARIO


def build_state(
    *,
    difficulty: str,
    rng: ArkhamRng,
    deck_path: str | Path | None = None,
    investigator_slug: str = "roland",
    house_burned: bool = False,
    ghoul_priest_alive: bool = False,
    lita_forced_to_find_others: bool = False,
) -> GameState:
    return build_midnight_state(
        difficulty=difficulty,
        rng=rng,
        deck_path=deck_path,
        investigator_slug=investigator_slug,
        scenario="the_midnight_masks",
        house_burned=house_burned,
        ghoul_priest_alive=ghoul_priest_alive,
        lita_forced_to_find_others=lita_forced_to_find_others,
    )


def build_return_state(
    *,
    difficulty: str,
    rng: ArkhamRng,
    deck_path: str | Path | None = None,
    investigator_slug: str = "roland",
    house_burned: bool = False,
    ghoul_priest_alive: bool = False,
    lita_forced_to_find_others: bool = False,
) -> GameState:
    return build_midnight_state(
        difficulty=difficulty,
        rng=rng,
        deck_path=deck_path,
        investigator_slug=investigator_slug,
        scenario=RETURN_SCENARIO,
        house_burned=house_burned,
        ghoul_priest_alive=ghoul_priest_alive,
        lita_forced_to_find_others=lita_forced_to_find_others,
    )


def build_midnight_state(
    *,
    difficulty: str,
    rng: ArkhamRng,
    deck_path: str | Path | None,
    investigator_slug: str,
    scenario: str,
    house_burned: bool,
    ghoul_priest_alive: bool,
    lita_forced_to_find_others: bool,
) -> GameState:
    cards = card_data.cards_by_code()
    if investigator_slug not in card_data.INVESTIGATOR_CODES:
        raise EngineError(f"unknown investigator: {investigator_slug}")
    investigator_code = card_data.INVESTIGATOR_CODES[investigator_slug]
    investigator_card = cards[investigator_code]
    instances: dict[str, CardInstance] = {}

    player_deck = build_player_deck(instances, deck_path, investigator_slug=investigator_slug)
    rng.shuffle(player_deck)
    hand, player_deck = draw_opening_hand_without_weaknesses(instances, player_deck, rng)

    return_variant = scenario == RETURN_SCENARIO
    encounter_deck = build_encounter_deck(instances, return_variant=return_variant)
    if ghoul_priest_alive:
        priest_id = next_encounter_id(instances)
        instances[priest_id] = CardInstance(id=priest_id, card_code="01116", zone="encounter_deck")
        encounter_deck.append(priest_id)
    else:
        instances["setaside_ghoul_priest"] = CardInstance(id="setaside_ghoul_priest", card_code="01116", zone="set_aside")
    rng.shuffle(encounter_deck)

    agenda1 = "01121a"
    if return_variant:
        agenda1 = rng.choice(["01121a", "50026a"])
    agenda_enemy = "50026b" if agenda1 == "50026a" else "01121b"
    instances["setaside_agenda_enemy"] = CardInstance(id="setaside_agenda_enemy", card_code=agenda_enemy, zone="set_aside")

    cultist_deck = build_cultist_deck(instances, rng, return_variant=return_variant)
    locations = build_locations(rng=rng, return_variant=return_variant, house_burned=house_burned)
    start_location = "rivertown" if house_burned else "your_house"
    locations[start_location].revealed = True
    locations[start_location].name = location_revealed_name(locations[start_location].code)
    locations[start_location].shroud = int(cards[locations[start_location].code].get("shroud") or 0)
    locations[start_location].clues = int(cards[locations[start_location].code].get("clues") or 0)
    locations[start_location].investigator_ids.append(investigator_slug)

    investigator = Investigator(
        id=investigator_slug,
        name=str(investigator_card["name"]),
        card_code=str(investigator_card["code"]),
        location_id=start_location,
        willpower=int(investigator_card["skill_willpower"]),
        intellect=int(investigator_card["skill_intellect"]),
        combat=int(investigator_card["skill_combat"]),
        agility=int(investigator_card["skill_agility"]),
        health=int(investigator_card["health"]),
        sanity=int(investigator_card["sanity"]),
        resources=5,
        actions_remaining=starting_actions(investigator_code),
        hand=hand,
        deck=player_deck,
    )
    state = GameState(
        schema_version=2,
        scenario=scenario,
        difficulty=difficulty,
        status="in_progress",
        round=1,
        phase="Investigation",
        turn=TurnState(investigator_id=investigator_slug, action_index=0),
        investigator=investigator,
        card_instances=instances,
        locations=locations,
        agenda=AgendaState(code=agenda1, name="Predator or Prey?", stage=1, threshold=6),
        act=ActState(code="01123", name="Uncovering the Conspiracy", stage=1, clues_required=None),
        chaos_bag=ChaosBag(tokens=list(CHAOS_BAGS[difficulty])),
        encounter_deck=encounter_deck,
    )
    state.limits["cultist_deck"] = cultist_deck
    state.limits["campaign_inputs"] = {
        "house_burned": house_burned,
        "ghoul_priest_alive": ghoul_priest_alive,
        "lita_forced": lita_forced_to_find_others,
    }
    state.limits["agenda1_enemy_code"] = agenda_enemy
    state.limits["mulligan_available"] = list(hand)
    present_mulligan_decision(state)
    return state


def next_encounter_id(instances: dict[str, CardInstance]) -> str:
    used = [int(key[2:]) for key in instances if key.startswith("ec") and key[2:].isdigit()]
    return f"ec{(max(used) if used else 0) + 1:04d}"


def build_encounter_deck(instances: dict[str, CardInstance], *, return_variant: bool) -> list[str]:
    ids: list[str] = []
    counts = RETURN_ENCOUNTER_COUNTS if return_variant else ENCOUNTER_COUNTS
    index = 1
    for code, count in counts.items():
        for _ in range(count):
            instance_id = f"ec{index:04d}"
            instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="encounter_deck")
            ids.append(instance_id)
            index += 1
    return ids


def build_cultist_deck(instances: dict[str, CardInstance], rng: ArkhamRng, *, return_variant: bool) -> list[str]:
    codes = CORE_CULTISTS + (RETURN_CULTISTS if return_variant else [])
    ids: list[str] = []
    for index, code in enumerate(codes, start=1):
        instance_id = f"cult{index:02d}"
        instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="cultist_deck")
        ids.append(instance_id)
    rng.shuffle(ids)
    if return_variant:
        removed = ids[:3]
        ids = ids[3:]
        for card_id in removed:
            instances[card_id].zone = "removed_unseen"
    return ids


def build_locations(*, rng: ArkhamRng, return_variant: bool, house_burned: bool) -> dict[str, Location]:
    codes = dict(BASE_LOCATION_CODES)
    codes["southside"] = rng.choice(SOUTHSIDE_CODES)
    codes["downtown"] = rng.choice(DOWNTOWN_CODES)
    if return_variant:
        for location_id, return_code in RETURN_LOCATION_CODES.items():
            codes[location_id] = rng.choice([BASE_LOCATION_CODES[location_id], return_code])
    if house_burned:
        codes.pop("your_house", None)
    locations: dict[str, Location] = {}
    for location_id, code in codes.items():
        connections = [neighbor for neighbor in LOCATION_CONNECTIONS[location_id] if neighbor in codes]
        locations[location_id] = Location(
            id=location_id,
            code=code,
            name=location_unrevealed_name(code),
            revealed=False,
            shroud=None,
            clues=0,
            connections=connections,
        )
    return locations


def location_unrevealed_name(code: str) -> str:
    card = card_data.get_card(code)
    name = str(card.get("name", code))
    subname = str(card.get("subname") or "")
    return f"{name} ({subname})" if subname else name


def location_revealed_name(code: str) -> str:
    return location_unrevealed_name(code)


def reveal_location(state: GameState, events: list[dict[str, Any]], location_id: str) -> None:
    from ..effects import log_event

    location = state.locations[location_id]
    if location.revealed:
        return
    card = card_data.get_card(location.code)
    location.revealed = True
    location.name = location_revealed_name(location.code)
    location.shroud = int(card.get("shroud") or 0)
    location.clues = int(card.get("clues") or 0)
    log_event(events, "location_revealed", f"{location.name} was revealed.", location=location_id)


def after_enter_location(state: GameState, events: list[dict[str, Any]], location_id: str) -> None:
    reveal_location(state, events, location_id)
    if location_id == "graveyard":
        from .. import skill_test

        skill_test.start(
            state,
            events,
            skill="willpower",
            difficulty=3,
            source="Graveyard",
            on_failure={"kind": "graveyard"},
        )


def resolve_scenario_choice(
    state: GameState,
    payload: dict[str, Any],
    events: list[dict[str, Any]],
    rng: ArkhamRng,
) -> None:
    choice = str(payload.get("choice"))
    if choice == "keep_hand":
        from ..effects import log_event

        state.limits.pop("mulligan_available", None)
        selected = [str(card_id) for card_id in state.limits.pop("mulligan_selected", [])]
        drawn = resolve_mulligan_replacements(state, selected, rng)
        if selected:
            out_names = ", ".join(card_name(state, card_id) for card_id in selected)
            in_names = ", ".join(card_name(state, card_id) for card_id in drawn) if drawn else "nothing"
            log_event(events, "mulligan", f"Mulliganed {out_names}; drew {in_names}.", out=selected, drew=drawn)
        final_hand = ", ".join(card_name(state, cid) for cid in state.investigator.hand)
        log_event(events, "setup_complete", f"Opening hand finalized: {final_hand}.")
    elif choice in {"toggle_mulligan_card", "mulligan_card"}:
        toggle_mulligan_card(state, str(payload.get("card")))
        present_mulligan_decision(state)
    elif choice == "spawn_at_location":
        resolve_spawn_at_location(state, payload, events, rng)
    elif choice == "hunting_shadow_clue":
        from ..effects import spend_clues

        card_id = str(payload.get("card", ""))
        if spend_clues(state, 1, events):
            discard_encounter_card(state, card_id)
    elif choice == "hunting_shadow_damage":
        from ..effects import start_damage_assignment

        discard_encounter_card(state, str(payload.get("card", "")))
        start_damage_assignment(state, events, source="Hunting Shadow", damage=2, horror=0)
    elif choice == "mysterious_chanting_target":
        place_doom_on_enemy(state, str(payload.get("enemy", "")), 2, events, source="Mysterious Chanting", rng=rng)
        discard_encounter_card(state, str(payload.get("card", "")))
    elif choice == "mask_target":
        attach_mask_to_enemy(state, str(payload.get("card", "")), str(payload.get("enemy", "")), events, rng)
    elif choice == "disciple_doom":
        enemy_id = str(payload.get("enemy", ""))
        place_doom_on_enemy(state, enemy_id, 1, events, source="Disciple of the Devourer", rng=rng)
    elif choice == "disciple_clue":
        enemy_id = str(payload.get("enemy", ""))
        if enemy_id in state.enemies and state.investigator.clues > 0:
            state.investigator.clues -= 1
            state.locations[state.enemies[enemy_id].location_id].clues += 1
            from ..effects import log_event

            log_event(events, "clue_placed", "Disciple of the Devourer placed 1 clue on its location.", enemy=enemy_id)
    elif choice == "herman_discard":
        resolve_herman_discard_choice(state, payload, events)
    elif choice == "graveyard_horror":
        from ..effects import start_damage_assignment

        start_damage_assignment(state, events, source="Graveyard", damage=0, horror=2)
    elif choice == "graveyard_move":
        move_investigator_to(state, events, "rivertown")
    elif choice == "midnight_search_deck":
        resolve_search_deck_choice(state, payload, events, rng)
    elif choice == "midnight_search_top":
        resolve_search_top_choice(state, payload, events, rng)
    elif choice == "cultist_search_choice":
        resolve_cultist_search_choice(state, payload, events, rng)
    elif choice == "midnight_train_move":
        destination = str(payload.get("location", ""))
        if destination in state.locations:
            move_investigator_to(state, events, destination)
    elif choice == "midnight_warehouse_card":
        resolve_warehouse_card_choice(state, payload, events)
    elif choice == "midnight_warehouse_enemy":
        resolve_warehouse_enemy_choice(state, payload, events)
    elif choice == "on_wings_continue":
        on_wings_disengage_and_move(state, events)


def add_action_options(state: GameState, options: list[DecisionOption]) -> None:
    if state.status != "in_progress":
        return
    if state.act and state.act.code == "01123" and state.investigator.clues >= 2 and state.limits.get("cultist_deck") and not masked_hunter_blocks_clues(state):
        options.append(DecisionOption("Spend 2 clues to draw from the Cultist deck", {"kind": "action", "action": "midnight_cultist_draw"}))
    for enemy_id in cultist_enemies_at_investigator_location(state):
        code = state.enemies[enemy_id].card_code
        if narogath_blocks_parley(state, enemy_id):
            continue
        if code == "01138" and len(state.investigator.hand) >= 4:
            options.append(DecisionOption("Parley with Herman Collins (discard 4 cards)", {"kind": "action", "action": "midnight_parley", "enemy": enemy_id}))
        elif code == "01139" and state.investigator.clues >= 2 and not masked_hunter_blocks_clues(state):
            options.append(DecisionOption("Parley with Peter Warren (spend 2 clues)", {"kind": "action", "action": "midnight_parley", "enemy": enemy_id}))
        elif code == "01140" and state.investigator.resources >= 5:
            options.append(DecisionOption("Parley with Victoria Devereux (spend 5 resources)", {"kind": "action", "action": "midnight_parley", "enemy": enemy_id}))
        elif code == "50044":
            options.append(DecisionOption("Parley with Jeremiah Pierce", {"kind": "action", "action": "midnight_parley", "enemy": enemy_id}))
        elif code == "50046":
            options.append(DecisionOption("Parley with Alma Hill", {"kind": "action", "action": "midnight_parley", "enemy": enemy_id}))
    if state.agenda and state.agenda.code in {"01121a", "50026a", "01122"}:
        options.append(DecisionOption("Resign", {"kind": "action", "action": "resign"}))
    add_location_action_options(state, options)


def add_location_action_options(state: GameState, options: list[DecisionOption]) -> None:
    location = state.locations[state.investigator.location_id]
    code = location.code
    if code == "01124" and not limit_used(state, location.id, per_turn=True):
        options.append(DecisionOption("Your House: draw 1 card and gain 1 resource", {"kind": "action", "action": "midnight_location_your_house"}))
    elif code == "01126" and not limit_used(state, location.id):
        options.append(DecisionOption("Historical Society: draw 3 cards", {"kind": "action", "action": "midnight_location_historical_society"}))
    elif code == "01127" and not limit_used(state, location.id):
        options.append(DecisionOption("Ma's Boarding House: search your deck for an Ally asset", {"kind": "action", "action": "midnight_location_mas"}))
    elif code == "01128" and state.investigator.damage > 0 and not limit_used(state, location.id):
        options.append(DecisionOption("St. Mary's Hospital: heal 3 damage", {"kind": "action", "action": "midnight_location_hospital"}))
    elif code == "01129":
        options.append(DecisionOption("Miskatonic University: search the top 6 cards for a Tome or Spell", {"kind": "action", "action": "midnight_location_university"}))
    elif code == "01130" and not limit_used(state, location.id):
        options.append(DecisionOption("First Bank: gain 3 resources", {"kind": "action", "action": "midnight_location_bank"}))
    elif code == "01131" and state.investigator.horror > 0 and not limit_used(state, location.id):
        options.append(DecisionOption("Arkham Asylum: heal 3 horror", {"kind": "action", "action": "midnight_location_asylum"}))
    elif code == "01134" and state.investigator.resources >= 5 and not limit_used(state, location.id):
        options.append(DecisionOption("Northside: spend 5 resources to gain 2 clues", {"kind": "action", "action": "midnight_location_northside"}))
    elif code == "50027" and not limit_used(state, location.id):
        for asset_id, use in police_station_targets(state):
            label = "ammo" if use == "ammo" else "supplies"
            options.append(DecisionOption(f"Police Station: add 2 {label} to {card_name(state, asset_id)}", {"kind": "action", "action": "midnight_location_police", "asset": asset_id, "use": use}))
    elif code == "50028" and train_destinations(state) and not limit_used(state, location.id):
        options.append(DecisionOption("Train Station: move to any Arkham location", {"kind": "action", "action": "midnight_location_train"}))
    elif code == "50029" and not limit_used(state, location.id):
        options.append(DecisionOption("Miskatonic Museum: take 2 horror to gain 1 clue", {"kind": "action", "action": "midnight_location_museum"}))
    elif code == "50030" and warehouse_card_choices(state) and warehouse_doom_targets(state) and not limit_used(state, location.id):
        options.append(DecisionOption("Abandoned Warehouse: discard a willpower-icon card to remove doom", {"kind": "action", "action": "midnight_location_warehouse"}))


def cultist_enemies_at_investigator_location(state: GameState) -> list[str]:
    location = state.locations[state.investigator.location_id]
    return [
        enemy_id
        for enemy_id in sorted(location.enemy_ids)
        if enemy_id in state.enemies and is_cultist_code(state.enemies[enemy_id].card_code)
    ]


def execute_action(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng) -> bool:
    action = str(payload.get("action", ""))
    if action == "midnight_cultist_draw":
        draw_from_cultist_deck(state, events)
        return True
    if action == "midnight_parley":
        parley_cultist(state, str(payload.get("enemy", "")), events, rng)
        return True
    if action.startswith("midnight_location_"):
        execute_location_action(state, payload, events, rng)
        return True
    return False


def execute_location_action(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    location = state.locations[state.investigator.location_id]
    action = str(payload.get("action", ""))
    if action == "midnight_location_your_house" and location.code == "01124" and not limit_used(state, location.id, per_turn=True):
        mark_limit_used(state, location.id, per_turn=True)
        draw_player_card_from_location(state, events, rng)
        from ..effects import gain_resource

        gain_resource(state, 1, events)
    elif action == "midnight_location_historical_society" and location.code == "01126" and not limit_used(state, location.id):
        mark_limit_used(state, location.id)
        for _ in range(3):
            draw_player_card_from_location(state, events, rng)
    elif action == "midnight_location_mas" and location.code == "01127" and not limit_used(state, location.id):
        mark_limit_used(state, location.id)
        present_deck_search_choice(state, events, rng, traits={"Ally"}, asset_only=True, source="Ma's Boarding House")
    elif action == "midnight_location_hospital" and location.code == "01128" and state.investigator.damage > 0 and not limit_used(state, location.id):
        mark_limit_used(state, location.id)
        from ..effects import heal_roland

        heal_roland(state, events, damage=3)
    elif action == "midnight_location_university" and location.code == "01129":
        present_top_search_choice(state, events, rng, count=6, traits={"Tome", "Spell"}, source="Miskatonic University")
    elif action == "midnight_location_bank" and location.code == "01130" and not limit_used(state, location.id):
        mark_limit_used(state, location.id)
        from ..effects import gain_resource

        gain_resource(state, 3, events)
    elif action == "midnight_location_asylum" and location.code == "01131" and state.investigator.horror > 0 and not limit_used(state, location.id):
        mark_limit_used(state, location.id)
        from ..effects import heal_roland

        heal_roland(state, events, horror=3)
    elif action == "midnight_location_northside" and location.code == "01134" and (payload.get("activation_cost_paid") or state.investigator.resources >= 5) and not limit_used(state, location.id):
        mark_limit_used(state, location.id)
        if not payload.get("activation_cost_paid"):
            state.investigator.resources -= 5
        gain_clues_from_pool(state, events, 2, source="Northside")
    elif action == "midnight_location_police" and location.code == "50027" and not limit_used(state, location.id):
        asset_id = str(payload.get("asset", ""))
        use = str(payload.get("use", ""))
        if (asset_id, use) in police_station_targets(state):
            mark_limit_used(state, location.id)
            state.card_instances[asset_id].uses[use] = state.card_instances[asset_id].uses.get(use, 0) + 2
            from ..effects import log_event

            log_event(events, "uses_added", f"Police Station added 2 {use} to {card_name(state, asset_id)}.", card=asset_id, use=use)
    elif action == "midnight_location_train" and location.code == "50028" and train_destinations(state) and not limit_used(state, location.id):
        mark_limit_used(state, location.id)
        present_train_move_choice(state)
    elif action == "midnight_location_museum" and location.code == "50029" and not limit_used(state, location.id):
        mark_limit_used(state, location.id)
        if not payload.get("activation_cost_paid"):
            from ..effects import start_damage_assignment

            start_damage_assignment(state, events, source="Miskatonic Museum", damage=0, horror=2)
            if state.status != "in_progress" or state.pending_damage or state.decision_queue:
                return
        gain_clues_from_pool(state, events, 1, source="Miskatonic Museum")
    elif action == "midnight_location_warehouse" and location.code == "50030" and not limit_used(state, location.id):
        if warehouse_card_choices(state) and warehouse_doom_targets(state):
            mark_limit_used(state, location.id)
            present_warehouse_card_choice(state)


def draw_player_card_from_location(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    from ..effects import draw_player_card

    draw_player_card(state, events, rng)


def gain_clues_from_pool(state: GameState, events: list[dict[str, Any]], amount: int, *, source: str) -> None:
    state.investigator.clues += amount
    from ..effects import log_event

    log_event(events, "clues_gained", f"{state.investigator.name} gained {amount} clue from the token pool.", amount=amount, source=source)


def location_limit_key(location_id: str, *, per_turn: bool = False, round_no: int = 0) -> str:
    if per_turn:
        return f"midnight_location_limit:{location_id}:round:{round_no}"
    return f"midnight_location_limit:{location_id}"


def limit_used(state: GameState, location_id: str, *, per_turn: bool = False) -> bool:
    return bool(state.limits.get(location_limit_key(location_id, per_turn=per_turn, round_no=state.round)))


def mark_limit_used(state: GameState, location_id: str, *, per_turn: bool = False) -> None:
    state.limits[location_limit_key(location_id, per_turn=per_turn, round_no=state.round)] = True


def card_has_any_trait(card: dict[str, Any], traits: set[str]) -> bool:
    text = str(card.get("traits", ""))
    return any(trait in text for trait in traits)


def present_deck_search_choice(
    state: GameState,
    events: list[dict[str, Any]],
    rng: ArkhamRng,
    *,
    traits: set[str],
    asset_only: bool,
    source: str,
) -> None:
    candidates = matching_deck_cards(state, list(state.investigator.deck), traits=traits, asset_only=asset_only)
    if not candidates:
        rng.shuffle(state.investigator.deck)
        from ..effects import log_event

        log_event(events, "deck_searched", f"{source} found no matching card.")
        return
    state.decision_queue = [
        PendingDecision(
            id="midnight-deck-search",
            kind="scenario",
            prompt=f"{source}: choose a card to add to hand.",
            options=[
                DecisionOption(
                    f"Add {card_name(state, card_id)} to hand",
                    {"kind": "scenario", "choice": "midnight_search_deck", "card": card_id, "source": source},
                )
                for card_id in candidates
            ],
        )
    ]


def present_top_search_choice(
    state: GameState,
    events: list[dict[str, Any]],
    rng: ArkhamRng,
    *,
    count: int,
    traits: set[str],
    source: str,
) -> None:
    seen = list(state.investigator.deck[:count])
    candidates = matching_deck_cards(state, seen, traits=traits, asset_only=False)
    if not candidates:
        rng.shuffle(state.investigator.deck)
        from ..effects import log_event

        log_event(events, "deck_searched", f"{source} found no matching card.")
        return
    state.decision_queue = [
        PendingDecision(
            id="midnight-top-search",
            kind="scenario",
            prompt=f"{source}: choose a card to add to hand.",
            options=[
                DecisionOption(
                    f"Add {card_name(state, card_id)} to hand",
                    {"kind": "scenario", "choice": "midnight_search_top", "card": card_id, "seen": seen, "source": source},
                )
                for card_id in candidates
            ],
        )
    ]


def matching_deck_cards(state: GameState, card_ids: list[str], *, traits: set[str], asset_only: bool) -> list[str]:
    cards = card_data.cards_by_code()
    found: dict[tuple[str, str], str] = {}
    for card_id in card_ids:
        card = cards[state.card_instances[card_id].card_code]
        if asset_only and card.get("type_code") != "asset":
            continue
        if not card_has_any_trait(card, traits):
            continue
        key = (str(card.get("name", state.card_instances[card_id].card_code)), state.card_instances[card_id].card_code)
        found.setdefault(key, card_id)
    return list(found.values())


def resolve_search_deck_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    chosen = str(payload.get("card", ""))
    if chosen not in state.investigator.deck:
        return
    state.investigator.deck.remove(chosen)
    from ..effects import add_player_card_to_hand

    add_player_card_to_hand(state, events, chosen, event_type="card_added_to_hand", message=f"{payload.get('source', 'Search')} added {card_name(state, chosen)} to hand.")
    rng.shuffle(state.investigator.deck)


def resolve_search_top_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    chosen = str(payload.get("card", ""))
    seen = [str(card_id) for card_id in payload.get("seen", []) if card_id in state.investigator.deck]
    if chosen not in seen:
        return
    for card_id in seen:
        state.investigator.deck.remove(card_id)
    from ..effects import add_player_card_to_hand

    add_player_card_to_hand(state, events, chosen, event_type="card_added_to_hand", message=f"{payload.get('source', 'Search')} added {card_name(state, chosen)} to hand.")
    rest = [card_id for card_id in seen if card_id != chosen]
    state.investigator.deck.extend(rest)
    rng.shuffle(state.investigator.deck)


def police_station_targets(state: GameState) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for asset_id in state.investigator.play_area:
        uses = state.card_instances[asset_id].uses
        for use in ("ammo", "supplies"):
            if use in uses:
                targets.append((asset_id, use))
    return targets


def train_destinations(state: GameState) -> list[str]:
    return [
        location_id
        for location_id, location in sorted(state.locations.items(), key=lambda item: (item[1].code, item[0]))
        if location_id != state.investigator.location_id and "Arkham" in str(card_data.get_card(location.code).get("traits", ""))
    ]


def present_train_move_choice(state: GameState) -> None:
    state.decision_queue = [
        PendingDecision(
            id="midnight-train-move",
            kind="scenario",
            prompt="Train Station: choose a location to move to.",
            options=[
                DecisionOption(
                    f"Move to {location.name}",
                    {"kind": "scenario", "choice": "midnight_train_move", "location": location_id},
                )
                for location_id, location in sorted(state.locations.items(), key=lambda item: (item[1].code, item[0]))
                if location_id in train_destinations(state)
            ],
        )
    ]


def willpower_icon_count(state: GameState, card_id: str) -> int:
    return int(card_data.get_card(state.card_instances[card_id].card_code).get("skill_willpower") or 0)


def warehouse_card_choices(state: GameState) -> list[str]:
    return [
        card_id
        for card_id in state.investigator.hand
        if willpower_icon_count(state, card_id) > 0 and not player_cards.is_weakness(state, card_id)
    ]


def warehouse_doom_targets(state: GameState) -> list[str]:
    return [
        enemy_id
        for enemy_id, enemy in sorted(state.enemies.items())
        if enemy.doom > 0 and is_cultist_code(enemy.card_code)
    ]


def present_warehouse_card_choice(state: GameState) -> None:
    state.decision_queue = [
        PendingDecision(
            id="midnight-warehouse-card",
            kind="scenario",
            prompt="Abandoned Warehouse: choose a willpower-icon card to discard.",
            options=[
                DecisionOption(
                    f"Discard {card_name(state, card_id)} ({willpower_icon_count(state, card_id)} willpower)",
                    {"kind": "scenario", "choice": "midnight_warehouse_card", "card": card_id},
                )
                for card_id in warehouse_card_choices(state)
            ],
        )
    ]


def resolve_warehouse_card_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    card_id = str(payload.get("card", ""))
    icons = willpower_icon_count(state, card_id) if card_id in state.card_instances else 0
    if card_id not in state.investigator.hand or icons <= 0:
        return
    from ..cards import player as player_cards
    from ..effects import log_event

    player_cards.discard_from_hand(state, card_id)
    log_event(events, "card_discarded", f"Discarded {card_name(state, card_id)} for Abandoned Warehouse.", card=card_id)
    targets = warehouse_doom_targets(state)
    if len(targets) == 1:
        remove_warehouse_doom(state, events, targets[0], icons)
        return
    state.decision_queue = [
        PendingDecision(
            id="midnight-warehouse-enemy",
            kind="scenario",
            prompt="Abandoned Warehouse: choose a Cultist to remove doom from.",
            options=[
                DecisionOption(
                    f"Remove doom from {card_data.get_card(state.enemies[enemy_id].card_code).get('name', enemy_id)} ({state.enemies[enemy_id].doom} doom)",
                    {"kind": "scenario", "choice": "midnight_warehouse_enemy", "enemy": enemy_id, "amount": icons},
                )
                for enemy_id in targets
            ],
        )
    ]


def resolve_warehouse_enemy_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    remove_warehouse_doom(state, events, str(payload.get("enemy", "")), int(payload.get("amount", 0)))


def remove_warehouse_doom(state: GameState, events: list[dict[str, Any]], enemy_id: str, amount: int) -> None:
    if enemy_id not in state.enemies or amount <= 0:
        return
    removed = min(amount, state.enemies[enemy_id].doom)
    state.enemies[enemy_id].doom -= removed
    from ..effects import log_event

    log_event(events, "doom_removed", f"Abandoned Warehouse removed {removed} doom from {card_data.get_card(state.enemies[enemy_id].card_code).get('name', enemy_id)}.", enemy=enemy_id, amount=removed)


def draw_from_cultist_deck(state: GameState, events: list[dict[str, Any]]) -> None:
    from ..effects import log_event, spend_clues

    deck = list(state.limits.get("cultist_deck", []))
    if not deck or masked_hunter_blocks_clues(state):
        return
    if not state.limits.pop("cultist_deck_cost_paid", False) and not spend_clues(state, 2, events):
        return
    card_id = deck.pop(0)
    state.limits["cultist_deck"] = deck
    spawn_named_cultist(state, events, card_id)
    log_event(events, "cultist_deck_draw", f"Drew {card_data.get_card(state.card_instances[card_id].card_code)['name']} from the Cultist deck.", card=card_id)
    from ..effects import check_act_objective

    check_act_objective(state, events)


def spawn_named_cultist(state: GameState, events: list[dict[str, Any]], card_id: str) -> None:
    code = state.card_instances[card_id].card_code
    location_id = CULTIST_SPAWNS[code]
    if code == "50044" and location_id not in state.locations:
        location_id = "rivertown"
    from ..enemies import spawn_enemy

    spawn_enemy(state, events, instance_id=card_id, location_id=location_id)


def parley_cultist(state: GameState, enemy_id: str, events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    if enemy_id not in state.enemies or narogath_blocks_parley(state, enemy_id):
        return
    code = state.enemies[enemy_id].card_code
    if code == "01138":
        if len(state.investigator.hand) < 4:
            return
        present_herman_discard_choice(state, enemy_id)
    elif code == "01139":
        from ..effects import spend_clues

        if not masked_hunter_blocks_clues(state) and (state.limits.pop("peter_parley_cost_paid", False) or spend_clues(state, 2, events)):
            add_enemy_to_victory(state, events, enemy_id, reason="Peter Warren was parleyed.")
    elif code == "01140":
        cost_paid = bool(state.limits.pop("victoria_parley_cost_paid", False))
        if cost_paid or state.investigator.resources >= 5:
            if not cost_paid:
                state.investigator.resources -= 5
            add_enemy_to_victory(state, events, enemy_id, reason="Victoria Devereux was parleyed.")
    elif code == "50044":
        add_enemy_to_victory(state, events, enemy_id, reason="Jeremiah Pierce was parleyed.")
        from .. import skill_test

        skill_test.start(
            state,
            events,
            skill="willpower",
            difficulty=4,
            source="Parley with Jeremiah Pierce",
            on_failure={"kind": "jeremiah_doom"},
        )
    elif code == "50046":
        from .. import encounter

        for _ in range(3):
            if state.status != "in_progress":
                break
            encounter.draw_encounter(state, rng, events)
        if enemy_id in state.enemies:
            add_enemy_to_victory(state, events, enemy_id, reason="Alma Hill was parleyed.")


def present_herman_discard_choice(state: GameState, enemy_id: str) -> None:
    selected = list(state.limits.get("herman_selected", []))
    options = []
    for card_id in state.investigator.hand:
        if card_id in selected:
            continue
        if player_cards.is_weakness(state, card_id):
            continue
        options.append(
            DecisionOption(
                f"Discard {card_name(state, card_id)}",
                {"kind": "scenario", "choice": "herman_discard", "enemy": enemy_id, "card": card_id},
            )
        )
    state.decision_queue = [
        PendingDecision(
            id="herman-discard",
            kind="scenario",
            prompt=f"Choose {4 - len(selected)} more cards to discard for Herman Collins.",
            options=options,
        )
    ]


def resolve_herman_discard_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
    enemy_id = str(payload.get("enemy", ""))
    card_id = str(payload.get("card", ""))
    if enemy_id not in state.enemies or card_id not in state.investigator.hand:
        state.limits.pop("herman_selected", None)
        return
    from ..cards import player as player_cards

    selected = list(state.limits.get("herman_selected", []))
    player_cards.discard_from_hand(state, card_id)
    selected.append(card_id)
    from ..effects import log_event

    log_event(events, "card_discarded", f"Discarded {card_name(state, card_id)} for Herman Collins.", card=card_id)
    if len(selected) >= 4:
        state.limits.pop("herman_selected", None)
        add_enemy_to_victory(state, events, enemy_id, reason="Herman Collins was parleyed.")
    else:
        state.limits["herman_selected"] = selected
        present_herman_discard_choice(state, enemy_id)


def add_enemy_to_victory(state: GameState, events: list[dict[str, Any]], enemy_id: str, *, reason: str) -> None:
    if enemy_id not in state.enemies:
        return
    enemy = state.enemies.pop(enemy_id)
    state.card_instances[enemy_id].doom = 0
    state.card_instances[enemy_id].clues = 0
    if enemy.location_id in state.locations and enemy_id in state.locations[enemy.location_id].enemy_ids:
        state.locations[enemy.location_id].enemy_ids.remove(enemy_id)
    if enemy_id in state.investigator.engaged_enemies:
        state.investigator.engaged_enemies.remove(enemy_id)
    state.card_instances[enemy_id].zone = "victory"
    if enemy_id not in state.victory_display:
        state.victory_display.append(enemy_id)
    from ..effects import log_event

    log_event(events, "enemy_victory", reason, enemy=enemy_id)
    from ..effects import check_act_objective

    check_act_objective(state, events)


def encounter_revelation(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]], instance_id: str) -> bool:
    code = state.card_instances[instance_id].card_code
    if code == "01116" and "your_house" in state.locations:
        from ..enemies import spawn_enemy

        spawn_enemy(state, events, instance_id=instance_id, location_id="your_house", engaged=False)
        return True
    if code in {"01169", "01170"}:
        spawn_any_empty_location_enemy(state, events, instance_id)
        return True
    if code == "01171":
        mysterious_chanting(state, events, rng, instance_id)
        return True
    if code == "01135":
        hunting_shadow(state, events, instance_id)
        return True
    if code == "01136":
        false_lead(state, events, rng, instance_id)
        return True
    if code == "01173":
        discard_encounter_card(state, instance_id)
        from .. import skill_test

        skill_test.start(
            state,
            events,
            skill="agility",
            difficulty=4,
            source="On Wings of Darkness",
            on_failure={"kind": "on_wings"},
        )
        return True
    if code == "50031":
        masked_horrors(state, events, rng, instance_id)
        return True
    if code in {"50041", "50042"}:
        spawn_farthest_empty_location_enemy(state, events, instance_id, rng)
        return True
    if code == "50043":
        mask_of_umordhoth(state, events, rng, instance_id)
        return True
    return False


def hunting_shadow(state: GameState, events: list[dict[str, Any]], instance_id: str) -> None:
    options = []
    if state.investigator.clues >= 1 and not masked_hunter_blocks_clues(state):
        options.append(DecisionOption("Spend 1 clue", {"kind": "scenario", "choice": "hunting_shadow_clue", "card": instance_id}))
    options.append(DecisionOption("Take 2 damage", {"kind": "scenario", "choice": "hunting_shadow_damage", "card": instance_id}))
    state.decision_queue = [
        PendingDecision(id="hunting-shadow", kind="scenario", prompt="Choose for Hunting Shadow.", options=options)
    ]


def false_lead(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng, instance_id: str) -> None:
    discard_encounter_card(state, instance_id)
    if state.investigator.clues <= 0:
        from ..encounter import draw_encounter

        from ..effects import log_event

        log_event(events, "surge", "False Lead surged because the investigator had no clues.")
        draw_encounter(state, rng, events)
        return
    from .. import skill_test

    skill_test.start(
        state,
        events,
        skill="intellect",
        difficulty=4,
        source="False Lead",
        on_failure={"kind": "false_lead"},
    )


def masked_horrors(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng, instance_id: str) -> None:
    discard_encounter_card(state, instance_id)
    if state.investigator.clues >= 2:
        from ..effects import start_damage_assignment

        start_damage_assignment(state, events, source="Masked Horrors", damage=0, horror=2)
    else:
        from ..effects import place_doom

        place_doom(state, 1, events, source="Masked Horrors", rng=rng, can_advance=True)


def spawn_any_empty_location_enemy(state: GameState, events: list[dict[str, Any]], instance_id: str) -> None:
    targets = empty_locations(state)
    if not targets:
        targets = [state.investigator.location_id]
    present_or_spawn_at_locations(state, events, instance_id, targets)


def spawn_farthest_empty_location_enemy(state: GameState, events: list[dict[str, Any]], instance_id: str, rng: ArkhamRng) -> None:
    targets = farthest_locations(state, empty_locations(state))
    if not targets:
        targets = [state.investigator.location_id]
    present_or_spawn_at_locations(state, events, instance_id, targets, farthest=True)


def present_or_spawn_at_locations(
    state: GameState,
    events: list[dict[str, Any]],
    instance_id: str,
    targets: list[str],
    *,
    farthest: bool = False,
) -> None:
    if instance_id in state.encounter_deck:
        state.encounter_deck.remove(instance_id)
    if instance_id in state.encounter_discard:
        state.encounter_discard.remove(instance_id)
    if instance_id in state.card_instances:
        state.card_instances[instance_id].zone = "encounter_drawn"
    if len(targets) == 1:
        spawn_enemy_resolving_forced(state, events, instance_id, targets[0])
        return
    state.decision_queue = [
        PendingDecision(
            id="enemy-spawn-location",
            kind="scenario",
            prompt="Choose an empty spawn location.",
            options=[
                DecisionOption(
                    f"Spawn at {state.locations[location_id].name}",
                    {"kind": "scenario", "choice": "spawn_at_location", "card": instance_id, "location": location_id},
                )
                for location_id in targets
            ],
        )
    ]


def resolve_spawn_at_location(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    card_id = str(payload.get("card", ""))
    location_id = str(payload.get("location", ""))
    if card_id in state.card_instances and location_id in state.locations:
        spawn_enemy_resolving_forced(state, events, card_id, location_id, rng)
        pending_mask = dict(state.limits.pop("pending_mask_after_spawn", {}))
        if pending_mask.get("enemy") == card_id and pending_mask.get("mask") in state.card_instances and card_id in state.enemies:
            attach_mask_to_enemy(state, str(pending_mask["mask"]), card_id, events, rng)


def spawn_enemy_resolving_forced(
    state: GameState,
    events: list[dict[str, Any]],
    instance_id: str,
    location_id: str,
    rng: ArkhamRng | None = None,
) -> None:
    from ..enemies import spawn_enemy

    spawned = spawn_enemy(state, events, instance_id=instance_id, location_id=location_id)
    if not spawned:
        return
    code = state.card_instances[instance_id].card_code
    if code == "01169":
        place_doom_on_enemy(state, instance_id, 1, events, source="Acolyte", rng=rng)
    elif code == "50041":
        disciple_after_spawn(state, events, instance_id, rng)


def disciple_after_spawn(state: GameState, events: list[dict[str, Any]], enemy_id: str, rng: ArkhamRng | None) -> None:
    if state.agenda and state.agenda.stage != 1:
        place_doom_on_enemy(state, enemy_id, 1, events, source="Disciple of the Devourer", rng=rng)
        if state.investigator.clues > 0 and enemy_id in state.enemies:
            state.investigator.clues -= 1
            state.locations[state.enemies[enemy_id].location_id].clues += 1
            from ..effects import log_event

            log_event(events, "clue_placed", "Disciple of the Devourer placed 1 clue on its location.", enemy=enemy_id)
        return
    options = [DecisionOption("Place 1 doom on Disciple", {"kind": "scenario", "choice": "disciple_doom", "enemy": enemy_id})]
    if state.investigator.clues > 0:
        options.append(DecisionOption("Place 1 clue on its location", {"kind": "scenario", "choice": "disciple_clue", "enemy": enemy_id}))
    state.decision_queue = [PendingDecision(id="disciple-forced", kind="scenario", prompt="Resolve Disciple of the Devourer.", options=options)]


def mysterious_chanting(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng, instance_id: str) -> None:
    cultists = cultist_enemy_ids(state)
    if not cultists:
        searched = search_and_draw_cultist_enemy(state, events, rng, source="Mysterious Chanting")
        discard_encounter_card(state, instance_id)
        return
    nearest = nearest_enemies(state, cultists)
    if len(nearest) == 1:
        place_doom_on_enemy(state, nearest[0], 2, events, source="Mysterious Chanting", rng=rng)
        discard_encounter_card(state, instance_id)
        return
    state.decision_queue = [
        PendingDecision(
            id="mysterious-chanting-target",
            kind="scenario",
            prompt="Choose the nearest Cultist enemy for Mysterious Chanting.",
            options=[
                DecisionOption(
                    f"Place doom on {card_data.get_card(state.enemies[enemy_id].card_code)['name']}",
                    {"kind": "scenario", "choice": "mysterious_chanting_target", "card": instance_id, "enemy": enemy_id},
                )
                for enemy_id in nearest
            ],
        )
    ]


def mask_of_umordhoth(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng, instance_id: str) -> None:
    cultists = cultist_enemy_ids(state)
    if not cultists:
        enemy_id = search_and_draw_cultist_enemy(state, events, rng, source="Mask of Umordhoth", mask_id=instance_id)
        if state.decision_queue:
            return
        cultists = [enemy_id] if enemy_id else []
    farthest = farthest_enemies(state, cultists)
    if not farthest:
        discard_encounter_card(state, instance_id)
    elif len(farthest) == 1:
        attach_mask_to_enemy(state, instance_id, farthest[0], events, rng)
    else:
        state.decision_queue = [
            PendingDecision(
                id="mask-target",
                kind="scenario",
                prompt="Choose the farthest Cultist enemy for Mask of Umordhoth.",
                options=[
                    DecisionOption(
                        f"Attach to {card_data.get_card(state.enemies[enemy_id].card_code)['name']}",
                        {"kind": "scenario", "choice": "mask_target", "card": instance_id, "enemy": enemy_id},
                    )
                    for enemy_id in farthest
                ],
            )
        ]


def attach_mask_to_enemy(state: GameState, mask_id: str, enemy_id: str, events: list[dict[str, Any]], rng: ArkhamRng | None) -> None:
    if mask_id not in state.card_instances or enemy_id not in state.enemies:
        return
    state.card_instances[mask_id].zone = "attachment"
    state.enemies[enemy_id].attachments.append(mask_id)
    from ..effects import log_event

    log_event(events, "treachery_attached", "Mask of Umordhoth attached to a Cultist enemy.", card=mask_id, enemy=enemy_id)
    place_doom_on_enemy(state, enemy_id, 1, events, source="Mask of Umordhoth", rng=rng)


def search_and_draw_cultist_enemy(
    state: GameState,
    events: list[dict[str, Any]],
    rng: ArkhamRng,
    *,
    source: str = "Cultist search",
    mask_id: str | None = None,
) -> str | None:
    combined = list(state.encounter_deck) + list(state.encounter_discard)
    candidates = [
        card_id
        for card_id in combined
        if card_data.get_card(state.card_instances[card_id].card_code).get("type_code") == "enemy"
        and is_cultist_code(state.card_instances[card_id].card_code)
    ]
    found = single_distinct_search_candidate(state, candidates)
    if not found:
        if candidates:
            present_cultist_search_choice(state, candidates, source=source, mask_id=mask_id)
        return None
    return draw_searched_cultist_enemy(state, events, rng, found, mask_id=mask_id)


def single_distinct_search_candidate(state: GameState, candidates: list[str]) -> str | None:
    by_name: dict[str, str] = {}
    for card_id in candidates:
        name = str(card_data.get_card(state.card_instances[card_id].card_code).get("name", card_id))
        by_name.setdefault(name, card_id)
    return next(iter(by_name.values())) if len(by_name) == 1 else None


def present_cultist_search_choice(state: GameState, candidates: list[str], *, source: str, mask_id: str | None) -> None:
    by_name: dict[str, str] = {}
    for card_id in candidates:
        name = str(card_data.get_card(state.card_instances[card_id].card_code).get("name", card_id))
        by_name.setdefault(name, card_id)
    state.decision_queue = [
        PendingDecision(
            id="cultist-search",
            kind="scenario",
            prompt=f"Choose a Cultist enemy for {source}.",
            options=[
                DecisionOption(
                    f"Draw {name}",
                    {"kind": "scenario", "choice": "cultist_search_choice", "card": card_id, "mask": mask_id or ""},
                )
                for name, card_id in sorted(by_name.items())
            ],
        )
    ]


def resolve_cultist_search_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    card_id = str(payload.get("card", ""))
    mask_id = str(payload.get("mask") or "") or None
    if card_id in state.encounter_deck or card_id in state.encounter_discard:
        enemy_id = draw_searched_cultist_enemy(state, events, rng, card_id, mask_id=mask_id)
        if mask_id and enemy_id and not state.decision_queue:
            attach_mask_to_enemy(state, mask_id, enemy_id, events, rng)


def draw_searched_cultist_enemy(
    state: GameState,
    events: list[dict[str, Any]],
    rng: ArkhamRng,
    found: str,
    *,
    mask_id: str | None = None,
) -> str | None:
    from ..encounter import resolve_revelation

    if found in state.encounter_deck:
        state.encounter_deck.remove(found)
    if found in state.encounter_discard:
        state.encounter_discard.remove(found)
    state.card_instances[found].zone = "encounter_drawn"
    state.limits["encounter_cards_drawn"] = int(state.limits.get("encounter_cards_drawn", 0)) + 1
    resolve_revelation(state, rng, events, found)
    if mask_id and mask_id in state.card_instances:
        if state.decision_queue:
            state.limits["pending_mask_after_spawn"] = {"mask": mask_id, "enemy": found}
    rng.shuffle(state.encounter_deck)
    return found if found in state.enemies else None


def place_doom_on_enemy(
    state: GameState,
    enemy_id: str,
    amount: int,
    events: list[dict[str, Any]],
    *,
    source: str,
    rng: ArkhamRng | None = None,
    can_advance: bool = False,
) -> None:
    if enemy_id not in state.enemies:
        return
    state.enemies[enemy_id].doom += amount
    from ..effects import log_event

    log_event(events, "doom_placed", f"Placed {amount} doom on {card_data.get_card(state.enemies[enemy_id].card_code)['name']}.", enemy=enemy_id, source=source)
    if can_advance:
        from ..effects import check_agenda_advance

        check_agenda_advance(state, events, rng=rng)


def end_mythos_phase(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None) -> None:
    for enemy_id in sorted(state.enemies):
        code = state.enemies[enemy_id].card_code
        if code == "01170":
            place_doom_on_enemy(state, enemy_id, 1, events, source="Wizard of the Order", rng=rng)
        elif code == "50042":
            place_doom_on_enemy(state, enemy_id, 1, events, source="Corpse-Taker", rng=rng)


def end_enemy_phase(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    from ..enemies import move_enemy_to, next_step_toward
    from ..effects import place_doom

    for enemy_id in sorted(list(state.enemies)):
        if enemy_id not in state.enemies or state.enemies[enemy_id].card_code != "50042":
            continue
        enemy = state.enemies[enemy_id]
        if enemy.location_id == "rivertown":
            doom = enemy.doom
            if doom:
                enemy.doom = 0
                place_doom(state, doom, events, source="Corpse-Taker", rng=rng, can_advance=True)
            continue
        step = next_step_toward(state, enemy.location_id, "rivertown", enemy_id)
        if step:
            move_enemy_to(state, events, enemy_id, step)


def after_enemy_defeated(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> bool:
    defeated_code = state.card_instances[enemy_id].card_code
    location_id = str(state.limits.get("last_defeated_enemy_location", ""))
    if "Monster" in str(card_data.get_card(defeated_code).get("traits", "")):
        for billy_id, enemy in list(state.enemies.items()):
            if enemy.card_code == "50045" and enemy.location_id == location_id:
                add_enemy_to_victory(state, events, billy_id, reason="Billy Cooper was added to the victory display.")
                break
    from ..effects import check_act_objective as dispatch_check_act_objective

    dispatch_check_act_objective(state, events)
    return False


def after_enemy_evaded(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> None:
    if enemy_id in state.enemies and state.enemies[enemy_id].card_code == "01141":
        add_enemy_to_victory(state, events, enemy_id, reason="Ruth Turner was evaded.")


def after_enemy_attacks(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> None:
    if enemy_id in state.enemies and state.enemies[enemy_id].card_code == "01137" and state.enemies[enemy_id].damage > 0:
        state.enemies[enemy_id].damage = max(0, state.enemies[enemy_id].damage - 1)
        from ..effects import log_event

        log_event(events, "enemy_healed", '"Wolf-Man" Drew healed 1 damage.', enemy=enemy_id)


def check_act_objective(state: GameState, events: list[dict[str, Any]]) -> None:
    if state.status != "in_progress":
        return
    if unique_cultists_in_victory(state) >= 6:
        from ..effects import finalize_result as dispatch_finalize_result

        dispatch_finalize_result(state, events, outcome="R1", resolution="R1", summary="R1: the cultists were unmasked")
        from ..effects import log_event

        log_event(events, "game_end", "R1: the cultists were unmasked")


def check_agenda_advance(state: GameState, events: list[dict[str, Any]], *, rng: ArkhamRng | None = None) -> None:
    if not state.agenda or state.agenda.threshold <= 0:
        return
    while total_doom(state) >= state.agenda.threshold and state.status == "in_progress" and not state.decision_queue:
        from ..effects import clear_all_doom, log_event

        clear_all_doom(state)
        if state.agenda.stage == 1:
            spawn_agenda_enemy(state, events)
            state.agenda = AgendaState(code="01122", name="Time Is Running Short", stage=2, threshold=8)
            log_event(events, "agenda_advanced", "Agenda advanced to Time Is Running Short.")
        elif state.agenda.stage == 2:
            finalize_result(state, events, outcome="R2", resolution="R2", summary="R2: the clock struck midnight")
            log_event(events, "game_end", "R2: the clock struck midnight")
            return
        else:
            return


def spawn_agenda_enemy(state: GameState, events: list[dict[str, Any]]) -> None:
    from ..enemies import spawn_enemy

    enemy_id = "setaside_agenda_enemy"
    if enemy_id not in state.card_instances:
        code = str(state.limits.get("agenda1_enemy_code", "01121b"))
        state.card_instances[enemy_id] = CardInstance(id=enemy_id, card_code=code, zone="set_aside")
    spawn_enemy(state, events, instance_id=enemy_id, location_id=state.investigator.location_id, engaged=True)


def total_doom(state: GameState) -> int:
    agenda = state.agenda.doom if state.agenda else 0
    enemies = sum(enemy.doom for enemy in state.enemies.values())
    cards = sum(instance.doom for instance in state.card_instances.values())
    return agenda + enemies + cards


def resign(state: GameState, events: list[dict[str, Any]]) -> None:
    finalize_result(state, events, outcome="R1", resolution="R1", summary=f"{state.investigator.name} resigned", resigned=True)
    from ..effects import log_event

    log_event(events, "game_end", f"{state.investigator.name} resigned")


def finalize_result(
    state: GameState,
    events: list[dict[str, Any]],
    *,
    outcome: str,
    summary: str,
    resolution: str | None = None,
    resigned: bool = False,
) -> None:
    from ..effects import apply_cover_up_trauma
    from .the_gathering import add_victory_locations, calculate_victory_points

    apply_cover_up_trauma(state, events)
    add_victory_locations(state)
    victory_points = calculate_victory_points(state)
    xp = victory_points
    hospital_debts_penalty = hospital_debts_xp_penalty(state)
    if hospital_debts_penalty:
        xp = max(0, xp - hospital_debts_penalty)
    score = max(0, xp - total_trauma(state))
    state.status = "ended"
    state.decision_queue = []
    state.result = {
        "scenario": state.scenario,
        "outcome": outcome,
        "resolution": resolution or outcome,
        "summary": summary,
        "rounds_played": state.round,
        "actions_taken": int(state.limits.get("actions_taken", state.turn.action_index)),
        "damage_taken": state.investigator.damage,
        "horror_taken": state.investigator.horror,
        "trauma": dict(state.trauma),
        "victory_points": victory_points,
        "xp": xp,
        "hospital_debts_xp_penalty": hospital_debts_penalty,
        "score": score,
        "resigned": resigned,
        "investigator_killed": False,
        "investigator_insane": False,
        "encounter_cards_drawn": int(state.limits.get("encounter_cards_drawn", 0)),
        "enemies_defeated": int(state.limits.get("enemies_defeated", 0)),
        "campaign": campaign_block(state, outcome),
    }


def campaign_block(state: GameState, outcome: str) -> dict[str, Any]:
    return {
        "scenario": state.scenario,
        "inputs": dict(state.limits.get("campaign_inputs", {})),
        "cultists_interrogated": sorted(unique_cultist_names_in_victory(state)),
        "cultists_got_away": sorted(cultists_got_away(state)),
        "past_midnight": outcome == "R2",
        "ghoul_priest_defeated_here": any(
            state.card_instances[item_id].card_code == "01116"
            for item_id in state.victory_display
            if item_id in state.card_instances
        ),
    }


def unique_cultist_names_in_victory(state: GameState) -> set[str]:
    names = set()
    for item_id in state.victory_display:
        if item_id in state.card_instances:
            code = state.card_instances[item_id].card_code
            if code in UNIQUE_CULTIST_CODES:
                names.add(str(card_data.get_card(code).get("name", code)))
    return names


def unique_cultists_in_victory(state: GameState) -> int:
    return len(unique_cultist_names_in_victory(state))


def cultists_got_away(state: GameState) -> set[str]:
    names: set[str] = set()
    for card_id in state.limits.get("cultist_deck", []):
        if card_id in state.card_instances:
            names.add(str(card_data.get_card(state.card_instances[card_id].card_code).get("name", card_id)))
    for enemy in state.enemies.values():
        if enemy.card_code in UNIQUE_CULTIST_CODES:
            names.add(str(card_data.get_card(enemy.card_code).get("name", enemy.card_code)))
    if state.agenda and state.agenda.stage == 1:
        names.add(str(card_data.get_card(str(state.limits.get("agenda1_enemy_code", "01121b"))).get("name", "The Masked Hunter")))
    return names


def apply_token_aftermath(state: GameState, events: list[dict[str, Any]], result: dict[str, Any], rng: ArkhamRng | None = None) -> None:
    tokens = [str(result.get("token"))] + [str(token) for token in result.get("extra_tokens", [])]
    failed = not bool(result.get("success"))
    if "cultist" in tokens and not result.get("reveal_effects_applied"):
        cultists = cultist_enemy_ids(state)
        if state.difficulty in {"easy", "standard"}:
            nearest = nearest_enemies(state, cultists)
            if nearest:
                place_doom_on_enemy(state, nearest[0], 1, events, source="Chaos token", rng=rng)
        else:
            for enemy_id in cultists:
                place_doom_on_enemy(state, enemy_id, 1, events, source="Chaos token", rng=rng)
    if "tablet" in tokens and failed and state.investigator.clues > 0:
        count = 1 if state.difficulty in {"easy", "standard"} else state.investigator.clues
        count = min(count, state.investigator.clues)
        state.investigator.clues -= count
        state.locations[state.investigator.location_id].clues += count
        from ..effects import log_event

        log_event(events, "clue_placed", f"Tablet token placed {count} clue on the location.", amount=count)


def apply_token_reveal_effects(state: GameState, events: list[dict[str, Any]], test: dict[str, Any], rng: ArkhamRng | None = None) -> None:
    tokens = [str(test.get("token"))] + [str(token) for token in test.get("extra_tokens", [])]
    if "cultist" not in tokens:
        return
    cultists = cultist_enemy_ids(state)
    if state.difficulty in {"easy", "standard"}:
        nearest = nearest_enemies(state, cultists)
        if nearest:
            place_doom_on_enemy(state, nearest[0], 1, events, source="Chaos token", rng=rng)
    else:
        for enemy_id in cultists:
            place_doom_on_enemy(state, enemy_id, 1, events, source="Chaos token", rng=rng)


def on_wings_aftermath(state: GameState, events: list[dict[str, Any]], *, failed: bool) -> None:
    if not failed:
        return
    from ..effects import start_damage_assignment

    start_damage_assignment(
        state,
        events,
        source="On Wings of Darkness",
        damage=1,
        horror=1,
        resume={"kind": "scenario", "choice": "on_wings_continue"},
    )


def on_wings_disengage_and_move(state: GameState, events: list[dict[str, Any]]) -> None:
    for enemy_id in list(state.investigator.engaged_enemies):
        if "Nightgaunt" not in str(card_data.get_card(state.enemies[enemy_id].card_code).get("traits", "")):
            from ..enemies import disengage_enemy

            disengage_enemy(state, events, enemy_id, exhaust=False)
    if state.investigator.location_id != "rivertown":
        move_investigator_to(state, events, "rivertown")


def move_investigator_to(state: GameState, events: list[dict[str, Any]], location_id: str) -> None:
    if location_id not in state.locations:
        return
    investigator_id = state.investigator.id
    old = state.investigator.location_id
    if old in state.locations and investigator_id in state.locations[old].investigator_ids:
        state.locations[old].investigator_ids.remove(investigator_id)
    state.investigator.location_id = location_id
    if investigator_id not in state.locations[location_id].investigator_ids:
        state.locations[location_id].investigator_ids.append(investigator_id)
    from ..enemies import move_engaged_enemies_with_roland, engage_ready_enemies_at_roland
    from ..effects import log_event

    move_engaged_enemies_with_roland(state, events, location_id)
    log_event(events, "investigator_moved", f"{state.investigator.name} moved to {state.locations[location_id].name}.", location=location_id)
    reveal_location(state, events, location_id)
    engage_ready_enemies_at_roland(state, events)


def false_lead_aftermath(state: GameState, events: list[dict[str, Any]], margin: int) -> None:
    count = min(margin, state.investigator.clues)
    if count <= 0:
        return
    state.investigator.clues -= count
    state.locations[state.investigator.location_id].clues += count
    from ..effects import log_event

    log_event(events, "clue_placed", f"False Lead placed {count} clue on the location.", amount=count)


def jeremiah_doom(state: GameState, events: list[dict[str, Any]], margin: int, rng: ArkhamRng | None) -> None:
    if margin <= 0:
        return
    from ..effects import place_doom

    place_doom(state, margin, events, source="Jeremiah Pierce", rng=rng, can_advance=True)


def graveyard_failure(state: GameState) -> None:
    state.decision_queue = [
        PendingDecision(
            id="graveyard-forced",
            kind="scenario",
            prompt="Choose the Graveyard failure effect.",
            options=[
                DecisionOption("Take 2 horror", {"kind": "scenario", "choice": "graveyard_horror"}),
                DecisionOption("Move to Rivertown", {"kind": "scenario", "choice": "graveyard_move"}),
            ],
        )
    ]


def masked_hunter_blocks_clues(state: GameState) -> bool:
    return any(
        enemy_id in state.enemies and state.enemies[enemy_id].card_code == "01121b"
        for enemy_id in state.investigator.engaged_enemies
    )


def narogath_blocks_parley(state: GameState, target_enemy_id: str | None = None) -> bool:
    if target_enemy_id is not None and target_enemy_id in state.enemies and not is_cultist_code(state.enemies[target_enemy_id].card_code):
        return False
    investigator_location = state.investigator.location_id
    blocked_locations = {investigator_location, *state.locations[investigator_location].connections}
    return any(
        enemy.card_code == "50026b" and not enemy.exhausted and enemy.location_id in blocked_locations
        for enemy in state.enemies.values()
    )


def is_cultist_code(code: str) -> bool:
    return "Cultist" in str(card_data.get_card(code).get("traits", ""))


def cultist_enemy_ids(state: GameState) -> list[str]:
    return [enemy_id for enemy_id, enemy in state.enemies.items() if is_cultist_code(enemy.card_code)]


def empty_locations(state: GameState) -> list[str]:
    return [
        location_id
        for location_id, location in state.locations.items()
        if not location.investigator_ids and not location.enemy_ids
    ]


def shortest_distance(state: GameState, start: str, goal: str) -> int | None:
    if start == goal:
        return 0
    queue: deque[tuple[str, int]] = deque([(start, 0)])
    seen = {start}
    while queue:
        current, distance = queue.popleft()
        for neighbor in state.locations[current].connections:
            if neighbor in seen:
                continue
            if neighbor == goal:
                return distance + 1
            seen.add(neighbor)
            queue.append((neighbor, distance + 1))
    return None


def nearest_enemies(state: GameState, enemy_ids: list[str]) -> list[str]:
    if not enemy_ids:
        return []
    distances = {
        enemy_id: shortest_distance(state, state.investigator.location_id, state.enemies[enemy_id].location_id)
        for enemy_id in enemy_ids
    }
    valid = {enemy_id: distance for enemy_id, distance in distances.items() if distance is not None}
    if not valid:
        return sorted(enemy_ids)
    best = min(valid.values())
    return sorted(enemy_id for enemy_id, distance in valid.items() if distance == best)


def farthest_enemies(state: GameState, enemy_ids: list[str]) -> list[str]:
    if not enemy_ids:
        return []
    distances = {
        enemy_id: shortest_distance(state, state.investigator.location_id, state.enemies[enemy_id].location_id)
        for enemy_id in enemy_ids
    }
    valid = {enemy_id: distance for enemy_id, distance in distances.items() if distance is not None}
    if not valid:
        return sorted(enemy_ids)
    best = max(valid.values())
    return sorted(enemy_id for enemy_id, distance in valid.items() if distance == best)


def farthest_locations(state: GameState, location_ids: list[str]) -> list[str]:
    if not location_ids:
        return []
    distances = {
        location_id: shortest_distance(state, state.investigator.location_id, location_id)
        for location_id in location_ids
    }
    valid = {location_id: distance for location_id, distance in distances.items() if distance is not None}
    if not valid:
        return sorted(location_ids)
    best = max(valid.values())
    return sorted(location_id for location_id, distance in valid.items() if distance == best)


def discard_encounter_card(state: GameState, instance_id: str) -> None:
    if not instance_id or instance_id not in state.card_instances:
        return
    state.card_instances[instance_id].zone = "encounter_discard"
    if instance_id not in state.encounter_discard:
        state.encounter_discard.append(instance_id)
