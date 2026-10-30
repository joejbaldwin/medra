"""Timeline: how much each topic is mentioned along the trace.

x is the position in words (from Sentence.words); a mention inside a sentence
is placed proportionally to its character offset. y is a Gaussian kernel
density of mentions (σ = SIGMA words, as in the demo): roughly "mentions of
this topic within ±σ words". The curve is sampled at most MAX_POINTS times;
for long traces σ grows to the sample spacing so no mention falls between
samples.
"""

from __future__ import annotations

import math
from bisect import bisect_right

from medra.contracts import Cluster, MiningUpdate, Timeline, TimelineSeries

SIGMA = 6.0
MAX_POINTS = 200


def word_positions(update: MiningUpdate, offsets: list[int]) -> list[float]:
    starts = [s.start for s in update.sentences]
    before = []
    total = 0
    for s in update.sentences:
        before.append(total)
        total += s.words
    out = []
    for off in offsets:
        i = bisect_right(starts, off) - 1
        if i < 0:
            continue
        s = update.sentences[i]
        frac = (off - s.start) / max(1, s.end - s.start)
        out.append(before[i] + min(1.0, frac) * s.words)
    return out


def build_timeline(update: MiningUpdate, clusters: list[Cluster]) -> Timeline:
    x_max = float(sum(s.words for s in update.sentences))
    n = max(2, min(MAX_POINTS, int(x_max) + 1))
    step = x_max / (n - 1) if x_max else 1.0
    sigma = max(SIGMA, step)
    xs = [i * step for i in range(n)]
    spans = {t.id: t.spans for t in update.terms}
    series = []
    for c in clusters:
        mentions = word_positions(update, sorted(a for tid in c.term_ids for a, _ in spans.get(tid, [])))
        ys = [sum(math.exp(-((x - m) ** 2) / (2 * sigma * sigma)) for m in mentions if abs(x - m) < 4 * sigma) for x in xs]
        series.append(TimelineSeries(topic_id=c.id, points=[(round(x, 1), round(y, 2)) for x, y in zip(xs, ys)]))
    return Timeline(x_max=x_max, series=series)
