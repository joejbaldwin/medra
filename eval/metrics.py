"""Evaluation metrics. Pure functions, no MeDRA imports.

Segmentation is compared sentence by sentence. A segmentation of n sentences
is the sorted list of the sentence indexes that start a segment (0 always
does), the same form as Annotation.starts and segment.boundaries().

Pk (Beeferman et al. 1999): slide a probe of width k over the text; at each
position ask "are sentence i and sentence i+k in the same segment?". Pk is
the share of positions where the reference and the hypothesis answer
differently. 0 is perfect; a segmentation with no boundaries, or one with a
boundary everywhere, typically scores around 0.4-0.6.

WindowDiff (Pevzner & Hearst 2002): same probe, but it compares how many
boundaries fall inside the window, so it also penalises a wrong number of
boundaries close together, which Pk can miss. Lower is better.

k is half the mean segment length of the reference, as both papers recommend.
"""

from __future__ import annotations

from collections import Counter


def default_k(ref: list[int], n: int) -> int:
    """Half the mean reference segment length, rounded half up, at least 1."""
    return max(1, int(n / len(ref) / 2 + 0.5))


def labels(starts: list[int], n: int) -> list[int]:
    """Segment number of each sentence."""
    out, seg = [], -1
    marks = set(starts)
    for i in range(n):
        if i in marks:
            seg += 1
        out.append(max(seg, 0))
    return out


def pk(ref: list[int], hyp: list[int], n: int, k: int | None = None) -> float:
    k = k or default_k(ref, n)
    if n - k <= 0:
        return 0.0
    r, h = labels(ref, n), labels(hyp, n)
    errors = sum((r[i] == r[i + k]) != (h[i] == h[i + k]) for i in range(n - k))
    return errors / (n - k)


def windowdiff(ref: list[int], hyp: list[int], n: int, k: int | None = None) -> float:
    k = k or default_k(ref, n)
    if n - k <= 0:
        return 0.0
    r, h = labels(ref, n), labels(hyp, n)
    # Boundaries strictly after sentence i and up to sentence i+k = label difference.
    errors = sum((r[i + k] - r[i]) != (h[i + k] - h[i]) for i in range(n - k))
    return errors / (n - k)


def boundary_prf(ref: list[int], hyp: list[int], tolerance: int = 1) -> tuple[float, float, float]:
    """Precision, recall and F1 of the boundaries (start 0 excluded), where a
    hypothesis boundary counts if it is within `tolerance` sentences of a
    reference boundary not already matched (one-to-one, nearest first)."""
    gold = [s for s in ref if s > 0]
    pred = [s for s in hyp if s > 0]
    if not gold and not pred:
        return 1.0, 1.0, 1.0
    free = set(gold)
    hits = 0
    for p in pred:
        near = sorted((abs(p - g), g) for g in free if abs(p - g) <= tolerance)
        if near:
            free.discard(near[0][1])
            hits += 1
    precision = hits / len(pred) if pred else 0.0
    recall = hits / len(gold) if gold else 0.0
    return precision, recall, f1(precision, recall)


def f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def set_prf(pred: set[str], gold: set[str]) -> tuple[float, float, float]:
    hits = len(pred & gold)
    precision = hits / len(pred) if pred else 0.0
    recall = hits / len(gold) if gold else 0.0
    return precision, recall, f1(precision, recall)


def classification(pairs: list[tuple[str, str]]) -> dict:
    """Accuracy, macro-F1 (over the classes in the reference) and the confusion
    counts, for (gold, predicted) pairs."""
    if not pairs:
        return {"n": 0, "accuracy": 0.0, "macro_f1": 0.0, "per_class": {}, "confusion": {}}
    confusion = Counter(pairs)
    classes = sorted({g for g, _ in pairs})
    per_class = {}
    for c in classes:
        tp = confusion[(c, c)]
        predicted = sum(n for (_, p), n in confusion.items() if p == c)
        actual = sum(n for (g, _), n in confusion.items() if g == c)
        precision = tp / predicted if predicted else 0.0
        recall = tp / actual
        per_class[c] = {"precision": precision, "recall": recall, "f1": f1(precision, recall), "support": actual}
    return {
        "n": len(pairs),
        "accuracy": sum(n for (g, p), n in confusion.items() if g == p) / len(pairs),
        "macro_f1": sum(v["f1"] for v in per_class.values()) / len(classes),
        "per_class": per_class,
        "confusion": {f"{g}->{p}": n for (g, p), n in sorted(confusion.items())},
    }


def bcubed(gold: list[list[str]], pred: list[list[str]]) -> dict:
    """B-cubed precision, recall and F1 (Bagga & Baldwin 1998) over the terms
    that appear in both clusterings, plus coverage: the share of gold terms
    that the prediction puts in some cluster.

    For each term: precision = share of its predicted cluster-mates that are
    also its gold cluster-mates; recall = the reverse. Unlike raw Jaccard
    between clusters, this does not punish MeDRA for clustering terms the
    annotator did not list."""
    gold_of = {t: i for i, group in enumerate(gold) for t in group}
    pred_of = {t: i for i, group in enumerate(pred) for t in group}
    items = sorted(set(gold_of) & set(pred_of))
    if not gold_of:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "coverage": 0.0, "items": 0}
    if not items:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "coverage": 0.0, "items": 0}
    precision = recall = 0.0
    for t in items:
        same_pred = {u for u in items if pred_of[u] == pred_of[t]}
        same_gold = {u for u in items if gold_of[u] == gold_of[t]}
        both = len(same_pred & same_gold)
        precision += both / len(same_pred)
        recall += both / len(same_gold)
    precision /= len(items)
    recall /= len(items)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1(precision, recall),
        "coverage": len(items) / len(gold_of),
        "items": len(items),
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0

