"""Shared pieces of the live source (DeepSeek)."""

from __future__ import annotations

import time

from medra.contracts import Channel, TextChunk


class SourceError(Exception):
    """A source could not produce its stream. The message is shown on the
    dashboard, so it is in Spanish and never contains credentials."""


class Emitter:
    """Builds the TextChunks of one live session: numbering, timing (seconds
    since the request was sent), and a final chunk per channel."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.start = time.monotonic()
        self.seq = 0
        self.closed: set[Channel] = set()

    def chunk(self, channel: Channel, text: str, final: bool = False) -> TextChunk:
        out = TextChunk(
            session_id=self.session_id,
            seq=self.seq,
            channel=channel,
            text=text,
            t=round(time.monotonic() - self.start, 3),
            final=final,
        )
        self.seq += 1
        if final:
            self.closed.add(channel)
        return out

    def close(self, channel: Channel) -> TextChunk | None:
        """An empty final chunk, unless the channel is already closed."""
        return None if channel in self.closed else self.chunk(channel, "", final=True)
