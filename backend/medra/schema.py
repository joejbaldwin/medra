"""Export the contracts as one JSON Schema document.

    python -m medra.schema ../docs/contracts/v1.schema.json

The frontend turns that file into TypeScript types (`npm run gen:types`).
Serialization mode is used because the dashboard receives fully-populated
messages: fields with defaults are always present on the wire.
"""

from __future__ import annotations

import json
import sys

from pydantic import BaseModel

from medra import contracts as c


class MedraContracts(BaseModel):
    """Not a message: a container so every contract lands in one schema."""

    text_chunk: c.TextChunk
    mining_update: c.MiningUpdate
    view_update: c.ViewUpdate
    server_message: c.ServerMessage
    session_config: c.SessionConfig
    session_created: c.SessionCreated
    sample_info: c.SampleInfo
    source_info: c.SourceInfo


def _drop_field_titles(model_schema: dict) -> None:
    # Pydantic titles every field ("Session Id"); TypeScript generators turn
    # each into a type alias. Model titles (interface names) are kept.
    for prop in model_schema.get("properties", {}).values():
        prop.pop("title", None)


def contracts_schema() -> dict:
    schema = MedraContracts.model_json_schema(mode="serialization")
    for model_schema in schema["$defs"].values():
        _drop_field_titles(model_schema)
    _drop_field_titles(schema)
    schema["properties"]["server_message"]["title"] = "ServerMessage"  # name the union
    schema["$comment"] = f"MeDRA contracts, schema_version {c.SCHEMA_VERSION}. Generated; do not edit."
    return schema


def render() -> str:
    return json.dumps(contracts_schema(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    # Optional output path; writing the file here (UTF-8, no BOM, LF) avoids
    # shell redirection differences between PowerShell and bash.
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as f:
            f.write(render())
    else:
        sys.stdout.write(render())


if __name__ == "__main__":
    main()
