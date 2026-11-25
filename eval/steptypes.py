"""Train and evaluate the step-type classifier (backend/medra/mining/steptypes.py).

    python -m eval.steptypes      # choose settings on dev, report on test, write the model

Training data: the dev traces plus the extra annotated traces of eval/train/
(the "extra" set, only ever used for training). The 11 test traces are the
same as for every other result, so the numbers stay comparable.

1. Settings: C and class weighting of the logistic regression, chosen by
   5-fold cross-validation over the dev traces, grouped by trace (the steps
   of one trace never sit on both sides), maximising macro-F1. The extra set
   is added to the training side of every fold and never scored.
2. Test: a model trained on dev + extra with those settings, scored on the
   test traces against a model trained on dev only (its own settings), the
   marker rule and the majority baseline (always "development"). Steps are
   taken at the reference boundaries, so segmentation errors do not count.
3. Learning curve: test scores as the number of extra traces grows (random
   subsets, fixed seed, the settings of step 1).
4. Leave-one-trace-out over the 30 evaluation traces (each predicted by a
   model trained on the other 29 + extra): a second estimate that does not
   depend on one dev/test split.
5. The shipped model: trained on every evaluation trace except the two of
   the user study (STUDY_TRACES) plus the extra set, so the study shows
   labels the model has not seen in either condition. Written to
   backend/medra/mining/models/.

Writes eval/results/steptypes.md and steptypes.json.
"""

from __future__ import annotations

import json
import random
from datetime import date
from itertools import product

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from eval.annotations import Annotation, load_all
from eval.common import RESULTS_DIR, TRAIN_ANNOTATIONS_DIR, Mined, git_commit, mine, split, trace_ids
from eval.metrics import classification
from medra.mining.steptypes import DEVELOPMENT, MODEL_PATH, StepInput, StepTypeModel, tokens

STUDY_TRACES = ("en-log-pets", "en-log-knights")  # frontend/src/studyPlan.ts
GRID = {"C": [0.3, 1, 3, 10, 30, 100], "class_weight": [None, "balanced"]}
FOLDS = 5
MIN_DF = 2  # a feature must occur in at least two training steps
CURVE = [0, 25, 50, 100, 150, 200]  # extra traces in the learning curve (plus all of them)


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


def choose(dev: Labelled, extra: Labelled) -> tuple[dict, list[dict]]:
    """Settings with the best grouped-CV macro-F1 on dev (ties: higher accuracy).
    The extra steps are added to the training side of every fold."""
    groups = [t for _, _, t in dev]
    folds = list(GroupKFold(n_splits=FOLDS).split(dev, groups=groups))
    grid = []
    for C, cw in product(GRID["C"], GRID["class_weight"]):
        pairs = []
        for train, held in folds:
            model = fit([dev[i] for i in train] + extra, C, cw)
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


def extra_traces() -> dict[str, Labelled]:
    """The training-only annotated traces (eval/train/)."""
    return labelled(load_all(status="corrected", directory=TRAIN_ANNOTATIONS_DIR))


def evaluate(by_trace: dict[str, Labelled], dev_ids: list[str], test_ids: list[str],
             extra_by_trace: dict[str, Labelled] | None = None) -> dict:
    """Steps 1-4 of the module docstring."""
    extra_by_trace = extra_by_trace or {}
    extra = [x for xs in extra_by_trace.values() for x in xs]
    dev = [x for t in dev_ids if t in by_trace for x in by_trace[t]]
    test = [x for t in test_ids if t in by_trace for x in by_trace[t]]

    settings, grid = choose(dev, extra)
    model = fit(dev + extra, **settings)
    dev_settings = choose(dev, [])[0] if extra else settings
    dev_model = fit(dev, **dev_settings) if extra else model

    curve = []
    if extra:
        order = random.Random(0).sample(sorted(extra_by_trace), len(extra_by_trace))
        for n in [k for k in CURVE if k < len(order)] + [len(order)]:
            subset = [x for t in order[:n] for x in extra_by_trace[t]]
            c = classification(predict(fit(dev + subset, **settings), test))
            curve.append({"extra_traces": n, "train_steps": len(dev) + len(subset),
                          "accuracy": c["accuracy"], "macro_f1": c["macro_f1"]})

    loto = []
    for held in by_trace:
        train = [x for t, xs in by_trace.items() if t != held for x in xs] + extra
        loto += predict(fit(train, **settings), by_trace[held])
    everything = [x for xs in by_trace.values() for x in xs]
    return {
        "settings": settings,
        "dev_settings": dev_settings,
        "grid": grid,
        "dev_steps": len(dev),
        "extra_traces": len(extra_by_trace),
        "extra_steps": len(extra),
        "test": {"classifier": classification(predict(model, test)),
                 "dev_only": classification(predict(dev_model, test)),
                 "rule": classification(rule(test)), "majority": classification(majority(test))},
        "curve": curve,
        "loto": {"classifier": classification(loto), "rule": classification(rule(everything)),
                 "majority": classification(majority(everything))},
        "top_features": top_features(model),
        "test_predictions": {t: [p for _, p in predict(model, by_trace[t])] for t in test_ids if t in by_trace},
    }


