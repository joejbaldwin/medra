"""Pasted text, replayed as a stream (costs nothing, works offline).

If the text contains </think> (copied from an R1-style model), what comes
before it is the reasoning and what comes after is the answer; otherwise it
is all reasoning.
"""

from __future__ import annotations

import re

from medra.sources.replay import Chunking, ReplaySource
from medra.sources.samples import Trace
from medra.sources.think import split_think


def pasted_trace(text: str) -> Trace:
    reasoning, answer = split_think(text)
    words = len(re.findall(r"\S+", reasoning))
    return Trace(
        id="paste", title=f"Texto pegado ({words} palabras)", language="", prompt="",
        reasoning=reasoning, answer=answer, origin="pegado por el usuario",
    )


class PasteSource(ReplaySource):
    name = "paste"

    def __init__(self, text: str, session_id: str, words_per_second: float = 15.0,
                 chunking: Chunking = "word", seed: int = 0) -> None:
        super().__init__(pasted_trace(text), session_id, words_per_second, chunking, seed)
