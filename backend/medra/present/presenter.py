"""Layer 3: the view presenter. Mining output in, visual decisions out.

Per MiningUpdate it decides which terms are bubbles (select.py), how big
(sizing.py), which pairs are linked (edges.py), what to underline for each
bubble, how to label each paragraph, and what the ticker shows. Then it
sends only what changed since the previous ViewUpdate (diff.py).

No colours by topic yet: topics arrive in step 4, so every bubble uses
palette slot 0 for now.
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
    ViewUpdate,
)
from medra.present.diff import Keyed
from medra.present.edges import select_edges
from medra.present.select import TOP_K, BubbleSelector
from medra.present.sizing import radius

LABEL_KEYWORDS = 3  # TF-IDF keywords shown in a paragraph's label
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
        self.counts: dict[str, int] = {}
        self.seq = 0

    def present(self, update: MiningUpdate) -> ViewUpdate:
        shown = self.selector.select(update)
        shown_ids = {t.id for t in shown}
        max_count = max((t.count for t in shown), default=1)
        nodes = [
            Node(
                id=t.id,
                label=label_for(t),
                count=t.count,
                radius=radius(t.count, max_count),
                colour_slot=0,
                emphasis=1.0 if t.count > self.counts.get(t.id, 0) else 0.0,
            )
            for t in shown
        ]
        self.counts = {t.id: t.count for t in shown}
        highlights = [Highlight(kind="node", id=t.id, spans=t.spans) for t in shown]
        edges = select_edges(update.cooc, shown_ids)

        labels = {t.id: label_for(t) for t in update.terms}
        keywords = {
            k.segment_id: [labels[w.term_id] for w in k.terms if w.term_id not in self.selector.nested][:LABEL_KEYWORDS]
            for k in update.tfidf
        }
        paragraphs = [
            Paragraph(
                segment_id=s.id,
                start=s.start,
                end=s.end,
                label=" · ".join(keywords.get(s.id, [])),
                provisional=s.provisional,
            )
            for s in update.segments
        ]
        ticker = [
            TickerItem(form=d.form, lemma=d.lemma, outcome=d.outcome, pos=d.pos,
                       node_id=d.lemma if d.lemma in shown_ids else None)
            for d in update.recent_tokens[-TICKER_ITEMS:]
        ]

        changed_nodes, removed_nodes = self.nodes.diff(nodes)
        changed_edges, removed_edges = self.edges.diff(edges)
        changed_hl, removed_hl = self.highlights.diff(highlights)
        changed_par, removed_par = self.paragraphs.diff(paragraphs)
        view = ViewUpdate(
            session_id=update.session_id,
            seq=self.seq,
            t=update.t,
            kind="snapshot" if self.seq == 0 else "diff",
            committed_upto=update.committed_upto,
            final=update.final,
            nodes=changed_nodes,
            edges=changed_edges,
            paragraphs=changed_par,
            highlights=changed_hl,
            ticker=ticker,
            stats=update.stats,
            removed=Removed(nodes=removed_nodes, edges=removed_edges, highlights=removed_hl, paragraphs=removed_par),
        )
        self.seq += 1
        return view
