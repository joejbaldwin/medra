"""Train and evaluate the step-type classifier (backend/medra/mining/steptypes.py).

    python -m eval.steptypes      # choose settings on dev, report on test, write the model

1. Settings: C and class weighting of the logistic regression, chosen by
   5-fold cross-validation on the dev traces, grouped by trace (the steps of
   one trace never sit on both sides), maximising macro-F1.
2. Test: a model trained on all dev steps with those settings, scored on the
   test traces against the marker rule and the majority baseline (always
   "development"). Steps are taken at the reference boundaries, as for the
   rule in eval.run, so segmentation errors do not count here.
3. Leave-one-trace-out over all annotated traces, with the same settings: a
   second estimate that does not depend on one dev/test split.
4. The shipped model: trained on every annotated trace except the two of the
   user study (STUDY_TRACES), so the study shows labels the model has not seen
   in either condition. Written to backend/medra/mining/models/.

Writes eval/results/steptypes.md and steptypes.json.
"""

from __future__ import annotations

import json
from datetime import date
from itertools import product

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from eval.annotations import Annotation, load_all
from eval.common import RESULTS_DIR, Mined, git_commit, mine, split, trace_ids
from eval.metrics import classification
from medra.mining.steptypes import DEVELOPMENT, MODEL_PATH, StepInput, StepTypeModel, tokens

STUDY_TRACES = ("en-log-pets", "en-log-knights")  # frontend/src/studyPlan.ts
GRID = {"C": [0.3, 1, 3, 10, 30, 100], "class_weight": [None, "balanced"]}
FOLDS = 5
MIN_DF = 2  # a feature must occur in at least two training steps


Labelled = list[tuple[StepInput, str, str]]  # (step, gold type, trace id)


def steps_of(a: Annotation, m: Mined) -> Labelled:
    """The annotated steps of one trace, as the classifier sees them."""
    out = []
    for k, (first, kind) in enumerate(zip(a.starts, a.types)):
        last = (a.starts[k + 1] if k + 1 < len(a.starts) else len(m.spans)) - 1
        opener = m.text[m.spans[first][0] : m.spans[first][1]]
        text = m.text[m.spans[first][0] : m.spans[last][1]]
        out.append((StepInput(opener, text, m.features[first].marker_type, k == 0), kind, a.trace_id))
    return out


def fit_sklearn(data: Labelled, C: float, class_weight: str | None) -> tuple[TfidfVectorizer, LogisticRegression]:
    vec = TfidfVectorizer(analyzer=tokens, sublinear_tf=True, min_df=MIN_DF)
    X = vec.fit_transform([s for s, _, _ in data])
    clf = LogisticRegression(C=C, class_weight=class_weight, max_iter=5000)
    clf.fit(X, [g for _, g, _ in data])
    return vec, clf


def fit(data: Labelled, C: float, class_weight: str | None) -> StepTypeModel:
    """Train, and export what prediction needs (StepTypeModel computes the
    same TF-IDF and scores; eval/test_steptypes.py checks it)."""
    vec, clf = fit_sklearn(data, C, class_weight)
    return StepTypeModel({
        "classes": [str(c) for c in clf.classes_],
        "vocabulary": {t: int(j) for t, j in sorted(vec.vocabulary_.items(), key=lambda kv: kv[1])},
        "idf": [float(v) for v in vec.idf_],
        "coef": [[round(float(w), 6) for w in row] for row in clf.coef_],
        "intercept": [round(float(b), 6) for b in clf.intercept_],
    })


def predict(model: StepTypeModel, data: Labelled) -> list[tuple[str, str]]:
    return [(g, model.predict(s)) for s, g, _ in data]


def rule(data: Labelled) -> list[tuple[str, str]]:
    return [(g, s.marker_type or DEVELOPMENT) for s, g, _ in data]


def majority(data: Labelled) -> list[tuple[str, str]]:
    return [(g, DEVELOPMENT) for _, g, _ in data]


def choose(dev: Labelled) -> tuple[dict, list[dict]]:
    """Settings with the best grouped-CV macro-F1 on dev (ties: higher accuracy)."""
    groups = [t for _, _, t in dev]
    folds = list(GroupKFold(n_splits=FOLDS).split(dev, groups=groups))
    grid = []
    for C, cw in product(GRID["C"], GRID["class_weight"]):
        pairs = []
        for train, held in folds:
            model = fit([dev[i] for i in train], C, cw)
            pairs += predict(model, [dev[i] for i in held])
        c = classification(pairs)
        grid.append({"C": C, "class_weight": cw, "accuracy": c["accuracy"], "macro_f1": c["macro_f1"]})
    best = max(grid, key=lambda r: (r["macro_f1"], r["accuracy"]))
    return {"C": best["C"], "class_weight": best["class_weight"]}, grid


def top_features(model: StepTypeModel, k: int = 8) -> dict[str, list[str]]:
    """The k features with the largest positive weight for each type."""
    names = sorted(model.vocabulary, key=model.vocabulary.__getitem__)
    return {c: [names[j] for j in sorted(range(len(names)), key=lambda j: -model.coef[i][j])[:k]]
            for i, c in enumerate(model.classes)}


def labelled(annotations: list[Annotation]) -> dict[str, Labelled]:
    return {a.trace_id: steps_of(a, mine(a.trace_id)) for a in annotations}


