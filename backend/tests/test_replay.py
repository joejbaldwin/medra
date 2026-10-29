import pytest

from conftest import SAMPLES, replay_chunks
from medra.sources import load_trace


@pytest.mark.parametrize("sample", SAMPLES)
@pytest.mark.parametrize("chunking,seed", [("word", 0), ("random", 0), ("random", 1), ("random", 42)])
def test_chunks_reassemble_the_trace(sample, chunking, seed):
    trace = load_trace(sample)
    chunks = replay_chunks(sample, chunking, seed)
    assert "".join(c.text for c in chunks if c.channel == "reasoning") == trace.reasoning
    assert "".join(c.text for c in chunks if c.channel == "answer") == trace.answer
    assert [c.seq for c in chunks] == list(range(len(chunks)))
    assert all(a.t <= b.t for a, b in zip(chunks, chunks[1:]))
    # Exactly one final chunk per channel, and it is that channel's last one.
    for channel in ("reasoning", "answer"):
        flags = [c.final for c in chunks if c.channel == channel]
        assert flags[-1] and sum(flags) == 1


def test_random_chunking_is_seeded():
    a = [c.text for c in replay_chunks("login-es", "random", 7)]
    b = [c.text for c in replay_chunks("login-es", "random", 7)]
    c = [c.text for c in replay_chunks("login-es", "random", 8)]
    assert a == b and a != c


def test_random_chunking_splits_words():
    chunks = replay_chunks("login-es", "random", 0)
    assert any(c.text[-1:].isalpha() and n.text[:1].isalpha() for c, n in zip(chunks, chunks[1:]))


def test_unknown_sample():
    with pytest.raises(FileNotFoundError):
        load_trace("does-not-exist")
    with pytest.raises(ValueError):
        load_trace("../secrets")
