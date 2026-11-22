"""Metric checks against values worked out by hand. Run: pytest eval"""

import pytest

from eval.metrics import bcubed, boundary_prf, classification, cohen_kappa, default_k, labels, pk, windowdiff

N = 10
REF = [0, 5]  # two segments of 5 sentences; k = 5 / 2 rounded half up = 3 (we pass k=2 below)


def test_labels():
    assert labels([0, 3, 7], 9) == [0, 0, 0, 1, 1, 1, 1, 2, 2]


def test_default_k():
    assert default_k(REF, N) == 3  # mean length 5, half is 2.5, rounded half up


def test_perfect():
    assert pk(REF, REF, N, k=2) == 0.0
    assert windowdiff(REF, REF, N, k=2) == 0.0


def test_missed_boundary():
    # Probes (i, i+2), i = 0..7. The reference changes segment only for i = 3, 4
    # (they straddle sentence 5); the hypothesis never does: 2 errors in 8.
    assert pk(REF, [0], N, k=2) == pytest.approx(2 / 8)
    assert windowdiff(REF, [0], N, k=2) == pytest.approx(2 / 8)


def test_boundary_off_by_one():
    # Hypothesis boundary at 6: it straddles for i = 4, 5; the reference for
    # i = 3, 4. They disagree at i = 3 and i = 5.
    assert pk(REF, [0, 6], N, k=2) == pytest.approx(2 / 8)
    assert windowdiff(REF, [0, 6], N, k=2) == pytest.approx(2 / 8)


def test_windowdiff_counts_extra_boundaries():
    # Two hypothesis boundaries at 5 and 6: Pk sees "different segment" at
    # i = 3, 4 (correct) and i = 5 (wrong) -> 1/8. WindowDiff also sees that the
    # window i = 4 holds 2 boundaries instead of 1 -> 2/8.
    assert pk(REF, [0, 5, 6], N, k=2) == pytest.approx(1 / 8)
    assert windowdiff(REF, [0, 5, 6], N, k=2) == pytest.approx(2 / 8)


def test_boundary_prf():
    assert boundary_prf(REF, [0, 6], tolerance=1) == (1.0, 1.0, 1.0)
    assert boundary_prf(REF, [0, 6], tolerance=0) == (0.0, 0.0, 0.0)
    # One reference boundary cannot be matched twice.
    p, r, f = boundary_prf(REF, [0, 4, 6], tolerance=1)
    assert (p, r) == (0.5, 1.0) and f == pytest.approx(2 / 3)


def test_classification():
    out = classification([("a", "a"), ("a", "b"), ("b", "b"), ("b", "b")])
    assert out["accuracy"] == 0.75
    # a: P 1/1, R 1/2, F1 2/3. b: P 2/3, R 1, F1 0.8.
    assert out["macro_f1"] == pytest.approx((2 / 3 + 0.8) / 2)


def test_bcubed():
    gold = [["a", "b", "c"], ["d", "e"]]
    assert bcubed(gold, gold)["f1"] == 1.0
    # Prediction merges everything: precision a,b,c = 3/5, d,e = 2/5; recall 1.
    out = bcubed(gold, [["a", "b", "c", "d", "e", "x"]])
    assert out["precision"] == pytest.approx((3 * 3 / 5 + 2 * 2 / 5) / 5)
    assert out["recall"] == 1.0 and out["coverage"] == 1.0
    # Terms only one side has are ignored; coverage counts the missing gold ones.
    out = bcubed(gold, [["a", "b"], ["d"]])
    assert out["coverage"] == pytest.approx(3 / 5) and out["f1"] == 1.0


def test_cohen_kappa():
    # Observed 3/4; chance: a has x,x,y,y and b has x,y,y,y -> (2*1 + 2*3) / 16 = 0.5.
    assert cohen_kappa(["x", "x", "y", "y"], ["x", "y", "y", "y"]) == pytest.approx((0.75 - 0.5) / 0.5)
