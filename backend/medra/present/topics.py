"""Topic colours, the topic of each segment, and the step graph.

Colours: each topic keeps its palette slot for as long as it exists
(SlotAllocator), so a bubble does not change colour when topics are
re-clustered. Slot NO_TOPIC is the neutral colour for terms without a topic.

Seed positions: each slot has a sector around the centre of the map; the
dashboard pulls bubbles towards their topic's sector, so topics form groups.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from collections import Counter

from medra.contracts import Cluster, MiningUpdate, Step

TOPIC_SLOTS = 5
NO_TOPIC = 5  # the sixth palette colour
_SECTOR_RADIUS = (0.28, 0.3)  # x, y as fractions of the map


class SlotAllocator:
    def __init__(self) -> None:
        self.slots: dict[str, int] = {}

    def assign(self, topic_ids: list[str]) -> dict[str, int]:
        self.slots = {tid: s for tid, s in self.slots.items() if tid in topic_ids}
        for tid in topic_ids:
            if tid not in self.slots:
                free = [s for s in range(TOPIC_SLOTS) if s not in self.slots.values()]
                self.slots[tid] = free[0] if free else NO_TOPIC
        return dict(self.slots)


def seed_for(slot: int) -> tuple[float, float]:
    if slot >= TOPIC_SLOTS:
        return (0.5, 0.5)
    angle = 2 * math.pi * slot / TOPIC_SLOTS - math.pi / 2
    return (round(0.5 + _SECTOR_RADIUS[0] * math.cos(angle), 3), round(0.5 + _SECTOR_RADIUS[1] * math.sin(angle), 3))


def segment_topics(update: MiningUpdate, clusters: list[Cluster]) -> dict[int, str | None]:
    """The topic with the most mentions in each segment (None if no topic term appears)."""
    spans = {t.id: [a for a, _ in t.spans] for t in update.terms}
    out: dict[int, str | None] = {}
    for seg in update.segments:
        mentions: Counter[str] = Counter()
        for c in clusters:
            for tid in c.term_ids:
                starts = spans.get(tid, [])
                mentions[c.id] += bisect_left(starts, seg.end) - bisect_left(starts, seg.start)
        best = max(clusters, key=lambda c: mentions[c.id], default=None)  # ties: the larger topic
        out[seg.id] = best.id if best and mentions[best.id] else None
    return out


def build_steps(update: MiningUpdate, topic_of: dict[int, str | None]) -> list[Step]:
    """One step per segment. A step 'returns to' (retoma) an earlier segment
    when its topic was left for at least one other step and comes back."""
    words: Counter[int] = Counter()
    for s in update.sentences:
        words[s.segment_id] += s.words
    marker_at = {m.span[0]: m for m in update.markers}
    first_sentence_end = {}
    for s in update.sentences:
        first_sentence_end.setdefault(s.segment_id, s.end)

    steps = []
    last_seen: dict[str, int] = {}
    prev_topic: str | None = None
    for seg in update.segments:
        topic = topic_of.get(seg.id)
        arcs = []
        if topic and topic != prev_topic and topic in last_seen:
            arcs.append(last_seen[topic])
        marker = next(
            (m for a, m in marker_at.items() if seg.start <= a < first_sentence_end.get(seg.id, seg.end)), None
        )
        steps.append(
            Step(
                segment_id=seg.id,
                step_type=seg.step_type,
                topic_id=topic,
                arcs_back_to=arcs,
                marker=seg.marker,
                marker_span=marker.span if marker else None,
                words=words[seg.id],
            )
        )
        if topic:
            last_seen[topic] = seg.id
        prev_topic = topic
    return steps
