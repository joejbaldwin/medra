import pytest

from conftest import SAMPLES, replay_chunks
from medra.contracts import MiningUpdate, TextChunk
from medra.mining import StubMiner
from medra.sources import load_trace


def mine(chunks: list[TextChunk]) -> list[MiningUpdate]:
    miner = StubMiner("test")
    return [u for u in (miner.feed(c) for c in chunks) if u is not None]


def chunk(text: str, seq: int, final: bool = False) -> TextChunk:
    return TextChunk(session_id="test", seq=seq, channel="reasoning", text=text, t=float(seq), final=final)


@pytest.mark.parametrize("sample", SAMPLES)
def test_every_span_points_at_its_term(sample):
    text = load_trace(sample).reasoning
    for update in mine(replay_chunks(sample, "random", 3)):
        for term in update.terms:
            for start, end in term.spans:
                assert end <= update.committed_upto
                assert text[start:end] in term.surface_forms
                assert text[start:end].lower() == term.id
        for s in update.sentences:
            assert text[s.start : s.end] == text[s.start : s.end].strip() != ""


@pytest.mark.parametrize("sample", SAMPLES)
@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_final_state_does_not_depend_on_chunking(sample, seed):
    trace = load_trace(sample)
    batch = mine([chunk(trace.reasoning, 0, final=True)])[-1]
    streamed = mine(replay_chunks(sample, "random", seed))[-1]
    by_word = mine(replay_chunks(sample, "word"))[-1]
    for update in (streamed, by_word):
        assert update.terms == batch.terms
        assert update.sentences == batch.sentences
        assert update.stats == batch.stats
        assert update.committed_upto == len(trace.reasoning)


def test_pending_tail_is_not_mined():
    updates = mine([chunk("Hola mundo. Esto sig", 0), chunk("ue sin acabar", 1)])
    assert len(updates) == 1
    assert updates[0].committed_upto == len("Hola mundo.")
    assert [t.id for t in updates[0].terms] == ["hola", "mundo"]


def test_decimal_point_does_not_commit():
    # "3." could still become "3.14": nothing is committed until whitespace follows.
    assert mine([chunk("El valor es 3.", 0)]) == []
    updates = mine([chunk("El valor es 3.", 0), chunk("14 aprox. ", 1)])
    assert updates[-1].committed_upto == len("El valor es 3.14 aprox.")


def test_hand_counted_terms():
    final = mine(replay_chunks("login-es"))[-1]
    counts = {t.id: t.count for t in final.terms}
    # Counted by hand in data/samples/login-es.json.
    assert counts["login"] == 5
    assert counts["sesión"] == 4
    assert counts["contraseña"] == 3
    assert counts["email"] == 3
    assert final.language == "es"
    assert mine(replay_chunks("odd-sum-en"))[-1].language == "en"


def test_answer_channel_is_ignored():
    miner = StubMiner("test")
    answer = TextChunk(session_id="test", seq=0, channel="answer", text="Respuesta final. ", t=0.0)
    assert miner.feed(answer) is None
    assert miner.text == ""