def evaluate(by_trace: dict[str, Labelled], dev_ids: list[str], test_ids: list[str]) -> dict:
    """Steps 1-3 of the module docstring."""
    dev = [x for t in dev_ids if t in by_trace for x in by_trace[t]]
    test = [x for t in test_ids if t in by_trace for x in by_trace[t]]
    settings, grid = choose(dev)
    model = fit(dev, **settings)
    loto = []
    for held in by_trace:
        train = [x for t, xs in by_trace.items() if t != held for x in xs]
        loto += predict(fit(train, **settings), by_trace[held])
    everything = [x for xs in by_trace.values() for x in xs]
    return {
        "settings": settings,
        "grid": grid,
        "dev_steps": len(dev),
        "test": {"classifier": classification(predict(model, test)), "rule": classification(rule(test)),
                 "majority": classification(majority(test))},
        "loto": {"classifier": classification(loto), "rule": classification(rule(everything)),
                 "majority": classification(majority(everything))},
        "top_features": top_features(model),
        "test_predictions": {t: [p for _, p in predict(model, by_trace[t])] for t in test_ids if t in by_trace},
    }


def report(res: dict) -> list[str]:
    """The step-type section of the report (also used by eval.run)."""
    t, lo = res["test"], res["loto"]
    s = res["settings"]
    lines = [
        "## Tipo de paso (en las fronteras de la referencia)", "",
        f"Clasificador: TF-IDF (palabras iniciales, palabras del tramo, marcador del léxico, primer tramo) y "
        f"regresión logística, C = {s['C']}, pesos de clase {s['class_weight'] or 'ninguno'} (elegidos por "
        f"validación cruzada agrupada por traza en dev, {res['dev_steps']} pasos). Regla: el marcador que abre "
        "el tramo, «development» si no hay.", "",
        "| Método | Test: exactitud | Test: F1 macro | Dejar-una-traza-fuera: exactitud | F1 macro |",
        "|---|---|---|---|---|",
    ]
    for key, label in (("classifier", "Clasificador"), ("rule", "Regla de marcadores"),
                       ("majority", "Siempre «development»")):
        lines.append(f"| {label} | {t[key]['accuracy']:.2f} | {t[key]['macro_f1']:.2f} "
                     f"| {lo[key]['accuracy']:.2f} | {lo[key]['macro_f1']:.2f} |")
    lines += ["", f"Test: {t['classifier']['n']} pasos. Dejar-una-traza-fuera: {lo['classifier']['n']} pasos "
              "(la regla y la línea base no se entrenan: son las mismas trazas).", "",
              "Por tipo, en test:", "",
              "| Tipo | Clasificador P | R | F1 | Regla P | R | F1 | Casos |", "|---|---|---|---|---|---|---|---|"]
    for c, v in t["classifier"]["per_class"].items():
        r = t["rule"]["per_class"][c]
        lines.append(f"| {c} | {v['precision']:.2f} | {v['recall']:.2f} | {v['f1']:.2f} "
                     f"| {r['precision']:.2f} | {r['recall']:.2f} | {r['f1']:.2f} | {v['support']} |")
    lines += ["", "Confusión del clasificador en test (referencia → predicción): " + ", ".join(
        f"{k}: {n}" for k, n in t["classifier"]["confusion"].items()), ""]
    return lines


def main() -> None:
    annotations = load_all(status="corrected")
    by_trace = labelled(annotations)
    dev_ids, test_ids = split(trace_ids())
    res = evaluate(by_trace, dev_ids, test_ids)

    shipped_on = sorted(t for t in by_trace if t not in STUDY_TRACES)
    shipped = fit([x for t in shipped_on for x in by_trace[t]], **res["settings"])
    commit = git_commit()
    data = {
        "classes": shipped.classes, "vocabulary": shipped.vocabulary, "idf": shipped.idf,
        "coef": shipped.coef, "intercept": shipped.intercept,
        "meta": {"trained": date.today().isoformat(), "commit": commit, "settings": res["settings"],
                 "min_df": MIN_DF, "traces": shipped_on, "steps": sum(len(by_trace[t]) for t in shipped_on),
                 "excluded": list(STUDY_TRACES), "script": "python -m eval.steptypes"},
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    res.update({"date": date.today().isoformat(), "commit": commit, "shipped": data["meta"]})
    (RESULTS_DIR / "steptypes.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    lines = [f"# Clasificador de tipo de paso ({res['date']}, commit {commit})", ""] + report(res)
    lines += ["## Selección en dev (validación cruzada agrupada, 5 particiones)", "",
              "| C | Pesos de clase | Exactitud | F1 macro |", "|---|---|---|---|"]
    lines += [f"| {g['C']} | {g['class_weight'] or 'ninguno'} | {g['accuracy']:.2f} | {g['macro_f1']:.2f} |"
              for g in res["grid"]]
    lines += ["", "## Rasgos con más peso (modelo entrenado en dev)", "",
              "o1: primera palabra; o: palabras iniciales; b: palabras del tramo; m: marcador del léxico.", ""]
    lines += [f"- **{c}**: " + ", ".join(f"`{f}`" for f in fs) for c, fs in res["top_features"].items()]
    lines += ["", "## Modelo instalado", "", f"Entrenado en {len(shipped_on)} trazas ({data['meta']['steps']} pasos), "
              f"todas las anotadas salvo las dos de la prueba con usuarios ({', '.join(STUDY_TRACES)}), con los "
              f"ajustes de dev. Archivo: backend/medra/mining/models/{MODEL_PATH.name}.", ""]
    (RESULTS_DIR / "steptypes.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
