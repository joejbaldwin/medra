"""Steps 7-8: TF-IDF per segment and pointwise mutual information.

Kept as pure functions over counts so they can be tested against hand
computations, independently of spaCy.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfTransformer


def tfidf_top_k(
    counts: dict[int, dict[str, int]], k: int
) -> dict[int, list[tuple[str, float]]]:
    """TF-IDF with each segment as a document (Salton & Buckley 1988).

    `counts` maps segment id -> {term id: count in that segment}. Uses
    scikit-learn's defaults: raw counts as tf, smoothed
    idf = ln((1 + N) / (1 + df)) + 1, and L2 normalisation per segment.
    Returns the top-k terms per segment, highest weight first (ties by id).
    """
    segments = sorted(counts)
    vocab = sorted({t for c in counts.values() for t in c})
    if not segments or not vocab:
        return {s: [] for s in segments}
    index = {t: i for i, t in enumerate(vocab)}
    rows, cols, vals = [], [], []
    for r, seg in enumerate(segments):
        for term, n in counts[seg].items():
            rows.append(r)
            cols.append(index[term])
            vals.append(n)
    matrix = csr_matrix((vals, (rows, cols)), shape=(len(segments), len(vocab)), dtype=np.float64)
    weights = TfidfTransformer(norm="l2", smooth_idf=True, sublinear_tf=False).fit_transform(matrix).tocsr()
    out: dict[int, list[tuple[str, float]]] = {}
    for r, seg in enumerate(segments):
        row = weights.getrow(r)
        pairs = [(vocab[c], float(w)) for c, w in zip(row.indices, row.data)]
        pairs.sort(key=lambda p: (-p[1], p[0]))
        out[seg] = [(t, round(w, 4)) for t, w in pairs[:k]]
    return out


def pmi(count_ab: int, count_a: int, count_b: int, total: int) -> float:
    """log2 P(a,b) / (P(a) P(b)), with probabilities over sentences."""
    return math.log2(count_ab * total / (count_a * count_b))
