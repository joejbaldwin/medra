"""User study support (memoria 3.11, item 5): serve a trace as plain text and
store each participant's results.

    GET  /study/traces/{id}   prompt, reasoning and answer of a sample trace,
                              for the plain-text condition of the study page
    POST /study/results       one participant's results (JSON), saved as a file

The study page (frontend/estudio.html) runs the protocol and posts everything
at the end. Results go to MEDRA_STUDY_DIR (default: study_results/ at the repo
root, gitignored), one file per submission, never overwritten. Nothing personal
is collected: participants are identified only by a code such as P3.

Kept out of contracts.py on purpose: the study is an evaluation tool, not one
of the four layers, so it does not change the versioned data contracts.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from medra.sources import load_trace

router = APIRouter(prefix="/study", tags=["study"])

_REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_RESULT_BYTES = 200_000  # a full session is ~10 KB; anything far bigger is not ours
PARTICIPANT = re.compile(r"[A-Za-z0-9_-]{1,32}")


def results_dir() -> Path:
    return Path(os.environ.get("MEDRA_STUDY_DIR", _REPO_ROOT / "study_results"))


class StudyTrace(BaseModel):
    id: str
    title: str
    prompt: str
    reasoning: str
    answer: str


class Saved(BaseModel):
    saved: str


@router.get("/traces/{trace_id}")
def study_trace(trace_id: str) -> StudyTrace:
    try:
        t = load_trace(trace_id)
    except (ValueError, FileNotFoundError):
        raise HTTPException(status_code=404, detail="Traza no encontrada.") from None
    return StudyTrace(id=t.id, title=t.title, prompt=t.prompt, reasoning=t.reasoning, answer=t.answer)


@router.post("/results")
async def save_results(request: Request) -> Saved:
    body = await request.body()
    if len(body) > MAX_RESULT_BYTES:
        raise HTTPException(status_code=413, detail="Resultados demasiado grandes.")
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="El cuerpo no es JSON válido.") from None
    participant = data.get("participant") if isinstance(data, dict) else None
    if not isinstance(participant, str) or not PARTICIPANT.fullmatch(participant):
        raise HTTPException(status_code=422, detail="Falta un código de participante válido.")

    folder = results_dir()
    folder.mkdir(parents=True, exist_ok=True)
    data["received_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    path = folder / f"{stamp}-{participant}.json"
    # "x": never overwrite an earlier submission, even with the same code.
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return Saved(saved=path.name)
