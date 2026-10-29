"""Contracts v1 are frozen: the models must match the committed schema."""

import json
from pathlib import Path

from pydantic import TypeAdapter

from medra.contracts import SCHEMA_VERSION, ServerMessage, TextChunk, ViewUpdate
from medra.schema import contracts_schema

SNAPSHOT = Path(__file__).resolve().parents[2] / "docs" / "contracts" / "v1.schema.json"


def test_schema_matches_frozen_snapshot():
    committed = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert contracts_schema() == committed, (
        "The contracts changed. If this is intended, bump SCHEMA_VERSION, then run "
        "`python -m medra.schema ../docs/contracts/v1.schema.json` and `npm run gen:types`."
    )


def test_schema_version_is_v1():
    assert SCHEMA_VERSION.startswith("1.")


def test_server_messages_parse_by_type():
    adapter = TypeAdapter(ServerMessage)
    chunk = TextChunk(session_id="s", seq=0, channel="reasoning", text="Hola", t=0.0)
    msg = adapter.validate_json(json.dumps({"type": "text", "chunk": chunk.model_dump()}))
    assert msg.type == "text" and msg.chunk == chunk

    view = ViewUpdate(session_id="s", seq=0, t=0.0, kind="snapshot", committed_upto=0)
    msg = adapter.validate_python({"type": "view", "view": view.model_dump()})
    assert msg.view == view


def test_unknown_fields_are_rejected():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TextChunk(session_id="s", seq=0, channel="reasoning", text="x", t=0.0, colour="red")
