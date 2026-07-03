"""Card registry placeholder for phase C."""

from __future__ import annotations

from typing import Any, Callable


REGISTRY: dict[str, type[Any]] = {}


def card(code: str) -> Callable[[type[Any]], type[Any]]:
    def decorator(cls: type[Any]) -> type[Any]:
        REGISTRY[code] = cls
        return cls

    return decorator
