"""Sample traces bundled in data/samples/ (one JSON file per trace)."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from medra.contracts import SampleInfo

# backend/medra/sources/samples.py -> repo root is three levels up.
_DEFAULT_DIR = Path(__file__).resolve().parents[3] / "data" / "samples"


def samples_dir() -> Path:
    return Path(os.environ.get("MEDRA_SAMPLES_DIR", _DEFAULT_DIR))


@dataclass(frozen=True)
class Trace:
    id: str
    title: str
    language: str
    prompt: str
    reasoning: str
    answer: str
    origin: str

    def info(self) -> SampleInfo:
        words = len(re.findall(r"\S+", self.reasoning))
        return SampleInfo(id=self.id, title=self.title, language=self.language, words=words, origin=self.origin)


def load_trace(sample: str) -> Trace:
    """Load by sample id (file stem in samples_dir) or by path to a JSON file."""
    path = Path(sample)
    if not path.suffix:
        if not re.fullmatch(r"[\w-]+", sample):
            raise ValueError(f"invalid sample id: {sample!r}")
        path = samples_dir() / f"{sample}.json"
    if not path.is_file():
        raise FileNotFoundError(f"sample not found: {sample}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Trace(
        id=data.get("id", path.stem),
        title=data["title"],
        language=data["language"],
        prompt=data.get("prompt", ""),
        reasoning=data["reasoning"],
        answer=data.get("answer", ""),
        origin=data.get("origin", ""),
    )


def list_samples() -> list[SampleInfo]:
    return [load_trace(str(p)).info() for p in sorted(samples_dir().glob("*.json"))]
