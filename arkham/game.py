from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from . import data as card_data
from .errors import EngineError
from .log import EventLog
from .model import GameState, PendingDecision
from .rng import ArkhamRng
from .serialize import atomic_write_json, atomic_write_text, decode_hidden, encode_hidden, sha256_text
from . import actions, enemies, phases, skill_test
from .effects import assign_damage_choice, discard_asset_choice, resolve_cover_up_choice


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
        rng = ArkhamRng(seed)
        from .scenarios.the_gathering import build_gathering_state

        state = build_gathering_state(difficulty=difficulty, rng=rng, deck_path=deck_path)
        game = cls(run_path, state, rng)
        game._initialize_files(seed=seed, difficulty=difficulty, deck_path=deck_path)
        init_events: list[dict[str, Any]] = []
        phases.advance_until_decision(state, rng, init_events)
        game.save()
        game._append_rule_events(init_events)
        if state.decision_queue:
            EventLog(run_path).append(round=state.round, phase=state.phase, type="decision_presented", data={"prompt": state.decision_queue[0].prompt})
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
                print("warning: hidden state checksum mismatch; continuing with hidden.blob", file=sys.stderr)
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
        if self.state.result:
            atomic_write_json(self.run_dir / "result.json", self.state.result)
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
        rule_events: list[dict[str, Any]] = []
        self._dispatch_payload(option.payload, rule_events)
        if not self.state.decision_queue and self.state.status == "in_progress":
            phases.advance_until_decision(self.state, self.rng, rule_events)
        events.extend(self._append_rule_events(rule_events))
        if self.state.status == "in_progress" and self.state.decision_queue:
            events.append(EventLog(self.run_dir).append(round=self.state.round, phase=self.state.phase, type="decision_presented", data={"prompt": self.state.decision_queue[0].prompt}))
        self.save()
        return events

    def _dispatch_payload(self, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
        kind = payload.get("kind")
        if kind == "action":
            actions.execute(self.state, payload, events)
        elif kind == "commit_card":
            skill_test.commit_card(self.state, payload, events)
        elif kind == "commit_done":
            skill_test.finish_commit(self.state, self.rng, events)
        elif kind == "skill_boost":
            skill_test.apply_skill_boost(self.state, payload, events)
        elif kind == "post_reveal_done":
            skill_test.resolve(self.state, events)
        elif kind == "assign_damage":
            resume = dict(self.state.pending_damage.get("resume", {})) if self.state.pending_damage else {}
            assign_damage_choice(self.state, payload, events)
            if (
                self.state.status == "in_progress"
                and self.state.pending_damage is None
                and not self.state.decision_queue
                and resume.get("kind") == "action"
            ):
                actions.execute(self.state, dict(resume.get("payload", {})), events)
            elif (
                self.state.status == "in_progress"
                and self.state.pending_damage is None
                and not self.state.decision_queue
                and resume.get("kind") == "scenario"
            ):
                from .scenarios import the_gathering

                the_gathering.resolve_scenario_choice(self.state, dict(resume), events, self.rng)
        elif kind == "dodge_attack":
            enemies.cancel_pending_attack(self.state, events, str(payload["card"]))
        elif kind == "take_attack":
            enemies.take_pending_attack(self.state, events)
        elif kind == "enemy_defeated_reaction":
            enemies.resolve_enemy_defeated_reaction(self.state, payload, events)
        elif kind == "discard_asset":
            discard_asset_choice(self.state, payload, events)
        elif kind == "discard_to_size":
            phases.discard_to_size(self.state, payload, events)
        elif kind == "cover_up_choice":
            resolve_cover_up_choice(self.state, payload, events)
        elif kind == "old_book_choice":
            actions.resolve_old_book_choice(self.state, payload, events, self.rng)
        elif kind == "scenario":
            from .scenarios import the_gathering

            the_gathering.resolve_scenario_choice(self.state, payload, events, self.rng)
        else:
            raise EngineError(f"unsupported decision payload: {kind}")

    def _append_rule_events(self, rule_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rendered: list[dict[str, Any]] = []
        log = EventLog(self.run_dir)
        for event in rule_events:
            event_type = event.get("type", "event")
            message = event.get("message", "")
            data = dict(event.get("data", {}))
            data["message"] = message
            if event_type == "game_end":
                data["summary"] = message
            rendered.append(log.append(round=self.state.round, phase=self.state.phase, type=event_type, data=data))
        return rendered

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
