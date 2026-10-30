"""Split text that wraps its reasoning in <think>...</think> into channels.

R1-style models (and text copied from them) write the chain of thought
between <think> and </think> and the answer after it. ThinkSplitter does
this on a stream, where a tag can be cut across two chunks ("<thi" + "nk>"):
it holds back any tail that could still become a tag.
"""

from __future__ import annotations

from medra.contracts import Channel

OPEN = "<think>"
CLOSE = "</think>"


class ThinkSplitter:
    def __init__(self) -> None:
        self.channel: Channel = "reasoning"
        self.seen_open = False
        self.answer_started = False
        self.buffer = ""

    def feed(self, text: str) -> list[tuple[Channel, str]]:
        self.buffer += text
        out: list[tuple[Channel, str]] = []
        while self.channel == "reasoning":
            # Drop the opening tag (some models omit it; text before it is reasoning too).
            i = self.buffer.find(OPEN) if not self.seen_open else -1
            if i >= 0:
                self._emit(out, self.buffer[:i])
                self.buffer = self.buffer[i + len(OPEN) :]
                self.seen_open = True
                continue
            # The closing tag switches to the answer.
            i = self.buffer.find(CLOSE)
            if i < 0:
                break
            self._emit(out, self.buffer[:i])
            self.buffer = self.buffer[i + len(CLOSE) :]
            self.channel = "answer"
        # Keep back a tail that is the start of a tag; release the rest.
        keep = _partial_tag(self.buffer) if self.channel == "reasoning" else 0
        self._emit(out, self.buffer[: len(self.buffer) - keep])
        self.buffer = self.buffer[len(self.buffer) - keep :]
        return out

    def flush(self) -> list[tuple[Channel, str]]:
        out: list[tuple[Channel, str]] = []
        self._emit(out, self.buffer)
        self.buffer = ""
        return out

    def _emit(self, out: list[tuple[Channel, str]], text: str) -> None:
        # Whitespace between </think> and the answer may arrive in later chunks.
        if self.channel == "answer" and not self.answer_started:
            text = text.lstrip()
            self.answer_started = bool(text)
        if text:
            out.append((self.channel, text))


def _partial_tag(text: str) -> int:
    """Length of the longest suffix of `text` that is a proper prefix of a tag."""
    for n in range(min(len(text), len(CLOSE) - 1), 0, -1):
        tail = text[-n:]
        if CLOSE.startswith(tail) or OPEN.startswith(tail):
            return n
    return 0


def split_think(text: str) -> tuple[str, str]:
    """(reasoning, answer) of a whole text. Without </think>, all of it is reasoning."""
    splitter = ThinkSplitter()
    parts = splitter.feed(text) + splitter.flush()
    reasoning = "".join(t for c, t in parts if c == "reasoning")
    answer = "".join(t for c, t in parts if c == "answer")
    return reasoning.strip(), answer.strip()
