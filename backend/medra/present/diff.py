"""Diffing for ViewUpdate: only what changed since the last frame is sent."""

from __future__ import annotations

from typing import Callable, Generic, Hashable, TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)
K = TypeVar("K", bound=Hashable)


class Keyed(Generic[K, M]):
    """Remembers the last version of each item sent, keyed by id."""

    def __init__(self, key: Callable[[M], K]) -> None:
        self.key = key
        self.sent: dict[K, M] = {}

    def diff(self, items: list[M]) -> tuple[list[M], list[K]]:
        """Return (added or changed items, removed keys) and remember `items`."""
        current = {self.key(item): item for item in items}
        changed = [item for k, item in current.items() if self.sent.get(k) != item]
        removed = [k for k in self.sent if k not in current]
        self.sent = current
        return changed, removed
