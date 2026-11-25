"""Step 5: pasted text and the DeepSeek source.

The live source runs against a mocked HTTP server (httpx.MockTransport), so
the tests spend no API credit.
"""

import asyncio
import json
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError

import medra.server as server
from medra.contracts import ServerMessage, SessionConfig, TextChunk
from medra.mining import TextMiner
from medra.settings import Settings
from medra.sources import DeepSeekSource, PasteSource, SourceError
from medra.sources.think import ThinkSplitter, split_think

KEY = "sk-test-not-a-real-key-123456"


def collect(source) -> list[TextChunk]:
    async def run():
        return [c async for c in source.stream()]

    return asyncio.run(run())


def joined(chunks: list[TextChunk], channel: str) -> str:
    return "".join(c.text for c in chunks if c.channel == channel)


def check_channels_close_once(chunks: list[TextChunk]) -> None:
    for channel in ("reasoning", "answer"):
        finals = [i for i, c in enumerate(chunks) if c.channel == channel and c.final]
        assert len(finals) == 1, channel
        assert all(c.channel != channel for c in chunks[finals[0] + 1 :]), f"{channel} after its final chunk"
    assert [c.seq for c in chunks] == list(range(len(chunks)))


# ---------------------------------------------------------------- <think> splitting


@pytest.mark.parametrize("size", [1, 2, 3, 5, 100])
def test_think_tags_split_across_chunks(size):
    text = "<think>Let me see. 2+2 is 4.</think>\n\nThe answer is 4."
    splitter = ThinkSplitter()
    parts = []
    for i in range(0, len(text), size):
        parts += splitter.feed(text[i : i + size])
    parts += splitter.flush()
    assert "".join(t for c, t in parts if c == "reasoning") == "Let me see. 2+2 is 4."
    assert "".join(t for c, t in parts if c == "answer") == "The answer is 4."


def test_missing_opening_tag_and_no_tags():
    assert split_think("Hmm, so x = 3.</think>x = 3") == ("Hmm, so x = 3.", "x = 3")
    assert split_think("Just reasoning, no tags. a < b and c > d.") == ("Just reasoning, no tags. a < b and c > d.", "")


def test_pasted_text_replays_reasoning_and_answer():
    chunks = collect(PasteSource("<think>First, the sum. Wait, check it.</think>\nIt is 9.", "p", words_per_second=0))
    assert joined(chunks, "reasoning") == "First, the sum. Wait, check it."
    assert joined(chunks, "answer") == "It is 9."
    check_channels_close_once(chunks)


def test_session_config_needs_the_right_input():
    SessionConfig(source="paste", text="Some reasoning.")
    for bad in [{"source": "paste"}, {"source": "paste", "text": "  "}, {"source": "deepseek"}, {"source": "replay"}]:
        with pytest.raises(ValidationError):
            SessionConfig(**bad)
    with pytest.raises(ValidationError):
        SessionConfig(source="deepseek", prompt="x" * 5000)


# ---------------------------------------------------------------- DeepSeek


def sse(*events: dict) -> bytes:
    return b"".join(f"data: {json.dumps(e)}\n\n".encode() for e in events) + b"data: [DONE]\n\n"


def delta(**d) -> dict:
    return {"choices": [{"index": 0, "delta": d, "finish_reason": None}]}


DEEPSEEK_STREAM = sse(
    delta(role="assistant", reasoning_content=""),
    delta(reasoning_content="The user asks 2+2. "),
    delta(reasoning_content="Wait, let me check: 4."),
    delta(content="The answer"),
    delta(content=" is 4."),
    {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
     "usage": {"prompt_tokens": 9, "completion_tokens": 20, "completion_tokens_details": {"reasoning_tokens": 12}}},
)


def deepseek(handler) -> DeepSeekSource:
    return DeepSeekSource("What is 2+2?", "d", api_key=KEY, model="deepseek-flash", base_url="https://api.test",
                          max_tokens=1000, transport=httpx.MockTransport(handler))


def test_deepseek_stream_maps_reasoning_and_answer_to_channels():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, content=DEEPSEEK_STREAM, headers={"content-type": "text/event-stream"})

    source = deepseek(handler)
    chunks = collect(source)
    assert joined(chunks, "reasoning") == "The user asks 2+2. Wait, let me check: 4."
    assert joined(chunks, "answer") == "The answer is 4."
    check_channels_close_once(chunks)
    # The reasoning is closed before the first answer chunk, so the miner can finish it right away.
    first_answer = next(i for i, c in enumerate(chunks) if c.channel == "answer")
    assert chunks[first_answer - 1].channel == "reasoning" and chunks[first_answer - 1].final
    assert seen["url"] == "https://api.test/chat/completions" and seen["auth"] == f"Bearer {KEY}"
    body = seen["body"]
    assert body["model"] == "deepseek-flash" and body["stream"] is True and body["max_tokens"] == 1000
    assert body["thinking"] == {"type": "enabled"} and body["stream_options"] == {"include_usage": True}
    assert source.usage["completion_tokens"] == 20 and source.finish_reason == "stop"


