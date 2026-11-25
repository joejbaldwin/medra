"""Train and evaluate the step-type classifier (backend/medra/mining/steptypes.py).

    python -m eval.steptypes      # choose settings on train, report on test, write the model

Data: every annotated trace, the 30 evaluation traces (eval/annotations/)
and the training traces (eval/train/), 302 in all. They get their own fixed
80/20 train/test split (the rule of eval.common.split: seed 0, stratified by
source model), separate from the 19/11 dev/test split of the 30 evaluation
traces that the segmentation, concept and topic results use. Steps are taken
at the reference boundaries, so segmentation errors do not count.

1. Settings: C and class weighting of the logistic regression, chosen by
   5-fold cross-validation over the train traces, grouped by trace (the steps
   of one trace never sit on both sides), maximising macro-F1.
2. Test: the model trained on the train traces with those settings, scored on
   the test traces against two baselines that need no training: the marker
   rule (the type of the lexicon marker that opens the step, "development"
   if none; MeDRA's first version) and the majority class (always
   "development").
3. Learning curve: test scores when the model is trained on random subsets
   of the train traces (fixed seed, the settings of step 1).
4. 10-fold cross-validation over all the traces, grouped by trace: a second
   estimate that does not depend on one train/test split.
5. The shipped model: trained on every trace except the two of the user
   study (STUDY_TRACES), so the study shows labels the model has not seen.
   Written to backend/medra/mining/models/.

Writes eval/results/steptypes.md and steptypes.json (eval.run copies the
step-type section into results.md).
"""

from __future__ import annotations

import json
import random
import sys
from datetime import date
from itertools import product

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from eval.annotations import Annotation, load_all
from eval.common import RESULTS_DIR, TRAIN_ANNOTATIONS_DIR, Mined, git_commit, mine, source_of, split
from eval.metrics import classification
from medra.mining.steptypes import DEVELOPMENT, MODEL_PATH, StepInput, StepTypeModel, tokens

STUDY_TRACES = ("en-log-pets", "en-log-knights")  # frontend/src/studyPlan.ts
TEST_SHARE = 0.2  # 80/20 train/test over the traces
GRID = {"C": [0.3, 1, 3, 10, 30, 100], "class_weight": [None, "balanced"]}
FOLDS = 5  # settings, within train
CV_FOLDS = 10  # second estimate, over every trace
MIN_DF = 2  # a feature must occur in at least two training steps
CURVE = [25, 50, 100, 150, 200]  # train traces in the learning curve (plus all of them)


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


def choose(train: Labelled) -> tuple[dict, list[dict]]:
    """Settings with the best grouped-CV macro-F1 on train (ties: higher accuracy)."""
    folds = list(GroupKFold(n_splits=FOLDS).split(train, groups=[t for _, _, t in train]))
    grid = []
    for C, cw in product(GRID["C"], GRID["class_weight"]):
        pairs = []
        for fit_on, held in folds:
            pairs += predict(fit([train[i] for i in fit_on], C, cw), [train[i] for i in held])
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


def all_traces() -> dict[str, Labelled]:
    """Every annotated trace: the evaluation set and eval/train/."""
    by_trace = labelled(load_all(status="corrected"))
    by_trace.update(labelled(load_all(status="corrected", directory=TRAIN_ANNOTATIONS_DIR)))
    return by_trace


def step_split(ids: list[str]) -> tuple[list[str], list[str]]:
    """The classifier's fixed train/test split of the traces."""
    return split(ids, test_share=TEST_SHARE)


