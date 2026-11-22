"""FastAPI backend: create a session over REST, stream it over a WebSocket.

    uvicorn medra.server:app --reload      (or: medra-serve)

Sources: replay (sample traces), paste (text from the dashboard), deepseek
(live, uses the group's API credit) and ollama (local model). Live sessions
can be switched off with MEDRA_LIVE_DISABLED=1, and only one DeepSeek session
runs at a time. When MEDRA_ACCESS_CODES is set (the deployed Space), a
DeepSeek session also needs an access code with budget left (access.py),
sent in the X-Access-Code header of POST /sessions. The WebSocket needs no
code: its session id is a one-time secret that only an accepted POST returns.
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from collections import OrderedDict
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from medra.access import AccessCodes, AccessDenied

from medra.contracts import ErrorMessage, SampleInfo, SessionConfig, SessionCreated, SourceInfo
from medra.mining import TextMiner
from medra.mining.language import LANGUAGES, load_nlp
from medra.pipeline import run_pipeline
from medra.present import ViewPresenter
from medra.settings import Settings, get_settings
from medra.sources import (
    DeepSeekSource,
    OllamaSource,
    PasteSource,
    ReplaySource,
    Source,
    SourceError,
    list_samples,
    load_trace,
)

log = logging.getLogger("medra.server")
LIVE_NOTE = "Las preguntas se envían a la API de DeepSeek: no escribas datos personales ni sensibles."


def model_label(model: str) -> str:
    """The configured model as the dashboard names it: "deepseek-flash" -> "DeepSeek Flash"."""
    words = [w for w in model.replace("_", "-").split("-") if w]
    return " ".join("DeepSeek" if w.lower() == "deepseek" else w[:1].upper() + w[1:] for w in words) or model


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Load the spaCy models once at startup (about a second each) instead of
    # stalling the first session that needs them.
    for lang in LANGUAGES:
        load_nlp(lang)
    yield


app = FastAPI(title="MeDRA", lifespan=lifespan)
# The dashboard on GitHub Pages is another origin. Only the listed origins may
# call the API from a browser; the access code header must be allowed too.
# (Settings are read once here: CORS is configured when the app is built.)
if get_settings().allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Access-Code"],
    )

# Sessions created but not yet connected. Bounded so abandoned ones don't pile up.
MAX_PENDING = 100
pending: OrderedDict[str, SessionConfig] = OrderedDict()
# One DeepSeek session at a time, so a stuck tab or a script cannot spend the credit in parallel.
deepseek_busy = asyncio.Lock()
_access: AccessCodes | None = None


def access_codes(s: Settings) -> AccessCodes:
    """The budget tracker for the configured codes (rebuilt only if the codes change)."""
    global _access
    if _access is None or _access.budgets != s.access_codes:
        _access = AccessCodes(s.access_codes)
    return _access


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/datasets")
def datasets() -> list[SampleInfo]:
    return list_samples()


@app.get("/sources")
async def sources() -> list[SourceInfo]:
    s = get_settings()
    off = "Desactivado por el administrador." if s.live_disabled else None
    return [
        SourceInfo(id="replay", label="Traza de ejemplo", available=True),
        SourceInfo(id="paste", label="Pegar texto", available=True),
        SourceInfo(
            id="deepseek",
            label=model_label(s.deepseek_model),
            available=bool(s.deepseek_api_key) and not s.live_disabled,
            note=off or (LIVE_NOTE if s.deepseek_api_key else "No hay clave de API configurada en el servidor."),
            needs_code=bool(s.access_codes),
        ),
        *([await _ollama_info(s, off)] if s.ollama_url else []),
    ]


async def _ollama_info(s: Settings, off: str | None) -> SourceInfo:
    up = not s.live_disabled and await _ollama_up(s.ollama_url)
    note = off or (f"Modelo {s.ollama_model}, en este equipo." if up else f"Ollama no responde en {s.ollama_url}.")
    return SourceInfo(id="ollama", label="Ollama (modelo local)", available=up, note=note)


async def _ollama_up(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=0.5) as client:
            return (await client.get(f"{url}/api/tags")).status_code == 200
    except httpx.HTTPError:
        return False


@app.post("/sessions")
def create_session(config: SessionConfig, x_access_code: str | None = Header(default=None)) -> SessionCreated:
    s = get_settings()
    if config.source == "replay":
        try:
            load_trace(config.sample or "")
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    if config.source in ("deepseek", "ollama") and s.live_disabled:
        raise HTTPException(status_code=503, detail="Las fuentes en directo están desactivadas.")
    if config.source == "deepseek" and not s.deepseek_api_key:
        raise HTTPException(status_code=503, detail="No hay clave de API de DeepSeek configurada.")
    if config.source == "ollama" and not s.ollama_url:
        raise HTTPException(status_code=503, detail="Ollama no está disponible en este servidor.")
    if config.source == "deepseek":
        try:
            access_codes(s).spend(x_access_code)  # last check, so a rejected request costs no budget
        except AccessDenied as exc:
            raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    session_id = secrets.token_urlsafe(9)
    pending[session_id] = config
    while len(pending) > MAX_PENDING:
        pending.popitem(last=False)
    return SessionCreated(session_id=session_id)


def make_source(config: SessionConfig, session_id: str) -> Source:
    s = get_settings()
    pace = {"words_per_second": config.words_per_second, "chunking": config.chunking, "seed": config.seed}
    if config.source == "replay":
        return ReplaySource(load_trace(config.sample or ""), session_id, **pace)
    if config.source == "paste":
        return PasteSource(config.text or "", session_id, **pace)
    if config.source == "deepseek":
        return DeepSeekSource(
            config.prompt or "", session_id, api_key=s.deepseek_api_key or "", model=s.deepseek_model,
            base_url=s.deepseek_url, max_tokens=s.max_tokens,
        )
    return OllamaSource(config.prompt or "", session_id, base_url=s.ollama_url, model=s.ollama_model)


@app.websocket("/sessions/{session_id}")
async def stream_session(ws: WebSocket, session_id: str) -> None:
    await ws.accept()
    config = pending.pop(session_id, None)
    if config is None:
        await ws.send_text(ErrorMessage(message="unknown or already used session").model_dump_json())
        await ws.close(code=4404)
        return
    if config.source == "deepseek" and deepseek_busy.locked():
        await ws.send_text(ErrorMessage(message="Ya hay una sesión con DeepSeek en curso; espera a que termine.").model_dump_json())
        await ws.close(code=4429)
        return
    source = make_source(config, session_id)
    try:
        if config.source == "deepseek":
            async with deepseek_busy:
                await _run(ws, session_id, source)
        else:
            await _run(ws, session_id, source)
        await ws.close()
    except WebSocketDisconnect:
        pass  # the dashboard closed the tab or started another session (the API request is cancelled too)
    except SourceError as exc:
        await ws.send_text(ErrorMessage(message=str(exc)).model_dump_json())
        await ws.close(code=4502)


async def _run(ws: WebSocket, session_id: str, source: Source) -> None:
    async for message in run_pipeline(session_id, source, TextMiner(session_id), ViewPresenter()):
        await ws.send_text(message.model_dump_json())
