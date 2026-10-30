"""Layer 3: the view presenter. Mining output in, visual decisions out.

Per MiningUpdate it decides which terms are bubbles (select.py), how big
(sizing.py), which pairs are linked (edges.py), the colour of each topic and
where its bubbles gather (topics.py), what to underline for each bubble, how
to label each paragraph, the step graph, the timeline (timeline.py) and what
the ticker shows. Then it sends only what changed since the previous
ViewUpdate (diff.py).
"""

from __future__ import annotations

from medra.contracts import (
    Highlight,
    MiningUpdate,
    Node,
    Paragraph,
    Removed,
    Term,
    TickerItem,
    Timeline,
    Topic,
    ViewUpdate,
)
from medra.present.diff import Keyed
from medra.present.edges import select_edges
from medra.present.select import TOP_K, BubbleSelector
from medra.present.sizing import radius
from medra.present.timeline import build_timeline
from medra.present.topics import NO_TOPIC, SlotAllocator, build_steps, seed_for, segment_topics

LABEL_KEYWORDS = 3  # TF-IDF keywords shown in a paragraph's label
TOPIC_NAME_TERMS = 2
TICKER_ITEMS = 4


def label_for(term: Term) -> str:
    """Prefer a surface form that is the lemma itself ("JWT" for jwt), else the
    lemma ("campo", not the more frequent "campos")."""
    same = [f for f in term.surface_forms if f.lower() == term.id]
    return same[0] if same else term.id


class ViewPresenter:
    def __init__(self, top_k: int = TOP_K) -> None:
        self.selector = BubbleSelector(top_k=top_k)
        self.nodes: Keyed[str, Node] = Keyed(lambda n: n.id)
        self.edges = Keyed(lambda e: e.id)
        self.highlights: Keyed[str, Highlight] = Keyed(lambda h: f"{h.kind}:{h.id}")
        self.paragraphs: Keyed[int, Paragraph] = Keyed(lambda p: p.segment_id)
        self.topics: Keyed[str, Topic] = Keyed(lambda t: t.id)
        self.steps = Keyed(lambda s: s.segment_id)
        self.slots = SlotAllocator()
        self.timeline: Timeline | None = None
        self.counts: dict[str, int] = {}
        self.seq = 0

    def present(self, update: MiningUpdate) -> ViewUpdate:
        shown = self.selector.select(update)
        labels = {t.id: label_for(t) for t in update.terms}
        slot_of = self.slots.assign([c.id for c in update.clusters])
        topic_of_term = {tid: c.id for c in update.clusters for tid in c.term_ids}
        # Name a topic by its most frequent terms, skipping words hidden inside
        # n-grams ("odd number · sum", not "number · odd").
        topics = [
            Topic(
                id=c.id,
                name=" · ".join(labels.get(t, t) for t in
                                [t for t in c.term_ids if t not in self.selector.nested][:TOPIC_NAME_TERMS]),
                colour_slot=slot_of[c.id],
            )
            for c in update.clusters
        ]

        shown_ids = {t.id for t in shown}
        max_count = max((t.count for t in shown), default=1)
        nodes = []
        for t in shown:
            topic = topic_of_term.get(t.id)
            slot = slot_of[topic] if topic else NO_TOPIC
            nodes.append(
                Node(
                    id=t.id,
                    label=label_for(t),
                    count=t.count,
                    radius=radius(t.count, max_count),
                    topic_id=topic,
                    colour_slot=slot,
                    seed_xy=seed_for(slot),
                    emphasis=1.0 if t.count > self.counts.get(t.id, 0) else 0.0,
                )
            )
        self.counts = {t.id: t.count for t in shown}
        highlights = [Highlight(kind="node", id=t.id, spans=t.spans) for t in shown]
        edges = select_edges(update.cooc, shown_ids)
        for e in edges:
            same = topic_of_term.get(e.a)
            e.colour_slot = slot_of[same] if same and same == topic_of_term.get(e.b) else NO_TOPIC

        keywords = {
            k.segment_id: [labels[w.term_id] for w in k.terms if w.term_id not in self.selector.nested][:LABEL_KEYWORDS]
            for k in update.tfidf
        }
        topic_of_segment = segment_topics(update, update.clusters)
        paragraphs = [
            Paragraph(
                segment_id=s.id,
                start=s.start,
                end=s.end,
                topic_id=topic_of_segment[s.id],
                label=" · ".join(keywords.get(s.id, [])),
                provisional=s.provisional,
            )
            for s in update.segments
        ]
        steps = build_steps(update, topic_of_segment)
        timeline = build_timeline(update, update.clusters)
        timeline_changed = timeline != self.timeline
        self.timeline = timeline
        ticker = [
            TickerItem(form=d.form, lemma=d.lemma, outcome=d.outcome, pos=d.pos,
                       node_id=d.lemma if d.lemma in shown_ids else None)
            for d in update.recent_tokens[-TICKER_ITEMS:]
        ]

        changed_nodes, removed_nodes = self.nodes.diff(nodes)
        changed_edges, removed_edges = self.edges.diff(edges)
        changed_hl, removed_hl = self.highlights.diff(highlights)
        changed_par, removed_par = self.paragraphs.diff(paragraphs)
        changed_topics, removed_topics = self.topics.diff(topics)
        changed_steps, removed_steps = self.steps.diff(steps)
        view = ViewUpdate(
            session_id=update.session_id,
            seq=self.seq,
            t=update.t,
            kind="snapshot" if self.seq == 0 else "diff",
            committed_upto=update.committed_upto,
            final=update.final,
            nodes=changed_nodes,
            edges=changed_edges,
            topics=changed_topics,
            paragraphs=changed_par,
            highlights=changed_hl,
            timeline=timeline if timeline_changed or self.seq == 0 else None,
            steps=changed_steps,
            ticker=ticker,
            stats=update.stats,
            removed=Removed(
                nodes=removed_nodes,
                edges=removed_edges,
                topics=removed_topics,
                highlights=removed_hl,
                paragraphs=removed_par,
                steps=removed_steps,
            ),
        )
        self.seq += 1
        return view
