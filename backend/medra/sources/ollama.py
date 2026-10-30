"""Live source: a local model served by Ollama (no API credit needed).

POST {url}/api/chat with stream=true returns one JSON object per line. With
"think": true, recent Ollama versions put the reasoning in
`message.thinking` and the answer in `message.content`. Older versions (or
models without thinking support) inline it as <think>...</think> in
`content`, which ThinkSplitter separates.

Not tried against a real Ollama install (none on the build machine); the
tests use a mocked server with both response styles.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from medra.contracts import TextChunk
from medra.sources.live import Emitter, SourceError
from medra.sources.think import ThinkSplitter


class OllamaSource:
    name = "ollama"

    def __init__(
        self,
        prompt: str,
        session_id: str,
        *,
        base_url: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.prompt = prompt
        self.title = f"Ollama ({model}, local)"
        self.session_id = session_id
        self.base_url = base_url
        self.model = model
        self.transport = transport

    async def stream(self) -> AsyncIterator[TextChunk]:
        emit = Emitter(self.session_id)
        splitter = ThinkSplitter()
        separate_thinking = False  # the server sends message.thinking: content is all answer
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": self.prompt}],
            "stream": True,
            "think": True,
        }
        try:
            async with httpx.AsyncClient(base_url=self.base_url, transport=self.transport, timeout=httpx.Timeout(10.0, read=300.0)) as client:
                async with client.stream("POST", "/api/chat", json=body) as resp:
                    if resp.status_code == 404:
                        raise SourceError(f"Ollama no tiene el modelo «{self.model}» (ollama pull {self.model}).")
                    if resp.status_code != 200:
                        raise SourceError(f"Ollama: error HTTP {resp.status_code}.")
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        event = json.loads(line)
                        message = event.get("message") or {}
                        if message.get("thinking"):
                            separate_thinking = True
                            yield emit.chunk("reasoning", message["thinking"])
                        content = message.get("content") or ""
                        if content:
                            parts = [("answer", content)] if separate_thinking else splitter.feed(content)
                            for channel, text in parts:
                                if channel == "answer" and (closing := emit.close("reasoning")):
                                    yield closing
                                yield emit.chunk(channel, text)
                        if event.get("done"):
                            break
        except httpx.HTTPError as exc:
            raise SourceError(f"No se pudo conectar con Ollama en {self.base_url}.") from exc
        for channel, text in splitter.flush():
            yield emit.chunk(channel, text)
        for channel in ("reasoning", "answer"):
            if closing := emit.close(channel):
                yield closing
