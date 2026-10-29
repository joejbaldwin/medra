"""The real miner (step 2). The two checks the build plan requires:
offsets round-trip, and random chunking gives the same final state."""

import math

import pytest

from conftest import SAMPLES, fixture_text, replay_chunks, text_chunks
from medra.contracts import MiningUpdate, TextChunk
from medra.mining import TextMiner
from medra.mining.miner import TFIDF_TOP_K
from medra.sources import load_trace

FIXTURES = ["tricky-en.txt", "mixed-en-es.txt"]


def mine(chunks: list[TextChunk]) -> tuple[TextMiner, list[MiningUpdate]]:
    miner = TextMiner("test")
    return miner, [u for u in (miner.feed(c) for c in chunks) if u is not None]


def final_state(chunks: list[TextChunk]) -> MiningUpdate:
    return mine(chunks)[1][-1]


def corpus() -> list[tuple[str, str]]:
    return [(s, load_trace(s).reasoning) for s in SAMPLES] + [(f, fixture_text(f)) for f in FIXTURES]


# ---------------------------------------------------------------- offsets


@pytest.mark.parametrize("name,text", corpus())
def test_every_span_points_at_its_term(name, text):
    for update in mine(text_chunks(text, "random", 5))[1]:
        for term in update.terms:
            assert term.count == len(term.spans)
            assert term.first_seen == term.spans[0][0]
            assert term.spans == sorted(term.spans)
            for start, end in term.spans:
                assert end <= update.committed_upto
                assert text[start:end] in term.surface_forms
        for s in update.sentences:
            assert s.end <= update.committed_upto
            assert text[s.start : s.end].strip() == text[s.start : s.end] != ""
        for seg in update.segments:
            assert text[seg.start : seg.end].strip() == text[seg.start : seg.end]


# ---------------------------------------------------------------- chunking


@pytest.mark.parametrize("name,text", corpus())
def test_final_state_does_not_depend_on_chunking(name, text):
    batch = final_state([_one_chunk(text)])
    for chunks in [text_chunks(text, "word")] + [text_chunks(text, "random", seed) for seed in range(6)]:
        streamed = final_state(chunks)
        for field in ("terms", "sentences", "segments", "tfidf", "cooc", "stats", "language", "committed_upto"):
            assert getattr(streamed, field) == getattr(batch, field), field


def _one_chunk(text: str) -> TextChunk:
    return TextChunk(session_id="test", seq=0, channel="reasoning", text=text, t=0.0, final=True)


def test_pending_tail_is_not_mined():
    chunks = [
        TextChunk(session_id="t", seq=0, channel="reasoning", text="The binary search works. The hash tab", t=0),
    ]
    miner, updates = mine(chunks)
    assert updates[-1].committed_upto == len("The binary search works.")
    assert "hash" not in {t.id for t in updates[-1].terms}


def test_masked_code_is_not_mined():
    final = final_state(text_chunks(fixture_text("tricky-en.txt")))
    ids = {t.id for t in final.terms}
    assert "binary search" in ids
    # Words that only occur inside code, inline code or maths.
    assert not ids & {"xs", "target", "mid", "lo", "hi", "def", "log", "overflow"} - {"overflow"}
    assert "overflow" in ids  # ...but text right after inline code still is mined


# ---------------------------------------------------------------- counts


def test_hand_counted_terms_spanish():
    final = final_state(replay_chunks("login-es", "random", 2))
    counts = {t.id: t.count for t in final.terms}
    # Counted by hand in data/samples/login-es.json (lemmas: "campos" -> campo).
    assert counts["login"] == 5
    assert counts["sesión"] == 4
    assert counts["contraseña"] == 3
    assert counts["email"] == 3
    assert counts["campo"] == 2
    assert final.language == "es"


def test_hand_counted_terms_english():
    final = final_state(replay_chunks("odd-sum-en", "random", 2))
    counts = {t.id: t.count for t in final.terms}
    # "number" and "numbers" are one lemma: 8 x "odd number(s)" + "the number of terms".
    assert counts["number"] == 9
    assert counts["odd number"] == 8
    assert counts["arithmetic series"] == 2
    assert final.language == "en"


def test_ngrams_need_two_occurrences():
    final = final_state(replay_chunks("login-es"))
    assert not [t for t in final.terms if " " in t.id and t.count < 2]


# ---------------------------------------------------------------- language


def test_language_is_detected_per_sentence():
    miner, updates = mine(text_chunks(fixture_text("mixed-en-es.txt")))
    assert miner.sentence_lang == ["en", "en", "es", "es", "es"]
    final = updates[-1]
    assert {"contraseña", "password"} <= {t.id for t in final.terms}
    assert set(final.stats.extra) == {"share_en", "share_es"}


# ---------------------------------------------------------------- segments


def test_paragraphs_are_provisional_segments():
    _, updates = mine(replay_chunks("login-es"))
    final = updates[-1]
    assert len(final.segments) == 4 and not any(s.provisional for s in final.segments)
    assert [s.segment_id for s in final.sentences] == [0] * 4 + [1] * 4 + [2] * 3 + [3] * 5
    assert updates[0].segments[-1].provisional


# ---------------------------------------------------------------- TF-IDF


def test_tfidf_per_segment():
    final = final_state(replay_chunks("login-es"))
    assert [k.segment_id for k in final.tfidf] == [0, 1, 2, 3]
    for keywords in final.tfidf:
        weights = [w.weight for w in keywords.terms]
        assert 0 < len(weights) <= TFIDF_TOP_K
        assert weights == sorted(weights, reverse=True) and all(0 < w <= 1 for w in weights)
    security = {w.term_id for w in final.tfidf[2].terms}  # "Espera, falta la seguridad..."
    assert {"hash", "seguridad", "servidor"} <= security


def test_term_df_segments():
    final = final_state(replay_chunks("login-es"))
    df = {t.id: t.df_segments for t in final.terms}
    assert df["login"] == 4 and df["hash"] == 1


# ---------------------------------------------------------------- co-occurrence


def test_cooccurrence_counts_and_pmi_from_sentences():
    final = final_state(replay_chunks("odd-sum-en"))
    assert final.cooc
    sentences_with = {t.id: _sentences_containing(final, t.spans) for t in final.terms}
    n = len(final.sentences)
    for pair in final.cooc:
        both = sentences_with[pair.a] & sentences_with[pair.b]
        assert pair.count == len(both) >= 2
        expected = math.log2(len(both) * n / (len(sentences_with[pair.a]) * len(sentences_with[pair.b])))
        assert pair.pmi == pytest.approx(expected, abs=1e-4)


def _sentences_containing(update: MiningUpdate, spans) -> set[int]:
    return {s.id for s in update.sentences for a, _ in spans if s.start <= a < s.end}
