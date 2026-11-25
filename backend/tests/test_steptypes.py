"""The step-type classifier's features and the shipped model (steptypes.py).
Its training and its agreement with scikit-learn are tested in eval/test_steptypes.py."""

from medra.mining.steptypes import STEP_TYPES, StepInput, default_model, step_type, tokens


def step(opener: str, text: str | None = None, marker: str | None = None, first: bool = False) -> StepInput:
    return StepInput(opener=opener, text=text or opener, marker_type=marker, first=first)


def test_tokens_keep_opening_words_body_words_and_marker_apart():
    t = tokens(step("Check both: P1 is valid.", "Check both: P1 is valid. Yes.", "verification", first=True))
    assert t[0] == "o1:check"
    assert {"o:check", "o:both", "o:check_both", "o:p", "b:check", "b:yes", "m:verification", "pos:first"} <= set(t)
    assert "m:none" in tokens(step("Case A1."))
    assert "pos:first" not in tokens(step("Case A1."))


def test_digits_are_one_token():
    assert "o:#" in tokens(step("2 + 2 = 4"))


def test_shipped_model_predicts_known_types():
    model = default_model()
    assert model is not None, "run python -m eval.steptypes to train the model"
    assert set(model.classes) <= set(STEP_TYPES)
    assert "en-log-pets" not in model.meta["traces"] and "en-log-knights" not in model.meta["traces"]
    assert step_type(step("Let me double-check the result: 3 + 5 = 8, yes."), "en") in STEP_TYPES


def test_spanish_keeps_the_marker_rule():
    assert step_type(step("Comprobemos el resultado.", marker="verification"), "es") == "verification"
    assert step_type(step("Tenemos tres casas."), "es") == "development"