def evaluate(by_trace: dict[str, Labelled]) -> dict:
    """Steps 1-4 of the module docstring."""
    train_ids, test_ids = step_split(sorted(by_trace))
    train = [x for t in train_ids for x in by_trace[t]]
    test = [x for t in test_ids for x in by_trace[t]]

    settings, grid = choose(train)
    model = fit(train, **settings)

    curve = []
    order = random.Random(0).sample(train_ids, len(train_ids))
    for n in [k for k in CURVE if k < len(order)] + [len(order)]:
        subset = [x for t in order[:n] for x in by_trace[t]]
        c = classification(predict(fit(subset, **settings), test))
        curve.append({"train_traces": n, "train_steps": len(subset),
                      "accuracy": c["accuracy"], "macro_f1": c["macro_f1"]})

    everything = [x for t in sorted(by_trace) for x in by_trace[t]]
    cv = []
    for fit_on, held in GroupKFold(n_splits=CV_FOLDS).split(everything, groups=[t for _, _, t in everything]):
        cv += predict(fit([everything[i] for i in fit_on], **settings), [everything[i] for i in held])

    by_source = {}
    for source in ("deepseek", "openthoughts"):
        sub = [x for x in test if source_of(x[2]) == source]
        by_source[source] = {"traces": sum(source_of(t) == source for t in test_ids),
                             "classifier": classification(predict(model, sub)), "rule": classification(rule(sub))}
    return {
        "test_share": TEST_SHARE,
        "split": {"train": train_ids, "test": test_ids},
        "train_traces": len(train_ids), "train_steps": len(train),
        "test_traces": len(test_ids), "test_steps": len(test),
        "settings": settings,
        "grid": grid,
        "test": {"classifier": classification(predict(model, test)),
                 "rule": classification(rule(test)), "majority": classification(majority(test))},
        "test_by_source": by_source,
        "curve": curve,
        "cv": {"folds": CV_FOLDS, "traces": len(by_trace), "classifier": classification(cv),
               "rule": classification(rule(everything)), "majority": classification(majority(everything))},
        "top_features": top_features(model),
        "test_predictions": {t: [p for _, p in predict(model, by_trace[t])] for t in test_ids},
    }


