"""Segmentation into 'tramos'.

TextTiling-style lexical cohesion (Hearst 1997) with a discourse-marker
prior. For every gap between two sentences:

1. similarity: cosine between the content lemmas of the WINDOW sentences
   before the gap and the WINDOW sentences after it;
2. depth: how far the similarity dips at this gap below the nearest peaks on
   each side (TextTiling's depth score), climbing at most CLIMB gaps;
3. score = depth + marker weight (if the next sentence opens with a marker)
   + PARAGRAPH_WEIGHT (if there is a blank line at the gap).

A gap becomes a boundary when its score reaches THRESHOLD, is a local maximum
(at least the score of the gaps on either side: one topic shift raises the
depth of several neighbouring gaps, and only the deepest should count), and
the segment it closes has at least MIN_SENTENCES sentences.

Why bounded windows and a fixed threshold (TextTiling uses mean - sd/2 of all
depth scores): every decision then depends only on sentences near the gap, so
once FROZEN_AFTER more sentences have arrived it can never change. That is
what lets the dashboard draw a boundary as final while the text is still
streaming, and makes the streamed result equal the batch one.

The evaluation (eval/tune.py) searches the weights and threshold against
annotated boundaries (Pk, WindowDiff) by passing a SegParams; the live miner
uses DEFAULT_PARAMS, built from the constants below.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

WINDOW = 3  # sentences on each side of a gap
CLIMB = 2  # gaps to climb on each side when looking for peaks
MARKER_WEIGHT = {
    "backtrack": 0.35,
    "alternative": 0.35,
    "verification": 0.25,
    "conclusion": 0.25,
    "planning": 0.25,
}
PARAGRAPH_WEIGHT = 0.25
THRESHOLD = 0.5
MIN_SENTENCES = 2
# A gap's decision uses the score of the next gap, which uses similarities up
# to CLIMB gaps further right, each reading WINDOW sentences ahead; so it is
# fixed once this many sentences follow the gap.
FROZEN_AFTER = 1 + CLIMB + WINDOW


@dataclass(frozen=True)
class SegParams:
    """Every tunable number of the segmenter. marker_scale multiplies all of
    MARKER_WEIGHT, so the grid search keeps the relative weights of the
    marker types and varies only how much markers count against cohesion."""

    window: int = WINDOW
    climb: int = CLIMB
    marker_scale: float = 1.0
    paragraph_weight: float = PARAGRAPH_WEIGHT
    threshold: float = THRESHOLD
    min_sentences: int = MIN_SENTENCES


DEFAULT_PARAMS = SegParams()


@dataclass(frozen=True)
class SentenceFeatures:
    words: Counter[str]  # content lemmas (nouns, proper nouns, adjectives)
    marker_type: str | None  # type of the marker opening the sentence
    paragraph_break: bool  # a blank line separates it from the previous sentence


@dataclass(frozen=True)
class Gap:
    """The gap before sentence `index` (index >= 1)."""

    index: int
    similarity: float
    depth: float
    score: float


def cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(n * b[w] for w, n in a.items() if w in b)
    return dot / math.sqrt(sum(n * n for n in a.values()) * sum(n * n for n in b.values()))


def gap_scores(feats: list[SentenceFeatures], params: SegParams = DEFAULT_PARAMS) -> list[Gap]:
    window, climb = params.window, params.climb
    n = len(feats)
    sims = [0.0] * n  # sims[g] for g in 1..n-1
    for g in range(1, n):
        left: Counter[str] = Counter()
        right: Counter[str] = Counter()
        for f in feats[max(0, g - window) : g]:
            left.update(f.words)
        for f in feats[g : g + window]:
            right.update(f.words)
        sims[g] = cosine(left, right)

    gaps = []
    for g in range(1, n):
        s = sims[g]
        peak_left = s
        for h in range(g - 1, max(0, g - climb) - 1, -1):
            if h < 1 or sims[h] < peak_left:
                break
            peak_left = sims[h]
        peak_right = s
        for h in range(g + 1, min(n, g + climb + 1)):
            if sims[h] < peak_right:
                break
            peak_right = sims[h]
        depth = (peak_left - s) + (peak_right - s)
        f = feats[g]
        marker = params.marker_scale * MARKER_WEIGHT.get(f.marker_type or "", 0.0)
        score = depth + marker + (params.paragraph_weight if f.paragraph_break else 0.0)
        gaps.append(Gap(index=g, similarity=round(s, 4), depth=round(depth, 4), score=round(score, 4)))
    return gaps


def boundaries(gaps: list[Gap], params: SegParams = DEFAULT_PARAMS) -> list[int]:
    """Indexes of the sentences that start a new segment (0 always does)."""
    starts = [0]
    for i, gap in enumerate(gaps):
        before = gaps[i - 1].score if i > 0 else float("-inf")
        after = gaps[i + 1].score if i + 1 < len(gaps) else float("-inf")
        # On a tie with the next gap the earlier one wins.
        peak = gap.score > before and gap.score >= after
        if gap.score >= params.threshold and peak and gap.index - starts[-1] >= params.min_sentences:
            starts.append(gap.index)
    return starts
