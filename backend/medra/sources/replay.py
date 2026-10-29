"""Replay a recorded trace as if a model were writing it.

The text is cut into chunks and released at a steady words-per-second rate.
Two chunkings:
- "word": one word plus its trailing whitespace per chunk (like a token stream).
- "random": seeded random sizes from 1 to 40 characters, which split words
  mid-way. Used by the tests: the miner must give the same result whatever
  the chunk boundaries are.
"""

from __future__ import annotations

import asyncio
import bisect
import random
import re
import time
from typing import AsyncIterator, Iterator, Literal

from medra.contracts import Channel, TextChunk
from medra.sources.samples import Trace

# Clock used for `t` when words_per_second is 0 (no pacing), so that t stays
# meaningful and deterministic in tests and CLI runs.
NOMINAL_WPS = 15.0

Chunking = Literal["word", "random"]


def split_chunks(text: str, chunking: Chunking, rng: random.Random) -> Iterator[str]:
    if chunking == "word":
        for m in re.finditer(r"\S+\s*|\s+", text):
            yield m.group()
    else:
        i = 0
        while i < len(text):
            # Mostly small pieces (token-like), sometimes a long run.
            size = rng.randint(1, 6) if rng.random() < 0.8 else rng.randint(7, 40)
            yield text[i : i + size]
            i += size


class ReplaySource:
    name = "replay"

    def __init__(
        self,
        trace: Trace,
        session_id: str,
        words_per_second: float = 15.0,
        chunking: Chunking = "word",
        seed: int = 0,
    ) -> None:
        self.trace = trace
        self.title = trace.title
        self.prompt = trace.prompt
        self.session_id = session_id
        self.words_per_second = words_per_second
        self.chunking = chunking
        self.seed = seed

    async def stream(self) -> AsyncIterator[TextChunk]:
        rng = random.Random(self.seed)
        rate = self.words_per_second or NOMINAL_WPS
        start = time.monotonic()
        seq = 0
        words_before = 0  # words in channels already sent
        channels: list[tuple[Channel, str]] = [("reasoning", self.trace.reasoning), ("answer", self.trace.answer)]
        for channel, text in channels:
            if not text:
                continue
            # Offsets where a word starts; a chunk's word count is how many of these it covers.
            word_starts = [m.start() for m in re.finditer(r"\S+", text)]
            pieces = list(split_chunks(text, self.chunking, rng))
            pos = 0
            for k, piece in enumerate(pieces):
                pos += len(piece)
                words = words_before + bisect.bisect_left(word_starts, pos)
                t = words / rate
                if self.words_per_second > 0:
                    delay = start + t - time.monotonic()
                    if delay > 0:
                        await asyncio.sleep(delay)
                yield TextChunk(
                    session_id=self.session_id,
                    seq=seq,
                    channel=channel,
                    text=piece,
                    t=round(t, 3),
                    final=k == len(pieces) - 1,
                )
                seq += 1
            words_before += len(word_starts)
