"""Step 2a: sentence boundaries that do not depend on how the text was chunked.

spaCy's parser can split sentences, but its decision for a boundary can
change when more text arrives after it, so a streamed trace and the same
trace in one piece could end up with different sentences. These rules
instead look at most at the next non-space character after the
punctuation, so a boundary decided early is the same one a batch run finds.

A boundary is:
- a newline (CoT often uses one line per step, list item or equation), or
- . ! ? … (plus closing quotes/brackets) followed by whitespace and then a
  character that can start a sentence. For "." the next character must be
  uppercase, a digit or an opening mark, and the word before must not be a
  known abbreviation ("e.g.", "Dr.", "p. ej."), and
- not the "." of a list number that opens the sentence ("2. Ben does not
  own the cat" is one sentence), unless the line ends right after it.
"""

from __future__ import annotations

import re

_END = re.compile(r"[.!?…]+[\"'»”’)\]]*")
_OPENING = set("¿¡\"'«“‘([*#-•")
# Lowercased words that take a period without ending a sentence (EN + ES).
ABBREVIATIONS = {
    # Not "no": in CoT "Hmm, no. Let me..." is far more common than "No. 5".
    "e.g", "i.e", "vs", "cf", "approx", "dr", "mr", "mrs", "ms", "fig", "eq", "st",
    "p.ej", "ej", "sr", "sra", "srta", "dra", "aprox", "núm", "pág", "pp", "ud", "uds",
}
_WORD_BEFORE = re.compile(r"([\w.]+)$")
_LIST_NUMBER = re.compile(r"\d{1,3}")


def find_sentences(masked: str, offset: int, limit: int, final: bool) -> tuple[list[tuple[int, int]], int]:
    """Split masked[offset:limit] (absolute offsets) into complete sentences.

    Returns (sentence spans, frontier). Text after the frontier is pending:
    its last sentence may not be finished. With final=True everything up to
    `limit` is committed.
    """
    spans: list[tuple[int, int]] = []
    sent_start = offset
    pos = offset
    while pos < limit:
        newline = masked.find("\n", pos, limit)
        m = _END.search(masked, pos, limit)
        if newline != -1 and (m is None or newline < m.start()):
            _add(masked, spans, sent_start, newline)
            sent_start = pos = newline + 1
            continue
        if m is None:
            break
        decision = _is_boundary(masked, m, limit, final)
        if decision and _list_number(masked, sent_start, m, limit):
            decision = False
        if decision is None:  # need more text to decide
            return spans, sent_start
        if decision:
            _add(masked, spans, sent_start, m.end())
            sent_start = m.end()
        pos = m.end()
    if final:
        _add(masked, spans, sent_start, limit)
        return spans, limit
    return spans, sent_start


def _is_boundary(masked: str, m: re.Match, limit: int, final: bool) -> bool | None:
    i = m.end()
    if i >= limit:
        return True if final else None
    if not masked[i].isspace():
        return False  # "3.14", "e.g.x", "?!" inside a token
    while i < limit and masked[i] in " \t":
        i += 1
    if i >= limit:
        return True if final else None
    nxt = masked[i]
    if nxt == "\n":
        return True
    if any(c in "!?…" for c in m.group()):
        return True
    # Only the last few characters matter; searching from 0 would be O(n) per period.
    word = _WORD_BEFORE.search(masked, max(0, m.start() - 12), m.start())
    if word and word.group(1).lower() in ABBREVIATIONS:
        return False
    if _spanish_p_ej(masked, m.start()):
        return False
    return nxt.isupper() or nxt.isdigit() or nxt in _OPENING


def _list_number(masked: str, sent_start: int, m: re.Match, limit: int) -> bool:
    """A "." right after a bare list number ("2.") at the start of a sentence,
    with more text on the same line. _is_boundary has already seen the next
    non-space character, so this needs no extra lookahead."""
    if m.group() != "." or not _LIST_NUMBER.fullmatch(masked[sent_start : m.start()].strip()):
        return False
    rest = masked[m.end() : limit].lstrip(" \t")
    return bool(rest) and rest[0] != "\n"


def _spanish_p_ej(masked: str, period: int) -> bool:
    # "p. ej." is written with a space, so the word before the second period is "ej".
    return masked[max(0, period - 5) : period].lower().endswith("p. ej")


def _add(masked: str, spans: list[tuple[int, int]], start: int, end: int) -> None:
    segment = masked[start:end]
    stripped = segment.strip()
    if not stripped:
        return
    a = start + (len(segment) - len(segment.lstrip()))
    spans.append((a, a + len(stripped)))
