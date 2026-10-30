"""Steps 3-4: candidate terms (lemmatised unigrams and n-grams) in one sentence.

Unigrams: content words (NOUN, PROPN, ADJ) that are not stopwords (spaCy's
list plus the project's CoT filler list), keyed by lowercased lemma, so
"numbers" and "number" are one term.

N-grams: short POS patterns over adjacent tokens, keyed by their lemmas.
English: (ADJ|NOUN|PROPN){1,2} followed by NOUN|PROPN ("arithmetic series").
Spanish: NOUN|PROPN followed by 1-2 ADJ ("texto plano"), or NOUN de NOUN
("inicio de sesión"). Patterns avoid the dependency parser (slow) that
spaCy's noun_chunks would need. Whether an n-gram is frequent enough to
count as a term is decided later, from its total count.
"""

from __future__ import annotations

from dataclasses import dataclass

from spacy.tokens import Doc, Token

CONTENT_POS = {"NOUN", "PROPN", "ADJ"}
NOUNISH = {"NOUN", "PROPN"}
# Live chains of thought write maths inline without $...$ ("t=500/220=25/11"),
# which spaCy keeps as one token: such tokens are not terms.
MATH_CHARS = set("=+*/^<>")


@dataclass(frozen=True)
class Occurrence:
    term_id: str
    start: int  # absolute offsets
    end: int
    kind: str  # "word" or "ngram"


def decide(tok: Token, stopwords: frozenset[str]) -> str:
    """Why a token is kept or dropped (a TokenDecision outcome code)."""
    lemma = tok.lemma_.lower()
    letters = sum(c.isalpha() for c in tok.text)
    if tok.like_num or sum(c.isdigit() for c in tok.text) > letters:
        return "number"
    if not letters or "." in tok.text or MATH_CHARS & set(tok.text) or len(lemma) < 2:
        return "other"  # punctuation, symbols, inline maths, abbreviations such as "Dr." or "e.g."
    if tok.is_stop:
        return "stopword"
    if lemma in stopwords:
        return "filler"
    if tok.pos_ not in CONTENT_POS:
        return "pos"
    return "term"


def is_content(tok: Token, stopwords: frozenset[str]) -> bool:
    return decide(tok, stopwords) == "term"


def lemma_of(tok: Token) -> str:
    return tok.lemma_.lower()


def extract(doc: Doc, offset: int, lang: str, stopwords: frozenset[str]) -> list[Occurrence]:
    """All candidate occurrences in a sentence; `offset` is where the sentence starts."""
    content = [is_content(t, stopwords) for t in doc]
    out = [
        Occurrence(lemma_of(t), offset + t.idx, offset + t.idx + len(t.text), "word")
        for t, ok in zip(doc, content)
        if ok
    ]
    for i in range(len(doc)):
        for n in (2, 3):
            window = doc[i : i + n]
            if len(window) == n and _is_ngram(window, content[i : i + n], lang):
                first, last = window[0], window[-1]
                term_id = " ".join(lemma_of(t) if c else t.lower_ for t, c in zip(window, content[i : i + n]))
                out.append(Occurrence(term_id, offset + first.idx, offset + last.idx + len(last.text), "ngram"))
    return out


def _is_ngram(window, content: list[bool], lang: str) -> bool:
    pos = [t.pos_ for t in window]
    if lang == "es":
        if len(window) == 3 and window[1].lower_ == "de":  # NOUN de NOUN
            return content[0] and content[2] and pos[0] in NOUNISH and pos[2] in NOUNISH
        if not all(content):
            return False
        noun_adj = pos[0] in NOUNISH and all(p == "ADJ" for p in pos[1:])
        return noun_adj or all(p == "PROPN" for p in pos)
    return all(content) and pos[-1] in NOUNISH
