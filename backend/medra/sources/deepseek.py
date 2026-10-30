"""Live source: DeepSeek's API with thinking mode.

The API is OpenAI-compatible (POST {base}/chat/completions, server-sent
events). In thinking mode each streamed delta carries either
`reasoning_content` (the chain of thought, which comes first) or `content`
(the final answer). They map to the "reasoning" and "answer" channels; the
reasoning channel is closed as soon as the answer starts, so the miner
analyses the last sentence of the reasoning without waiting for the answer.

Checked against api-docs.deepseek.com on 2026-10-30: models deepseek-flash
and deepseek-v4-pro, thinking enabled by default, `thinking` and
`reasoning_effort` parameters, `stream_options.include_usage`.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

from medra.contracts import TextChunk
from medra.sources.live import Emitter, SourceError

log = logging.getLogger("medra.deepseek")

_STATUS_ES = {
    400: "la petición no es válida",
    401: "la clave de la API no es válida",
    402: "no queda saldo en la cuenta de la API",
    422: "parámetros no válidos",
    429: "demasiadas peticiones; prueba en un momento",
    500: "error del servidor de DeepSeek",
    503: "DeepSeek está saturado; prueba en un momento",
}


class DeepSeekSource:
    name = "deepseek"

    def __init__(
        self,
        prompt: str,
        session_id: str,
        *,
        api_key: str,
        model: str,
        base_url: str,
        max_tokens: int,
        transport: httpx.AsyncBaseTransport | None = None,  # tests pass a mock
    ) -> None:
        self.prompt = prompt
        self.title = f"DeepSeek ({model}, en directo)"
        self.session_id = session_id
        self._api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.transport = transport
        self.usage: dict | None = None  # token counts reported at the end (for budgets, step 6)
        self.finish_reason: str | None = None

    async def stream(self) -> AsyncIterator[TextChunk]:
        emit = Emitter(self.session_id)
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": self.prompt}],
            "stream": True,
            "stream_options": {"include_usage": True},
            "thinking": {"type": "enabled"},
            "max_tokens": self.max_tokens,
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        timeout = httpx.Timeout(30.0, read=120.0)  # reasoning can pause between deltas
        try:
            async with httpx.AsyncClient(base_url=self.base_url, transport=self.transport, timeout=timeout) as client:
                async with client.stream("POST", "/chat/completions", json=body, headers=headers) as resp:
                    if resp.status_code != 200:
                        # The response body is not passed on: an auth error can echo part of the key.
                        log.warning("DeepSeek returned HTTP %s", resp.status_code)
                        reason = _STATUS_ES.get(resp.status_code, f"error HTTP {resp.status_code}")
                        raise SourceError(f"DeepSeek: {reason}.")
                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue  # blank separators and ": keep-alive" comments
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        event = json.loads(data)
                        if event.get("usage"):
                            self.usage = event["usage"]
                        for choice in event.get("choices") or []:
                            delta = choice.get("delta") or {}
                            if delta.get("reasoning_content"):
                                yield emit.chunk("reasoning", delta["reasoning_content"])
                            if delta.get("content"):
                                if closing := emit.close("reasoning"):
                                    yield closing
                                yield emit.chunk("answer", delta["content"])
                            if choice.get("finish_reason"):
                                self.finish_reason = choice["finish_reason"]
        except httpx.HTTPError as exc:
            log.warning("DeepSeek request failed: %s", type(exc).__name__)
            raise SourceError("No se pudo conectar con DeepSeek.") from exc
        for channel in ("reasoning", "answer"):
            if closing := emit.close(channel):
                yield closing
        log.info("DeepSeek session %s: finish=%s usage=%s", self.session_id, self.finish_reason, self.usage)
