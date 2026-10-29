"""Per-sentence language (EN/ES), lexicons and spaCy models.

Reasoning models often switch language mid-trace, so each sentence gets its
own language. The test is cheap: count words that are stopwords in only one
of the two languages. A sentence with clear evidence (3+ hits, at least
twice the other language) takes that language; otherwise it follows the
running total for the trace, which also decides very short sentences
("Wait.") from context. The decision only uses earlier sentences, so it is
the same however the text was chunked.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import spacy
import yaml
from spacy.lang.en.stop_words import STOP_WORDS as EN_STOP
from spacy.lang.es.stop_words import STOP_WORDS as ES_STOP

LANGUAGES = ("en", "es")
# Medium models: the small Spanish one mis-tags common CoT words (e.g. "login"
# as a verb, "contraseña" as an adjective with lemma "contraseño") and is only
# ~14% faster on the sample trace.
MODELS = {"en": "en_core_web_md", "es": "es_core_news_md"}
DEFAULT_LANGUAGE = "en"

_ONLY = {"en": EN_STOP - ES_STOP, "es": ES_STOP - EN_STOP}
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_LEXICON_DIR = Path(__file__).parent / "lexicons"


def stopword_hits(text: str) -> dict[str, int]:
    words = [w.lower() for w in _WORD.findall(text)]
    return {lang: sum(w in _ONLY[lang] for w in words) for lang in LANGUAGES}


class LanguageTracker:
    def __init__(self) -> None:
        self.totals = {lang: 0 for lang in LANGUAGES}

    def detect(self, text: str) -> str:
        hits = stopword_hits(text)
        for lang in LANGUAGES:
            self.totals[lang] += hits[lang]
        best, other = sorted(LANGUAGES, key=lambda lang: -hits[lang])
        if hits[best] >= 3 and hits[best] >= 2 * hits[other]:
            return best
        if self.totals["es"] != self.totals["en"]:
            return max(LANGUAGES, key=lambda lang: self.totals[lang])
        return DEFAULT_LANGUAGE


@lru_cache(maxsize=None)
def load_nlp(lang: str) -> spacy.language.Language:
    # The parser and NER are not needed for lemmas and POS tags, and are the slow parts.
    return spacy.load(MODELS[lang], exclude=["parser", "ner"])


@lru_cache(maxsize=None)
def lexicon(lang: str) -> dict:
    with open(_LEXICON_DIR / f"{lang}.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data["stopwords"] = frozenset(w.lower() for w in data.get("stopwords", []))
    return data
