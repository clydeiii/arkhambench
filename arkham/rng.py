from __future__ import annotations

import base64
import pickle
import random
from dataclasses import dataclass, field
from typing import Any, Iterable, MutableSequence, TypeVar


T = TypeVar("T")


@dataclass
class ArkhamRng:
    seed: int
    _random: random.Random = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._random = random.Random(self.seed)

    def shuffle(self, values: MutableSequence[T]) -> None:
        self._random.shuffle(values)

    def choice(self, values: Iterable[T]) -> T:
        items = list(values)
        if not items:
            raise ValueError("cannot choose from an empty iterable")
        return self._random.choice(items)

    def randint(self, a: int, b: int) -> int:
        return self._random.randint(a, b)

    def to_dict(self) -> dict[str, Any]:
        state_bytes = pickle.dumps(self._random.getstate())
        return {
            "seed": self.seed,
            "state": base64.b64encode(state_bytes).decode("ascii"),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArkhamRng":
        rng = cls(seed=int(data["seed"]))
        state = pickle.loads(base64.b64decode(data["state"].encode("ascii")))
        rng._random.setstate(state)
        return rng
