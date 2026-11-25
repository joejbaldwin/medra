"""User study endpoints: plain-text traces and result storage."""

import json

from fastapi.testclient import TestClient

from medra.server import app
from medra.sources import load_trace

client = TestClient(app)


def test_study_trace_is_the_sample_text():
    res = client.get("/study/traces/en-log-pets")
    assert res.status_code == 200
    body = res.json()
    t = load_trace("en-log-pets")
    assert (body["prompt"], body["reasoning"], body["answer"]) == (t.prompt, t.reasoning, t.answer)


def test_study_traces_are_listed_for_replay():
    ids = {s["id"] for s in client.get("/datasets").json()}
    assert {"en-log-pets", "en-log-knights"} <= ids


def test_unknown_or_bad_trace_is_404():
    assert client.get("/study/traces/nope").status_code == 404
    assert client.get("/study/traces/..%2Fsecrets").status_code == 404


def test_results_are_saved_one_file_per_submission(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDRA_STUDY_DIR", str(tmp_path))
    payload = {"participant": "P1", "blocks": [{"condition": "medra", "tasks": [{"answer": "Let's verify"}]}]}
    first = client.post("/study/results", json=payload)
    second = client.post("/study/results", json=payload)
    assert first.status_code == 200 and second.status_code == 200
    files = sorted(tmp_path.glob("*.json"))
    assert len(files) == 2 and first.json()["saved"] != second.json()["saved"]
    saved = json.loads(files[0].read_text(encoding="utf-8"))
    assert saved["blocks"] == payload["blocks"] and "received_at" in saved


def test_results_need_a_valid_participant_code(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDRA_STUDY_DIR", str(tmp_path))
    assert client.post("/study/results", json={"blocks": []}).status_code == 422
    assert client.post("/study/results", json={"participant": "../x"}).status_code == 422
    assert client.post("/study/results", content=b"not json").status_code == 400
    assert not list(tmp_path.iterdir())


def test_oversized_results_are_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDRA_STUDY_DIR", str(tmp_path))
    res = client.post("/study/results", json={"participant": "P1", "pad": "x" * 250_000})
    assert res.status_code == 413
