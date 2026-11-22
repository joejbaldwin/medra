"""Shared helpers for the evaluation: load the traces and run MeDRA on them.

Each trace is mined once, through the same TextMiner the server uses, fed as
a single final chunk (the streamed result equals the batch one; tested in
backend/tests/test_miner.py). Everything the metrics need is kept: the
sentence spans and features (so segmentation can be re-run with other
parameters in milliseconds), the final MiningUpdate and the presenter's view.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from medra.contracts import MiningUpdate, TextChunk, ViewUpdate
from medra.mining.miner import TextMiner
from medra.mining.segment import SentenceFeatures
from medra.present import ViewPresenter
from medra.sources import Trace, load_trace

EVAL_DIR = Path(__file__).parent
TRACES_DIR = EVAL_DIR / "traces"
ANNOTATIONS_DIR = EVAL_DIR / "annotations"
RESULTS_DIR = EVAL_DIR / "results"


def trace_ids() -> list[str]:
    return sorted(p.stem for p in TRACES_DIR.glob("*.json"))


def get_trace(trace_id: str) -> Trace:
    return load_trace(str(TRACES_DIR / f"{trace_id}.json"))


@dataclass(frozen=True)
class Mined:
    trace: Trace
    spans: list[tuple[int, int]]  # sentence (start, end) offsets into trace.reasoning
    features: list[SentenceFeatures]
    update: MiningUpdate  # final snapshot
    view: ViewUpdate  # presenter's final view (bubbles, links, topics)

    @property
    def text(self) -> str:
        return self.trace.reasoning


@lru_cache(maxsize=None)
def mine(trace_id: str) -> Mined:
    trace = get_trace(trace_id)
    miner = TextMiner(trace_id)
    chunk = TextChunk(session_id=trace_id, seq=0, channel="reasoning", text=trace.reasoning, t=0.0, final=True)
    update = miner.feed(chunk)
    assert update is not None and update.final
    view = ViewPresenter().present(update)
    assert view is not None
    return Mined(
        trace=trace,
        spans=[(s.start, s.end) for s in miner.sentences],
        features=[s.features for s in miner.sentences],
        update=update,
        view=view,
    )
