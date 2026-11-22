"""Evaluate MeDRA against the hand annotations (build plan §8.3).

    python -m eval.run            # corrected annotations only: the reported results
    python -m eval.run --drafts   # also drafts: PRELIMINARY, written to eval/results/drafts/

Writes results.json (every number, per trace) and results.md (tables) to
eval/results/ (or eval/results/drafts/). If eval.tune has been run, the tuned
segmenter is added, evaluated on the test traces only.

What is measured:
- Segmentation: Pk, WindowDiff and boundary P/R/F1 (within one sentence) of
  MeDRA's segments and of baselines: fixed-size segments, a boundary at every
  blank line, at every discourse marker, and TextTiling (cohesion only, with
  Hearst's adaptive threshold mean - sd/2).
- Step types: the type MeDRA gives the step opened at each reference boundary
  (the marker of its first sentence, development if none), against the
  annotated type. Measured at the reference boundaries so that segmentation
  errors do not count twice.
- Concepts: the bubbles of the final view against the annotated concepts,
  both as lemma keys. Baseline: the 16 most frequent terms.
- Topics: B-cubed F1 of MeDRA's Louvain topics against the annotated topics,
  and of agglomerative clustering on the same terms (the comparison left open
  in build plan §4.4).
- Agreement between annotators, on traces annotated twice.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from dataclasses import asdict, replace
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from eval.annotations import Annotation, annotation_files, load_all, parse
from eval.common import RESULTS_DIR, Mined, lemma_key, mine, source_of, split, trace_ids
from eval.metrics import bcubed, boundary_prf, classification, cohen_kappa, labels, mean, pk, set_prf, windowdiff
from medra.mining.segment import SegParams, boundaries, gap_scores
from medra.mining.topics import MIN_TERM_COUNT, WINDOW as TOPIC_WINDOW

DEVELOPMENT = "development"  # MeDRA's type for a step that no marker opens


# ------------------------------------------------------------- segmenters


def seg_medra(m: Mined, ctx: dict) -> list[int]:
    return m.starts()


def seg_fixed(m: Mined, ctx: dict) -> list[int]:
    return list(range(0, len(m.spans), ctx["fixed_length"]))


def seg_paragraphs(m: Mined, ctx: dict) -> list[int]:
    return [0] + [i for i, f in enumerate(m.features) if i and f.paragraph_break]


def seg_markers(m: Mined, ctx: dict) -> list[int]:
    return [0] + [i for i, f in enumerate(m.features) if i and f.marker_type]


def seg_texttiling(m: Mined, ctx: dict) -> list[int]:
    cohesion_only = SegParams(marker_scale=0.0, paragraph_weight=0.0)
    gaps = gap_scores(m.features, cohesion_only)
    if len(gaps) < 2:
        return [0]
    depths = [g.depth for g in gaps]
    cutoff = statistics.mean(depths) - statistics.stdev(depths) / 2
    return boundaries(gaps, replace(cohesion_only, threshold=cutoff))


def seg_tuned(m: Mined, ctx: dict) -> list[int]:
    params = ctx["tuned"]
    return boundaries(gap_scores(m.features, params), params)


BASELINES = {
    "fixed": ("Tamaño fijo", seg_fixed),
    "paragraphs": ("Solo párrafos", seg_paragraphs),
    "markers": ("Solo marcadores", seg_markers),
    "texttiling": ("TextTiling", seg_texttiling),
    "medra": ("MeDRA (por defecto)", seg_medra),
}


def segmentation_scores(ref: list[int], hyp: list[int], n: int) -> dict:
    p, r, f = boundary_prf(ref, hyp, tolerance=1)
    return {"pk": pk(ref, hyp, n), "windowdiff": windowdiff(ref, hyp, n), "precision": p, "recall": r, "f1": f,
            "segments": len(hyp)}


def fixed_length(annotations: list[Annotation]) -> int:
    """Mean reference segment length (sentences) on the given traces."""
    return max(1, round(mean([a.n_sentences / len(a.starts) for a in annotations])))


# ------------------------------------------------------------- other parts


def step_type_pairs(a: Annotation, m: Mined) -> list[tuple[str, str]]:
    return [(kind, m.features[s].marker_type or DEVELOPMENT) for s, kind in zip(a.starts, a.types)]


def lenient_match(pred: set[str], gold: set[str]) -> tuple[float, float, float]:
    """A predicted and a gold term match if one's words contain the other's
    ("odd number" and "odd"): MeDRA may show the n-gram where the annotator
    wrote the word, or the other way round."""
    def near(x: str, ys: set[str]) -> bool:
        wx = set(x.split())
        return any(wx <= set(y.split()) or set(y.split()) <= wx for y in ys)

    precision = sum(near(p, gold) for p in pred) / len(pred) if pred else 0.0
    recall = sum(near(g, pred) for g in gold) / len(gold) if gold else 0.0
    return precision, recall, (2 * precision * recall / (precision + recall) if precision + recall else 0.0)


def concept_scores(a: Annotation, m: Mined) -> dict:
    gold = {lemma_key(c) for c in a.concepts}
    medra = {node.id for node in m.view.nodes}
    frequent = {t.id for t in m.update.terms[: len(medra) or 16]}  # update.terms is sorted by count
    out = {}
    for name, pred in (("medra", medra), ("frequency", frequent)):
        p, r, f = set_prf(pred, gold)
        lp, lr, lf = lenient_match(pred, gold)
        out[name] = {"precision": p, "recall": r, "f1": f, "lenient_precision": lp, "lenient_recall": lr,
                     "lenient_f1": lf}
    return out


def agglomerative_topics(m: Mined, n_clusters: int) -> list[list[str]]:
    """Average-linkage clustering (cosine) of the terms that Louvain also
    clusters, each described by the sentence windows it appears in: the same
    co-occurrence evidence as the Louvain graph, a different algorithm."""
    counts = {t.id: t.count for t in m.update.terms}
    terms = sorted(t for t, c in counts.items() if c >= MIN_TERM_COUNT)
    st = m.sentence_terms()
    windows = [set().union(*map(set, st[i : i + TOPIC_WINDOW])) for i in range(max(1, len(st) - TOPIC_WINDOW + 1))]
    if len(terms) <= n_clusters or n_clusters < 2:
        return [terms] if terms else []
    x = np.array([[1.0 if t in w else 0.0 for w in windows] for t in terms])
    found = AgglomerativeClustering(n_clusters=n_clusters, metric="cosine", linkage="average").fit_predict(x)
    groups: dict[int, list[str]] = {}
    for term, c in zip(terms, found):
        groups.setdefault(int(c), []).append(term)
    return list(groups.values())


def topic_scores(a: Annotation, m: Mined) -> dict:
    gold = [[lemma_key(t) for t in group] for group in a.topics]
    louvain = [c.term_ids for c in m.update.clusters]
    agglo = agglomerative_topics(m, max(2, len(louvain)))
    return {"louvain": bcubed(gold, louvain), "agglomerative": bcubed(gold, agglo), "n_topics": len(louvain)}


def agreement(first: Annotation, second: Annotation) -> dict:
    """How far two annotators agree on the same trace: segmentation metrics
    with the first as reference, and Cohen's kappa on the step type of each
    sentence (the type of the segment it is in)."""
    n = first.n_sentences
    p, r, f = boundary_prf(first.starts, second.starts, tolerance=1)
    ta = [first.types[i] for i in labels(first.starts, n)]
    tb = [second.types[i] for i in labels(second.starts, n)]
    return {"trace": first.trace_id, "annotators": [first.annotator, second.annotator],
            "pk": pk(first.starts, second.starts, n), "windowdiff": windowdiff(first.starts, second.starts, n),
            "f1": f, "type_kappa": cohen_kappa(ta, tb)}


# ------------------------------------------------------------- driver


def git_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                             check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "backend", "eval"], capture_output=True,
                               text=True).stdout.strip()
        return sha + (" (+ cambios sin commit)" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "desconocido"


def load_tuned(out_dir: Path) -> SegParams | None:
    path = out_dir / "tuned.json"
    if not path.exists():
        return None
    return SegParams(**json.loads(path.read_text(encoding="utf-8"))["params"])


def evaluate(drafts: bool) -> dict:
    annotations = load_all() if drafts else load_all(status="corrected")
    if not annotations:
        raise SystemExit("no corrected annotations yet (use --drafts for a preliminary run)")
    out_dir = RESULTS_DIR / "drafts" if drafts else RESULTS_DIR
    dev_ids, test_ids = split(trace_ids())
    by_id = {a.trace_id: a for a in annotations}
    ctx = {"fixed_length": fixed_length([by_id[i] for i in dev_ids if i in by_id] or annotations),
           "tuned": load_tuned(out_dir)}
    methods = dict(BASELINES)
    if ctx["tuned"]:
        methods["tuned"] = ("MeDRA (ajustado)", seg_tuned)

    per_trace = []
    for a in annotations:
        m = mine(a.trace_id)
        row = {
            "trace": a.trace_id, "source": source_of(a.trace_id), "status": a.status, "annotator": a.annotator,
            "split": "test" if a.trace_id in test_ids else "dev", "sentences": a.n_sentences,
            "reference_segments": len(a.starts),
            "segmentation": {key: segmentation_scores(a.starts, fn(m, ctx), a.n_sentences)
                             for key, (_, fn) in methods.items()},
            "step_types": step_type_pairs(a, m),
            "concepts": concept_scores(a, m) if a.concepts else None,
            "topics": topic_scores(a, m) if a.topics else None,
        }
        per_trace.append(row)

    second = []
    for path in annotation_files():
        if path.name.count(".") == 2:
            b = parse(path)
            if b.trace_id in by_id and (drafts or b.status == "corrected"):
                second.append(agreement(by_id[b.trace_id], b))

    return {
        "date": date.today().isoformat(),
        "commit": git_commit(),
        "preliminary": drafts,
        "annotations": {"n": len(annotations), "corrected": sum(a.status == "corrected" for a in annotations)},
        "split": {"dev": dev_ids, "test": test_ids},
        "fixed_length": ctx["fixed_length"],
        "tuned_params": asdict(ctx["tuned"]) if ctx["tuned"] else None,
        "methods": {key: label for key, (label, _) in methods.items()},
        "per_trace": per_trace,
        "agreement": second,
        "out_dir": str(out_dir),
    }


# ------------------------------------------------------------- report


def _avg(rows: list[dict], path: list[str]) -> float:
    vals = []
    for r in rows:
        v = r
        for p in path:
            v = v.get(p) if isinstance(v, dict) else None
            if v is None:
                break
        if isinstance(v, (int, float)):
            vals.append(v)
    return mean(vals)


def _seg_table(rows: list[dict], methods: dict[str, str]) -> list[str]:
    out = ["| Método | Pk ↓ | WindowDiff ↓ | Precisión | Cobertura | F1 (±1 frase) | Tramos/traza |",
           "|---|---|---|---|---|---|---|"]
    for key, label in methods.items():
        s = lambda m: _avg(rows, ["segmentation", key, m])  # noqa: E731
        out.append(f"| {label} | {s('pk'):.3f} | {s('windowdiff'):.3f} | {s('precision'):.2f} | {s('recall'):.2f} "
                   f"| {s('f1'):.2f} | {s('segments'):.1f} |")
    return out


def report(res: dict) -> str:
    rows = res["per_trace"]
    test = [r for r in rows if r["split"] == "test"]
    untuned = {k: v for k, v in res["methods"].items() if k != "tuned"}
    lines = ["# Resultados de la evaluación de MeDRA", ""]
    if res["preliminary"]:
        lines += ["> **PRELIMINAR.** Calculado sobre anotaciones que incluyen borradores sin corregir "
                  "(`status: draft`). Sirve para probar el código; **no son resultados** y no van a la memoria.", ""]
    lines += [f"Generado con `python -m eval.run{' --drafts' if res['preliminary'] else ''}` el {res['date']}, "
              f"commit {res['commit']}. Anotaciones: {res['annotations']['n']} "
              f"({res['annotations']['corrected']} corregidas). Trazas en inglés: "
              f"{sum(r['source'] == 'deepseek' for r in rows)} de DeepSeek y "
              f"{sum(r['source'] == 'openthoughts' for r in rows)} de OpenThoughts (DeepSeek-R1).", ""]
    ref_len = mean([r["sentences"] / r["reference_segments"] for r in rows])
    lines += [f"Referencia: {mean([r['reference_segments'] for r in rows]):.1f} tramos por traza, "
              f"{ref_len:.1f} frases por tramo de media. Tamaño fijo = {res['fixed_length']} frases "
              f"(media de la referencia en dev).", ""]

    lines += ["## Segmentación (todas las trazas)", ""] + _seg_table(rows, untuned) + [""]
    for source, label in (("deepseek", "DeepSeek"), ("openthoughts", "OpenThoughts")):
        sub = [r for r in rows if r["source"] == source]
        if sub:
            lines += [f"### Solo {label} ({len(sub)} trazas)", ""] + _seg_table(sub, untuned) + [""]
    if test:
        lines += [f"## Segmentación en test ({len(test)} trazas)", ""]
        if res["tuned_params"]:
            lines += [f"Parámetros ajustados en dev con `python -m eval.tune`: `{res['tuned_params']}`.", ""]
        lines += _seg_table(test, res["methods"]) + [""]

    pairs = [tuple(p) for r in rows for p in r["step_types"]]
    medra_types = classification(pairs)
    majority = classification([(g, DEVELOPMENT) for g, _ in pairs])
    lines += ["## Tipo de paso (en las fronteras de la referencia)", "",
              f"{medra_types['n']} pasos. MeDRA: exactitud {medra_types['accuracy']:.2f}, F1 macro "
              f"{medra_types['macro_f1']:.2f}. Línea base (siempre «development»): exactitud "
              f"{majority['accuracy']:.2f}, F1 macro {majority['macro_f1']:.2f}.", "",
              "| Tipo | Precisión | Cobertura | F1 | Casos |", "|---|---|---|---|---|"]
    for c, v in medra_types["per_class"].items():
        lines.append(f"| {c} | {v['precision']:.2f} | {v['recall']:.2f} | {v['f1']:.2f} | {v['support']} |")
    lines += ["", "Confusión (referencia → MeDRA): " + ", ".join(f"{k}: {n}" for k, n in
                                                            medra_types["confusion"].items()), ""]

    with_concepts = [r for r in rows if r["concepts"]]
    if with_concepts:
        lines += ["## Conceptos clave (burbujas)", "",
                  "| Método | Precisión | Cobertura | F1 | F1 flexible |", "|---|---|---|---|---|"]
        for key, label in (("medra", "MeDRA (burbujas)"), ("frequency", "Frecuencia (top-16)")):
            c = lambda m: _avg(with_concepts, ["concepts", key, m])  # noqa: E731
            lines.append(f"| {label} | {c('precision'):.2f} | {c('recall'):.2f} | {c('f1'):.2f} "
                         f"| {c('lenient_f1'):.2f} |")
        lines += ["", "Flexible: cuenta como acierto si las palabras de un término contienen las del otro "
                  "(«odd number» y «odd»).", ""]

    with_topics = [r for r in rows if r["topics"]]
    if with_topics:
        lines += ["## Temas", "", "| Agrupación | Precisión B³ | Cobertura B³ | F1 B³ | Términos anotados encontrados |",
                  "|---|---|---|---|---|"]
        for key, label in (("louvain", "Louvain (MeDRA)"), ("agglomerative", "Aglomerativa (coseno, media)")):
            t = lambda m: _avg(with_topics, ["topics", key, m])  # noqa: E731
            lines.append(f"| {label} | {t('precision'):.2f} | {t('recall'):.2f} | {t('f1'):.2f} "
                         f"| {t('coverage'):.0%} |")
        lines.append("")

    if res["agreement"]:
        lines += ["## Acuerdo entre anotadores", "", "| Traza | Anotadores | Pk | WindowDiff | F1 (±1) | κ tipos |",
                  "|---|---|---|---|---|---|"]
        for g in res["agreement"]:
            lines.append(f"| {g['trace']} | {' / '.join(g['annotators'])} | {g['pk']:.3f} | {g['windowdiff']:.3f} "
                         f"| {g['f1']:.2f} | {g['type_kappa']:.2f} |")
        lines.append("")

    lines += ["## Por traza (MeDRA por defecto)", "", "| Traza | Fuente | Split | Frases | Tramos ref. | Tramos MeDRA "
              "| Pk | WindowDiff |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        s = r["segmentation"]["medra"]
        lines.append(f"| {r['trace']} | {r['source']} | {r['split']} | {r['sentences']} | {r['reference_segments']} "
                     f"| {s['segments']} | {s['pk']:.3f} | {s['windowdiff']:.3f} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate MeDRA against the hand annotations.")
    parser.add_argument("--drafts", action="store_true", help="include draft annotations (preliminary run)")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles default to cp1252
    res = evaluate(args.drafts)
    out_dir = Path(res.pop("out_dir"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = report(res)
    (out_dir / "results.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"written to {out_dir}")


if __name__ == "__main__":
    main()
