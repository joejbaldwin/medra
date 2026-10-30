"""Discourse markers and hedges (build plan §4.2 steps 10 and 11).

A marker is a phrase that opens a reasoning step ("Wait,", "Alternatively",
"Let me check", "Primero"). Only sentence-initial markers count: "so" in the
middle of a sentence is not a step boundary. Up to two prefixes ("Hmm,",
"But", "Wait,") may come first, and a marker after a prefix wins over the
prefix, so "Wait, let me check" is a verification step while a bare "Wait."
is a backtrack.

Both lists live in the per-language lexicons (lexicons/*.yaml).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from medra.mining.language import lexicon


@dataclass(frozen=True)
class FoundMarker:
    type: str
    start: int  # offsets relative to the text passed in
    end: int


def _alternation(phrases: list[str]) -> str:
    # Longest first, so "let me check" is preferred to a shorter overlapping phrase.
    # Spaces match any run of spaces or commas: "no, wait" and "no wait" are one marker.
    parts = sorted({p.lower() for p in phrases}, key=len, reverse=True)
    return "|".join(r"[\s,]+".join(re.escape(w) for w in re.split(r"[\s,]+", p)) for p in parts)


@lru_cache(maxsize=None)
def _patterns(lang: str) -> tuple[re.Pattern[str], list[tuple[str, re.Pattern[str]]], re.Pattern[str] | None]:
    lex = lexicon(lang)
    prefix = _alternation(lex.get("marker_prefixes", []))
    # Up to two prefixes, each followed by punctuation or spaces (matched from
    # the first letter of the sentence; leading quotes/bullets are skipped first).
    head = re.compile(rf"((?:(?:{prefix})\b[\s,.:;!?-]*){{0,2}})", re.IGNORECASE) if prefix else None
    by_type = [
        (step_type, re.compile(rf"(?:{_alternation(phrases)})\b", re.IGNORECASE))
        for step_type, phrases in lex.get("markers", {}).items()
    ]
    hedges = lex.get("hedges", [])
    hedge = re.compile(rf"\b(?:{_alternation(hedges)})\b", re.IGNORECASE) if hedges else None
    return head, by_type, hedge


def find_marker(sentence: str, lang: str) -> FoundMarker | None:
    """The marker that opens `sentence`, if any. The span covers the prefixes
    too ("Wait, let me check"), which is what the dashboard shows."""
    head, by_type, _ = _patterns(lang)
    lead = len(sentence) - len(sentence.lstrip("\"'¿¡*-#> \t\n("))
    # Try the longest prefix run first, then shorter ones: each prefix may also
    # be a marker in its own right ("so", "wait").
    starts = [lead]
    if head:
        m = head.match(sentence, lead)
        if m and m.group(1):
            run = m.group(1)
            cuts = [lead + w.end() for w in re.finditer(r"[^\s,.:;!?-]+[\s,.:;!?-]*", run)]
            starts = list(reversed(cuts)) + [lead]
    for pos in starts:
        best: FoundMarker | None = None
        for step_type, pattern in by_type:
            m = pattern.match(sentence, pos)
            if m and (best is None or m.end() > best.end):
                best = FoundMarker(step_type, lead, m.end())
        if best:
            return best
    return None


def count_hedges(sentence: str, lang: str) -> int:
    hedge = _patterns(lang)[2]
    return len(hedge.findall(sentence)) if hedge else 0
