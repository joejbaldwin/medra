"""Wire the layers together: source -> miner -> presenter -> messages.

Everything runs in one asyncio task. Raw text is yielded the moment it
arrives (so the dashboard feels live); the view update for it follows once
the miner commits a sentence.
"""

from __future__ import annotations

from typing import AsyncIterator

from medra.contracts import EndMessage, HelloMessage, ServerMessage, TextMessage, ViewMessage
from medra.mining import Miner
from medra.present import Presenter
from medra.sources import Source


async def run_pipeline(
    session_id: str, source: Source, miner: Miner, presenter: Presenter
) -> AsyncIterator[ServerMessage]:
    yield HelloMessage(session_id=session_id, source=source.name, title=source.title, prompt=source.prompt)
    async for chunk in source.stream():
        yield TextMessage(chunk=chunk)
        mining = miner.feed(chunk)
        if mining is None:
            continue
        view = presenter.present(mining)
        if view is not None:
            yield ViewMessage(view=view)
    yield EndMessage()
