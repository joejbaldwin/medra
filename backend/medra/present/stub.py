"""Stub presenter for the walking skeleton: the top-K most frequent terms
become bubbles, with area proportional to count. Step 3 adds hysteresis,
edges, topics and colours."""

from __future__ import annotations

import math

from medra.contracts import Highlight, MiningUpdate, Node, Removed, ViewUpdate
from medra.present.diff import Keyed

TOP_K = 16
R_MIN, R_MAX = 18.0, 64.0


def radius(count: int, max_count: int) -> float:
    # Area grows with count (radius with its square root), rescaled against
    # the current maximum so the biggest bubble is always R_MAX.
    return round(R_MIN + (R_MAX - R_MIN) * math.sqrt(count / max_count), 1)


class StubPresenter:
    def __init__(self, top_k: int = TOP_K) -> None:
        self.top_k = top_k
        self.nodes: Keyed[str, Node] = Keyed(lambda n: n.id)
        self.highlights: Keyed[str, Highlight] = Keyed(lambda h: f"{h.kind}:{h.id}")
        self.seq = 0

    def present(self, update: MiningUpdate) -> ViewUpdate | None:
        top = update.terms[: self.top_k]  # the miner sorts terms by count
        max_count = top[0].count if top else 1
        nodes = [
            Node(
                id=term.id,
                label=term.surface_forms[0],
                count=term.count,
                radius=radius(term.count, max_count),
                colour_slot=0,
            )
            for term in top
        ]
        highlights = [Highlight(kind="node", id=term.id, spans=term.spans) for term in top]

        changed_nodes, removed_nodes = self.nodes.diff(nodes)
        changed_hl, removed_hl = self.highlights.diff(highlights)
        view = ViewUpdate(
            session_id=update.session_id,
            seq=self.seq,
            t=update.t,
            kind="snapshot" if self.seq == 0 else "diff",
            committed_upto=update.committed_upto,
            final=update.final,
            nodes=changed_nodes,
            highlights=changed_hl,
            stats=update.stats,
            removed=Removed(nodes=removed_nodes, highlights=removed_hl),
        )
        self.seq += 1
        return view
