"""Which co-occurrence pairs become edges between bubbles.

Only pairs of bubbles on screen, that co-occur more than chance would
predict (PMI > 0) and in at least MIN_COUNT sentences. Each bubble keeps at
most MAX_PER_NODE edges, strongest first, so the map stays readable.
"""

from __future__ import annotations

from medra.contracts import Cooccurrence, Edge
from medra.present.sizing import edge_width

PMI_MIN = 0.0
MIN_COUNT = 2
MAX_PER_NODE = 3


def select_edges(cooc: list[Cooccurrence], shown: set[str]) -> list[Edge]:
    pairs = [p for p in cooc if p.a in shown and p.b in shown and p.pmi > PMI_MIN and p.count >= MIN_COUNT]
    pairs.sort(key=lambda p: (-p.count, -p.pmi, p.a, p.b))
    degree: dict[str, int] = {}
    edges = []
    for p in pairs:
        if degree.get(p.a, 0) >= MAX_PER_NODE or degree.get(p.b, 0) >= MAX_PER_NODE:
            continue
        degree[p.a] = degree.get(p.a, 0) + 1
        degree[p.b] = degree.get(p.b, 0) + 1
        edges.append(Edge(id=f"{p.a}|{p.b}", a=p.a, b=p.b, width=edge_width(p.count), colour_slot=0))
    return edges
