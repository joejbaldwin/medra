"""Layer 2: the incremental text miner (pipeline steps 1-8 of the build plan).

For each chunk:
1. Append it to the buffer and mask code/LaTeX/<think> in the uncommitted
   tail (clean.py; offsets unchanged).
2. Find the sentences that are certainly complete (sentences.py) and commit
   them. The rest stays pending until more text arrives.
3. For each committed sentence: detect its language, run spaCy (lemmas, POS),
   extract terms and n-grams (terms.py), and update the counts: frequencies,
   spans, per-segment counts and per-sentence co-occurrence.
4. Emit a MiningUpdate snapshot. TF-IDF and PMI are recomputed from the
   counts at that point (weights.py).

Work per sentence is proportional to the sentence, except the snapshot,
which is rebuilt from the counts each time (measured in step 7).

Segments are paragraphs (blank-line separated) for now; step 4 replaces
them with TextTiling + discourse markers.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations

from medra.contracts import (
    Cooccurrence,
    MiningUpdate,
    Segment,
    SegmentKeywords,
    Sentence,
    Stats,
    Term,
    TermWeight,
    TextChunk,
    TokenDecision,
)
from medra.mining.clean import mask
from medra.mining.language import LanguageTracker, lexicon, load_nlp
from medra.mining.sentences import find_sentences
from medra.mining.terms import decide, extract
from medra.mining.weights import pmi, tfidf_top_k

MIN_NGRAM_COUNT = 2  # an n-gram becomes a term once it has appeared this often
MIN_COOC_COUNT = 2  # pairs seen in fewer sentences are not reported
TFIDF_TOP_K = 8
RECENT_TOKENS = 20  # token decisions kept per update, for the dashboard's ticker
_BLANK_LINE = re.compile(r"\n[ \t]*\n")


@dataclass
class _TermStat:
    kind: str  # "word" or "ngram"
    first_seen: int
    count: int = 0
    spans: list[tuple[int, int]] = field(default_factory=list)
    forms: dict[str, list[int]] = field(default_factory=dict)  # surface form -> [count, first offset]
    by_segment: Counter[int] = field(default_factory=Counter)


class TextMiner:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.text = ""
        self.masked = ""  # masked copy of text[:committed_upto]
        self.committed_upto = 0
        self.done = False
        self.seq = 0
        self.tracker = LanguageTracker()
        self.sentences: list[Sentence] = []
        self.sentence_lang: list[str] = []
        self.segments: list[list[int]] = []  # [start, end] per segment
        self.terms: dict[str, _TermStat] = {}
        self.sentence_df: Counter[str] = Counter()  # sentences containing each term
        self.pairs: Counter[tuple[str, str]] = Counter()
        self.words = 0
        self.vocabulary: set[str] = set()
        self.words_by_lang: Counter[str] = Counter()
        self.recent: list[TokenDecision] = []  # decisions in the current update only

    # ------------------------------------------------------------------ feed

    def feed(self, chunk: TextChunk) -> MiningUpdate | None:
        if chunk.channel != "reasoning" or self.done:
            return None
        self.text += chunk.text
        final = chunk.final
        start = self.committed_upto
        region = mask(self.text, start, final)
        limit = len(self.text) if final else region.hold
        spans, frontier = find_sentences(region.text, 0, limit - start, final)
        if not spans and not final:
            return None
        masked_full = self.masked + region.text
        self.recent = []
        self._commit([(start + a, start + b) for a, b in spans], masked_full)
        self.masked += region.text[:frontier]
        self.committed_upto = start + frontier
        self.done = final
        return self._snapshot(chunk.t)

    # ---------------------------------------------------------------- commit

    def _commit(self, spans: list[tuple[int, int]], masked: str) -> None:
        # Language first (cheap), then spaCy in runs of same-language sentences.
        langs = [self.tracker.detect(masked[a:b]) for a, b in spans]
        i = 0
        while i < len(spans):
            j = i
            while j < len(spans) and langs[j] == langs[i]:
                j += 1
            run = spans[i:j]
            docs = load_nlp(langs[i]).pipe(masked[a:b] for a, b in run)
            for (a, b), doc in zip(run, docs):
                self._add_sentence(a, b, langs[i], doc, masked)
            i = j

    def _add_sentence(self, start: int, end: int, lang: str, doc, masked: str) -> None:
        prev_end = self.sentences[-1].end if self.sentences else 0
        if not self.segments or _BLANK_LINE.search(masked, prev_end, start):
            self.segments.append([start, end])
        seg_id = len(self.segments) - 1
        self.segments[seg_id][1] = end
        self.sentences.append(Sentence(id=len(self.sentences), start=start, end=end, segment_id=seg_id))
        self.sentence_lang.append(lang)

        stopwords = lexicon(lang)["stopwords"]
        n_words = 0
        for tok in doc:
            if tok.is_alpha or tok.like_num or any(c.isalnum() for c in tok.text):
                n_words += 1
                self.vocabulary.add(tok.lemma_.lower())
                a = start + tok.idx
                self.recent.append(
                    TokenDecision(
                        form=self.text[a : a + len(tok.text)],
                        lemma=tok.lemma_.lower(),
                        pos=tok.pos_,
                        outcome=decide(tok, stopwords),
                        span=(a, a + len(tok.text)),
                    )
                )
        del self.recent[:-RECENT_TOKENS]
        self.words += n_words
        self.words_by_lang[lang] += n_words

        occurrences = extract(doc, start, lang, stopwords)
        for occ in occurrences:
            stat = self.terms.get(occ.term_id)
            if stat is None:
                stat = self.terms[occ.term_id] = _TermStat(kind=occ.kind, first_seen=occ.start)
            stat.count += 1
            stat.spans.append((occ.start, occ.end))
            stat.by_segment[seg_id] += 1
            form = self.text[occ.start : occ.end]
            entry = stat.forms.setdefault(form, [0, occ.start])
            entry[0] += 1

        present = sorted({occ.term_id for occ in occurrences})
        self.sentence_df.update(present)
        for a, b in combinations(present, 2):
            if not _nested(a, b):  # "binary search" always co-occurs with "search"
                self.pairs[(a, b)] += 1

    # -------------------------------------------------------------- snapshot

    def _reported(self) -> dict[str, _TermStat]:
        return {
            tid: s for tid, s in self.terms.items() if s.kind == "word" or s.count >= MIN_NGRAM_COUNT
        }

    def _snapshot(self, t: float) -> MiningUpdate:
        reported = self._reported()
        terms = [
            Term(
                id=tid,
                surface_forms=[f for f, _ in sorted(s.forms.items(), key=lambda kv: (-kv[1][0], kv[1][1]))],
                count=s.count,
                df_segments=len(s.by_segment),
                spans=list(s.spans),
                first_seen=s.first_seen,
            )
            for tid, s in reported.items()
        ]
        terms.sort(key=lambda term: (-term.count, term.first_seen, term.id))

        per_segment: dict[int, dict[str, int]] = {seg: {} for seg in range(len(self.segments))}
        for tid, s in reported.items():
            for seg, n in s.by_segment.items():
                per_segment[seg][tid] = n
        tfidf = [
            SegmentKeywords(segment_id=seg, terms=[TermWeight(term_id=tid, weight=w) for tid, w in top])
            for seg, top in sorted(tfidf_top_k(per_segment, TFIDF_TOP_K).items())
        ]

        n_sent = len(self.sentences)
        cooc = [
            Cooccurrence(a=a, b=b, count=c, pmi=round(pmi(c, self.sentence_df[a], self.sentence_df[b], n_sent), 4))
            for (a, b), c in self.pairs.items()
            if c >= MIN_COOC_COUNT and a in reported and b in reported
        ]
        cooc.sort(key=lambda p: (-p.count, -p.pmi, p.a, p.b))

        segments = [
            Segment(id=i, start=a, end=b, provisional=(i == len(self.segments) - 1 and not self.done))
            for i, (a, b) in enumerate(self.segments)
        ]
        language = max(self.words_by_lang, key=self.words_by_lang.get) if self.words_by_lang else None
        update = MiningUpdate(
            session_id=self.session_id,
            seq=self.seq,
            t=t,
            language=language,
            text_length=len(self.text),
            committed_upto=self.committed_upto,
            final=self.done,
            sentences=list(self.sentences),
            segments=segments,
            terms=terms,
            tfidf=tfidf,
            cooc=cooc,
            stats=Stats(
                words=self.words,
                sentences=n_sent,
                segments=len(segments),
                lexical_diversity=round(len(self.vocabulary) / self.words, 4) if self.words else None,
                extra={
                    f"share_{lang}": round(n / self.words, 4) for lang, n in sorted(self.words_by_lang.items())
                },
            ),
            recent_tokens=list(self.recent),
        )
        self.seq += 1
        return update


def _nested(a: str, b: str) -> bool:
    wa, wb = set(a.split()), set(b.split())
    return wa <= wb or wb <= wa
