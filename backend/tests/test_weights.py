import math

import pytest

from medra.mining.weights import pmi, tfidf_top_k


def test_tfidf_matches_hand_computation():
    counts = {0: {"a": 2, "b": 1}, 1: {"b": 1, "c": 1}}
    top = tfidf_top_k(counts, k=5)
    # idf = ln((1 + N) / (1 + df)) + 1 with N = 2 segments; then L2-normalise each segment.
    idf_rare = math.log(3 / 2) + 1  # a, c: in one segment
    idf_common = 1.0  # b: in both
    a, b = 2 * idf_rare, 1 * idf_common
    norm = math.hypot(a, b)
    assert top[0] == [("a", pytest.approx(a / norm, abs=1e-4)), ("b", pytest.approx(b / norm, abs=1e-4))]
    b, c = 1 * idf_common, 1 * idf_rare
    norm = math.hypot(b, c)
    assert top[1] == [("c", pytest.approx(c / norm, abs=1e-4)), ("b", pytest.approx(b / norm, abs=1e-4))]


def test_tfidf_top_k_and_empty():
    assert len(tfidf_top_k({0: {str(i): i + 1 for i in range(20)}}, k=8)[0]) == 8
    assert tfidf_top_k({0: {}}, k=8) == {0: []}


def test_pmi():
    # Two terms each in half of 8 sentences, together in 2: independent -> 0.
    assert pmi(2, 4, 4, 8) == 0
    # Always together -> log2(8 / 2) = 2.
    assert pmi(2, 2, 2, 8) == 2
