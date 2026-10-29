"""FastAPI backend: create a session over REST, stream it over a WebSocket.

    uvicorn medra.server:app --reload      (or: medra-serve)

Access codes, budgets and live sources arrive in later steps.
"""

from __future__ import annotations

import secrets
from collections import OrderedDict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from medra.contracts import ErrorMessage, SampleInfo, SessionConfig, SessionCreated
from medra.mining import TextMiner
from medra.mining.language import LANGUAGES, load_nlp
from medra.pipeline import run_pipeline
from medra.present import StubPresenter
from medra.sources import ReplaySource, list_samples, load_trace


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Load the spaCy models once at startup (about a second each) instead of
    # stalling the first session that needs them.
    for lang in LANGUAGES:
        load_nlp(lang)
    yield


app = FastAPI(title="MeDRA", lifespan=lifespan)

# Sessions created but not yet connected. Bounded so abandoned ones don't pile up.
MAX_PENDING = 100
pending: OrderedDict[str, SessionConfig] = OrderedDict()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/datasets")
def datasets() -> list[SampleInfo]:
    return list_samples()


@app.post("/sessions")
def create_session(config: SessionConfig) -> SessionCreated:
    try:
        load_trace(config.sample)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    session_id = secrets.token_urlsafe(9)
    pending[session_id] = config
    while len(pending) > MAX_PENDING:
        pending.popitem(last=False)
    return SessionCreated(session_id=session_id)


@app.websocket("/sessions/{session_id}")
async def stream_session(ws: WebSocket, session_id: str) -> None:
    await ws.accept()
    config = pending.pop(session_id, None)
    if config is None:
        await ws.send_text(ErrorMessage(message="unknown or already used session").model_dump_json())
        await ws.close(code=4404)
        return
    source = ReplaySource(
        load_trace(config.sample),
        session_id,
        words_per_second=config.words_per_second,
        chunking=config.chunking,
        seed=config.seed,
    )
    try:
        async for message in run_pipeline(session_id, source, TextMiner(session_id), StubPresenter()):
            await ws.send_text(message.model_dump_json())
        await ws.close()
    except WebSocketDisconnect:
        pass  # the dashboard closed the tab or started another session
