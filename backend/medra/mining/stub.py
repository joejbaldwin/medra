"""Stub miner for the walking skeleton: regex sentences + word counts.

It already follows the real miner's shape (buffer + commit frontier, spans
for every term) so the layers around it can be built and tested now. Step 2
replaces the regexes and the tiny stoplists with spaCy.
"""

from __future__ import annotations

import re
from collections import Counter

from medra.contracts import MiningUpdate, Sentence, Stats, Term, TextChunk

# A sentence ends at . ! ? or … (plus closing quotes/brackets) when followed
# by whitespace, or at a blank line. Requiring the whitespace means a chunk
# ending in "3." does not commit until we know it is not "3.14".
SENTENCE_END = re.compile(r"[.!?…]+[\"'»”)\]]*(?=\s)|\n\s*\n")
WORD = re.compile(r"\w+", re.UNICODE)

STOPWORDS = {
    "en": set(
        "the a an and or but if then so of to in on at for with from by as is are was were be been "
        "this that these those it its i me my we our you your he she they them their not no yes do does "
        "did can could should would will may might must have has had there here what which who how why "
        "when where all any some just also than too very about into out up down over again let okay hmm "
        "well wait now one need".split()
    ),
    "es": set(
        "el la los las un una unos unas y o pero si sino de del al a en con por para sin sobre entre "
        "es son fue ser está están estar ha han hay que qué se lo le les me mi te tu su sus nos no sí "
        "ya más muy también como cómo cuando cuándo donde dónde este esta estos estas ese esa eso esto "
        "hasta desde puede pueden debe vale bueno pues ahora aunque porque tengo tiene".split()
    ),
}


def guess_language(text: str) -> str | None:
    """Pick the language whose stopwords appear most often (stub heuristic)."""
    words = [w.lower() for w in WORD.findall(text)]
    hits = {lang: sum(w in stops for w in words) for lang, stops in STOPWORDS.items()}
    best = max(hits, key=hits.get)
    return best if hits[best] > 0 else None


class StubMiner:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.text = ""
        self.committed_upto = 0
        self.language: str | None = None
        self.sentences: list[Sentence] = []
        self.counts: Counter[str] = Counter()
        self.spans: dict[str, list[tuple[int, int]]] = {}
        self.forms: dict[str, list[str]] = {}
        self.total_words = 0
        self.vocabulary: set[str] = set()
        self.seq = 0
        self.done = False

    def feed(self, chunk: TextChunk) -> MiningUpdate | None:
        if chunk.channel != "reasoning" or self.done:
            return None
        self.text += chunk.text
        frontier = len(self.text) if chunk.final else self._find_frontier()
        if frontier <= self.committed_upto and not chunk.final:
            return None
        self._commit(frontier)
        self.done = chunk.final
        return self._snapshot(chunk.t)

    def _find_frontier(self) -> int:
        """End of the last complete sentence in the uncommitted tail."""
        frontier = self.committed_upto
        for m in SENTENCE_END.finditer(self.text, self.committed_upto):
            frontier = m.end()
        return frontier

    def _commit(self, upto: int) -> None:
        start = self.committed_upto
        # Split the newly committed region into sentences.
        pos = start
        for m in SENTENCE_END.finditer(self.text, start, upto):
            self._add_sentence(pos, m.end())
            pos = m.end()
        self._add_sentence(pos, upto)
        # Count words. The frontier is always after a sentence end, so no
        # word straddles it.
        for m in WORD.finditer(self.text, start, upto):
            form = m.group()
            self.total_words += 1
            lemma = form.lower()
            self.vocabulary.add(lemma)
            if len(lemma) < 3 or lemma.isdigit() or self._is_stopword(lemma):
                continue
            self.counts[lemma] += 1
            self.spans.setdefault(lemma, []).append((m.start(), m.end()))
            if form not in self.forms.setdefault(lemma, []):
                self.forms[lemma].append(form)
        self.committed_upto = upto
        if self.language is None:
            self.language = guess_language(self.text[:upto])

    def _add_sentence(self, start: int, end: int) -> None:
        # Trim surrounding whitespace so the span covers only the sentence.
        segment = self.text[start:end]
        if not segment.strip():
            return
        start += len(segment) - len(segment.lstrip())
        end -= len(segment) - len(segment.rstrip())
        self.sentences.append(Sentence(id=len(self.sentences), start=start, end=end))

    @staticmethod
    def _is_stopword(word: str) -> bool:
        # Union of both lists: if it depended on the detected language, the
        # result would depend on where the first commit happened to fall.
        return any(word in stops for stops in STOPWORDS.values())

    def _snapshot(self, t: float) -> MiningUpdate:
        terms = [
            Term(
                id=lemma,
                surface_forms=self.forms[lemma],
                count=n,
                df_segments=0,  # no segmentation yet
                spans=self.spans[lemma],
                first_seen=self.spans[lemma][0][0],
            )
            for lemma, n in self.counts.items()
        ]
        terms.sort(key=lambda term: (-term.count, term.first_seen))
        update = MiningUpdate(
            session_id=self.session_id,
            seq=self.seq,
            t=t,
            language=self.language,
            text_length=len(self.text),
            committed_upto=self.committed_upto,
            final=self.done,
            sentences=list(self.sentences),
            terms=terms,
            stats=Stats(
                words=self.total_words,
                sentences=len(self.sentences),
                lexical_diversity=round(len(self.vocabulary) / self.total_words, 4) if self.total_words else None,
            ),
        )
        self.seq += 1
        return update