def test_deepseek_stream_is_mined_like_any_other_source():
    chunks = collect(deepseek(lambda r: httpx.Response(200, content=DEEPSEEK_STREAM)))
    miner = TextMiner("d")
    final = [u for u in (miner.feed(c) for c in chunks) if u][-1]
    assert final.final and final.committed_upto == len(joined(chunks, "reasoning"))
    assert [m.type for m in final.markers] == ["verification"]


@pytest.mark.parametrize("status", [401, 402, 429, 500])
def test_deepseek_errors_never_leak_the_key(status):
    body = {"error": {"message": f"Authentication Fails, Your api key: {KEY} is invalid"}}
    with pytest.raises(SourceError) as err:
        collect(deepseek(lambda r: httpx.Response(status, json=body)))
    assert KEY not in str(err.value) and "DeepSeek" in str(err.value)


def test_deepseek_connection_failure_is_a_source_error():
    def handler(request):
        raise httpx.ConnectError("no route")

    with pytest.raises(SourceError, match="No se pudo conectar"):
        collect(deepseek(handler))


# ---------------------------------------------------------------- server


client = TestClient(server.app)
messages_adapter = TypeAdapter(ServerMessage)
BASE = Settings(deepseek_api_key=None, deepseek_model="deepseek-flash", deepseek_url="https://api.test",
                max_tokens=1000, live_disabled=False)


def use_settings(monkeypatch, **kw) -> None:
    monkeypatch.setattr(server, "get_settings", lambda: replace(BASE, **kw))


def run_session(config: dict) -> list:
    created = client.post("/sessions", json=config)
    assert created.status_code == 200, created.text
    out = []
    with client.websocket_connect(f"/sessions/{created.json()['session_id']}") as ws:
        while True:
            msg = messages_adapter.validate_json(ws.receive_text())
            out.append(msg)
            if msg.type in ("end", "error"):
                return out


def test_paste_session_streams_through_all_layers():
    text = "<think>First, the fields. The email must be valid.\n\nWait, the password needs a hash.</think>Use a hash."
    messages = run_session({"source": "paste", "text": text, "words_per_second": 0})
    assert messages[-1].type == "end"
    reasoning = "".join(m.chunk.text for m in messages if m.type == "text" and m.chunk.channel == "reasoning")
    assert reasoning == split_think(text)[0]
    views = [m.view for m in messages if m.type == "view"]
    assert views[-1].final and views[-1].committed_upto == len(reasoning)


def test_sources_reports_what_is_available(monkeypatch):
    use_settings(monkeypatch)
    by_id = {s["id"]: s for s in client.get("/sources").json()}
    assert by_id["replay"]["available"] and by_id["paste"]["available"]
    assert not by_id["deepseek"]["available"] and "clave" in by_id["deepseek"]["note"]
    assert set(by_id) == {"replay", "paste", "deepseek"}
    use_settings(monkeypatch, deepseek_api_key=KEY)
    deepseek_info = next(s for s in client.get("/sources").json() if s["id"] == "deepseek")
    assert deepseek_info["available"] and KEY not in json.dumps(deepseek_info)
    assert deepseek_info["label"] == server.model_label(BASE.deepseek_model)


def test_model_label_names_the_model():
    assert server.model_label("deepseek-flash") == "DeepSeek Flash"
    assert server.model_label("deepseek-v4-pro") == "DeepSeek V4 Pro"


def test_live_sessions_need_a_key_and_respect_the_kill_switch(monkeypatch):
    use_settings(monkeypatch)
    assert client.post("/sessions", json={"source": "deepseek", "prompt": "hi"}).status_code == 503
    use_settings(monkeypatch, deepseek_api_key=KEY, live_disabled=True)
    assert client.post("/sessions", json={"source": "deepseek", "prompt": "hi"}).status_code == 503
    assert client.post("/sessions", json={"source": "ollama", "prompt": "hi"}).status_code == 422  # removed
    # Replay and paste keep working with the kill switch on.
    assert client.post("/sessions", json={"source": "paste", "text": "Some text."}).status_code == 200
    assert client.post("/sessions", json={"source": "paste"}).status_code == 422


def test_source_error_reaches_the_dashboard(monkeypatch):
    use_settings(monkeypatch, deepseek_api_key=KEY)
    failing = deepseek(lambda r: httpx.Response(401, json={"error": {"message": KEY}}))
    monkeypatch.setattr(server, "make_source", lambda config, session_id: failing)
    messages = run_session({"source": "deepseek", "prompt": "hi"})
    assert messages[-1].type == "error" and "clave" in messages[-1].message and KEY not in messages[-1].message
