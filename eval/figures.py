"""Figures for the memoria, from the files eval.run / eval.bench wrote.

    python -m eval.figures            # from eval/results/
    python -m eval.figures --drafts   # from eval/results/drafts/ (marked PRELIMINAR)

- segmentation.png: Pk and WindowDiff of each method on the test traces.
- boundaries.png: reference vs MeDRA boundaries along one test trace.
- bench.png: milliseconds per update as the text grows (if bench.json exists).
- steptypes.png: step-type scores on the classifier's test traces, classifier
  vs marker rule vs always "development" (if steptypes.json exists).
- learning_curve.png: the classifier's test macro-F1 as its training set grows.

Numbers use a decimal comma, as in the Spanish text of the memoria.

Static images for a document: light background, thin marks, a legend for
two or more series, grid and axes kept faint so the data reads first.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # files only, no window
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from eval.annotations import load_all  # noqa: E402
from eval.common import RESULTS_DIR, mine  # noqa: E402
from eval.run import BASELINES, seg_paragraphs, seg_paragraphs_min, seg_tuned  # noqa: E402
from medra.mining.segment import SegParams  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # categorical slots 1-3, fixed order

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "text.color": INK, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
})


def _num(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")


COMMA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
METHODS = {"classifier": "Clasificador", "rule": "Regla de marcadores", "majority": "Siempre «desarrollo»"}
TYPES = {"planning": "planificación", "development": "desarrollo", "verification": "verificación",
         "backtrack": "corrección", "alternative": "alternativa", "conclusion": "conclusión"}


def _title(ax, text: str, preliminary: bool) -> None:
    ax.set_title(text + ("  (PRELIMINAR: borradores)" if preliminary else ""), loc="left", fontsize=11, color=INK)


def segmentation_chart(res: dict, out: Path) -> None:
    test = [r for r in res["per_trace"] if r["split"] == "test"]
    keys = list(res["methods"])
    labels = [res["methods"][k] for k in keys]
    pk = [sum(r["segmentation"][k]["pk"] for r in test) / len(test) for k in keys]
    wd = [sum(r["segmentation"][k]["windowdiff"] for r in test) / len(test) for k in keys]

    fig, ax = plt.subplots(figsize=(7.5, 0.55 * len(keys) + 1.4))
    y = range(len(keys))
    h = 0.36
    ax.barh([i - h / 2 - 0.01 for i in y], pk, height=h, color=SERIES[0], label="Pk")
    ax.barh([i + h / 2 + 0.01 for i in y], wd, height=h, color=SERIES[1], label="WindowDiff")
    for i in y:
        ax.text(pk[i] + 0.008, i - h / 2, _num(pk[i]), va="center", fontsize=8, color=INK_2)
        ax.text(wd[i] + 0.008, i + h / 2, _num(wd[i]), va="center", fontsize=8, color=INK_2)
    ax.set_yticks(list(y), labels)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(wd + pk) * 1.15)
    ax.set_xlabel("Error (menor es mejor)")
    ax.xaxis.set_major_formatter(COMMA)
    ax.legend(loc="lower right", frameon=False)
    _title(ax, f"Segmentación en las {len(test)} trazas de prueba", res["preliminary"])
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def boundary_strip(res: dict, trace_id: str, out: Path) -> None:
    annotation = next(a for a in load_all() if a.trace_id == trace_id)
    m = mine(trace_id)
    rows = [("Referencia", annotation.starts), ("Solo párrafos", seg_paragraphs(m, {})),
            ("MeDRA (por defecto)", BASELINES["medra"][1](m, {}))]
    if res.get("paragraph_min"):
        rows.append((f"Párrafos + mín. {res['paragraph_min']}",
                     seg_paragraphs_min(m, {"paragraph_min": res["paragraph_min"]})))
    if res["tuned_params"]:
        rows.append(("MeDRA (ajustado)", seg_tuned(m, {"tuned": SegParams(**res["tuned_params"])})))
    n = annotation.n_sentences

    fig, ax = plt.subplots(figsize=(8, 0.5 * len(rows) + 1.3))
    for i, (_, starts) in enumerate(rows):
        colour = INK if i == 0 else SERIES[0]
        ax.vlines([s for s in starts if s > 0], i - 0.32, i + 0.32, colors=colour, linewidth=2)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, n)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Frase")
    _title(ax, f"Fronteras de tramo en {trace_id} ({n} frases)", res["preliminary"])
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def bench_chart(bench: dict, out: Path) -> None:
    # Middle of the words each bucket really covers (the last one is partial).
    spans = [tuple(int(x) for x in b["words"].split("-")) for b in bench["buckets"]]
    mids = [(lo + min(hi, bench["words"])) / 2 for lo, hi in spans]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.plot(mids, [b["miner_p50_ms"] for b in bench["buckets"]], color=SERIES[0], linewidth=2, marker="o",
            markersize=5, label="Minero (mediana)")
    ax.plot(mids, [b["total_p50_ms"] for b in bench["buckets"]], color=SERIES[1], linewidth=2, marker="o",
            markersize=5, label="Minero + presentador (mediana)")
    ax.plot(mids, [b["total_p95_ms"] for b in bench["buckets"]], color=SERIES[1], linewidth=1.2, linestyle="--",
            label="Minero + presentador (p95)")
    ax.set_xlabel("Palabras ya recibidas")
    ax.set_ylabel("ms por actualización")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, loc="upper left")
    _title(ax, "Coste por actualización según crece el texto", False)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def step_type_chart(st: dict, out: Path) -> None:
    """Left: accuracy and macro-F1 of each method. Right: F1 per type, classifier vs rule.
    One colour per method in both panels."""
    test = st["test"]
    colour = dict(zip(METHODS, SERIES))
    fig, (left, right) = plt.subplots(1, 2, figsize=(9, 3.6), gridspec_kw={"width_ratios": [1, 2.3]})
    w = 0.26
    for j, key in enumerate(METHODS):
        vals = [test[key]["accuracy"], test[key]["macro_f1"]]
        xs = [i + (j - 1) * (w + 0.02) for i in range(2)]
        left.bar(xs, vals, width=w, color=colour[key], label=METHODS[key])
        for x, v in zip(xs, vals):
            left.text(x, v + 0.015, _num(v), ha="center", fontsize=8, color=INK_2)
    left.set_xticks([0, 1], ["Exactitud", "F1 macro"])
    left.set_ylim(0, 1)
    left.yaxis.set_major_formatter(COMMA)
    left.grid(axis="x", visible=False)
    _title(left, "Todos los pasos", False)

    types = list(TYPES)
    for j, key in enumerate(("classifier", "rule")):
        vals = [test[key]["per_class"][t]["f1"] for t in types]
        xs = [i + (j - 0.5) * (w + 0.02) for i in range(len(types))]
        right.bar(xs, vals, width=w, color=colour[key])
        if key == "classifier":  # label the method being presented, not every bar
            for x, v in zip(xs, vals):
                right.text(x, v + 0.015, _num(v), ha="center", fontsize=8, color=INK_2)
    right.set_xticks(range(len(types)),
                     [f"{TYPES[t]}\n({test['classifier']['per_class'][t]['support']})" for t in types])
    right.set_ylim(0, 1)
    right.yaxis.set_major_formatter(COMMA)
    right.grid(axis="x", visible=False)
    _title(right, "F1 por tipo (entre paréntesis, pasos en prueba)", False)
    fig.legend(*left.get_legend_handles_labels(), loc="upper left", ncol=3, frameon=False,
               bbox_to_anchor=(0.005, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(out, dpi=200)
    plt.close(fig)


def learning_curve_chart(st: dict, out: Path) -> None:
    curve = st["curve"]
    xs = [c["train_traces"] for c in curve]
    ys = [c["macro_f1"] for c in curve]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.plot(xs, ys, color=SERIES[0], linewidth=2, marker="o", markersize=6, label=METHODS["classifier"])
    for key, c in (("rule", SERIES[1]), ("majority", SERIES[2])):
        v = st["test"][key]["macro_f1"]
        ax.axhline(v, color=c, linewidth=2, linestyle="--", label=f"{METHODS[key]} (no se entrena)")
        ax.text(xs[-1], v + 0.02, _num(v), ha="right", fontsize=8, color=INK_2)
    for i in (0, len(xs) - 1):
        ax.text(xs[i], ys[i] + 0.035, _num(ys[i]), ha="center", fontsize=8, color=INK_2)
    ax.set_xticks(xs)
    ax.set_xlabel("Trazas de entrenamiento (subconjuntos aleatorios de train)")
    ax.set_ylabel("F1 macro en prueba")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(COMMA)
    ax.legend(frameon=False, loc="upper left")
    _title(ax, f"Curva de aprendizaje del clasificador ({st['test_traces']} trazas de prueba)", False)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw the evaluation figures.")
    parser.add_argument("--drafts", action="store_true")
    parser.add_argument("--trace", default="en-log-pets", help="test trace for the boundary strip")
    args = parser.parse_args()
    out_dir = RESULTS_DIR / "drafts" if args.drafts else RESULTS_DIR
    res_path = out_dir / "results.json"
    if res_path.exists():
        res = json.loads(res_path.read_text(encoding="utf-8"))
        segmentation_chart(res, out_dir / "segmentation.png")
        boundary_strip(res, args.trace, out_dir / "boundaries.png")
        print(f"wrote segmentation.png, boundaries.png to {out_dir}")
    else:
        print(f"no {res_path}: run python -m eval.run{' --drafts' if args.drafts else ''} first")
    bench_path = RESULTS_DIR / "bench.json"
    if bench_path.exists():
        bench_chart(json.loads(bench_path.read_text(encoding="utf-8")), RESULTS_DIR / "bench.png")
        print(f"wrote bench.png to {RESULTS_DIR}")
    st_path = RESULTS_DIR / "steptypes.json"
    if st_path.exists():
        st = json.loads(st_path.read_text(encoding="utf-8"))
        step_type_chart(st, RESULTS_DIR / "steptypes.png")
        learning_curve_chart(st, RESULTS_DIR / "learning_curve.png")
        print(f"wrote steptypes.png, learning_curve.png to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
