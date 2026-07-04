from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from . import data as card_data
from .errors import EngineError
from .log import EventLog, status_line
from .model import GameState, PendingDecision
from .rng import ArkhamRng
from .serialize import atomic_write_json, atomic_write_text, decode_hidden, encode_hidden, sha256_text
from . import actions, enemies, phases, skill_test
from .effects import (
    RuleEventList,
    assign_damage_choice,
    discard_asset_choice,
    resolve_agnes_horror_reaction,
    resolve_amnesia_keep,
    resolve_cover_up_choice,
)


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
        scenario: str = "the_gathering",
        investigator: str = "roland",
        notebook: str | Path | None = None,
    ) -> "Game":
        if difficulty not in CHAOS_BAGS:
            raise EngineError(f"unknown difficulty: {difficulty}")
        run_path = Path(run_dir)
        rng = ArkhamRng(seed)
        from .scenarios import SCENARIOS

        if scenario not in SCENARIOS:
            raise EngineError(f"unknown scenario: {scenario}")
        state = SCENARIOS[scenario].build_state(
            difficulty=difficulty,
            rng=rng,
            deck_path=deck_path,
            investigator_slug=investigator,
        )
        game = cls(run_path, state, rng)
        game._initialize_files(
            seed=seed,
            difficulty=difficulty,
            deck_path=deck_path or card_data.default_deck_for_investigator(investigator),
            scenario=scenario,
            notebook=notebook,
        )
        init_events: list[dict[str, Any]] = RuleEventList(state)
        phases.advance_until_decision(state, rng, init_events)
        game.save()
        rendered_events = game._append_rule_events(init_events)
        if state.decision_queue:
            game._append_decision_presented()
        game._append_timeline(chose=None, events=rendered_events)
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
        rule_events: list[dict[str, Any]] = RuleEventList(self.state)
        self._dispatch_payload(option.payload, rule_events)
        if not self.state.decision_queue and self.state.status == "in_progress":
            phases.advance_until_decision(self.state, self.rng, rule_events)
        rendered_events = self._append_rule_events(rule_events)
        events.extend(rendered_events)
        if self.state.status == "in_progress" and self.state.decision_queue:
            events.append(self._append_decision_presented())
        self.save()
        self._append_timeline(
            chose={"decision_id": decision.id, "option": option_index, "label": option.label},
            events=rendered_events,
        )
        return events

    def _append_decision_presented(self) -> dict[str, Any]:
        return EventLog(self.run_dir).append(
            round=self.state.round,
            phase=self.state.phase,
            type="decision_presented",
            data={"prompt": self.state.decision_queue[0].prompt},
            status=status_line(self.state),
            status_in_jsonl=True,
        )

    def _dispatch_payload(self, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
        kind = payload.get("kind")
        if kind == "action":
            actions.execute(self.state, payload, events, self.rng)
        elif kind == "commit_card":
            skill_test.commit_card(self.state, payload, events)
        elif kind == "commit_done":
            skill_test.finish_commit(self.state, self.rng, events)
        elif kind == "skill_boost":
            skill_test.apply_skill_boost(self.state, payload, events)
        elif kind == "post_reveal_done":
            skill_test.resolve(self.state, events, self.rng)
        elif kind == "wendy_token_reaction":
            skill_test.resolve_wendy_token_reaction(self.state, payload, events, self.rng)
        elif kind == "lucky_would_fail":
            skill_test.resolve_lucky_would_fail(self.state, payload, events, self.rng)
        elif kind == "after_fail_reaction":
            skill_test.resolve_after_fail_reaction(self.state, payload, events, self.rng)
        elif kind == "scavenging_reaction":
            skill_test.resolve_scavenging_reaction(self.state, payload, events)
        elif kind == "survival_instinct":
            skill_test.resolve_survival_instinct(self.state, payload, events)
        elif kind == "pickpocketing_reaction":
            actions.resolve_pickpocketing_reaction(self.state, payload, events, self.rng)
        elif kind == "ward_revelation":
            from . import encounter

            encounter.resolve_ward_revelation(self.state, payload, events, self.rng)
        elif kind == "assign_damage":
            resume = dict(self.state.pending_damage.get("resume", {})) if self.state.pending_damage else {}
            assign_damage_choice(self.state, payload, events, self.rng)
            if (
                self.state.status == "in_progress"
                and self.state.pending_damage is None
                and not self.state.decision_queue
                and resume.get("kind") == "action"
            ):
                actions.execute(self.state, dict(resume.get("payload", {})), events, self.rng)
            elif (
                self.state.status == "in_progress"
                and self.state.pending_damage is None
                and not self.state.decision_queue
                and resume.get("kind") == "scenario"
            ):
                self._resolve_scenario_choice(dict(resume), events)
        elif kind == "dodge_attack":
            enemies.cancel_pending_attack(self.state, events, str(payload["card"]), self.rng)
        elif kind == "take_attack":
            enemies.take_pending_attack(self.state, events, self.rng)
        elif kind == "aoo_attack_order":
            actions.resolve_ordered_aoo(
                self.state,
                events,
                str(payload["enemy"]),
                [str(enemy_id) for enemy_id in payload.get("remaining", [])],
                dict(payload.get("action_payload", {})),
                self.rng,
            )
        elif kind == "enemy_attack_order":
            phases.resolve_enemy_attack_order(self.state, payload, events, self.rng)
        elif kind == "enemy_defeated_reaction":
            enemies.resolve_enemy_defeated_reaction(self.state, payload, events)
        elif kind == "discard_asset":
            discard_asset_choice(self.state, payload, events)
        elif kind == "amnesia_keep":
            resolve_amnesia_keep(self.state, payload, events)
        elif kind == "agnes_horror_reaction":
            resolve_agnes_horror_reaction(self.state, payload, events)
        elif kind == "slot_discard":
            actions.resolve_slot_discard(self.state, payload, events)
        elif kind == "discard_to_size":
            phases.discard_to_size(self.state, payload, events)
        elif kind == "fast_window_pass":
            self.state.limits[str(payload["key"])] = True
        elif kind == "cover_up_choice":
            resolve_cover_up_choice(self.state, payload, events)
        elif kind == "old_book_choice":
            actions.resolve_old_book_choice(self.state, payload, events, self.rng)
        elif kind == "scrying_order":
            actions.resolve_scrying_order(self.state, payload, events)
        elif kind == "arcane_initiate_choice":
            actions.resolve_arcane_initiate_choice(self.state, payload, events, self.rng)
        elif kind == "heirloom_reaction":
            actions.resolve_heirloom_reaction(self.state, payload, events, self.rng)
        elif kind == "scenario":
            self._resolve_scenario_choice(payload, events)
        else:
            raise EngineError(f"unsupported decision payload: {kind}")

    def _resolve_scenario_choice(self, payload: dict[str, Any], events: list[dict[str, Any]]) -> None:
        from .scenarios import SCENARIOS

        scenario = SCENARIOS.get(self.state.scenario)
        if scenario is None:
            raise EngineError(f"unsupported scenario choice for {self.state.scenario}")
        scenario.resolve_choice(self.state, payload, events, self.rng)

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
            status = status_line(self.state) if event_type == "game_end" else None
            rendered.append(
                log.append(
                    round=int(event.get("round", self.state.round)),
                    phase=str(event.get("phase", self.state.phase)),
                    type=event_type,
                    data=data,
                    status=status,
                )
            )
        return rendered

    def _append_timeline(self, *, chose: dict[str, Any] | None, events: list[dict[str, Any]]) -> None:
        try:
            path = self.run_dir / "timeline.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            line = {
                "i": _next_timeline_index(path),
                "round": self.state.round,
                "phase": self.state.phase,
                "status": status_line(self.state),
                "chose": chose,
                "events": [_timeline_event(event) for event in events],
                "pending": _timeline_pending(self.current_decision()),
                "state": self.state.public_dict(),
            }
            payload = (json.dumps(line, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o666)
            try:
                os.write(fd, payload)
            finally:
                os.close(fd)
        except OSError as exc:
            print(f"warning: failed to append timeline: {exc}", file=sys.stderr)

    def _initialize_files(
        self,
        *,
        seed: int,
        difficulty: str,
        deck_path: str | Path | None,
        scenario: str = "the_gathering",
        notebook: str | Path | None = None,
    ) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "seed": seed,
            "difficulty": difficulty,
            "deck": str(deck_path or card_data.DEFAULT_DECK),
            "scenario": scenario,
            "investigator": {
                "id": self.state.investigator.id,
                "code": self.state.investigator.card_code,
                "name": self.state.investigator.name,
            },
            "created_at": _now(),
            "engine_version": __version__,
            "status": self.state.status,
        }
        if notebook is not None:
            meta["notebook"] = str(Path(notebook).resolve())
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


def _next_timeline_index(path: Path) -> int:
    if not path.exists():
        return 0
    index = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                index += 1
    return index


def _timeline_pending(decision: PendingDecision | None) -> dict[str, Any] | None:
    if decision is None:
        return None
    return {
        "id": decision.id,
        "prompt": decision.prompt,
        "options": [option.label for option in decision.options],
    }


def _timeline_event(event: dict[str, Any]) -> dict[str, Any]:
    data = event.get("data", {})
    message = data.get("message") if isinstance(data, dict) else None
    if message is None:
        message = event.get("message")
    if message is None and isinstance(data, dict):
        message = data.get("summary")
    return {"type": str(event.get("type", "event")), "message": str(message or "")}
