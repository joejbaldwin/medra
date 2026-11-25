"""Shared helpers for the evaluation: load the traces and run MeDRA on them.

Each trace is mined once, through the same TextMiner the server uses, fed as
a single final chunk (the streamed result equals the batch one; tested in
backend/tests/test_miner.py). Everything the metrics need is kept: the
sentence spans and features (so segmentation can be re-run with other
parameters in milliseconds), the final MiningUpdate and the presenter's view.
"""

from __future__ import annotations

import bisect
import random
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from medra.contracts import MiningUpdate, TextChunk, ViewUpdate
from medra.mining.language import load_nlp
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


def source_of(trace_id: str) -> str:
    """Which model wrote the trace: recorded DeepSeek (en-*) or OpenThoughts R1 (ot-*)."""
    return "openthoughts" if trace_id.startswith("ot-") else "deepseek"


SPLIT_SEED = 0
TEST_SHARE = 0.375  # 6 of 16 traces


def split(ids: list[str], seed: int = SPLIT_SEED, test_share: float = TEST_SHARE) -> tuple[list[str], list[str]]:
    """Fixed dev/test split, stratified by source model so both sides have
    DeepSeek and OpenThoughts traces. Depends only on the ids and the seed."""
    rng = random.Random(seed)
    dev, test = [], []
    for source in ("deepseek", "openthoughts"):
        group = sorted(i for i in ids if source_of(i) == source)
        rng.shuffle(group)
        n_test = round(len(group) * test_share)
        test += group[:n_test]
        dev += group[n_test:]
    return sorted(dev), sorted(test)


def lemma_key(phrase: str, lang: str = "en") -> str:
    """An annotated term in the form of MeDRA's term ids: lowercased lemmas
    joined by spaces ("Dog owners" -> "dog owner"), via the same spaCy model."""
    doc = _nlp(lang)(phrase.strip())
    return " ".join(t.lemma_.lower() for t in doc if not t.is_punct)


@lru_cache(maxsize=None)
def _nlp(lang: str):
    return load_nlp(lang)


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

    def starts(self) -> list[int]:
        """Sentence indexes where MeDRA's segments start (the live result)."""
        return [i for i, s in enumerate(self.update.sentences) if i == 0 or s.segment_id != self.update.sentences[i - 1].segment_id]

    def sentence_terms(self) -> list[list[str]]:
        """Reported terms mentioned in each sentence (the input to topics.communities)."""
        firsts = [a for a, _ in self.spans]
        out: list[set[str]] = [set() for _ in self.spans]
        for term in self.update.terms:
            for a, _ in term.spans:
                out[bisect.bisect_right(firsts, a) - 1].add(term.id)
        return [sorted(s) for s in out]


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


def git_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                             check=True).stdout.strip()
        # Code and data only: eval/results/ and the trained step-type model
        # (written by eval.steptypes) are the scripts' own outputs.
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "backend", "eval", ":!eval/results",
                                ":!backend/medra/mining/models"],
                               capture_output=True, text=True).stdout.strip()
        return sha + (" (+ cambios sin commit)" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "desconocido"
