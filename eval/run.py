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
- Step types: the type given to each annotated step (at the reference
  boundaries, so segmentation errors do not count twice) by the classifier
  of eval/steptypes.py, trained on dev and scored on test, against the old
  marker rule and the majority baseline.
- Concepts: the bubbles of the final view against the annotated concepts,
  both as lemma keys. Baseline: the 16 most frequent terms.
- Topics: B-cubed F1 of MeDRA's Louvain topics against the annotated topics,
  and of agglomerative clustering on the same terms (the comparison left open
  in build plan §4.4).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict, replace
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from eval.annotations import Annotation, load_all
from eval.common import RESULTS_DIR, Mined, git_commit, lemma_key, mine, source_of, split, trace_ids
from eval.metrics import bcubed, boundary_prf, mean, pk, set_prf, windowdiff
from eval.steptypes import evaluate as evaluate_step_types, report as step_type_report, steps_of
from eval.tune import DECISION_GRID
from medra.mining.segment import SegParams, boundaries, gap_scores
from medra.mining.topics import MIN_TERM_COUNT, WINDOW as TOPIC_WINDOW


# ------------------------------------------------------------- segmenters


def seg_medra(m: Mined, ctx: dict) -> list[int]:
    return m.starts()


def seg_fixed(m: Mined, ctx: dict) -> list[int]:
    return list(range(0, len(m.spans), ctx["fixed_length"]))


def seg_paragraphs(m: Mined, ctx: dict) -> list[int]:
    return [0] + [i for i, f in enumerate(m.features) if i and f.paragraph_break]


def min_length(starts: list[int], min_sentences: int) -> list[int]:
    """Drop every start closer than min_sentences to the last one kept: the
    same greedy rule as the segmenter's own min_sentences."""
    kept = [starts[0]]
    for s in starts[1:]:
        if s - kept[-1] >= min_sentences:
            kept.append(s)
    return kept


def seg_paragraphs_min(m: Mined, ctx: dict) -> list[int]:
    # Ablation for the tuned segmenter, which learned "paragraph breaks + a
    # long minimum": this is that rule alone, without cohesion or markers.
    return min_length(seg_paragraphs(m, ctx), ctx["paragraph_min"])


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


DEV_TUNED = {"paragraphs_min", "tuned"}  # a parameter chosen on dev: reported on test only

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


def paragraph_min(annotations: list[Annotation]) -> int:
    """The minimum segment length for seg_paragraphs_min, chosen on the given
    (dev) traces by mean WindowDiff over the values eval.tune searches, so the
    ablation gets the same tuning budget for that parameter as MeDRA."""
    def score(k: int) -> float:
        return mean([windowdiff(a.starts, min_length(seg_paragraphs(mine(a.trace_id), {}), k), a.n_sentences)
                     for a in annotations])
    return min(DECISION_GRID["min_sentences"], key=lambda k: (score(k), k))


# ------------------------------------------------------------- other parts


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


# ------------------------------------------------------------- driver




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
    dev = [by_id[i] for i in dev_ids if i in by_id] or annotations
    ctx = {"fixed_length": fixed_length(dev), "paragraph_min": paragraph_min(dev), "tuned": load_tuned(out_dir)}
    methods = dict(BASELINES)
    methods["paragraphs_min"] = (f"Párrafos + mín. {ctx['paragraph_min']} frases", seg_paragraphs_min)
    if ctx["tuned"]:
        methods["tuned"] = ("MeDRA (ajustado)", seg_tuned)

    per_trace = []
    steps = {}
    for a in annotations:
        m = mine(a.trace_id)
        steps[a.trace_id] = steps_of(a, m)
        row = {
            "trace": a.trace_id, "source": source_of(a.trace_id), "status": a.status, "annotator": a.annotator,
            "split": "test" if a.trace_id in test_ids else "dev", "sentences": a.n_sentences,
            "reference_segments": len(a.starts),
            "segmentation": {key: segmentation_scores(a.starts, fn(m, ctx), a.n_sentences)
                             for key, (_, fn) in methods.items()},
            "concepts": concept_scores(a, m) if a.concepts else None,
            "topics": topic_scores(a, m) if a.topics else None,
        }
        per_trace.append(row)

    return {
        "date": date.today().isoformat(),
        "commit": git_commit(),
        "preliminary": drafts,
        "annotations": {"n": len(annotations), "corrected": sum(a.status == "corrected" for a in annotations)},
        "split": {"dev": dev_ids, "test": test_ids},
        "fixed_length": ctx["fixed_length"],
        "paragraph_min": ctx["paragraph_min"],
        "tuned_params": asdict(ctx["tuned"]) if ctx["tuned"] else None,
        "methods": {key: label for key, (label, _) in methods.items()},
        "per_trace": per_trace,
        "step_types": evaluate_step_types(steps, dev_ids, test_ids),
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
    # Methods with a parameter chosen on dev are only reported on test.
    untuned = {k: v for k, v in res["methods"].items() if k not in DEV_TUNED}
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
        lines += [f"«Párrafos + mín.»: un corte en cada línea en blanco, descartando los que quedan a menos de "
                  f"{res['paragraph_min']} frases del anterior (mínimo elegido en dev). Es la ablación del "
                  "segmentador ajustado: la misma regla sin cohesión ni marcadores.", ""]
        lines += _seg_table(test, res["methods"]) + [""]
        for source, label in (("deepseek", "DeepSeek"), ("openthoughts", "OpenThoughts")):
            sub = [r for r in test if r["source"] == source]
            if sub:
                lines += [f"### Test, solo {label} ({len(sub)} trazas)", ""] + _seg_table(sub, res["methods"]) + [""]

    lines += step_type_report(res["step_types"])

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
