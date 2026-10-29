"""Layer 1 interface. A source only produces TextChunks; it knows nothing
about mining or display, so any adapter can be swapped in."""

from __future__ import annotations

from typing import AsyncIterator, Protocol

from medra.contracts import TextChunk


class Source(Protocol):
    name: str
    title: str | None
    prompt: str | None

    def stream(self) -> AsyncIterator[TextChunk]: ...
