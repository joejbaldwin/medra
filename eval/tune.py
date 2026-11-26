"""Tune the segmenter's parameters on the annotated traces.

    python -m eval.tune

Tuning the segmenter means choosing its numbers (window, climb, marker and
paragraph weights, threshold, minimum segment length) by grid search
against annotated boundaries (`status: corrected` files only). The
step-type classifier, the one trained model, is in eval/steptypes.py.

Protocol:
1. Fixed dev/test split, stratified by source model (eval.common.split, seed 0).
2. Grid search on dev; the objective is mean WindowDiff (ties: mean Pk, then
   the configuration closest to the defaults).
3. The chosen parameters are scored once on test, next to the defaults; run
   `python -m eval.run` afterwards for the full test table with baselines.
4. With so few traces a single split is noisy, so leave-one-out cross-
   validation is also reported: for each trace, tune on the other traces and
   score the held-out one. If LOOCV does not beat the defaults, the gain on dev
   is overfitting.

Every number depends only on the annotations, the code and the grid, so a
rerun gives the same output. Writes tuned.json (read by eval.run) and tune.md.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from dataclasses import asdict, fields
from datetime import date

import numpy as np

from eval.annotations import load_all
from eval.common import RESULTS_DIR, git_commit, mine, split, trace_ids
from eval.metrics import default_k, mean, pk, windowdiff
from medra.mining.segment import DEFAULT_PARAMS, SegParams, boundaries, gap_scores

# Gap-score parameters (each combination recomputes gap_scores) and decision
# parameters (only boundaries() reruns). The defaults are inside every range.
GAP_GRID = {
    "window": [2, 3, 4],
    "climb": [1, 2, 3],
    "marker_scale": [0.0, 0.5, 1.0, 1.5, 2.0, 3.0],
    "paragraph_weight": [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0],
}
# Upper ends widened after the first run chose values at the edge
# (threshold 1.8 of max 2.0, min_sentences 8 of max 8, paragraph_weight tie at 3.0).
DECISION_GRID = {
    "threshold": [round(0.3 + 0.1 * i, 1) for i in range(23)],  # 0.3 .. 2.5
    "min_sentences": [2, 3, 4, 5, 6, 8, 10, 12],
}


def configs() -> list[SegParams]:
    names = list(GAP_GRID) + list(DECISION_GRID)
    values = list(GAP_GRID.values()) + list(DECISION_GRID.values())
    return [SegParams(**dict(zip(names, combo))) for combo in itertools.product(*values)]


def distance_to_default(p: SegParams) -> int:
    return sum(getattr(p, f.name) != getattr(DEFAULT_PARAMS, f.name) for f in fields(SegParams))


def score_grid(annotations) -> tuple[list[SegParams], np.ndarray, np.ndarray]:
    """WindowDiff and Pk of every configuration on every trace:
    arrays of shape (configurations, traces)."""
    grid = configs()
    index = {p: i for i, p in enumerate(grid)}
    wd = np.zeros((len(grid), len(annotations)))
    pkk = np.zeros_like(wd)
    for t, a in enumerate(annotations):
        feats = mine(a.trace_id).features
        n, ref = a.n_sentences, a.starts
        k = default_k(ref, n)
        for gap_values in itertools.product(*GAP_GRID.values()):
            gap_params = SegParams(**dict(zip(GAP_GRID, gap_values)))
            gaps = gap_scores(feats, gap_params)
            for dec_values in itertools.product(*DECISION_GRID.values()):
                p = SegParams(**{**dict(zip(GAP_GRID, gap_values)), **dict(zip(DECISION_GRID, dec_values))})
                hyp = boundaries(gaps, p)
                i = index[p]
                wd[i, t] = windowdiff(ref, hyp, n, k)
                pkk[i, t] = pk(ref, hyp, n, k)
    return grid, wd, pkk


def best(grid: list[SegParams], wd: np.ndarray, pkk: np.ndarray, cols: list[int]) -> int:
    """Index of the configuration with the lowest mean WindowDiff on these traces."""
    w = wd[:, cols].mean(axis=1)
    p = pkk[:, cols].mean(axis=1)
    order = sorted(range(len(grid)), key=lambda i: (round(w[i], 9), round(p[i], 9), distance_to_default(grid[i])))
    return order[0]


def main() -> None:
    argparse.ArgumentParser(description="Grid-search the segmenter's parameters.").parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    annotations = load_all(status="corrected")
    if not annotations:
        raise SystemExit("no corrected annotations")
    out_dir = RESULTS_DIR
    ids = [a.trace_id for a in annotations]
    dev_ids, test_ids = split(trace_ids())
    dev = [i for i, t in enumerate(ids) if t in dev_ids]
    test = [i for i, t in enumerate(ids) if t in test_ids]
    if not dev or not test:
        raise SystemExit(f"need annotated traces on both sides of the split (dev {len(dev)}, test {len(test)})")

    started = time.perf_counter()
    grid, wd, pkk = score_grid(annotations)
    elapsed = time.perf_counter() - started
    d = grid.index(DEFAULT_PARAMS)
    chosen = best(grid, wd, pkk, dev)

    def scores(i: int, cols: list[int]) -> dict:
        return {"windowdiff": float(wd[i, cols].mean()), "pk": float(pkk[i, cols].mean())}

    # Leave-one-out: tune on all traces but one, score that one.
    loo = []
    everything = list(range(len(ids)))
    for t in everything:
        b = best(grid, wd, pkk, [c for c in everything if c != t])
        loo.append({"trace": ids[t], "params": asdict(grid[b]), "windowdiff": float(wd[b, t]), "pk": float(pkk[b, t]),
                    "default_windowdiff": float(wd[d, t]), "default_pk": float(pkk[d, t])})

    # How much each parameter matters: the best dev WindowDiff with that
    # parameter fixed at each value and the others free.
    dev_mean = wd[:, dev].mean(axis=1)
    sensitivity = {}
    for name, values in {**GAP_GRID, **DECISION_GRID}.items():
        sensitivity[name] = {str(v): float(min(dev_mean[i] for i, p in enumerate(grid) if getattr(p, name) == v))
                             for v in values}

    result = {
        "date": date.today().isoformat(),
        "commit": git_commit(),
        "objective": "mean WindowDiff on dev (ties: Pk, then closest to defaults)",
        "dev": [ids[i] for i in dev],
        "test": [ids[i] for i in test],
        "grid": {**GAP_GRID, **DECISION_GRID},
        "configurations": len(grid),
        "seconds": round(elapsed, 1),
        "params": asdict(grid[chosen]),
        "default_params": asdict(DEFAULT_PARAMS),
        "dev_scores": {"tuned": scores(chosen, dev), "default": scores(d, dev)},
        "test_scores": {"tuned": scores(chosen, test), "default": scores(d, test)},
        "loocv": {
            "tuned": {"windowdiff": mean([r["windowdiff"] for r in loo]), "pk": mean([r["pk"] for r in loo])},
            "default": {"windowdiff": mean([r["default_windowdiff"] for r in loo]),
                        "pk": mean([r["default_pk"] for r in loo])},
            "per_trace": loo,
        },
        "sensitivity": sensitivity,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tuned.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = report(result)
    (out_dir / "tune.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"written to {out_dir}")


def report(r: dict) -> str:
    lines = ["# Ajuste de parámetros del segmentador", ""]
    lines += [f"`python -m eval.tune`, {r['date']}, commit {r['commit']}. "
              f"Búsqueda en rejilla: {r['configurations']} configuraciones × {len(r['dev']) + len(r['test'])} trazas "
              f"en {r['seconds']} s. Objetivo: {r['objective']}.", "",
              f"Dev ({len(r['dev'])}): {', '.join(r['dev'])}.  ", f"Test ({len(r['test'])}): {', '.join(r['test'])}.", "",
              "| Parámetro | Por defecto | Ajustado |", "|---|---|---|"]
    for k, v in r["params"].items():
        lines.append(f"| {k} | {r['default_params'][k]} | {v} |")
    lines += ["", "| | WindowDiff dev | Pk dev | WindowDiff test | Pk test | WindowDiff LOOCV | Pk LOOCV |",
              "|---|---|---|---|---|---|---|"]
    for key, label in (("default", "Por defecto"), ("tuned", "Ajustado")):
        dv, ts, lo = r["dev_scores"][key], r["test_scores"][key], r["loocv"][key]
        lines.append(f"| {label} | {dv['windowdiff']:.3f} | {dv['pk']:.3f} | {ts['windowdiff']:.3f} | {ts['pk']:.3f} "
                     f"| {lo['windowdiff']:.3f} | {lo['pk']:.3f} |")
    lines += ["", "LOOCV: para cada traza, se ajusta con las demás y se evalúa en ella; la columna «Por defecto» es la "
              "media de los parámetros por defecto en las mismas trazas.", "",
              "## Sensibilidad (mejor WindowDiff en dev fijando cada valor, el resto libre)", ""]
    for name, by_value in r["sensitivity"].items():
        lines.append(f"- **{name}**: " + ", ".join(f"{v} → {s:.3f}" for v, s in by_value.items()))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
