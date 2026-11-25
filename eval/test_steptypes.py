"""The JSON model computes what scikit-learn computes (eval/steptypes.py)."""

import numpy as np

from eval.steptypes import fit, fit_sklearn
from medra.mining.steptypes import StepInput

TEXTS = [
    ("We need to find x.", "planning"), ("First, list the cases.", "planning"),
    ("Check: 2 + 2 = 4, yes.", "verification"), ("Let me verify the sum again.", "verification"),
    ("So the answer is 4.", "conclusion"), ("Thus the final answer is 12.", "conclusion"),
    ("Alternatively, use a table.", "alternative"), ("Another way: count the pairs.", "alternative"),
    ("The sum of 3 and 5 is 8.", "development"), ("Each house has one pet.", "development"),
] * 2


def data():
    return [(StepInput(t, t + " More words here.", None, i == 0), g, f"t{i % 4}") for i, (t, g) in enumerate(TEXTS)]


def test_json_model_matches_scikit_learn():
    d = data()
    vec, clf = fit_sklearn(d, C=3, class_weight="balanced")
    model = fit(d, C=3, class_weight="balanced")
    steps = [s for s, _, _ in d] + [StepInput("Check again: unseen words", "Check again: unseen words", "verification", False)]
    ours = np.array([[model.scores(s)[c] for c in model.classes] for s in steps])
    theirs = clf.decision_function(vec.transform(steps))
    assert model.classes == list(clf.classes_)
    assert np.allclose(ours, theirs, atol=1e-4)  # the JSON rounds weights to 6 decimals
    assert [model.predict(s) for s in steps] == list(clf.predict(vec.transform(steps)))
