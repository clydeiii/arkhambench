"""The Devourer Below and Return to The Devourer Below."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import data as card_data
from ..cards import player as player_cards
from ..cards.player import card_name
from ..errors import EngineError
from ..model import ActState, AgendaState, CardInstance, ChaosBag, DecisionOption, GameState, Investigator, Location, PendingDecision, TurnState
from ..rng import ArkhamRng
from . import the_midnight_masks
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


RETURN_SCENARIO = "return_to_the_devourer_below"
DEVOURER_FAMILY = {"the_devourer_below", RETURN_SCENARIO}

CORE_ENCOUNTER_COUNTS = {
    "01158": 2,
    "01166": 3,
    "01163": 3,
    "01164": 2,
    "01165": 2,
    "01160": 3,
    "01161": 1,
    "01162": 3,
    "01169": 3,
    "01170": 1,
    "01171": 2,
}
RETURN_REPLACEMENTS = {
    "01160": 0,
    "01161": 0,
    "01162": 0,
    "01169": 0,
    "01170": 0,
    "01171": 0,
}
RETURN_COUNTS = {
    "50037": 2,
    "50038": 3,
    "50039": 1,
    "50040": 3,
    "50041": 3,
    "50042": 1,
    "50043": 2,
}
AGENT_SETS = {
    "agents_of_yog": {"01177": 2, "01178": 2},
    "agents_of_shub": {"01179": 1, "01180": 3},
    "agents_of_cthulhu": {"01181": 2, "01182": 2},
    "agents_of_hastur": {"01175": 2, "01176": 2},
}

CORE_WOODS = ["01150", "01151", "01152", "01153", "01154", "01155"]
RETURN_WOODS = ["50033", "50034", "50035", "50036"]
WOOD_IDS = {
    "01150": "unhallowed_ground",
    "01151": "twisting_paths",
    "01152": "old_house",
    "01153": "cliffside",
    "01154": "tangled_thicket",
    "01155": "quiet_glade",
    "50033": "great_willow",
    "50034": "lakeside",
    "50035": "corpse_ridden_clearing",
    "50036": "wooden_bridge",
}
WOOD_SYMBOLS = {
    "01150": "triangle",
    "01151": "t",
    "01152": "diamond",
    "01153": "hourglass",
    "01154": "equals",
    "01155": "moon",
    "50033": "heart",
    "50034": "star",
    "50035": "comma",
    "50036": "circle",
}
WOOD_FRONT_CONNECTION_SYMBOLS = {
    "01150": {"hourglass", "diamond"},
    "01151": {"diamond", "equals"},
    "01152": {"triangle", "t"},
    "01153": {"moon", "triangle"},
    "01154": {"t", "moon"},
    "01155": {"equals", "hourglass"},
    "50033": {"star"},
    "50034": {"heart"},
    "50035": {"circle"},
    "50036": {"comma"},
}
NAMED_CULTIST_BY_NAME = {
    str(card_data.get_card(code).get("name", code)): code
    for code in [*the_midnight_masks.CORE_CULTISTS, *the_midnight_masks.RETURN_CULTISTS, "01121b", "50026b"]
}


def is_return(state: GameState) -> bool:
    return state.scenario == RETURN_SCENARIO


def build_state(
    *,
    difficulty: str,
    rng: ArkhamRng,
    deck_path: str | Path | None = None,
    investigator_slug: str = "roland",
    cultists_got_away: list[str] | str | None = None,
    past_midnight: bool = False,
    ghoul_priest_alive: bool = False,
    lita_in_deck: bool = False,
) -> GameState:
    return build_devourer_state(
        difficulty=difficulty,
        rng=rng,
        deck_path=deck_path,
        investigator_slug=investigator_slug,
        scenario="the_devourer_below",
        cultists_got_away=cultists_got_away,
        past_midnight=past_midnight,
        ghoul_priest_alive=ghoul_priest_alive,
        lita_in_deck=lita_in_deck,
    )


def build_return_state(**kwargs: Any) -> GameState:
    kwargs["scenario"] = RETURN_SCENARIO
    return build_devourer_state(**kwargs)


def build_devourer_state(
    *,
    difficulty: str,
    rng: ArkhamRng,
    deck_path: str | Path | None,
    investigator_slug: str,
    scenario: str,
    cultists_got_away: list[str] | str | None = None,
    past_midnight: bool = False,
    ghoul_priest_alive: bool = False,
    lita_in_deck: bool = False,
) -> GameState:
    cards = card_data.cards_by_code()
    if investigator_slug not in card_data.INVESTIGATOR_CODES:
        raise EngineError(f"unknown investigator: {investigator_slug}")
    investigator_code = card_data.INVESTIGATOR_CODES[investigator_slug]
    investigator_card = cards[investigator_code]
    instances: dict[str, CardInstance] = {}
    player_deck = build_player_deck(instances, deck_path, investigator_slug=investigator_slug)
    if lita_in_deck and not any(inst.card_code == "01117" for inst in instances.values()):
        lita_id = f"pc{len(instances) + 1:04d}"
        instances[lita_id] = CardInstance(id=lita_id, card_code="01117", zone="deck", owner=investigator_slug)
        player_deck.append(lita_id)
    rng.shuffle(player_deck)
    hand, player_deck = draw_opening_hand_without_weaknesses(instances, player_deck, rng)

    got_away = normalize_got_away(cultists_got_away)
    encounter_deck = build_encounter_deck(instances, rng, return_variant=scenario == RETURN_SCENARIO)
    if ghoul_priest_alive:
        priest_id = next_encounter_id(instances)
        instances[priest_id] = CardInstance(id=priest_id, card_code="01116", zone="encounter_deck")
        encounter_deck.append(priest_id)
        rng.shuffle(encounter_deck)
    else:
        instances["setaside_ghoul_priest"] = CardInstance(id="setaside_ghoul_priest", card_code="01116", zone="set_aside")
    locations = build_locations(rng, return_variant=scenario == RETURN_SCENARIO)
    locations["main_path"].revealed = True
    reveal_location_fields(locations["main_path"])
    locations["main_path"].investigator_ids.append(investigator_slug)
    instances["setaside_ritual_site"] = CardInstance(id="setaside_ritual_site", card_code="01156", zone="set_aside")
    instances["setaside_umordhoth"] = CardInstance(id="setaside_umordhoth", card_code="01157", zone="set_aside")
    if scenario == RETURN_SCENARIO:
        instances["vault_of_earthly_demise"] = CardInstance(id="vault_of_earthly_demise", card_code="50032", zone="set_aside")
        instances["setaside_umordhoth"].attachments.append("vault_of_earthly_demise")
    for index, name in enumerate(got_away, start=1):
        code = NAMED_CULTIST_BY_NAME[name]
        instances[f"gotaway{index:02d}"] = CardInstance(id=f"gotaway{index:02d}", card_code=code, zone="set_aside")
    investigator = Investigator(
        id=investigator_slug,
        name=str(investigator_card["name"]),
        card_code=str(investigator_card["code"]),
        location_id="main_path",
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
    chaos = list(CHAOS_BAGS[difficulty])
    chaos.append("elderthing")
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
        agenda=AgendaState(code="01143", name="The Arkham Woods", stage=1, doom=setup_doom(len(got_away)), threshold=4),
        act=ActState(code="01146", name="Investigating the Trail", stage=1, clues_required=3),
        chaos_bag=ChaosBag(tokens=chaos),
        encounter_deck=encounter_deck,
    )
    state.limits["campaign_inputs"] = {
        "cultists_got_away": got_away,
        "past_midnight": past_midnight,
        "ghoul_priest_alive": ghoul_priest_alive,
        "lita_in_deck": lita_in_deck,
    }
    state.limits["mulligan_available"] = list(hand)
    present_mulligan_decision(state)
    return state


def normalize_got_away(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []
    names = [item.strip() for item in value.split(",")] if isinstance(value, str) else [str(item).strip() for item in value]
    names = [name for name in names if name]
    unknown = [name for name in names if name not in NAMED_CULTIST_BY_NAME]
    if unknown:
        raise EngineError(f"unknown cultist got away: {', '.join(unknown)}")
    return sorted(set(names))


def setup_doom(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 4:
        return 2
    return 3


def next_encounter_id(instances: dict[str, CardInstance]) -> str:
    used = [int(key[2:]) for key in instances if key.startswith("ec") and key[2:].isdigit()]
    return f"ec{(max(used) if used else 0) + 1:04d}"


def build_encounter_deck(instances: dict[str, CardInstance], rng: ArkhamRng, *, return_variant: bool) -> list[str]:
    counts = dict(CORE_ENCOUNTER_COUNTS)
    if return_variant:
        for code, count in RETURN_REPLACEMENTS.items():
            counts[code] = count
        for code, count in RETURN_COUNTS.items():
            counts[code] = count
    chosen_agents = rng.choice(sorted(AGENT_SETS))
    for code, count in AGENT_SETS[chosen_agents].items():
        counts[code] = count
    ids: list[str] = []
    index = 1
    for code, count in counts.items():
        for _ in range(count):
            instance_id = f"ec{index:04d}"
            instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="encounter_deck")
            ids.append(instance_id)
            index += 1
    rng.shuffle(ids)
    return ids


def build_locations(rng: ArkhamRng, *, return_variant: bool) -> dict[str, Location]:
    woods_pool = CORE_WOODS + (RETURN_WOODS if return_variant else [])
    chosen = list(woods_pool)
    rng.shuffle(chosen)
    chosen = chosen[:4]
    locations = {
        "main_path": Location(id="main_path", code="01149", name="Main Path", revealed=False, connections=[]),
    }
    for index, code in enumerate(chosen, start=1):
        locations[WOOD_IDS[code]] = Location(
            id=WOOD_IDS[code],
            code=code,
            name=f"Arkham Woods {index}",
            revealed=False,
            shroud=None,
            clues=0,
            connections=["main_path"],
        )
    update_connections(locations)
    return locations


def reveal_location_fields(location: Location) -> None:
    card = card_data.get_card(location.code)
    location.name = str(card.get("name", location.code))
    if location.code != "01149" and card.get("name") == "Arkham Woods":
        sub = {
            "01150": "Unhallowed Ground",
            "01151": "Twisting Paths",
            "01152": "Old House",
            "01153": "Cliffside",
            "01154": "Tangled Thicket",
            "01155": "Quiet Glade",
            "50033": "Great Willow",
            "50034": "Lakeside",
            "50035": "Corpse-Ridden Clearing",
            "50036": "Wooden Bridge",
        }.get(location.code)
        if sub:
            location.name = sub
    location.shroud = int(card.get("shroud") or 0)
    location.clues = int(card.get("clues") or 0)


def reveal_location(state: GameState, events: list[dict[str, Any]], location_id: str) -> None:
    location = state.locations[location_id]
    if location.revealed:
        return
    reveal_location_fields(location)
    location.revealed = True
    update_connections(state.locations)
    from ..effects import log_event

    log_event(events, "location_revealed", f"{location.name} was revealed.", location=location_id)


def update_connections(locations: dict[str, Location]) -> None:
    for location in locations.values():
        location.connections = []
    if "main_path" in locations:
        locations["main_path"].connections = sorted([loc_id for loc_id in locations if loc_id != "main_path"])
        if "ritual_site" in locations and "ritual_site" not in locations["main_path"].connections:
            locations["main_path"].connections.append("ritual_site")
    if "ritual_site" in locations:
        locations["ritual_site"].connections = ["main_path"] if "main_path" in locations else []
    for loc_id, location in locations.items():
        if loc_id in {"main_path", "ritual_site"}:
            continue
        connections = {"main_path"}
        if location.revealed:
            wanted = WOOD_FRONT_CONNECTION_SYMBOLS.get(location.code, set())
            for other_id, other in locations.items():
                if other_id in {"main_path", "ritual_site", loc_id} or not other.revealed:
                    continue
                if WOOD_SYMBOLS.get(other.code) in wanted:
                    connections.add(other_id)
        location.connections = sorted(loc for loc in connections if loc in locations)


def resolve_scenario_choice(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng) -> None:
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
        if state.limits.get("campaign_inputs", {}).get("past_midnight"):
            discard_random_from_hand(state, events, rng, 2, source="Past Midnight")
        log_event(events, "setup_complete", "Opening hand finalized.")
    elif choice in {"toggle_mulligan_card", "mulligan_card"}:
        toggle_mulligan_card(state, str(payload.get("card")))
        present_mulligan_decision(state)
    elif choice == "spawn_at_location":
        the_midnight_masks.resolve_spawn_at_location(state, payload, events, rng)
    elif choice == "mysterious_chanting_target":
        the_midnight_masks.place_doom_on_enemy(state, str(payload.get("enemy", "")), 2, events, source="Mysterious Chanting", rng=rng)
        discard_encounter_card(state, str(payload.get("card", "")))
    elif choice == "mask_target":
        the_midnight_masks.attach_mask_to_enemy(state, str(payload.get("card", "")), str(payload.get("enemy", "")), events, rng)
    elif choice == "disciple_doom":
        the_midnight_masks.place_doom_on_enemy(state, str(payload.get("enemy", "")), 1, events, source="Disciple of the Devourer", rng=rng)
    elif choice == "disciple_clue":
        enemy_id = str(payload.get("enemy", ""))
        if enemy_id in state.enemies and state.investigator.clues > 0:
            state.investigator.clues -= 1
            state.locations[state.enemies[enemy_id].location_id].clues += 1
    elif choice == "wrath_discard":
        card_id = str(payload.get("card", ""))
        if card_id in state.investigator.hand:
            player_cards.discard_from_hand(state, card_id)
            state.limits["wrath_remaining"] = int(state.limits.get("wrath_remaining", 1)) - 1
            continue_wrath(state)
    elif choice == "wrath_damage":
        state.limits["wrath_remaining"] = int(state.limits.get("wrath_remaining", 1)) - 1
        from ..effects import start_damage_assignment

        start_damage_assignment(state, events, source="Umordhoth's Wrath", damage=1, horror=1, resume={"kind": "scenario", "choice": "wrath_continue"}, rng=rng)
    elif choice == "wrath_continue":
        continue_wrath(state)


def discard_random_from_hand(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng, count: int, *, source: str) -> None:
    from ..effects import log_event

    for _ in range(count):
        if not state.investigator.hand:
            return
        card_id = rng.choice(state.investigator.hand)
        player_cards.discard_from_hand(state, card_id)
        log_event(events, "card_discarded", f"{source} discarded {card_name(state, card_id)}.", card=card_id)


def add_action_options(state: GameState, options: list[DecisionOption]) -> None:
    if state.status != "in_progress":
        return
    if state.act and state.act.code == "01148" and state.investigator.clues >= 1:
        options.append(DecisionOption("Spend 1 clue to disrupt with willpower", {"kind": "action", "action": "devourer_disrupt", "skill": "willpower"}))
        options.append(DecisionOption("Spend 1 clue to disrupt with agility", {"kind": "action", "action": "devourer_disrupt", "skill": "agility"}))
    if state.investigator.location_id == "quiet_glade" and not state.limits.get(f"quiet_glade:{state.round}") and (state.investigator.damage or state.investigator.horror):
        if state.investigator.damage:
            options.append(DecisionOption("Quiet Glade: heal 1 damage", {"kind": "action", "action": "devourer_quiet_glade", "heal": "damage"}))
        if state.investigator.horror:
            options.append(DecisionOption("Quiet Glade: heal 1 horror", {"kind": "action", "action": "devourer_quiet_glade", "heal": "horror"}))
    if state.investigator.location_id == "main_path":
        options.append(DecisionOption("Resign", {"kind": "action", "action": "resign"}))
    if umordhoth_at_investigator_location(state) and player_cards.controls_code(state, "01117"):
        options.append(DecisionOption("Throw Lita to Umordhoth", {"kind": "action", "action": "devourer_lita"}))


def execute_action(state: GameState, payload: dict[str, Any], events: list[dict[str, Any]], rng: ArkhamRng) -> bool:
    action = str(payload.get("action", ""))
    if action == "devourer_disrupt" and state.act and state.act.code == "01148" and state.investigator.clues >= 1:
        state.investigator.clues -= 1
        from .. import skill_test

        skill_test.start(state, events, skill=str(payload.get("skill", "willpower")), difficulty=3, source="Disrupting the Ritual", on_success={"kind": "devourer_disrupt"})
        return True
    if action == "devourer_quiet_glade" and state.investigator.location_id == "quiet_glade":
        state.limits[f"quiet_glade:{state.round}"] = True
        from ..effects import heal_roland

        if payload.get("heal") == "damage":
            heal_roland(state, events, damage=1)
        else:
            heal_roland(state, events, horror=1)
        return True
    if action == "devourer_lita":
        finalize_result(state, events, outcome="R3", resolution="R3", summary="R3: Lita was sacrificed", rng=rng)
        return True
    return False


def after_enter_location(state: GameState, events: list[dict[str, Any]], location_id: str, rng: ArkhamRng | None = None) -> None:
    reveal_location(state, events, location_id)
    if state.locations[location_id].code == "01150":
        from .. import skill_test

        skill_test.start(state, events, skill="willpower", difficulty=4, source="Unhallowed Ground", on_failure={"kind": "devourer_unhallowed"})
    if state.act and state.act.code == "01147" and location_id == "ritual_site":
        advance_act(state, events, rng=rng)


def before_move_from_twisting(state: GameState, destination: str, events: list[dict[str, Any]]) -> bool:
    if state.limits.pop("twisting_move_allowed", False):
        return False
    if state.locations[state.investigator.location_id].code != "01151":
        return False
    state.limits["twisting_destination"] = destination
    from .. import skill_test

    skill_test.start(state, events, skill="intellect", difficulty=3, source="Twisting Paths", on_success={"kind": "devourer_twisting"}, on_failure={"kind": "devourer_twisting"})
    return True


def finish_twisting_paths_move(state: GameState, events: list[dict[str, Any]], *, success: bool, rng: ArkhamRng | None = None) -> None:
    destination = str(state.limits.pop("twisting_destination", ""))
    if success and destination in state.locations:
        state.limits["twisting_move_allowed"] = True
        from ..actions import move

        move(state, destination, events, rng=rng)


def advance_act(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    if not state.act:
        return
    from ..effects import log_event

    if state.act.stage == 1:
        put_ritual_site_into_play(state, events)
        spawn_got_away_cultists(state, events)
        state.act = ActState(code="01147", name="Into the Darkness", stage=2, clues_required=None)
        log_event(events, "act_advanced", "Act advanced to Into the Darkness.")
    elif state.act.stage == 2:
        spawn_enemy_from_top_until(state, events, rng=rng, location_id="ritual_site", monster_only=False, doom=0)
        state.act = ActState(code="01148", name="Disrupting the Ritual", stage=3, clues_required=None)
        log_event(events, "act_advanced", "Act advanced to Disrupting the Ritual.")
    elif state.act.stage == 3:
        finalize_result(state, events, outcome="R1", resolution="R1", summary="R1: the ritual was broken", rng=rng)


def put_ritual_site_into_play(state: GameState, events: list[dict[str, Any]]) -> None:
    if "ritual_site" in state.locations:
        return
    state.locations["ritual_site"] = Location(id="ritual_site", code="01156", name="Ritual Site", revealed=True, shroud=3, clues=2, connections=["main_path"])
    update_connections(state.locations)
    from ..effects import log_event

    log_event(events, "location_put_into_play", "Ritual Site entered play.", location="ritual_site")


def spawn_got_away_cultists(state: GameState, events: list[dict[str, Any]]) -> None:
    from ..enemies import spawn_enemy

    for card_id, instance in list(state.card_instances.items()):
        if card_id.startswith("gotaway") and instance.zone == "set_aside":
            spawn_enemy(state, events, instance_id=card_id, location_id="main_path", engaged=False)


def place_clue_on_act(state: GameState, events: list[dict[str, Any]]) -> None:
    if not state.act:
        return
    state.limits["act3_clues"] = int(state.limits.get("act3_clues", 0)) + 1
    from ..effects import log_event

    log_event(events, "clue_placed", "Placed 1 clue on Disrupting the Ritual.", amount=1)
    if int(state.limits.get("act3_clues", 0)) >= 2:
        advance_act(state, events)


def check_agenda_advance(state: GameState, events: list[dict[str, Any]], *, rng: ArkhamRng | None = None) -> None:
    if not state.agenda or state.agenda.threshold <= 0:
        return
    while total_doom(state) >= state.agenda.threshold and state.status == "in_progress" and not state.decision_queue:
        from ..effects import clear_all_doom, log_event

        clear_all_doom(state)
        if state.agenda.stage == 1:
            spawn_enemy_from_top_until(state, events, rng=rng, location_id="main_path", monster_only=True, doom=1)
            state.agenda = AgendaState(code="01144", name="The Ritual Begins", stage=2, threshold=5)
            log_event(events, "agenda_advanced", "Agenda advanced to The Ritual Begins.")
        elif state.agenda.stage == 2:
            from .. import skill_test

            skill_test.start(state, events, skill="willpower", difficulty=6, source="The Ritual Begins", on_success={"kind": "devourer_agenda2"}, on_failure={"kind": "devourer_agenda2"})
            return
        elif state.agenda.stage == 3:
            advance_agenda3_to_devourer(state, events)
            return


def advance_to_agenda3(state: GameState, events: list[dict[str, Any]]) -> None:
    if state.status == "in_progress":
        state.agenda = AgendaState(code="01145", name="Vengeance Awaits", stage=3, threshold=5)
        from ..effects import log_event

        log_event(events, "agenda_advanced", "Agenda advanced to Vengeance Awaits.")


def advance_agenda3_to_devourer(state: GameState, events: list[dict[str, Any]]) -> None:
    put_ritual_site_into_play(state, events)
    if state.act and state.act.stage in {2, 3}:
        for enemy_id in list(state.locations["ritual_site"].enemy_ids):
            discard_enemy_from_play(state, enemy_id)
    spawn_umordhoth(state, events)
    state.agenda = AgendaState(code="01145b", name="The Devourer Below", stage=4, threshold=0)
    state.act = ActState(code="01145b", name="The Devourer Below", stage=4, clues_required=None)
    from ..effects import log_event

    log_event(events, "agenda_advanced", "The Devourer Below replaced the act and agenda.")


def spawn_umordhoth(state: GameState, events: list[dict[str, Any]]) -> None:
    from ..enemies import spawn_enemy

    enemy_id = "setaside_umordhoth"
    if enemy_id in state.enemies:
        return
    spawn_enemy(state, events, instance_id=enemy_id, location_id="ritual_site", engaged=False)
    if state.scenario == RETURN_SCENARIO:
        resources = max(1, 4 - (state.act.stage if state.act else 3))
        state.card_instances["vault_of_earthly_demise"].zone = "attachment"
        state.card_instances["vault_of_earthly_demise"].uses["resource"] = resources
        state.enemies[enemy_id].attachments.append("vault_of_earthly_demise")


def spawn_enemy_from_top_until(state: GameState, events: list[dict[str, Any]], *, rng: ArkhamRng | None, location_id: str, monster_only: bool, doom: int) -> str | None:
    from ..enemies import spawn_enemy

    if state.encounter_discard:
        if rng is None:
            raise EngineError("encounter dig reshuffle requires the game RNG")
        state.encounter_deck = list(state.encounter_deck) + list(state.encounter_discard)
        state.encounter_discard = []
        for instance_id in state.encounter_deck:
            state.card_instances[instance_id].zone = "encounter_deck"
        rng.shuffle(state.encounter_deck)
        from ..effects import log_event

        log_event(events, "encounter_reshuffled", "Encounter discard was shuffled into the encounter deck.")
    searched: list[str] = []
    found = None
    while state.encounter_deck:
        card_id = state.encounter_deck.pop(0)
        searched.append(card_id)
        card = card_data.get_card(state.card_instances[card_id].card_code)
        if card.get("type_code") == "enemy" and (not monster_only or "Monster" in str(card.get("traits", ""))):
            found = card_id
            break
    for card_id in searched:
        if card_id != found:
            state.encounter_discard.append(card_id)
            state.card_instances[card_id].zone = "encounter_discard"
    if found:
        spawn_enemy(state, events, instance_id=found, location_id=location_id, engaged=False)
        if doom and found in state.enemies:
            state.enemies[found].doom += doom
    return found


def total_doom(state: GameState) -> int:
    return (state.agenda.doom if state.agenda else 0) + sum(enemy.doom for enemy in state.enemies.values()) + sum(inst.doom for inst in state.card_instances.values())


def end_mythos_phase(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None) -> None:
    for enemy_id in sorted(state.enemies):
        code = state.enemies[enemy_id].card_code
        if code == "01170":
            the_midnight_masks.place_doom_on_enemy(state, enemy_id, 1, events, source="Wizard of the Order", rng=rng)
        elif code == "50042":
            the_midnight_masks.place_doom_on_enemy(state, enemy_id, 1, events, source="Corpse-Taker", rng=rng)


def end_enemy_phase(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None = None) -> None:
    from ..enemies import move_enemy_to, next_step_toward
    from ..effects import place_doom

    for enemy_id in sorted(list(state.enemies)):
        if enemy_id not in state.enemies or state.enemies[enemy_id].card_code != "50042":
            continue
        enemy = state.enemies[enemy_id]
        if enemy.location_id == "main_path":
            doom = enemy.doom
            if doom:
                enemy.doom = 0
                place_doom(state, doom, events, source="Corpse-Taker", rng=rng, can_advance=True)
            continue
        step = next_step_toward(state, enemy.location_id, "main_path", enemy_id)
        if step:
            move_enemy_to(state, events, enemy_id, step)


def end_round(state: GameState, events: list[dict[str, Any]]) -> None:
    if "ritual_site" in state.locations and state.locations["ritual_site"].clues < 2:
        state.locations["ritual_site"].clues = 2
    for enemy in state.enemies.values():
        if enemy.card_code == "01179":
            enemy.damage = max(0, enemy.damage - 2)


def end_investigator_turn(state: GameState, events: list[dict[str, Any]]) -> None:
    for enemy_id, enemy in state.enemies.items():
        if enemy.card_code == "01157" and enemy.exhausted:
            enemy.exhausted = False
            from ..effects import log_event

            log_event(events, "enemy_readied", "Umordhoth readied at end of turn.", enemy=enemy_id)


def massive_attackers(state: GameState, attacked: set[str]) -> list[str]:
    return [
        enemy_id
        for enemy_id, enemy in state.enemies.items()
        if enemy.card_code == "01157"
        and enemy.location_id == state.investigator.location_id
        and not enemy.exhausted
        and enemy_id not in attacked
        and enemy_id not in state.investigator.engaged_enemies
    ]


def umordhoth_at_investigator_location(state: GameState) -> bool:
    return any(enemy.card_code == "01157" and enemy.location_id == state.investigator.location_id for enemy in state.enemies.values())


def vault_resources(state: GameState) -> int:
    if "vault_of_earthly_demise" not in state.card_instances:
        return 0
    return int(state.card_instances["vault_of_earthly_demise"].uses.get("resource", 0))


def enemy_fight_bonus(state: GameState, enemy_id: str) -> int:
    bonus = 1 if state.agenda and state.agenda.stage == 2 else 0
    if enemy_id in state.enemies and state.enemies[enemy_id].card_code == "01157":
        bonus += vault_resources(state)
    return bonus


def enemy_evade_bonus(state: GameState, enemy_id: str) -> int:
    return 1 if state.agenda and state.agenda.stage == 2 else 0


def damage_amount_to_enemy(state: GameState, enemy_id: str, amount: int) -> int:
    enemy = state.enemies.get(enemy_id)
    if enemy and enemy.location_id in state.locations and state.locations[enemy.location_id].code == "50035":
        return min(amount, 1)
    return amount


def after_enemy_defeated(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> bool:
    if state.card_instances[enemy_id].card_code == "01157":
        finalize_result(state, events, outcome="R2", resolution="R2", summary="R2: Umordhoth was defeated")
        return True
    return False


def encounter_revelation(state: GameState, rng: ArkhamRng, events: list[dict[str, Any]], instance_id: str) -> bool:
    code = state.card_instances[instance_id].card_code
    if code in {"50041", "50042"}:
        the_midnight_masks.spawn_farthest_empty_location_enemy(state, events, instance_id, rng)
        return True
    if code in {"01169", "01170"}:
        the_midnight_masks.spawn_any_empty_location_enemy(state, events, instance_id)
        return True
    if code == "01171":
        the_midnight_masks.mysterious_chanting(state, events, rng, instance_id)
        return True
    if code == "50043":
        the_midnight_masks.mask_of_umordhoth(state, events, rng, instance_id)
        return True
    if code == "01158":
        discard_encounter_card(state, instance_id)
        from .. import skill_test

        skill_test.start(state, events, skill="willpower", difficulty=5, source="Umordhoth's Wrath", on_failure={"kind": "umordhoths_wrath"})
        return True
    if code == "50037":
        discard_encounter_card(state, instance_id)
        if not state.investigator.hand:
            finalize_result(state, events, outcome="no_resolution", resolution="no_resolution", summary="Umordhoth's Hunger killed the investigator")
            return True
        discard_random_from_hand(state, events, rng, 1, source="Umordhoth's Hunger")
        for enemy in state.enemies.values():
            enemy.damage = max(0, enemy.damage - 1)
        return True
    return False


def discard_encounter_card(state: GameState, instance_id: str) -> None:
    if instance_id in state.encounter_deck:
        state.encounter_deck.remove(instance_id)
    if instance_id not in state.encounter_discard:
        state.encounter_discard.append(instance_id)
    if instance_id in state.card_instances:
        state.card_instances[instance_id].zone = "encounter_discard"


def present_wrath_choices(state: GameState, margin: int) -> None:
    state.limits["wrath_remaining"] = margin
    continue_wrath(state)


def continue_wrath(state: GameState) -> None:
    remaining = int(state.limits.get("wrath_remaining", 0))
    if remaining <= 0:
        state.limits.pop("wrath_remaining", None)
        return
    options = [
        DecisionOption("Take 1 damage and 1 horror", {"kind": "scenario", "choice": "wrath_damage"}),
    ]
    for card_id in state.investigator.hand:
        options.append(DecisionOption(f"Discard {card_name(state, card_id)}", {"kind": "scenario", "choice": "wrath_discard", "card": card_id}))
    state.decision_queue = [PendingDecision(id="umordhoths-wrath", kind="scenario", prompt=f"Resolve {remaining} more Umordhoth's Wrath effect.", options=options)]


MADNESS_WEAKNESSES = ["01096", "01097", "01099", "01100"]


def gain_madness_weakness(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng | None, *, to_hand: bool) -> str:
    if rng is None:
        raise EngineError("Madness weakness selection requires the game RNG")
    code = rng.choice(MADNESS_WEAKNESSES)
    instance_id = f"weak{len([key for key in state.card_instances if key.startswith('weak')]) + 1:02d}"
    zone = "hand" if to_hand else "deck"
    state.card_instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone=zone, owner=state.investigator.id)
    if to_hand:
        state.investigator.hand.append(instance_id)
    else:
        state.investigator.deck.append(instance_id)
    gained = list(state.limits.get("weakness_gained", []))
    gained.append(code)
    state.limits["weakness_gained"] = gained
    from ..effects import log_event

    log_event(events, "weakness_gained", f"Gained {card_data.get_card(code)['name']}.", card=instance_id, code=code)
    return code


def monster_enemies_in_play(state: GameState) -> int:
    return sum(1 for enemy in state.enemies.values() if "Monster" in str(card_data.get_card(enemy.card_code).get("traits", "")))


def nearest_enemies_any(state: GameState) -> list[str]:
    return the_midnight_masks.nearest_enemies(state, list(state.enemies))


def apply_token_aftermath(state: GameState, events: list[dict[str, Any]], result: dict[str, Any], rng: ArkhamRng | None = None) -> None:
    tokens = [str(result.get("token"))] + [str(token) for token in result.get("extra_tokens", [])]
    if "cultist" in tokens and not result.get("reveal_effects_applied"):
        nearest = nearest_enemies_any(state)
        amount = 1 if state.difficulty in {"easy", "standard"} else 2
        if nearest:
            the_midnight_masks.place_doom_on_enemy(state, nearest[0], amount, events, source="Chaos token", rng=rng)
    if "tablet" in tokens and not result.get("reveal_effects_applied") and monster_at_investigator_location(state):
        from ..effects import start_damage_assignment

        if state.difficulty in {"easy", "standard"}:
            start_damage_assignment(state, events, source="Tablet token", damage=1, horror=0)
        else:
            start_damage_assignment(state, events, source="Tablet token", damage=1, horror=1)
    if "skull" in tokens and state.difficulty in {"hard", "expert"} and not result.get("success") and rng is not None:
        draw_monster_from_deck_or_discard(state, events, rng)


def apply_token_reveal_effects(state: GameState, events: list[dict[str, Any]], test: dict[str, Any], rng: ArkhamRng | None = None) -> None:
    tokens = [str(test.get("token"))] + [str(token) for token in test.get("extra_tokens", [])]
    if "cultist" in tokens:
        nearest = nearest_enemies_any(state)
        amount = 1 if state.difficulty in {"easy", "standard"} else 2
        if nearest:
            the_midnight_masks.place_doom_on_enemy(state, nearest[0], amount, events, source="Chaos token", rng=rng)
    if "tablet" in tokens and monster_at_investigator_location(state):
        from ..effects import start_damage_assignment

        if state.difficulty in {"easy", "standard"}:
            start_damage_assignment(state, events, source="Tablet token", damage=1, horror=0)
        else:
            start_damage_assignment(state, events, source="Tablet token", damage=1, horror=1)


def monster_at_investigator_location(state: GameState) -> bool:
    return any(
        enemy_id in state.enemies and "Monster" in str(card_data.get_card(state.enemies[enemy_id].card_code).get("traits", ""))
        for enemy_id in state.locations[state.investigator.location_id].enemy_ids
    )


def draw_monster_from_deck_or_discard(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    from ..encounter import resolve_revelation

    for card_id in list(state.encounter_deck) + list(state.encounter_discard):
        card = card_data.get_card(state.card_instances[card_id].card_code)
        if card.get("type_code") == "enemy" and "Monster" in str(card.get("traits", "")):
            if card_id in state.encounter_deck:
                state.encounter_deck.remove(card_id)
            if card_id in state.encounter_discard:
                state.encounter_discard.remove(card_id)
            state.card_instances[card_id].zone = "encounter_drawn"
            resolve_revelation(state, rng, events, card_id)
            rng.shuffle(state.encounter_deck)
            return


def location_extra_token_applies(state: GameState, test: dict[str, Any]) -> bool:
    code = state.locations[state.investigator.location_id].code
    callback = dict(test.get("on_success", {}))
    fail_callback = dict(test.get("on_failure", {}))
    kind = callback.get("kind") or fail_callback.get("kind")
    if code == "50034" and kind == "investigate":
        return True
    if code == "50036" and kind == "evade":
        return True
    return False


def after_skill_test(state: GameState, events: list[dict[str, Any]], test: dict[str, Any], result: dict[str, Any], rng: ArkhamRng | None) -> None:
    if not result.get("success") or state.locations[state.investigator.location_id].code != "50033":
        return
    key = f"great_willow:{state.round}"
    source = str(test.get("source", ""))
    if state.limits.get(key) or source.startswith(("Investigate", "Fight", "Evade", "Disrupting")):
        return
    state.limits[key] = True
    from ..effects import log_event

    log_event(events, "surge", "Great Willow caused the treachery to surge.")
    if rng is not None and state.status == "in_progress":
        from ..encounter import draw_encounter

        draw_encounter(state, rng, events)


def discard_enemy_from_play(state: GameState, enemy_id: str) -> None:
    if enemy_id not in state.enemies:
        return
    enemy = state.enemies.pop(enemy_id)
    if enemy.location_id in state.locations and enemy_id in state.locations[enemy.location_id].enemy_ids:
        state.locations[enemy.location_id].enemy_ids.remove(enemy_id)
    if enemy_id in state.investigator.engaged_enemies:
        state.investigator.engaged_enemies.remove(enemy_id)
    state.card_instances[enemy_id].zone = "encounter_discard"
    state.encounter_discard.append(enemy_id)


def resign(state: GameState, events: list[dict[str, Any]]) -> None:
    finalize_result(state, events, outcome="no_resolution", resolution="no_resolution", summary=f"{state.investigator.name} resigned", resigned=True)


def finalize_result(
    state: GameState,
    events: list[dict[str, Any]],
    *,
    outcome: str,
    summary: str,
    resolution: str | None = None,
    resigned: bool = False,
    rng: ArkhamRng | None = None,
) -> None:
    from ..effects import apply_cover_up_trauma
    from .the_gathering import add_victory_locations, calculate_victory_points

    if state.status == "ended" and state.result and state.result.get("scenario") == state.scenario:
        return
    apply_cover_up_trauma(state, events)
    add_victory_locations(state)
    victory_points = calculate_victory_points(state)
    bonus = 5 if outcome == "R1" else (10 if outcome == "R2" else 0)
    xp = victory_points + bonus
    hospital_debts_penalty = hospital_debts_xp_penalty(state)
    if hospital_debts_penalty:
        xp = max(0, xp - hospital_debts_penalty)
    trauma = dict(state.trauma)
    if outcome == "R1":
        trauma["mental"] = int(trauma.get("mental", 0)) + 2
    elif outcome in {"R2", "R3"}:
        trauma["physical"] = int(trauma.get("physical", 0)) + 2
        trauma["mental"] = int(trauma.get("mental", 0)) + 2
    state.trauma = trauma
    if outcome == "R3":
        gain_madness_weakness(state, events, rng, to_hand=False)
    killed = outcome == "no_resolution"
    score = 0 if outcome == "no_resolution" else max(0, xp - total_trauma(state))
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
        "investigator_killed": killed,
        "investigator_insane": False,
        "encounter_cards_drawn": int(state.limits.get("encounter_cards_drawn", 0)),
        "enemies_defeated": int(state.limits.get("enemies_defeated", 0)),
        "campaign": campaign_block(state, outcome),
    }
    from ..effects import log_event

    log_event(events, "game_end", summary)


def campaign_block(state: GameState, outcome: str) -> dict[str, Any]:
    block: dict[str, Any] = {
        "scenario": state.scenario,
        "inputs": dict(state.limits.get("campaign_inputs", {})),
        "arkham_succumbed": outcome == "no_resolution",
        "ritual_broken": outcome == "R1",
        "umordhoth_repelled": outcome == "R2",
        "lita_sacrificed": outcome == "R3",
        "investigator_killed": outcome == "no_resolution",
        "elderthing_added": True,
    }
    if state.limits.get("weakness_gained"):
        block["weakness_gained"] = list(state.limits.get("weakness_gained", []))
        block["weaknesses_added"] = list(state.limits.get("weakness_gained", []))
    return block
