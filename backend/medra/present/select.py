"""Which terms become bubbles.

1. Nested words: a single word whose mentions are mostly inside a reported
   n-gram ("odd" inside "odd number") is dropped, so the map does not show
   the same mentions three times.
2. Score = count x (1 + best TF-IDF weight of the term in any segment).
   Frequency dominates; a term that characterises some segment gets up to
   twice the weight of an equally frequent term that does not.
3. Hysteresis: a term enters when it ranks within the top K and leaves only
   when it falls below rank K + MARGIN, so bubbles do not flicker in and out
   as counts change by one.
"""

from __future__ import annotations

import bisect
from collections import defaultdict

from medra.contracts import MiningUpdate, Term

TOP_K = 16
MARGIN = 3
NESTED_SHARE = 0.75  # drop a word if at least this share of its mentions sit inside n-grams


def nested_words(terms: list[Term], share: float = NESTED_SHARE) -> set[str]:
    """Ids of single words whose mentions are mostly covered by reported n-grams."""
    ngram_spans: dict[str, list[tuple[int, int]]] = defaultdict(list)  # word -> spans of n-grams containing it
    for term in terms:
        if " " in term.id:
            for word in set(term.id.split()):
                ngram_spans[word].extend(term.spans)
    out = set()
    for term in terms:
        if " " in term.id or term.id not in ngram_spans:
            continue
        covering = sorted(ngram_spans[term.id])
        inside = sum(_covered(span, covering) for span in term.spans)
        if inside >= share * term.count:
            out.add(term.id)
    return out


_MAX_NGRAM_CHARS = 200  # an n-gram (at most 3 tokens) never starts further back than this


def _covered(span: tuple[int, int], covering: list[tuple[int, int]]) -> bool:
    # `covering` is sorted by start: only spans starting shortly before `span` can contain it.
    lo = bisect.bisect_left(covering, (span[0] - _MAX_NGRAM_CHARS, -1))
    hi = bisect.bisect_right(covering, (span[0], float("inf")))
    return any(span[1] <= b for _, b in covering[lo:hi])


def scores(update: MiningUpdate) -> dict[str, float]:
    best_tfidf: dict[str, float] = {}
    for keywords in update.tfidf:
        for tw in keywords.terms:
            best_tfidf[tw.term_id] = max(best_tfidf.get(tw.term_id, 0.0), tw.weight)
    return {t.id: t.count * (1.0 + best_tfidf.get(t.id, 0.0)) for t in update.terms}


class BubbleSelector:
    def __init__(self, top_k: int = TOP_K, margin: int = MARGIN) -> None:
        self.top_k = top_k
        self.margin = margin
        self.shown: set[str] = set()
        self.nested: set[str] = set()  # words dropped in favour of an n-gram, last update

    def select(self, update: MiningUpdate) -> list[Term]:
        """Terms to show, highest score first."""
        self.nested = nested_words(update.terms)
        score = scores(update)
        candidates = [t for t in update.terms if t.id not in self.nested]
        candidates.sort(key=lambda t: (-score[t.id], -t.count, t.first_seen, t.id))
        rank = {t.id: i for i, t in enumerate(candidates)}
        keep = {tid for tid in self.shown if tid in rank and rank[tid] < self.top_k + self.margin}
        for t in candidates:
            if len(keep) >= self.top_k:
                break
            keep.add(t.id)
        self.shown = keep
        return [t for t in candidates if t.id in keep]
