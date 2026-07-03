from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from . import data as card_data
from .errors import EngineError
from .log import EventLog
from .model import (
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
from .rng import ArkhamRng
from .serialize import atomic_write_json, atomic_write_text, decode_hidden, encode_hidden, sha256_text


CHAOS_BAGS: dict[str, list[str]] = {
    "easy": ["+1", "+1", "0", "0", "0", "-1", "-1", "-1", "-2", "-2", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
    "standard": ["+1", "0", "0", "-1", "-1", "-1", "-2", "-2", "-3", "-4", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
    "hard": ["0", "0", "0", "-1", "-1", "-2", "-2", "-3", "-3", "-4", "-5", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
    "expert": ["0", "-1", "-1", "-2", "-2", "-3", "-3", "-4", "-4", "-5", "-6", "-8", "skull", "skull", "cultist", "tablet", "autofail", "eldersign"],
}


class Game:
    def __init__(self, run_dir: Path, state: GameState, rng: ArkhamRng) -> None:
        self.run_dir = run_dir
        self.state = state
        self.rng = rng

    @classmethod
    def new(
        cls,
        *,
        seed: int,
        difficulty: str,
        deck_path: str | Path | None,
        run_dir: str | Path,
    ) -> "Game":
        if difficulty not in CHAOS_BAGS:
            raise EngineError(f"unknown difficulty: {difficulty}")
        run_path = Path(run_dir)
        deck = card_data.load_deck(deck_path)
        cards = card_data.cards_by_code()
        investigator_card = cards[str(deck["investigator"])]
        rng = ArkhamRng(seed)
        instances: dict[str, CardInstance] = {}
        deck_ids: list[str] = []
        counter = 1
        for code, count in sorted(deck["slots"].items()):
            for _ in range(int(count)):
                instance_id = f"pc{counter:04d}"
                counter += 1
                instances[instance_id] = CardInstance(
                    id=instance_id,
                    card_code=str(code),
                    zone="player_deck",
                )
                deck_ids.append(instance_id)
        rng.shuffle(deck_ids)
        hand = deck_ids[:5]
        remaining_deck = deck_ids[5:]
        for instance_id in hand:
            instances[instance_id].zone = "hand"
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
            deck=remaining_deck,
        )
        state = GameState(
            schema_version=1,
            scenario="stub",
            difficulty=difficulty,
            status="in_progress",
            round=1,
            phase="Investigation",
            turn=TurnState(investigator_id="roland", action_index=0),
            investigator=investigator,
            card_instances=instances,
            locations={
                "study": Location(
                    id="study",
                    code="01111",
                    name="Study",
                    revealed=True,
                    shroud=2,
                    clues=2,
                    investigator_ids=["roland"],
                )
            },
            agenda=AgendaState(
                code="01105",
                name="What's Going On?!",
                stage=1,
                threshold=3,
            ),
            act=ActState(code="01108", name="Trapped", stage=1, clues_required=2),
            chaos_bag=ChaosBag(tokens=list(CHAOS_BAGS[difficulty])),
            decision_queue=[stub_decision()],
        )
        game = cls(run_path, state, rng)
        game._initialize_files(seed=seed, difficulty=difficulty, deck_path=deck_path)
        game.save()
        EventLog(run_path).append(
            round=state.round,
            phase=state.phase,
            type="decision_presented",
            data={"prompt": state.decision_queue[0].prompt},
        )
        return game

    @classmethod
    def load(cls, run_dir: str | Path) -> "Game":
        run_path = Path(run_dir)
        hidden_path = run_path / "hidden.blob"
        if not hidden_path.exists():
            raise EngineError(f"missing hidden state: {hidden_path}")
        hidden_text = hidden_path.read_text(encoding="utf-8")
        meta_path = run_path / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            expected = meta.get("hidden_sha256")
            if expected and expected != sha256_text(hidden_text):
                raise EngineError("hidden state checksum mismatch")
        hidden = decode_hidden(hidden_text)
        return cls(
            run_path,
            GameState.from_dict(hidden["state"]),
            ArkhamRng.from_dict(hidden["rng"]),
        )

    def save(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        public = self.state.public_dict()
        hidden_text = encode_hidden({"state": self.state.to_dict(), "rng": self.rng.to_dict()})
        atomic_write_json(self.run_dir / "state.json", public)
        atomic_write_text(self.run_dir / "hidden.blob", hidden_text)
        meta = self._read_meta()
        meta["hidden_sha256"] = sha256_text(hidden_text)
        meta["status"] = self.state.status
        meta["updated_at"] = _now()
        atomic_write_json(self.run_dir / "meta.json", meta)

    def current_decision(self) -> PendingDecision | None:
        if not self.state.decision_queue:
            return None
        return self.state.decision_queue[0]

    def apply(self, option_index: int) -> list[dict[str, Any]]:
        decision = self.current_decision()
        if decision is None:
            raise EngineError("no current decision")
        if option_index < 1 or option_index > len(decision.options):
            raise EngineError("invalid option")
        option = decision.options[option_index - 1]
        events: list[dict[str, Any]] = []
        events.append(
            EventLog(self.run_dir).append(
                round=self.state.round,
                phase=self.state.phase,
                type="decision_made",
                data={"decision_id": decision.id, "option": option_index, "label": option.label},
            )
        )
        self.state.decision_queue.pop(0)
        choice = option.payload.get("choice")
        if choice == "end":
            self.state.status = "ended"
            events.append(
                EventLog(self.run_dir).append(
                    round=self.state.round,
                    phase=self.state.phase,
                    type="game_end",
                    data={"summary": "stub game ended"},
                )
            )
        else:
            self.state.turn.action_index += 1
            self.state.investigator.actions_remaining = max(
                0, self.state.investigator.actions_remaining - 1
            )
            message = f"Stub option {str(choice).upper()} resolved."
            events.append(
                EventLog(self.run_dir).append(
                    round=self.state.round,
                    phase=self.state.phase,
                    type="action_taken",
                    data={"message": message},
                )
            )
            if self.state.investigator.actions_remaining == 0:
                self.state.round += 1
                self.state.turn.action_index = 0
                self.state.investigator.actions_remaining = 3
            self.state.decision_queue.append(stub_decision())
            events.append(
                EventLog(self.run_dir).append(
                    round=self.state.round,
                    phase=self.state.phase,
                    type="decision_presented",
                    data={"prompt": self.state.decision_queue[0].prompt},
                )
            )
        self.save()
        return events

    def _initialize_files(
        self, *, seed: int, difficulty: str, deck_path: str | Path | None
    ) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "seed": seed,
            "difficulty": difficulty,
            "deck": str(deck_path or card_data.DEFAULT_DECK),
            "created_at": _now(),
            "engine_version": __version__,
            "status": self.state.status,
        }
        atomic_write_json(self.run_dir / "meta.json", meta)
        for path in (self.run_dir / "log.jsonl", self.run_dir / "log.md"):
            if not path.exists():
                path.write_text("", encoding="utf-8")

    def _read_meta(self) -> dict[str, Any]:
        path = self.run_dir / "meta.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stub_decision() -> PendingDecision:
    return PendingDecision(
        id="stub-decision",
        prompt="[Round stub · Investigation · Roland Banks] stub decision: option A/B/end",
        options=[
            DecisionOption(label="Option A", payload={"choice": "a"}),
            DecisionOption(label="Option B", payload={"choice": "b"}),
            DecisionOption(label="End stub game", payload={"choice": "end"}),
        ],
    )
