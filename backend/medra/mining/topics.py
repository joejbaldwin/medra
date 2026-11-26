"""Topics: clusters of terms.

Graph: one node per term mentioned at least MIN_TERM_COUNT times; an edge
between two terms weighted by how many windows of WINDOW consecutive
sentences contain both. Topics are the graph's communities (Louvain, fixed
seed, so the same graph always gives the same partition). Only the
MAX_TOPICS largest communities with at least MIN_TOPIC_TERMS terms become
topics. Terms seen too rarely to shape the communities are then attached to
the topic they share most windows with (none if they share none), so a
term mentioned once next to "hash" and "contraseña" joins their topic.

Re-clustering as text arrives changes the communities, so ids would jump.
TopicTracker keeps them stable: each new community takes the id of the old
topic it overlaps most (Jaccard on term sets, optimal one-to-one matching by
the Hungarian algorithm), if the overlap is at least MIN_JACCARD; otherwise
it gets a fresh id. Ids therefore depend on the history of the stream (that
is the point: a topic keeps its colour), while the partition itself only
depends on the text.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

import networkx as nx
import numpy as np
from scipy.optimize import linear_sum_assignment

WINDOW = 2  # consecutive sentences that count as "together"
MIN_TERM_COUNT = 2
MIN_TOPIC_TERMS = 2
MAX_TOPICS = 5  # the dashboard has 6 colours; the 6th is for terms without a topic
MIN_JACCARD = 0.2
SEED = 0


def communities(
    sentence_terms: list[list[str]], counts: dict[str, int], window: int = WINDOW, min_count: int = MIN_TERM_COUNT
) -> list[list[str]]:
    """Term communities, largest first (by total mentions), each sorted by count.
    window and min_count default to the module constants (the evaluation varies them)."""
    weights: Counter[tuple[str, str]] = Counter()
    for i in range(max(1, len(sentence_terms) - window + 1)):
        together = sorted({t for terms in sentence_terms[i : i + window] for t in terms if t in counts})
        for a, b in combinations(together, 2):
            if not _nested(a, b):
                weights[(a, b)] += 1

    keep = {t for t, n in counts.items() if n >= min_count}
    graph = nx.Graph()
    graph.add_nodes_from(sorted(keep))  # insertion order matters to Louvain: keep it fixed
    graph.add_weighted_edges_from((a, b, w) for (a, b), w in sorted(weights.items()) if a in keep and b in keep)
    if graph.number_of_edges() == 0:
        return []
    found = nx.community.louvain_communities(graph, weight="weight", seed=SEED)
    groups = [set(c) for c in found if len(c) >= MIN_TOPIC_TERMS]
    groups.sort(key=lambda g: (-sum(counts[t] for t in g), min(g)))
    groups = groups[:MAX_TOPICS]

    # Attach the rare terms (and terms of dropped communities) to their closest topic.
    member = {t: i for i, g in enumerate(groups) for t in g}
    pull: dict[str, Counter[int]] = {}
    for (a, b), w in weights.items():
        for x, y in ((a, b), (b, a)):
            if x not in member and y in member:
                pull.setdefault(x, Counter())[member[y]] += w
    for term, by_group in sorted(pull.items()):
        best = min(by_group, key=lambda i: (-by_group[i], i))
        groups[best].add(term)
    return [sorted(g, key=lambda t: (-counts[t], t)) for g in groups]


def _nested(a: str, b: str) -> bool:
    # "odd number" always appears with "number": not evidence of a topic.
    wa, wb = set(a.split()), set(b.split())
    return wa <= wb or wb <= wa


class TopicTracker:
    def __init__(self) -> None:
        self.topics: dict[str, set[str]] = {}  # id -> terms, from the last update
        self.next_id = 0

    def assign(self, groups: list[list[str]]) -> list[tuple[str, list[str]]]:
        """Give each group an id, reusing the ids of the previous update where they overlap."""
        old = list(self.topics.items())
        ids: list[str | None] = [None] * len(groups)
        if old and groups:
            sim = np.array([[_jaccard(set(g), terms) for _, terms in old] for g in groups])
            for gi, oi in zip(*linear_sum_assignment(sim, maximize=True)):
                if sim[gi, oi] >= MIN_JACCARD:
                    ids[gi] = old[oi][0]
        out = []
        for g, tid in zip(groups, ids):
            if tid is None:
                tid = f"t{self.next_id}"
                self.next_id += 1
            out.append((tid, g))
        self.topics = {tid: set(g) for tid, g in out}
        return out


def _jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a or b else 0.0
