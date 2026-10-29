import asyncio

from medra.contracts import TextChunk
from medra.sources import ReplaySource, load_trace

SAMPLES = ["login-es", "odd-sum-en"]


def replay_chunks(sample: str, chunking: str = "word", seed: int = 0) -> list[TextChunk]:
    """All chunks of a sample, unpaced."""
    source = ReplaySource(load_trace(sample), "test", words_per_second=0, chunking=chunking, seed=seed)

    async def collect() -> list[TextChunk]:
        return [chunk async for chunk in source.stream()]

    return asyncio.run(collect())
