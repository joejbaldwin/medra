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


@dataclass(frozen=True)
class Occurrence:
    term_id: str
    start: int  # absolute offsets
    end: int
    kind: str  # "word" or "ngram"


def is_content(tok: Token, stopwords: frozenset[str]) -> bool:
    lemma = tok.lemma_.lower()
    return (
        tok.pos_ in CONTENT_POS
        and not tok.is_stop
        and lemma not in stopwords
        and not tok.like_num
        and any(c.isalpha() for c in tok.text)
        and "." not in tok.text  # abbreviations such as "Dr." or "e.g."
        and len(lemma) >= 2
    )


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
