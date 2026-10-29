"""End to end: one trace streams through all four layers' contracts."""

import json

from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from medra.contracts import ServerMessage
from medra.server import app
from medra.sources import load_trace

client = TestClient(app)
messages_adapter = TypeAdapter(ServerMessage)


def stream(sample: str) -> list:
    created = client.post("/sessions", json={"sample": sample, "words_per_second": 0, "chunking": "random"})
    assert created.status_code == 200
    session_id = created.json()["session_id"]
    out = []
    with client.websocket_connect(f"/sessions/{session_id}") as ws:
        while True:
            msg = messages_adapter.validate_json(ws.receive_text())
            out.append(msg)
            if msg.type in ("end", "error"):
                return out


def test_datasets_lists_samples():
    ids = {s["id"] for s in client.get("/datasets").json()}
    assert {"login-es", "odd-sum-en"} <= ids


def test_trace_streams_through_all_layers():
    messages = stream("login-es")
    assert messages[0].type == "hello" and messages[-1].type == "end"
    text = "".join(m.chunk.text for m in messages if m.type == "text" and m.chunk.channel == "reasoning")
    assert text == load_trace("login-es").reasoning
    views = [m.view for m in messages if m.type == "view"]
    assert views[0].kind == "snapshot" and views[-1].final
    assert views[-1].committed_upto == len(text)
    assert any(node.id == "login" for v in views for node in v.nodes)


def test_unknown_sample_is_404():
    assert client.post("/sessions", json={"sample": "nope"}).status_code == 404


def test_session_can_only_be_used_once():
    session_id = client.post("/sessions", json={"sample": "login-es", "words_per_second": 0}).json()["session_id"]
    with client.websocket_connect(f"/sessions/{session_id}") as ws:
        while json.loads(ws.receive_text())["type"] != "end":
            pass
    with client.websocket_connect(f"/sessions/{session_id}") as ws:
        assert json.loads(ws.receive_text())["type"] == "error"
