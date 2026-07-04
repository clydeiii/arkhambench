"""The Gathering scenario and the small phase-B engine fixture."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import data as card_data
from ..model import GATHERING_FAMILY as model_GATHERING_FAMILY, ActState, AgendaState, CardInstance, ChaosBag, DecisionOption, GameState, Investigator, Location, PendingDecision, TurnState
from ..cards import player as player_cards
from ..cards.player import card_name
from ..cards.registry import REGISTRY
from ..errors import EngineError
from ..rng import ArkhamRng


# Campaign-equity value of earning Lita Chantler, added to the benchmark score.
LITA_SCORE_VALUE = 3

CHAOS_BAGS: dict[str, list[str]] = {
    "easy": ["+1", "+1", "0", "0", "0", "-1", "-1", "-1", "-2", "-2", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
    "standard": ["+1", "0", "0", "-1", "-1", "-1", "-2", "-2", "-3", "-4", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
    "hard": ["0", "0", "0", "-1", "-1", "-2", "-2", "-3", "-3", "-4", "-5", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
    "expert": ["0", "-1", "-1", "-2", "-2", "-3", "-3", "-4", "-4", "-5", "-6", "-8", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
}

PLAYER_WEAKNESSES = {"01007", "01102"}
LOCATION_INFO = {
    "hallway": ("01112", "Hallway", 1, 0, ["attic", "cellar", "parlor"]),
    "attic": ("01113", "Attic", 1, 2, ["hallway"]),
    "cellar": ("01114", "Cellar", 4, 2, ["hallway"]),
    "parlor": ("01115", "Parlor", 2, 0, ["hallway"]),
}
ENCOUNTER_COUNTS = {
    "01118": 1,
    "01119": 1,
    "01159": 3,
    "01160": 3,
    "01161": 1,
    "01162": 3,
    "01163": 3,
    "01164": 2,
    "01165": 2,
    "01166": 3,
    "01167": 2,
    "01168": 2,
    "01174": 2,
}

RETURN_SCENARIO = "return_to_the_gathering"
GATHERING_FAMILY = model_GATHERING_FAMILY

# Return to The Gathering swaps the Ghouls set (01160 x3, 01161 x1, 01162 x3 — 7 cards)
# for Ghouls of Umôrdhoth (50038 x3, 50039 x1, 50040 x3 — 7 cards) and adds the Return
# set's deck cards (50022, 50023, 50024 x2). Everything else matches the core scenario.
RETURN_ENCOUNTER_COUNTS = {
    "01118": 1,
    "01119": 1,
    "01159": 3,
    "50038": 3,
    "50039": 1,
    "50040": 3,
    "01163": 3,
    "01164": 2,
    "01165": 2,
    "01166": 3,
    "01167": 2,
    "01168": 2,
    "01174": 2,
    "50022": 1,
    "50023": 1,
    "50024": 2,
}

# id: (code, unrevealed_name, revealed_name, shroud, clues, connections-when-in-play)
# Connections were transcribed and verified from the physical card scans (see
# specs/phase_v6_return.md). Neighbors are linked only once both sides are in play.
RETURN_LOCATION_INFO: dict[str, tuple[str, str, str, int, int, list[str]]] = {
    "study": ("50013", "Study (Aberrant Gateway)", "Study (Aberrant Gateway)", 3, 1, ["guest_hall"]),
    "guest_hall": ("50014", "Guest Hall", "Guest Hall", 1, 0, ["study", "bedroom", "bathroom", "hallway"]),
    "bedroom": ("50015", "Bedroom", "Bedroom", 2, 1, ["guest_hall"]),
    "bathroom": ("50016", "Bathroom", "Bathroom", 1, 1, ["guest_hall"]),
    "hallway": ("50017", "Hole in the Wall", "Hallway", 1, 0, ["guest_hall", "attic", "cellar", "parlor"]),
    "attic": ("50018", "Attic", "Attic", 3, 1, ["hallway", "field_of_graves"]),
    "cellar": ("50020", "Cellar", "Cellar", 2, 1, ["hallway", "ghoul_pits"]),
    "parlor": ("01115", "Parlor", "Parlor", 2, 0, ["hallway"]),
    "field_of_graves": ("50019", "Far Above Your House", "Field of Graves", 2, 1, ["attic"]),
    "ghoul_pits": ("50021", "Deep Below Your House", "Ghoul Pits", 4, 1, ["cellar"]),
}
# Original core Attic/Cellar stats when the random setup picks the old versions.
RETURN_ORIGINAL_VARIANTS = {
    "attic": ("01113", "Attic", "Attic", 1, 2, ["hallway"]),
    "cellar": ("01114", "Cellar", "Cellar", 4, 2, ["hallway"]),
}


def is_return(state: GameState) -> bool:
    return state.scenario == RETURN_SCENARIO


def return_location_info(state: GameState, location_id: str) -> tuple[str, str, str, int, int, list[str]]:
    variant_key = f"return_variant:{location_id}"
    if state.limits.get(variant_key) == "original":
        return RETURN_ORIGINAL_VARIANTS[location_id]
    return RETURN_LOCATION_INFO[location_id]


def build_gathering_state(
    *,
    difficulty: str,
    rng: ArkhamRng,
    deck_path: str | Path | None = None,
    investigator_slug: str = "roland",
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

    encounter_deck = build_encounter_deck(instances)
    rng.shuffle(encounter_deck)
    ghoul_priest = "setaside_ghoul_priest"
    lita = "setaside_lita"
    instances[ghoul_priest] = CardInstance(id=ghoul_priest, card_code="01116", zone="set_aside")
    instances[lita] = CardInstance(id=lita, card_code="01117", zone="set_aside")

    investigator = Investigator(
        id=investigator_slug,
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
        actions_remaining=starting_actions(investigator_code),
        hand=hand,
        deck=player_deck,
    )
    state = GameState(
        schema_version=2,
        scenario="the_gathering",
        difficulty=difficulty,
        status="in_progress",
        round=1,
        phase="Investigation",
        turn=TurnState(investigator_id=investigator_slug, action_index=0),
        investigator=investigator,
        card_instances=instances,
        locations={
            "study": Location(id="study", code="01111", name="Study", revealed=True, shroud=2, clues=2, connections=[], investigator_ids=[investigator_slug]),
        },
        agenda=AgendaState(code="01105", name="What's Going On?!", stage=1, threshold=3),
        act=ActState(code="01108", name="Trapped", stage=1, clues_required=2),
        chaos_bag=ChaosBag(tokens=list(CHAOS_BAGS[difficulty])),
        encounter_deck=encounter_deck,
    )
    state.limits["mulligan_available"] = list(hand)
    present_mulligan_decision(state)
    return state


def build_return_state(
    *,
    difficulty: str,
    rng: ArkhamRng,
    deck_path: str | Path | None = None,
    investigator_slug: str = "roland",
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

    encounter_deck = build_return_encounter_deck(instances)
    rng.shuffle(encounter_deck)
    instances["setaside_ghoul_priest"] = CardInstance(id="setaside_ghoul_priest", card_code="01116", zone="set_aside")
    instances["setaside_lita"] = CardInstance(id="setaside_lita", card_code="01117", zone="set_aside")

    investigator = Investigator(
        id=investigator_slug,
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
        actions_remaining=starting_actions(investigator_code),
        hand=hand,
        deck=player_deck,
    )
    state = GameState(
        schema_version=2,
        scenario=RETURN_SCENARIO,
        difficulty=difficulty,
        status="in_progress",
        round=1,
        phase="Investigation",
        turn=TurnState(investigator_id=investigator_slug, action_index=0),
        investigator=investigator,
        card_instances=instances,
        locations={},
        agenda=AgendaState(code="01105", name="What's Going On?!", stage=1, threshold=3),
        act=ActState(code="50012", name="Mysterious Gateway", stage=1, clues_required=3),
        chaos_bag=ChaosBag(tokens=list(CHAOS_BAGS[difficulty])),
        encounter_deck=encounter_deck,
    )
    # Setup card 50011: choose one of the two Attic and one of the two Cellar
    # versions at random; the other copies are removed from the game.
    state.limits["return_variant:attic"] = rng.choice(["original", "return"])
    state.limits["return_variant:cellar"] = rng.choice(["original", "return"])
    put_return_location_into_play(state, [], "study", revealed=True)
    for location_id in ("guest_hall", "bedroom", "bathroom"):
        put_return_location_into_play(state, [], location_id)
    state.locations["study"].investigator_ids.append(investigator_slug)
    state.limits["mulligan_available"] = list(hand)
    present_mulligan_decision(state)
    return state


def build_return_encounter_deck(instances: dict[str, CardInstance]) -> list[str]:
    ids: list[str] = []
    index = 1
    for code, count in RETURN_ENCOUNTER_COUNTS.items():
        for _ in range(count):
            instance_id = f"ec{index:04d}"
            instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="encounter_deck")
            ids.append(instance_id)
            index += 1
    return ids


def put_return_location_into_play(
    state: GameState,
    events: list[dict[str, Any]],
    location_id: str,
    *,
    revealed: bool = False,
) -> None:
    if location_id in state.locations:
        return
    code, unrevealed_name, revealed_name, shroud, clues, connections = return_location_info(state, location_id)
    if location_id == "hallway" and not revealed:
        # Hole in the Wall (the unrevealed face) connects only to the Guest Hall;
        # the full Hallway connections apply once it is revealed (RR: unrevealed-
        # side connection icons govern while unrevealed).
        connections = ["guest_hall"]
    in_play = [neighbor for neighbor in connections if neighbor in state.locations]
    state.locations[location_id] = Location(
        id=location_id,
        code=code,
        name=revealed_name if revealed else unrevealed_name,
        revealed=revealed,
        shroud=shroud if revealed else None,
        clues=clues if revealed else 0,
        connections=in_play,
    )
    for neighbor in in_play:
        neighbor_connections = state.locations[neighbor].connections
        if location_id not in neighbor_connections:
            neighbor_connections.append(location_id)
    if events:
        from ..effects import log_event

        log_event(events, "location_added", f"{state.locations[location_id].name} was put into play.", location=location_id)


def starting_actions(investigator_code: str) -> int:
    return 4 if investigator_code == "01002" else 3


def build_player_deck(
    instances: dict[str, CardInstance],
    deck_path: str | Path | None,
    *,
    investigator_slug: str,
) -> list[str]:
    actual_path = Path(deck_path) if deck_path else card_data.default_deck_for_investigator(investigator_slug)
    deck = card_data.load_deck(actual_path)
    expected_code = card_data.INVESTIGATOR_CODES[investigator_slug]
    deck_investigator = deck.get("investigator_code")
    if deck_investigator and str(deck_investigator) != expected_code:
        raise EngineError(
            f"deck investigator_code {deck_investigator} does not match {investigator_slug} ({expected_code})"
        )
    missing = sorted(str(code) for code in deck["slots"] if str(code) not in REGISTRY)
    if missing:
        raise EngineError(f"deck contains unimplemented card codes: {', '.join(missing)}")
    deck_ids: list[str] = []
    index = 1
    for code, count in deck["slots"].items():
        for _ in range(int(count)):
            instance_id = f"pc{index:04d}"
            instances[instance_id] = CardInstance(
                id=instance_id,
                card_code=str(code),
                zone="player_deck",
                owner=investigator_slug,
            )
            deck_ids.append(instance_id)
            index += 1
    return deck_ids


def draw_opening_hand_without_weaknesses(
    instances: dict[str, CardInstance],
    deck: list[str],
    rng: ArkhamRng,
) -> tuple[list[str], list[str]]:
    hand: list[str] = []
    set_aside: list[str] = []
    while len(hand) < 5 and deck:
        card_id = deck.pop(0)
        if is_player_weakness(instances[card_id].card_code):
            set_aside.append(card_id)
        else:
            instances[card_id].zone = "hand"
            hand.append(card_id)
    deck.extend(set_aside)
    rng.shuffle(deck)
    return hand, deck


def present_mulligan_decision(state: GameState) -> None:
    cards = card_data.cards_by_code()
    available = set(state.limits.get("mulligan_available", state.investigator.hand))
    options = [DecisionOption("Keep opening hand", {"kind": "scenario", "choice": "keep_hand"})]
    for card_id in state.investigator.hand:
        if card_id not in available:
            continue
        card = cards[state.card_instances[card_id].card_code]
        options.append(DecisionOption(f"Mulligan {card.get('name', card_id)}", {"kind": "scenario", "choice": "mulligan_card", "card": card_id}))
    hand_names = ", ".join(cards[state.card_instances[cid].card_code].get("name", cid) for cid in state.investigator.hand)
    state.decision_queue = [
        PendingDecision(
            id="opening-mulligan",
            kind="scenario",
            prompt=f"Opening hand: {hand_names}. Choose cards to mulligan (one at a time; weaknesses are never dealt into your opening hand), then keep.",
            options=options,
        )
    ]


def build_encounter_deck(instances: dict[str, CardInstance]) -> list[str]:
    ids: list[str] = []
    index = 1
    for code, count in ENCOUNTER_COUNTS.items():
        for _ in range(count):
            instance_id = f"ec{index:04d}"
            instances[instance_id] = CardInstance(id=instance_id, card_code=code, zone="encounter_deck")
            ids.append(instance_id)
            index += 1
    return ids


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
        aside = state.limits.pop("mulliganed_aside", [])
        for aside_id in aside:
            state.card_instances[str(aside_id)].zone = "player_deck"
            state.investigator.deck.append(str(aside_id))
        if aside:
            rng.shuffle(state.investigator.deck)
        final_hand = ", ".join(card_name(state, cid) for cid in state.investigator.hand)
        log_event(events, "setup_complete", f"Opening hand finalized: {final_hand}.")
        if is_return(state):
            attic_variant = state.limits.get("return_variant:attic", "return")
            cellar_variant = state.limits.get("return_variant:cellar", "return")
            log_event(
                events,
                "setup_variants",
                f"Setup chose the {attic_variant} Attic and the {cellar_variant} Cellar.",
                attic=attic_variant,
                cellar=cellar_variant,
            )
    elif choice == "mulligan_card":
        mulligan_card(state, str(payload.get("card")), events, rng)
        present_mulligan_decision(state)
    elif choice == "agenda1_discard":
        agenda1_discard(state, events, rng)
        set_agenda_2(state, events)
        finish_mythos_after_agenda_choice(state, events, rng)
    elif choice == "agenda1_horror":
        from ..effects import start_damage_assignment

        set_agenda_2(state, events)
        start_damage_assignment(
            state,
            events,
            source="What's Going On?!",
            damage=0,
            horror=2,
            resume={"kind": "scenario", "choice": "finish_mythos_after_agenda"},
        )
        if state.status == "in_progress" and not state.pending_damage and not state.decision_queue:
            finish_mythos_after_agenda_choice(state, events, rng)
    elif choice == "finish_mythos_after_agenda":
        finish_mythos_after_agenda_choice(state, events, rng)
    elif choice == "act2_advance":
        from ..effects import spend_clues

        if state.act and spend_clues(state, 3, events):
            advance_act(state, events)
        start_next_round_after_end_round_choice(state, events)
    elif choice == "act2_wait":
        from ..effects import log_event

        log_event(events, "act_objective_declined", "Roland did not advance The Barrier.")
        start_next_round_after_end_round_choice(state, events)
    elif choice == "resolution_r1":
        from ..effects import log_event

        state.trauma["mental"] = int(state.trauma.get("mental", 0)) + 1
        finalize_result(state, events, outcome="R1", resolution="R1", summary="R1: the house burned down")
        log_event(events, "game_end", "R1: the house burned down")
    elif choice == "resolution_r2":
        from ..effects import log_event

        finalize_result(state, events, outcome="R2", resolution="R2", summary="R2: the house still stands")
        log_event(events, "game_end", "R2: the house still stands")


def mulligan_card(state: GameState, card_id: str, events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    from ..effects import log_event

    if card_id not in state.investigator.hand:
        return
    available = list(state.limits.get("mulligan_available", []))
    if card_id not in available:
        return
    available.remove(card_id)
    state.limits["mulligan_available"] = available
    state.investigator.hand.remove(card_id)
    # RAW: mulliganed cards are set aside and only shuffled back after the
    # opening hand is finalized — you cannot redraw a card you just tossed.
    state.card_instances[card_id].zone = "aside"
    aside = list(state.limits.get("mulliganed_aside", []))
    aside.append(card_id)
    state.limits["mulliganed_aside"] = aside
    replacement = draw_one_nonweakness(state.card_instances, state.investigator.deck, rng)
    if replacement:
        state.investigator.hand.append(replacement)
    out_name = card_name(state, card_id)
    in_name = card_name(state, replacement) if replacement else "nothing (deck empty)"
    log_event(events, "mulligan", f"Mulliganed {out_name}, drew {in_name}.", out=card_id, drew=replacement)


def draw_one_nonweakness(
    instances: dict[str, CardInstance],
    deck: list[str],
    rng: ArkhamRng,
) -> str | None:
    set_aside: list[str] = []
    found: str | None = None
    while deck and found is None:
        card_id = deck.pop(0)
        if is_player_weakness(instances[card_id].card_code):
            set_aside.append(card_id)
        else:
            instances[card_id].zone = "hand"
            found = card_id
    deck.extend(set_aside)
    rng.shuffle(deck)
    return found


def is_player_weakness(card_code: str) -> bool:
    card = card_data.get_card(card_code)
    return str(card.get("subtype_code", "")) in {"weakness", "basicweakness"}


def reveal_location(state: GameState, events: list[dict[str, Any]], location_id: str) -> None:
    from ..effects import log_event

    location = state.locations[location_id]
    if location.revealed:
        return
    if is_return(state):
        reveal_return_location(state, events, location_id)
        return
    location.revealed = True
    _, _, shroud, clues, _ = LOCATION_INFO[location_id]
    location.shroud = shroud
    location.clues = clues
    log_event(events, "location_revealed", f"{location.name} was revealed.", location=location_id)


def reveal_return_location(state: GameState, events: list[dict[str, Any]], location_id: str) -> None:
    from .. import skill_test
    from ..effects import log_event

    location = state.locations[location_id]
    code, _unrevealed_name, revealed_name, shroud, clues, connections = return_location_info(state, location_id)
    location.revealed = True
    location.name = revealed_name
    location.shroud = shroud
    location.clues = clues
    log_event(events, "location_revealed", f"{location.name} was revealed.", location=location_id)
    variant = state.limits.get(f"return_variant:{location_id}")
    if location_id == "hallway":
        # The Hole in the Wall flips to the Hallway: restore its printed
        # connections and put the set-aside Attic, Cellar, and Parlor into play.
        for neighbor_id in ("attic", "cellar", "parlor"):
            put_return_location_into_play(state, events, neighbor_id)
        for neighbor_id in connections:
            if neighbor_id in state.locations:
                if neighbor_id not in location.connections:
                    location.connections.append(neighbor_id)
                if location_id not in state.locations[neighbor_id].connections:
                    state.locations[neighbor_id].connections.append(location_id)
    elif location_id == "attic" and variant != "original":
        put_return_location_into_play(state, events, "field_of_graves")
    elif location_id == "cellar" and variant != "original":
        put_return_location_into_play(state, events, "ghoul_pits")
    elif location_id == "field_of_graves":
        skill_test.start(
            state,
            events,
            skill="willpower",
            difficulty=4,
            source="Field of Graves",
            on_failure={"kind": "discard_random_per_fail", "source": "Field of Graves"},
        )
    elif location_id == "ghoul_pits":
        skill_test.start(
            state,
            events,
            skill="agility",
            difficulty=3,
            source="Ghoul Pits",
            on_failure={"kind": "ghoul_pits_rats", "source": "Ghoul Pits"},
        )


def after_enter_location(state: GameState, events: list[dict[str, Any]], location_id: str) -> None:
    reveal_location(state, events, location_id)
    original_variant = not is_return(state) or state.limits.get(f"return_variant:{location_id}") == "original"
    if location_id == "attic" and original_variant:
        from ..effects import start_damage_assignment

        start_damage_assignment(state, events, source="Attic", damage=0, horror=1)
    elif location_id == "cellar" and original_variant:
        from ..effects import start_damage_assignment

        start_damage_assignment(state, events, source="Cellar", damage=1, horror=0)


def advance_act(state: GameState, events: list[dict[str, Any]]) -> None:
    if state.act is None:
        return
    if state.act.stage == 1:
        advance_act_1(state, events)
    elif state.act.stage == 2:
        advance_act_2(state, events)
    elif state.act.stage == 3:
        present_final_resolution(state)


def advance_act_1(state: GameState, events: list[dict[str, Any]]) -> None:
    from ..effects import log_event

    if is_return(state):
        advance_act_1_return(state, events)
        return
    for location_id, (code, name, _shroud, _clues, connections) in LOCATION_INFO.items():
        state.locations[location_id] = Location(
            id=location_id,
            code=code,
            name=name,
            revealed=False,
            shroud=None,
            clues=0,
            connections=list(connections),
        )
    discard_enemies_at_location(state, "study", events)
    discard_location_attachments(state, "study", events)
    investigator_id = state.investigator.id
    if "study" in state.locations and investigator_id in state.locations["study"].investigator_ids:
        state.locations["study"].investigator_ids.remove(investigator_id)
    state.investigator.location_id = "hallway"
    state.locations["hallway"].investigator_ids.append(investigator_id)
    reveal_location(state, events, "hallway")
    state.removed_from_game.append("study")
    state.locations.pop("study", None)
    state.act = ActState(code="01109", name="The Barrier", stage=2, clues_required=3)
    log_event(events, "act_advanced", "Act advanced to The Barrier.")


def advance_act_1_return(state: GameState, events: list[dict[str, Any]]) -> None:
    """Act 1b 'Breaking the Wall': Hole in the Wall enters play, the investigator
    moves into it and reveals it (flipping it to the Hallway, which pulls the
    Attic, Cellar, and Parlor into play), then tests willpower (4), discarding
    1 random card per point failed by."""
    from .. import skill_test
    from ..effects import log_event
    from ..enemies import engage_ready_enemies_at_roland, move_engaged_enemies_with_roland

    put_return_location_into_play(state, events, "hallway")
    investigator_id = state.investigator.id
    previous = state.investigator.location_id
    if previous in state.locations and investigator_id in state.locations[previous].investigator_ids:
        state.locations[previous].investigator_ids.remove(investigator_id)
    state.investigator.location_id = "hallway"
    state.locations["hallway"].investigator_ids.append(investigator_id)
    move_engaged_enemies_with_roland(state, events, "hallway")
    log_event(events, "forced_move", f"{state.investigator.name} moved into the Hole in the Wall.")
    reveal_location(state, events, "hallway")
    engage_ready_enemies_at_roland(state, events)
    state.act = ActState(code="01109", name="The Barrier", stage=2, clues_required=3)
    log_event(events, "act_advanced", "Act advanced to The Barrier.")
    skill_test.start(
        state,
        events,
        skill="willpower",
        difficulty=4,
        source="Breaking the Wall",
        on_failure={"kind": "discard_random_per_fail", "source": "Breaking the Wall"},
    )


def discard_enemies_at_location(state: GameState, location_id: str, events: list[dict[str, Any]]) -> None:
    from ..effects import log_event

    location = state.locations.get(location_id)
    if not location:
        return
    for enemy_id in list(location.enemy_ids):
        enemy = state.enemies.pop(enemy_id, None)
        if not enemy:
            continue
        if enemy_id in state.investigator.engaged_enemies:
            state.investigator.engaged_enemies.remove(enemy_id)
        for attachment in list(enemy.attachments):
            state.card_instances[attachment].zone = "discard"
            state.investigator.discard.append(attachment)
        location.enemy_ids.remove(enemy_id)
        state.card_instances[enemy_id].zone = "encounter_discard"
        state.encounter_discard.append(enemy_id)
        log_event(events, "enemy_discarded", f"{card_data.get_card(enemy.card_code)['name']} was discarded.", enemy=enemy_id)


def discard_location_attachments(state: GameState, location_id: str, events: list[dict[str, Any]]) -> None:
    from ..effects import log_event

    location = state.locations.get(location_id)
    if not location:
        return
    for attachment in list(location.attached_instance_ids):
        location.attached_instance_ids.remove(attachment)
        state.card_instances[attachment].zone = "discard"
        state.investigator.discard.append(attachment)
        log_event(events, "attachment_discarded", "An attachment was discarded.", card=attachment)


def advance_act_2(state: GameState, events: list[dict[str, Any]]) -> None:
    from ..effects import log_event
    from ..enemies import engage_ready_enemies_at_roland, spawn_enemy

    reveal_location(state, events, "parlor")
    lita = next((card_id for card_id, instance in state.card_instances.items() if instance.card_code == "01117"), None)
    if lita:
        state.card_instances[lita].zone = "story"
        state.locations["parlor"].attached_instance_ids.append(lita)
    priest = next((card_id for card_id, instance in state.card_instances.items() if instance.card_code == "01116"), None)
    if priest:
        spawn_enemy(state, events, instance_id=priest, location_id="hallway", engaged=False)
        engage_ready_enemies_at_roland(state, events)
    state.act = ActState(code="01110", name="What Have You Done?", stage=3, clues_required=None)
    log_event(events, "act_advanced", "Act advanced to What Have You Done?.")


def present_final_resolution(state: GameState) -> None:
    state.decision_queue = [
        PendingDecision(
            id="final-resolution",
            kind="scenario",
            prompt="The Ghoul Priest is defeated. Choose a resolution.",
            options=[
                DecisionOption("Burn it down (R1)", {"kind": "scenario", "choice": "resolution_r1"}),
                DecisionOption("Refuse to burn it (R2)", {"kind": "scenario", "choice": "resolution_r2"}),
            ],
        )
    ]


def after_enemy_defeated(state: GameState, events: list[dict[str, Any]], enemy_id: str) -> bool:
    state.limits["enemies_defeated"] = int(state.limits.get("enemies_defeated", 0)) + 1
    if state.card_instances[enemy_id].card_code == "01116" and state.act and state.act.stage == 3:
        advance_act(state, events)
        return True
    return False


def end_round(state: GameState, events: list[dict[str, Any]]) -> None:
    if state.act and state.act.stage == 2 and state.investigator.location_id == "hallway" and state.investigator.clues >= 3:
        state.decision_queue = [
            PendingDecision(
                id="act2-objective",
                kind="scenario",
                prompt="Spend 3 clues to advance The Barrier?",
                options=[
                    DecisionOption("Spend 3 clues and advance", {"kind": "scenario", "choice": "act2_advance"}),
                    DecisionOption("Do not advance", {"kind": "scenario", "choice": "act2_wait"}),
                ],
            )
        ]
        return
    if state.agenda and state.agenda.stage == 3:
        from ..effects import place_doom

        count = sum(
            1
            for enemy in state.enemies.values()
            if is_ghoul_card(enemy.card_code) and enemy.location_id in {"hallway", "parlor"}
        )
        if count:
            place_doom(state, count, events, source="They're Getting Out!")


def start_next_round_after_end_round_choice(state: GameState, events: list[dict[str, Any]]) -> None:
    from ..effects import log_event

    if state.status != "in_progress":
        return
    state.round += 1
    state.phase = "Mythos"
    state.limits = {
        key: value
        for key, value in state.limits.items()
        if not str(key).startswith("frozen:")
        and not str(key).startswith("enemy_phase_attacked:")
        and not str(key).startswith("mind_over_matter:")
        and not str(key).startswith("daisy_tome:")
        and not str(key).startswith("skids_action:")
        and not str(key).startswith("agnes_horror:")
        and not str(key).startswith("frozen_end_turn:")
        and not str(key).startswith("mythos_")
        and not str(key).startswith("on_the_lam:")
        and not str(key).startswith("hospital_debts:")
        and not str(key).startswith("dark_memory_end_turn:")
    }
    log_event(events, "round_started", f"Round {state.round} began.")


def end_enemy_phase(state: GameState, events: list[dict[str, Any]]) -> None:
    if not state.agenda or state.agenda.stage != 3 or "parlor" not in state.locations:
        return
    from ..enemies import move_enemy_to, next_step_toward

    for enemy_id in sorted(state.enemies):
        enemy = state.enemies[enemy_id]
        if enemy.engaged_with is not None or not is_ghoul_card(enemy.card_code):
            continue
        step = next_step_toward(state, enemy.location_id, "parlor", enemy_id)
        if step:
            move_enemy_to(state, events, enemy_id, step)


def check_agenda_advance(state: GameState, events: list[dict[str, Any]], *, rng: ArkhamRng | None = None) -> None:
    if not state.agenda:
        return
    from ..effects import clear_all_doom

    while total_doom(state) >= state.agenda.threshold and state.status == "in_progress" and not state.decision_queue:
        if state.agenda.stage == 1:
            # Keep the doom visible (e.g. 3/3) while the flip choice is pending;
            # it is cleared when the choice resolves (set_agenda_2) — clearing it
            # here made the panel read "0/3 What's Going On?!" mid-flip, which
            # looked like the agenda advanced early.
            present_agenda_1_choice(state)
            return
        clear_all_doom(state)
        if state.agenda.stage == 2:
            if rng is None:
                from ..errors import EngineError

                raise EngineError("agenda 2 advancement requires the game RNG")
            advance_agenda_2(state, events, rng)
            continue
        if state.agenda.stage == 3:
            agenda_3_doom_out(state, events)
            return


def total_doom(state: GameState) -> int:
    agenda = state.agenda.doom if state.agenda else 0
    enemies = sum(enemy.doom for enemy in state.enemies.values())
    cards = sum(instance.doom for instance in state.card_instances.values())
    return agenda + enemies + cards


def present_agenda_1_choice(state: GameState) -> None:
    state.decision_queue = [
        PendingDecision(
            id="agenda1-back",
            kind="scenario",
            prompt="Agenda 1 advanced. Choose the back effect.",
            options=[
                DecisionOption("Discard 1 random card from hand", {"kind": "scenario", "choice": "agenda1_discard"}),
                DecisionOption("Take 2 horror", {"kind": "scenario", "choice": "agenda1_horror"}),
            ],
        )
    ]


def agenda1_discard(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    from ..cards import player as player_cards
    from ..effects import log_event

    if not state.investigator.hand:
        return
    card_id = rng.choice(state.investigator.hand)
    player_cards.discard_from_hand(state, card_id)
    log_event(events, "card_discarded", "Roland discarded 1 random card for Agenda 1.", card=card_id)


def set_agenda_2(state: GameState, events: list[dict[str, Any]]) -> None:
    from ..effects import clear_all_doom, log_event

    clear_all_doom(state)
    state.agenda = AgendaState(code="01106", name="Rise of the Ghouls", stage=2, threshold=7)
    log_event(events, "agenda_advanced", "Agenda advanced to Rise of the Ghouls.")


def finish_mythos_after_agenda_choice(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    if state.status != "in_progress" or state.phase != "Mythos":
        return
    from .. import encounter
    from ..effects import log_event
    from ..enemies import engage_ready_enemies_at_roland

    state.limits[f"mythos_doom_placed:{state.round}"] = True
    encounter_key = f"mythos_encounter_drawn:{state.round}"
    encounter_already_drawn = bool(state.limits.get(encounter_key))
    state.limits[encounter_key] = True
    if not encounter_already_drawn:
        encounter.draw_encounter(state, rng, events)
    engage_ready_enemies_at_roland(state, events)
    if state.status == "in_progress" and not state.decision_queue:
        state.phase = "Investigation"
        state.investigator.actions_remaining = starting_actions(state.investigator.card_code)
        if player_cards.controls_code(state, "01048"):
            state.investigator.actions_remaining += 1
        state.turn.action_index = 0
        log_event(events, "phase_started", "Investigation phase began.")


def advance_agenda_2(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    from ..effects import log_event
    from ..encounter import resolve_revelation

    state.encounter_deck.extend(state.encounter_discard)
    state.encounter_discard = []
    for card_id in state.encounter_deck:
        state.card_instances[card_id].zone = "encounter_deck"
    rng.shuffle(state.encounter_deck)
    drawn: str | None = None
    while state.encounter_deck:
        card_id = state.encounter_deck.pop(0)
        code = state.card_instances[card_id].card_code
        if is_ghoul_card(code) and card_data.get_card(code).get("type_code") == "enemy":
            drawn = card_id
            break
        state.card_instances[card_id].zone = "encounter_discard"
        state.encounter_discard.append(card_id)
    state.agenda = AgendaState(code="01107", name="They're Getting Out!", stage=3, threshold=10)
    log_event(events, "agenda_advanced", "Agenda advanced to They're Getting Out!.")
    if drawn:
        state.limits["encounter_cards_drawn"] = int(state.limits.get("encounter_cards_drawn", 0)) + 1
        log_event(events, "encounter_drawn", f"Roland drew encounter card {card_data.get_card(state.card_instances[drawn].card_code)['name']}.", card=drawn)
        resolve_revelation(state, rng, events, drawn)


def agenda_3_doom_out(state: GameState, events: list[dict[str, Any]]) -> None:
    from ..effects import apply_cover_up_trauma, end_game, log_event

    if state.act and state.act.stage <= 2:
        apply_cover_up_trauma(state, events)
        finalize_result(state, events, outcome="R3", resolution="R3", summary="R3: Roland was killed")
        log_event(events, "game_end", "R3: Roland was killed")
        return
    state.trauma["physical"] = int(state.trauma.get("physical", 0)) + 1
    end_game(state, events, "Roland was defeated by agenda 3")


def resign(state: GameState, events: list[dict[str, Any]]) -> None:
    from ..effects import end_game

    end_game(state, events, "Roland resigned")


def finalize_result(
    state: GameState,
    events: list[dict[str, Any]],
    *,
    outcome: str,
    summary: str,
    resolution: str | None = None,
) -> None:
    from ..effects import apply_cover_up_trauma

    apply_cover_up_trauma(state, events)
    add_victory_locations(state)
    victory_points = calculate_victory_points(state)
    # Lita Chantler is earned on R1 and no-resolution (she follows you out of the
    # house) but NOT on R2 (you kicked her out; "she doesn't seem to trust you")
    # or R3. Score values her at 3 XP of campaign equity — she is the real prize
    # of this scenario, which is why experienced players burn the house down.
    if outcome == "R3":
        xp = 0
        score = 0
        lita_earned = False
    elif outcome == "R2":
        xp = victory_points + 3
        lita_earned = False
        score = max(0, xp - total_trauma(state))
    else:
        xp = victory_points + 2
        lita_earned = True
        score = max(0, xp - total_trauma(state) + LITA_SCORE_VALUE)
    hospital_debts_penalty = hospital_debts_xp_penalty(state)
    if hospital_debts_penalty:
        xp = max(0, xp - hospital_debts_penalty)
        if outcome == "R3":
            score = 0
        else:
            lita_bonus = LITA_SCORE_VALUE if lita_earned else 0
            score = max(0, xp - total_trauma(state) + lita_bonus)
    state.status = "ended"
    state.decision_queue = []
    state.result = {
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
        "ghoul_priest_defeated": any(
            state.card_instances[card_id].card_code == "01116"
            for card_id in state.victory_display
            if card_id in state.card_instances
        ),
        "lita_recruited": any(
            state.card_instances[card_id].card_code == "01117"
            for card_id in state.investigator.play_area
            if card_id in state.card_instances
        ),
        "lita_earned": lita_earned,
        "encounter_cards_drawn": int(state.limits.get("encounter_cards_drawn", 0)),
        "enemies_defeated": int(state.limits.get("enemies_defeated", 0)),
        "campaign_log": campaign_log(state, outcome, lita_earned),
    }


def campaign_log(state: GameState, outcome: str, lita_earned: bool) -> dict[str, Any]:
    # The Ghoul Priest is "still alive" unless it was defeated (in the victory
    # display) — including when it never spawned (still set aside). The campaign
    # guide records this on the no-resolution and R3 outcomes.
    priest_defeated = any(
        state.card_instances[card_id].card_code == "01116"
        for card_id in state.victory_display
        if card_id in state.card_instances
    )
    return {
        "house": "burned_down" if outcome == "R1" else "standing",
        "lita": "earned" if lita_earned else "seeking_others",
        "ghoul_priest_still_alive": (not priest_defeated) if outcome in ("no_resolution", "R3") else False,
    }


def add_victory_locations(state: GameState) -> None:
    # RR: a cleared (no clues), revealed location with Victory X goes to the
    # victory display at game end. Covers core Attic/Cellar and the Return
    # scenario's Field of Graves / Ghoul Pits via their printed victory values.
    for location_id, location in state.locations.items():
        if not location.revealed or location.clues != 0 or location_id in state.victory_display:
            continue
        if int(card_data.get_card(location.code).get("victory") or 0) > 0:
            state.victory_display.append(location_id)


def calculate_victory_points(state: GameState) -> int:
    total = 0
    for item_id in state.victory_display:
        if item_id in state.card_instances:
            total += int(card_data.get_card(state.card_instances[item_id].card_code).get("victory") or 0)
        elif item_id in state.locations:
            total += int(card_data.get_card(state.locations[item_id].code).get("victory") or 0)
    return total


def total_trauma(state: GameState) -> int:
    return sum(int(value) for value in state.trauma.values())


def hospital_debts_xp_penalty(state: GameState) -> int:
    for instance_id in state.investigator.threat_area:
        instance = state.card_instances[instance_id]
        if instance.card_code == "01011" and instance.uses.get("resources", 0) < 6:
            return 2
    return 0


def ghouls_at_roland_location(state: GameState) -> int:
    location = state.locations[state.investigator.location_id]
    return sum(1 for enemy_id in location.enemy_ids if enemy_id in state.enemies and is_ghoul_card(state.enemies[enemy_id].card_code))


def is_ghoul_card(card_code: str) -> bool:
    return "Ghoul" in str(card_data.get_card(card_code).get("traits", ""))


def is_investigate_result(result: dict[str, Any]) -> bool:
    return str(result.get("callback_kind") or "") in {"investigate", "burglary"} or str(result.get("source", "")).startswith(
        ("Investigate", "Burglary")
    )


def apply_token_aftermath(state: GameState, events: list[dict[str, Any]], result: dict[str, Any], rng: ArkhamRng | None = None) -> None:
    tokens = [str(result.get("token"))] + [str(token) for token in result.get("extra_tokens", [])]
    failed = not bool(result.get("success"))
    if is_return(state) and is_investigate_result(result):
        from ..effects import log_event

        location_id = state.investigator.location_id
        if location_id == "bathroom" and any(token in {"skull", "cultist", "tablet", "autofail"} for token in tokens):
            # Bathroom Forced: lose all remaining actions and end your turn.
            state.investigator.actions_remaining = 0
            log_event(events, "bathroom_forced", "The Bathroom drained all remaining actions; the turn ends.")
        if location_id == "bedroom" and failed:
            # Bedroom Forced: discard 1 random card after failing an investigate here.
            if state.investigator.hand and rng is not None:
                card_id = rng.choice(state.investigator.hand)
                player_cards.discard_from_hand(state, card_id)
                log_event(events, "bedroom_forced", f"The Bedroom forced a random discard of {card_name(state, card_id)}.", card=card_id)
    damage = 0
    horror = 0
    if "cultist" in tokens and failed:
        horror += 1 if state.difficulty in {"easy", "standard"} else 2
    if "tablet" in tokens and ghouls_at_roland_location(state) > 0:
        damage += 1
        horror += 0 if state.difficulty in {"easy", "standard"} else 1
    if damage or horror:
        from ..effects import start_damage_assignment

        start_damage_assignment(state, events, source="Chaos token", damage=damage, horror=horror)
    if "skull" in tokens and failed and state.difficulty in {"hard", "expert"} and not state.decision_queue:
        if rng is None:
            from ..errors import EngineError

            raise EngineError("skull ghoul search requires the game RNG")
        search_and_draw_ghoul(state, events, rng)


def ghoul_pits_draw_rats(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng, count: int) -> None:
    """Ghoul Pits: for each point failed by, search the encounter deck and
    discard pile for a Swarm of Rats and draw it, then shuffle the deck."""
    from ..encounter import resolve_revelation
    from ..effects import log_event

    drawn = 0
    for _ in range(count):
        if state.status != "in_progress":
            return
        combined = list(state.encounter_deck) + list(state.encounter_discard)
        found = next((card_id for card_id in combined if state.card_instances[card_id].card_code == "01159"), None)
        if not found:
            break
        if found in state.encounter_deck:
            state.encounter_deck.remove(found)
        if found in state.encounter_discard:
            state.encounter_discard.remove(found)
        state.limits["encounter_cards_drawn"] = int(state.limits.get("encounter_cards_drawn", 0)) + 1
        log_event(events, "encounter_drawn", "Ghoul Pits pulled a Swarm of Rats from the encounter deck.", card=found)
        resolve_revelation(state, rng, events, found)
        drawn += 1
    rng.shuffle(state.encounter_deck)
    if drawn:
        log_event(events, "encounter_reshuffled", "The encounter deck was shuffled after Ghoul Pits' search.")


def search_and_draw_ghoul(state: GameState, events: list[dict[str, Any]], rng: ArkhamRng) -> None:
    from ..encounter import resolve_revelation

    combined = list(state.encounter_deck) + list(state.encounter_discard)
    found = next(
        (
            card_id
            for card_id in combined
            if is_ghoul_card(state.card_instances[card_id].card_code)
            and card_data.get_card(state.card_instances[card_id].card_code).get("type_code") == "enemy"
        ),
        None,
    )
    if not found:
        return
    if found in state.encounter_deck:
        state.encounter_deck.remove(found)
    if found in state.encounter_discard:
        state.encounter_discard.remove(found)
    rng.shuffle(state.encounter_deck)
    state.limits["encounter_cards_drawn"] = int(state.limits.get("encounter_cards_drawn", 0)) + 1
    resolve_revelation(state, rng, events, found)


ENGINE_TEST_PLAYER_CODES = [
    "01021",
    "01016",
    "01020",
    "01018",
    "01023",
    "01019",
    "01022",
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
