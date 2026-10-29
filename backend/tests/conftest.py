import asyncio
from pathlib import Path

from medra.contracts import TextChunk
from medra.sources import ReplaySource, Trace, load_trace

SAMPLES = ["login-es", "odd-sum-en"]
FIXTURES = Path(__file__).parent / "fixtures"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _collect(source: ReplaySource) -> list[TextChunk]:
    async def collect() -> list[TextChunk]:
        return [chunk async for chunk in source.stream()]

    return asyncio.run(collect())


def replay_chunks(sample: str, chunking: str = "word", seed: int = 0) -> list[TextChunk]:
    """All chunks of a sample, unpaced."""
    return _collect(ReplaySource(load_trace(sample), "test", words_per_second=0, chunking=chunking, seed=seed))


def text_chunks(text: str, chunking: str = "random", seed: int = 0) -> list[TextChunk]:
    """Chunks of an arbitrary reasoning text (no answer channel)."""
    trace = Trace(id="t", title="t", language="", prompt="", reasoning=text, answer="", origin="test")
    return _collect(ReplaySource(trace, "test", words_per_second=0, chunking=chunking, seed=seed))
