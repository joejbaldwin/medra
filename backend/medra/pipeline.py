"""Wire the layers together: source -> miner -> presenter -> messages.

Everything runs in one asyncio task. Raw text is yielded the moment it
arrives (so the dashboard feels live); the view update for it follows once
the miner commits a sentence.

Views are throttled to at most one per MIN_VIEW_INTERVAL seconds. Because a
MiningUpdate is a complete snapshot, skipping one loses nothing except its
token decisions (for the ticker), which are carried over into the next.
"""

from __future__ import annotations

import time
from typing import AsyncIterator

from medra.contracts import (
    EndMessage,
    HelloMessage,
    MiningUpdate,
    ServerMessage,
    TextMessage,
    ViewMessage,
)
from medra.mining import Miner
from medra.present import Presenter
from medra.sources import Source

MIN_VIEW_INTERVAL = 0.2  # seconds: at most 5 view updates per second
RECENT_TOKENS_KEPT = 20


async def run_pipeline(
    session_id: str,
    source: Source,
    miner: Miner,
    presenter: Presenter,
    min_interval: float = MIN_VIEW_INTERVAL,
) -> AsyncIterator[ServerMessage]:
    yield HelloMessage(session_id=session_id, source=source.name, title=source.title, prompt=source.prompt)
    pending: MiningUpdate | None = None
    last_view = float("-inf")
    async for chunk in source.stream():
        yield TextMessage(chunk=chunk)
        mining = miner.feed(chunk)
        if mining is not None:
            if pending is not None:
                tokens = (pending.recent_tokens + mining.recent_tokens)[-RECENT_TOKENS_KEPT:]
                mining = mining.model_copy(update={"recent_tokens": tokens})
            pending = mining
        now = time.monotonic()
        if pending is not None and (pending.final or now - last_view >= min_interval):
            view = presenter.present(pending)
            pending = None
            last_view = now
            if view is not None:
                yield ViewMessage(view=view)
    if pending is not None:
        view = presenter.present(pending)
        if view is not None:
            yield ViewMessage(view=view)
    yield EndMessage()
