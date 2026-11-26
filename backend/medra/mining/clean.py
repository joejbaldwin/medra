"""Cleaning (limpieza), done without changing any offsets.

Instead of deleting code, LaTeX and <think> tags (which would shift every
position after them and need an offset map), they are overwritten with
spaces in a *masked copy* of the text. The copy has exactly the same length,
so an offset in the masked text is the same offset in the original. The
miner analyses the masked copy and reads surface forms from the original.

Streaming complication: an opener whose closer has not arrived yet (a ```
fence still being written) cannot be classified. `mask` reports the
position of the first such opener as `hold`, and the miner does not commit
past it until more text arrives (or the stream ends).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Length-preserving character normalisation (one character in, one out).
_CHAR_MAP = str.maketrans({" ": " ", " ": " ", " ": " ", "’": "'", "\t": " "})


@dataclass(frozen=True)
class _Construct:
    name: str
    opener: str
    closer: str
    multiline: bool  # may span lines; single-line ones are literal text if a newline comes first


_CONSTRUCTS = [
    _Construct("fence", "```", "```", multiline=True),
    _Construct("display_math", "$$", "$$", multiline=True),
    _Construct("bracket_math", "\\[", "\\]", multiline=True),
    _Construct("paren_math", "\\(", "\\)", multiline=False),
    _Construct("inline_code", "`", "`", multiline=False),
    _Construct("inline_math", "$", "$", multiline=False),
]
# Longest openers first so "```" wins over "`" and "$$" over "$".
_OPENER = re.compile("|".join(re.escape(c.opener) for c in sorted(_CONSTRUCTS, key=lambda c: -len(c.opener))))
_BY_OPENER = {c.opener: c for c in _CONSTRUCTS}
_THINK_TAG = re.compile(r"</?think>")
_THINK_PREFIXES = ("<", "</", "<t", "</t", "<th", "</th", "<thi", "</thi", "<thin", "</thin", "<think", "</think")


@dataclass(frozen=True)
class Masked:
    text: str  # masked copy of text[start:], same length
    hold: int  # absolute offset of the first unresolved opener (len(text) if none)


def mask(text: str, start: int = 0, final: bool = False) -> Masked:
    """Mask text[start:]. `start` must not lie inside a construct (the commit
    frontier never does, because nothing is committed past `hold`)."""
    region = text[start:].translate(_CHAR_MAP)
    chars = list(region)
    hold = len(text)

    def blank(a: int, b: int) -> None:
        chars[a:b] = " " * (b - a)

    pos = 0
    while True:
        m = _OPENER.search(region, pos)
        if not m:
            break
        construct = _BY_OPENER[m.group()]
        if construct.name == "inline_math" and not _looks_like_math_start(region, m.end()):
            pos = m.end()  # "$5" or "costs $ 5": a currency sign, not math
            continue
        close = region.find(construct.closer, m.end())
        newline = region.find("\n", m.end())
        if not construct.multiline and newline != -1 and (close == -1 or newline < close):
            pos = m.end()  # the line ended first: literal text
            continue
        if close == -1:
            if not final:
                hold = start + m.start()
                break
            if construct.multiline:
                blank(m.start(), len(region))  # unterminated block at the end: still code/maths
                break
            pos = m.end()  # unterminated inline construct at the end: literal
            continue
        blank(m.start(), close + len(construct.closer))
        pos = close + len(construct.closer)

    for t in _THINK_TAG.finditer(region):
        blank(t.start(), t.end())
    if not final:
        # A tag still being written at the very end ("<thi") must not be analysed yet.
        tail = region[max(0, len(region) - 8) :]
        for k in range(len(tail)):
            if tail[k:] in _THINK_PREFIXES:
                hold = min(hold, start + len(region) - len(tail) + k)
                break
    return Masked("".join(chars), hold)


def _looks_like_math_start(region: str, i: int) -> bool:
    # TeX convention: the opening $ is followed directly by a non-space, non-digit.
    return i < len(region) and not region[i].isspace() and not region[i].isdigit()