def report(res: dict) -> list[str]:
    """The step-type section of the report (also used by eval.run)."""
    t, lo = res["test"], res["loto"]
    s, ds = res["settings"], res["dev_settings"]

    def weights(x: dict) -> str:
        return x["class_weight"] or "ninguno"

    lines = [
        "## Tipo de paso (en las fronteras de la referencia)", "",
        "Clasificador: TF-IDF (palabras iniciales, palabras del tramo, marcador del léxico, primer tramo) y "
        f"regresión logística, entrenada con los {res['dev_steps']} pasos de dev más {res['extra_steps']} pasos de "
        f"{res['extra_traces']} trazas anotadas solo para entrenar (eval/train/); C = {s['C']}, pesos de clase "
        f"{weights(s)}, elegidos por validación cruzada agrupada por traza en dev. «Solo dev»: el mismo modelo "
        f"entrenado solo con dev (C = {ds['C']}, pesos {weights(ds)}). Regla: el marcador que abre el tramo, "
        "«development» si no hay.", "",
        "| Método | Test: exactitud | Test: F1 macro |", "|---|---|---|",
    ]
    for key, label in (("classifier", f"Clasificador (dev + {res['extra_traces']} trazas)"),
                       ("dev_only", "Clasificador (solo dev)"), ("rule", "Regla de marcadores"),
                       ("majority", "Siempre «development»")):
        lines.append(f"| {label} | {t[key]['accuracy']:.2f} | {t[key]['macro_f1']:.2f} |")
    lines += ["", f"Test: {t['classifier']['n']} pasos de 11 trazas. Dejando una traza fuera (cada una de las 30 "
              "trazas de evaluación con un modelo entrenado con las otras 29 más las trazas extra; "
              f"{lo['classifier']['n']} pasos): clasificador {lo['classifier']['accuracy']:.2f} de exactitud y "
              f"{lo['classifier']['macro_f1']:.2f} de F1 macro; regla {lo['rule']['accuracy']:.2f} y "
              f"{lo['rule']['macro_f1']:.2f}.", ""]
    if res["curve"]:
        lines += ["Curva de aprendizaje (test, con más trazas extra en el entrenamiento):", "",
                  "| Trazas extra | Pasos de entrenamiento | Exactitud | F1 macro |", "|---|---|---|---|"]
        lines += [f"| {c['extra_traces']} | {c['train_steps']} | {c['accuracy']:.2f} | {c['macro_f1']:.2f} |"
                  for c in res["curve"]]
        lines.append("")
    lines += ["Por tipo, en test:", "",
              "| Tipo | Clasificador P | R | F1 | Solo dev F1 | Regla F1 | Casos |", "|---|---|---|---|---|---|---|"]
    for c, v in t["classifier"]["per_class"].items():
        d, r = t["dev_only"]["per_class"][c], t["rule"]["per_class"][c]
        lines.append(f"| {c} | {v['precision']:.2f} | {v['recall']:.2f} | {v['f1']:.2f} | {d['f1']:.2f} "
                     f"| {r['f1']:.2f} | {v['support']} |")
    lines += ["", "Confusión del clasificador en test (referencia → predicción): " + ", ".join(
        f"{k}: {n}" for k, n in t["classifier"]["confusion"].items()), ""]
    return lines


def main() -> None:
    annotations = load_all(status="corrected")
    by_trace = labelled(annotations)
    extra = extra_traces()
    dev_ids, test_ids = split(trace_ids())
    res = evaluate(by_trace, dev_ids, test_ids, extra)

    shipped_on = sorted(t for t in by_trace if t not in STUDY_TRACES)
    shipped = fit([x for t in shipped_on for x in by_trace[t]] + [x for xs in extra.values() for x in xs],
                  **res["settings"])
    commit = git_commit()
    data = {
        "classes": shipped.classes, "vocabulary": shipped.vocabulary, "idf": shipped.idf,
        "coef": shipped.coef, "intercept": shipped.intercept,
        "meta": {"trained": date.today().isoformat(), "commit": commit, "settings": res["settings"],
                 "min_df": MIN_DF, "traces": shipped_on, "extra_traces": len(extra),
                 "steps": sum(len(by_trace[t]) for t in shipped_on) + res["extra_steps"],
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
    lines += ["", "## Rasgos con más peso (modelo entrenado en dev + trazas extra)", "",
              "o1: primera palabra; o: palabras iniciales; b: palabras del tramo; m: marcador del léxico.", ""]
    lines += [f"- **{c}**: " + ", ".join(f"`{f}`" for f in fs) for c, fs in res["top_features"].items()]
    lines += ["", "## Modelo instalado", "", f"Entrenado en {len(shipped_on)} trazas de evaluación (todas salvo las "
              f"dos de la prueba con usuarios: {', '.join(STUDY_TRACES)}) más las {len(extra)} trazas extra, "
              f"{data['meta']['steps']} pasos, con los ajustes elegidos en dev. Archivo: "
              f"backend/medra/mining/models/{MODEL_PATH.name}.", ""]
    (RESULTS_DIR / "steptypes.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
