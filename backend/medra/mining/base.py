"""Layer 2 interface. A miner sees only TextChunks (never the source) and
reports what it found as MiningUpdate snapshots with character offsets."""

from __future__ import annotations

from typing import Protocol

from medra.contracts import MiningUpdate, TextChunk


class Miner(Protocol):
    def feed(self, chunk: TextChunk) -> MiningUpdate | None:
        """Consume one chunk. Return an update when new text was committed."""
        ...