def report(res: dict) -> list[str]:
    """The step-type section of the report (also copied into results.md by eval.run)."""
    t, cv, s = res["test"], res["cv"], res["settings"]
    lines = [
        "## Tipo de paso (en las fronteras de la referencia)", "",
        "Clasificador: TF-IDF (palabras iniciales, palabras del tramo, marcador del léxico, primer tramo) y "
        f"regresión logística; C = {s['C']}, pesos de clase {s['class_weight'] or 'ninguno'}, elegidos por "
        "validación cruzada agrupada por traza en train. Datos: las "
        f"{cv['traces']} trazas anotadas (las 30 de evaluación y las de eval/train/), divididas en train "
        f"({res['train_traces']} trazas, {res['train_steps']} pasos) y test ({res['test_traces']} trazas, "
        f"{res['test_steps']} pasos): {round(100 * (1 - res['test_share']))}/{round(100 * res['test_share'])}, "
        "semilla 0, estratificado por modelo de origen. Regla de marcadores: el tipo del marcador que abre el "
        "tramo, «development» si no hay (la primera versión de MeDRA).", "",
        "| Método | Test: exactitud | Test: F1 macro |", "|---|---|---|",
    ]
    for key, label in (("classifier", "Clasificador"), ("rule", "Regla de marcadores"),
                       ("majority", "Siempre «development»")):
        lines.append(f"| {label} | {t[key]['accuracy']:.2f} | {t[key]['macro_f1']:.2f} |")
    lines += ["", f"Validación cruzada de {cv['folds']} particiones sobre las {cv['traces']} trazas, agrupada por "
              f"traza ({cv['classifier']['n']} pasos): clasificador {cv['classifier']['accuracy']:.2f} de exactitud "
              f"y {cv['classifier']['macro_f1']:.2f} de F1 macro; regla {cv['rule']['accuracy']:.2f} y "
              f"{cv['rule']['macro_f1']:.2f}; siempre «development» {cv['majority']['accuracy']:.2f} y "
              f"{cv['majority']['macro_f1']:.2f}.", ""]
    lines += ["Test por origen:", "", "| Origen | Trazas | Pasos | Clasificador: exactitud | F1 macro "
              "| Regla: exactitud | F1 macro |", "|---|---|---|---|---|---|---|"]
    for source, label in (("deepseek", "DeepSeek"), ("openthoughts", "OpenThoughts (DeepSeek-R1)")):
        b = res["test_by_source"][source]
        lines.append(f"| {label} | {b['traces']} | {b['classifier']['n']} | {b['classifier']['accuracy']:.2f} "
                     f"| {b['classifier']['macro_f1']:.2f} | {b['rule']['accuracy']:.2f} | {b['rule']['macro_f1']:.2f} |")
    lines += ["", "Curva de aprendizaje (test, entrenando con subconjuntos aleatorios de train):", "",
              "| Trazas de entrenamiento | Pasos | Exactitud | F1 macro |", "|---|---|---|---|"]
    lines += [f"| {c['train_traces']} | {c['train_steps']} | {c['accuracy']:.2f} | {c['macro_f1']:.2f} |"
              for c in res["curve"]]
    lines += ["", "Por tipo, en test:", "",
              "| Tipo | Clasificador P | R | F1 | Regla F1 | Casos |", "|---|---|---|---|---|---|"]
    for c, v in t["classifier"]["per_class"].items():
        r = t["rule"]["per_class"][c]
        lines.append(f"| {c} | {v['precision']:.2f} | {v['recall']:.2f} | {v['f1']:.2f} | {r['f1']:.2f} "
                     f"| {v['support']} |")
    lines += ["", "Confusión del clasificador en test (referencia → predicción): " + ", ".join(
        f"{k}: {n}" for k, n in t["classifier"]["confusion"].items()), ""]
    return lines


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles default to cp1252
    by_trace = all_traces()
    res = evaluate(by_trace)

    shipped_on = sorted(t for t in by_trace if t not in STUDY_TRACES)
    shipped = fit([x for t in shipped_on for x in by_trace[t]], **res["settings"])
    commit = git_commit()
    data = {
        "classes": shipped.classes, "vocabulary": shipped.vocabulary, "idf": shipped.idf,
        "coef": shipped.coef, "intercept": shipped.intercept,
        "meta": {"trained": date.today().isoformat(), "commit": commit, "settings": res["settings"],
                 "min_df": MIN_DF, "traces": shipped_on,
                 "steps": sum(len(by_trace[t]) for t in shipped_on),
                 "excluded": list(STUDY_TRACES), "script": "python -m eval.steptypes"},
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    res.update({"date": date.today().isoformat(), "commit": commit, "shipped": data["meta"]})
    (RESULTS_DIR / "steptypes.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    lines = [f"# Clasificador de tipo de paso ({res['date']}, commit {commit})", ""] + report(res)
    lines += [f"## Selección en train (validación cruzada agrupada, {FOLDS} particiones)", "",
              "| C | Pesos de clase | Exactitud | F1 macro |", "|---|---|---|---|"]
    lines += [f"| {g['C']} | {g['class_weight'] or 'ninguno'} | {g['accuracy']:.2f} | {g['macro_f1']:.2f} |"
              for g in res["grid"]]
    lines += ["", "## Rasgos con más peso (modelo entrenado en train)", "",
              "o1: primera palabra; o: palabras iniciales; b: palabras del tramo; m: marcador del léxico.", ""]
    lines += [f"- **{c}**: " + ", ".join(f"`{f}`" for f in fs) for c, fs in res["top_features"].items()]
    lines += ["", "## Modelo instalado", "", f"Entrenado en {len(shipped_on)} trazas (todas salvo las dos de la "
              f"prueba con usuarios: {', '.join(STUDY_TRACES)}), {data['meta']['steps']} pasos, con los ajustes "
              f"elegidos en train. Archivo: backend/medra/mining/models/{MODEL_PATH.name}.", "",
              "## Trazas de test", "", ", ".join(res["split"]["test"]), ""]
    (RESULTS_DIR / "steptypes.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
