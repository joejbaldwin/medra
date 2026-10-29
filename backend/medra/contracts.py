"""Data contracts between the four MeDRA layers (schema v1).

This module is the single source of truth for every message that crosses a
layer boundary:

    Layer 1 (source) --TextChunk--> Layer 2 (miner) --MiningUpdate-->
    Layer 3 (presenter) --ViewUpdate--> Layer 4 (dashboard, over a WebSocket)

The models are exported to JSON Schema (`python -m medra.schema`) and from
there to TypeScript types for the frontend. A snapshot of the schema is
committed in `docs/contracts/`, and `tests/test_contracts.py` fails if the
models drift from it: a change to a contract must bump SCHEMA_VERSION and
regenerate the snapshot on purpose.

Conventions:
- Every offset is an absolute character offset into the *reasoning* channel
  text (the concatenation of all reasoning chunks, as Python `str` indices,
  i.e. Unicode code points). A span is a half-open `(start, end)` pair, so
  `text[start:end]` is the surface form.
- Sentence, segment ids are ints (positional); term, node and edge ids are
  strings (a lemma or n-gram); topic ids are strings ("t0", "t1"...) so
  they can stay stable when clusters are recomputed.
- `t` is seconds since the session started (source time, not wall time), so
  a recorded session replays with its original rhythm.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"

Span = tuple[int, int]
"""Half-open character range [start, end) into the reasoning text."""

Channel = Literal["reasoning", "answer", "meta"]


class _Model(BaseModel):
    # Unknown fields are an error: a typo in a producer should fail loudly.
    # Fields with defaults are always present in serialized output, so the
    # exported schema marks them required (TypeScript can then rely on them).
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)


# ---------------------------------------------------------------------------
# Layer 1 -> Layer 2
# ---------------------------------------------------------------------------


class TextChunk(_Model):
    """A piece of streamed text. Boundaries are arbitrary (may split a word)."""

    schema_version: str = SCHEMA_VERSION
    session_id: str
    seq: int = Field(description="Strictly increasing within a session.")
    channel: Channel = Field(description="reasoning = chain-of-thought, answer = final answer.")
    text: str
    t: float = Field(description="Seconds since session start.")
    final: bool = Field(default=False, description="Last chunk of this channel.")


# ---------------------------------------------------------------------------
# Layer 2 -> Layer 3
# ---------------------------------------------------------------------------


class Sentence(_Model):
    id: int
    start: int
    end: int
    segment_id: int | None = None


class Segment(_Model):
    """A 'tramo': a run of sentences about one step of the reasoning."""

    id: int
    start: int
    end: int
    provisional: bool = Field(description="The boundary may still move; drawn dashed.")
    marker: str | None = Field(default=None, description="Discourse marker that opened it.")
    step_type: str | None = None
    boundary_score: float = 0.0


class Term(_Model):
    id: str = Field(description="Lemma or n-gram; the key used by every other field.")
    surface_forms: list[str]
    count: int
    df_segments: int = Field(description="Number of segments the term appears in.")
    spans: list[Span]
    first_seen: int = Field(description="Offset of the first mention.")


class TermWeight(_Model):
    term_id: str
    weight: float


class SegmentKeywords(_Model):
    segment_id: int
    terms: list[TermWeight] = Field(description="Top-k by TF-IDF, highest first.")


class Cooccurrence(_Model):
    a: str
    b: str
    count: int
    pmi: float


class Cluster(_Model):
    id: str
    label_terms: list[str]
    term_ids: list[str]


class Marker(_Model):
    type: str = Field(description="e.g. backtrack, alternative, verification, conclusion.")
    text: str
    span: Span


class Stats(_Model):
    words: int = 0
    sentences: int = 0
    segments: int = 0
    lexical_diversity: float | None = None
    hedges_per_100w: float | None = None
    extra: dict[str, float] = Field(default_factory=dict)


class MiningUpdate(_Model):
    """Full snapshot of the miner's state after a commit.

    Emitted each time at least one sentence is committed. It is a snapshot,
    not a diff: Layer 2 and 3 run in the same process, so this costs no
    network traffic, and it keeps the "incremental == batch" test simple.
    Diffing happens in Layer 3, before the network.
    """

    schema_version: str = SCHEMA_VERSION
    session_id: str
    seq: int
    t: float
    language: str | None = Field(default=None, description="ISO 639-1, e.g. 'en' or 'es'.")
    text_length: int = Field(description="Reasoning characters received so far.")
    committed_upto: int = Field(description="Characters analysed; text after this is pending.")
    final: bool = False
    sentences: list[Sentence] = Field(default_factory=list)
    segments: list[Segment] = Field(default_factory=list)
    terms: list[Term] = Field(default_factory=list)
    tfidf: list[SegmentKeywords] = Field(default_factory=list)
    cooc: list[Cooccurrence] = Field(default_factory=list)
    clusters: list[Cluster] = Field(default_factory=list)
    markers: list[Marker] = Field(default_factory=list)
    stats: Stats = Field(default_factory=Stats)


# ---------------------------------------------------------------------------
# Layer 3 -> Layer 4
# ---------------------------------------------------------------------------


class Node(_Model):
    """A bubble in the concept map. The browser runs the physics."""

    id: str
    label: str
    count: int
    radius: float
    topic_id: str | None = None
    colour_slot: int = Field(description="Index into the dashboard's categorical palette.")
    seed_xy: tuple[float, float] | None = Field(
        default=None, description="Starting position in a 0..1 box; the force layout moves it."
    )
    emphasis: float = Field(default=0.0, description="0..1, e.g. recently mentioned.")


class Edge(_Model):
    id: str
    a: str
    b: str
    width: float
    colour_slot: int


class Topic(_Model):
    id: str
    name: str
    colour_slot: int


class Paragraph(_Model):
    segment_id: int
    start: int
    end: int
    topic_id: str | None = None
    label: str
    provisional: bool = False


class Highlight(_Model):
    """Spans to underline when a node or topic is selected."""

    kind: Literal["node", "topic"]
    id: str
    spans: list[Span]


class TimelineSeries(_Model):
    topic_id: str
    points: list[tuple[float, float]]


class Timeline(_Model):
    x_axis: Literal["words"] = "words"
    x_max: float
    series: list[TimelineSeries]


class Step(_Model):
    segment_id: int
    step_type: str | None
    topic_id: str | None
    arcs_back_to: list[int] = Field(default_factory=list)


class TickerItem(_Model):
    """One entry of the 'pipeline working' strip: form -> lemma -> outcome."""

    form: str
    lemma: str
    outcome: str


class Removed(_Model):
    nodes: list[str] = Field(default_factory=list)
    edges: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    paragraphs: list[int] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list, description="'kind:id' keys.")
    steps: list[int] = Field(default_factory=list)


class ViewUpdate(_Model):
    """What the screen should show, as a diff against the previous update.

    The first update of a session has kind="snapshot". After that, each list
    holds only items that were added or changed (upsert by id), and `removed`
    lists ids to delete. `timeline` and `stats`, when present, replace the
    previous value whole. `ticker` items are appended.
    """

    schema_version: str = SCHEMA_VERSION
    session_id: str
    seq: int
    t: float
    kind: Literal["snapshot", "diff"]
    committed_upto: int
    final: bool = False
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    topics: list[Topic] = Field(default_factory=list)
    paragraphs: list[Paragraph] = Field(default_factory=list)
    highlights: list[Highlight] = Field(default_factory=list)
    timeline: Timeline | None = None
    steps: list[Step] = Field(default_factory=list)
    ticker: list[TickerItem] = Field(default_factory=list)
    stats: Stats | None = None
    removed: Removed = Field(default_factory=Removed)


# ---------------------------------------------------------------------------
# Backend -> dashboard (WebSocket messages; also the lines of frames.jsonl)
# ---------------------------------------------------------------------------


class HelloMessage(_Model):
    type: Literal["hello"] = "hello"
    schema_version: str = SCHEMA_VERSION
    session_id: str
    source: str
    title: str | None = None
    prompt: str | None = None
    language: str | None = None


class TextMessage(_Model):
    """Raw text, passed straight through so the stream feels live."""

    type: Literal["text"] = "text"
    chunk: TextChunk


class ViewMessage(_Model):
    type: Literal["view"] = "view"
    view: ViewUpdate


class MiningMessage(_Model):
    """Optional: the raw miner output, for a debug panel."""

    type: Literal["mining"] = "mining"
    mining: MiningUpdate


class EndMessage(_Model):
    type: Literal["end"] = "end"
    reason: Literal["completed", "cancelled", "error"] = "completed"


class ErrorMessage(_Model):
    type: Literal["error"] = "error"
    message: str


ServerMessage = Annotated[
    Union[HelloMessage, TextMessage, ViewMessage, MiningMessage, EndMessage, ErrorMessage],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------


class SessionConfig(_Model):
    """Body of POST /sessions. More sources are added in later schema versions."""

    source: Literal["replay"] = "replay"
    sample: str = Field(description="Sample trace id, as listed by GET /datasets.")
    words_per_second: float = Field(default=15.0, ge=0, description="0 = as fast as possible.")
    chunking: Literal["word", "random"] = "word"
    seed: int = 0


class SessionCreated(_Model):
    session_id: str


class SampleInfo(_Model):
    id: str
    title: str
    language: str
    words: int
    origin: str
