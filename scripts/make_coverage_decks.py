#!/usr/bin/env python3
"""Generate XP-card coverage decks (data/decks/coverage/) for playtesting.

Each deck starts from the investigator's killbray list and swaps in that class's
XP cards (upgrades replace their level-0 versions; new cards replace fillers),
keeping the deck legal: 30 counted cards, <=2 copies per title, class/level
access, signatures + fixed weakness intact. Together the five decks cover all
32 XP cards. Usage: python3 scripts/make_coverage_decks.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# XP cards per deck. "replace" = remove one copy of this code to make room
# (None -> remove a filler from FILLERS below).
ASSIGNMENTS: dict[str, list[tuple[str, str | None]]] = {
    "roland": [
        ("01028", "01018"),  # Beat Cop (2) <- Beat Cop
        ("50001", "01017"),  # Physical Training (2) <- Physical Training
        ("50002", "01024"),  # Dynamite Blast (2) <- Dynamite Blast
        ("01026", None),     # Extra Ammunition (1)
        ("01027", None),     # Police Badge (2)
        ("01029", None),     # Shotgun (4)
        ("01040", "01030"),  # Magnifying Glass (1) <- Magnifying Glass
        ("01094", None),     # Bulletproof Vest (3)
    ],
    "daisy": [
        ("50003", "01034"),  # Hyperawareness (2) <- Hyperawareness
        ("50004", None),     # Barricade (3)  (daisy has no Barricade; roland's is seeker)
        ("01041", None),     # Disc of Itzamna (2)
        ("01042", None),     # Encyclopedia (2)
        ("01043", None),     # Cryptic Research (4)
        ("01069", "01066"),  # Blinding Light (2) <- Blinding Light
        ("01095", None),     # Elder Sign Amulet (3)
    ],
    "skids": [
        ("50005", "01049"),  # Hard Knocks (2) <- Hard Knocks
        ("50006", None),     # Hot Streak (2)
        ("01057", None),     # Hot Streak (4)  (2nd copy of the title)
        ("01055", None),     # Cat Burglar (1)
        ("01056", None),     # Sure Gamble (3)
        ("01054", None),     # Leo De Luca (1)  (skids has no Leo; rogue 0-5)
    ],
    "agnes": [
        ("50007", "01062"),  # Arcane Studies (2) <- Arcane Studies
        ("01068", None),     # Mind Wipe (1)
        ("50008", None),     # Mind Wipe (3)  (2nd copy of the title)
        ("01070", None),     # Book of Shadows (3)
        ("01071", None),     # Grotesque Statue (4)
        ("01082", None),     # Aquinnah (1)   (survivor 0-2? Aquinnah is level 1 ok)
        ("01083", None),     # Close Call (2) (survivor level 2 ok)
    ],
    "wendy": [
        ("50009", "01077"),  # Dig Deep (2) <- Dig Deep
        ("50010", "01075"),  # Rabbit's Foot (3) <- Rabbit's Foot
        ("01084", "01080"),  # Lucky! (2) <- Lucky!
        ("01085", None),     # Will to Survive (3)
        ("01054", "01048"),  # Leo De Luca (1) <- Leo De Luca (wendy: rogue 0-2? level 1 ok)
    ],
}

# Preferred filler removals per investigator (skills/duplicates that keep the
# deck functional), consumed in order when "replace" is None.
FILLERS: dict[str, list[str]] = {
    "roland": ["01089", "01090", "01086", "01087", "01088", "01022", "01023", "01039"],
    "daisy": ["01092", "01093", "01086", "01087", "01088", "01035", "01036", "01037"],
    "skids": ["01089", "01091", "01086", "01087", "01088", "01050", "01053", "01052"],
    "agnes": ["01091", "01093", "01086", "01087", "01088", "01067", "01064", "01076"],
    "wendy": ["01090", "01092", "01086", "01087", "01088", "01081", "01078", "01079"],
}


def main() -> int:
    out_dir = ROOT / "data" / "decks" / "coverage"
    out_dir.mkdir(parents=True, exist_ok=True)
    covered: set[str] = set()
    for investigator, swaps in ASSIGNMENTS.items():
        src = json.loads((ROOT / "data" / "decks" / "killbray" / f"{investigator}.json").read_text())
        slots = {str(k): int(v) for k, v in src["slots"].items()}
        fillers = list(FILLERS[investigator])
        for code, replace in swaps:
            victim = replace
            if victim is None or slots.get(victim, 0) <= 0:
                victim = next((f for f in fillers if slots.get(f, 0) > 0), None)
                if victim in fillers:
                    fillers.remove(victim)
            if victim is None:
                raise SystemExit(f"{investigator}: no removable filler for {code}")
            slots[victim] -= 1
            if slots[victim] == 0:
                del slots[victim]
            slots[code] = slots.get(code, 0) + 1
            covered.add(code)
        deck = {
            "name": f"{investigator} XP coverage deck",
            "campaign_deck": True,
            "investigator_code": src.get("investigator_code"),
            "slots": dict(sorted(slots.items())),
        }
        path = out_dir / f"{investigator}.json"
        path.write_text(json.dumps(deck, indent=2) + "\n", encoding="utf-8")
        total = sum(slots.values())
        print(f"{investigator}: {total} cards -> {path}")

    # validate with the engine's own rules
    import sys

    sys.path.insert(0, str(ROOT))
    from arkham import upgrade

    for investigator in ASSIGNMENTS:
        deck = json.loads((out_dir / f"{investigator}.json").read_text())
        weaknesses = []
        slots = {}
        for code, count in deck["slots"].items():
            from arkham import data as card_data

            card = card_data.get_card(code)
            if str(card.get("subtype_code", "")) in {"weakness", "basicweakness"} and code not in upgrade.SIGNATURE_CODES[investigator]:
                weaknesses.extend([code] * count)
            else:
                slots[code] = count
        campaign = {
            "investigator": investigator,
            "deck": {"slots": slots, "story_assets": [], "weaknesses": weaknesses},
            "xp_unspent": 0,
        }
        upgrade.validate_deck(campaign, final=True)
        print(f"{investigator}: legal ✓")

    expected = {
        "01026", "01027", "01028", "01029", "01040", "01041", "01042", "01043",
        "01054", "01055", "01056", "01057", "01068", "01069", "01070", "01071",
        "01082", "01083", "01084", "01085", "01094", "01095",
        "50001", "50002", "50003", "50004", "50005", "50006", "50007", "50008",
        "50009", "50010",
    }
    missing = expected - covered
    print(f"coverage: {len(covered & expected)}/32; missing: {sorted(missing) or 'none'}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
