"""Step type of a segment: a classifier trained on the group's annotations.

The first version typed a step by the discourse marker that opens its first
sentence (markers.py) and called everything else "development". Its labels
were mostly right but rare: on the annotated traces it found 10% of the
verification steps and 18% of the conclusions, because models open steps with
words the lexicon does not list ("Check both:", "Case A2, B1...", "Both
valid..."). This module replaces that rule for English with a linear model:

- Features (`tokens`): the first words of the step (position-specific first
  word, unigrams and bigrams), the words of the whole step, the lexicon's
  marker type (so the rule is one feature among others) and whether it is the
  trace's first step. TF-IDF weighted (sublinear tf, l2 norm).
- Model: multinomial logistic regression (scikit-learn), trained by
  eval/steptypes.py, which also chooses its settings on the dev traces and
  reports it on the test traces.

The trained model is stored as JSON (vocabulary, idf, weights), not a pickle:
it is readable, safe to load, and independent of the scikit-learn version.
Prediction is a sparse dot product, so the live miner can afford it on every
snapshot. Spanish keeps the marker rule (no Spanish annotations).
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "models" / "step_types_en.json"
DEVELOPMENT = "development"  # the type of a step nothing else describes
# The annotation guide's types (eval/annotations/GUIDE.md), as in markers.py.
STEP_TYPES = ("planning", "development", "verification", "alternative", "backtrack", "conclusion")
OPENER_WORDS = 6  # words of the first sentence that get opener features

_WORD = re.compile(r"[a-z]+(?:['’-][a-z]+)*|\d+")


@dataclass(frozen=True)
class StepInput:
    opener: str  # the step's first sentence
    text: str  # the whole step
    marker_type: str | None  # lexicon marker opening the first sentence (markers.py)
    first: bool  # the first step of the trace


def words(text: str) -> list[str]:
    return [("#" if w.isdigit() else w) for w in _WORD.findall(text.lower())]


def tokens(step: StepInput) -> list[str]:
    """The step as feature tokens. Shared by training and prediction, so both
    always see the same features. Prefixes keep the groups apart: "o:check"
    (opening words) and "b:check" (anywhere in the step) are different features."""
    opening = words(step.opener)[:OPENER_WORDS]
    out = [f"o1:{opening[0]}"] if opening else []
    out += [f"o:{w}" for w in opening]
    out += [f"o:{a}_{b}" for a, b in zip(opening, opening[1:])]
    out += [f"b:{w}" for w in words(step.text)]
    out.append(f"m:{step.marker_type or 'none'}")
    if step.first:
        out.append("pos:first")
    return out


class StepTypeModel:
    """The trained classifier, from the JSON written by eval/steptypes.py."""

    def __init__(self, data: dict) -> None:
        self.classes: list[str] = data["classes"]
        self.vocabulary: dict[str, int] = data["vocabulary"]
        self.idf: list[float] = data["idf"]
        self.coef: list[list[float]] = data["coef"]  # one row per class, one column per feature
        self.intercept: list[float] = data["intercept"]
        self.meta: dict = data.get("meta", {})

    @classmethod
    def load(cls, path: Path = MODEL_PATH) -> StepTypeModel:
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def vector(self, step: StepInput) -> dict[int, float]:
        """TF-IDF of the step's tokens, as scikit-learn's TfidfVectorizer
        computes it with sublinear_tf=True: (1 + ln tf) * idf, then l2 norm."""
        counts: dict[int, int] = {}
        for t in tokens(step):
            j = self.vocabulary.get(t)
            if j is not None:
                counts[j] = counts.get(j, 0) + 1
        vec = {j: (1 + math.log(n)) * self.idf[j] for j, n in counts.items()}
        norm = math.sqrt(sum(v * v for v in vec.values()))
        return {j: v / norm for j, v in vec.items()} if norm else vec

    def scores(self, step: StepInput) -> dict[str, float]:
        vec = self.vector(step)
        return {
            c: self.intercept[k] + sum(self.coef[k][j] * v for j, v in vec.items())
            for k, c in enumerate(self.classes)
        }

    def predict(self, step: StepInput) -> str:
        s = self.scores(step)
        return max(s, key=s.__getitem__)


@lru_cache(maxsize=1)
def default_model() -> StepTypeModel | None:
    """The shipped English model, or None if it has not been trained yet."""
    return StepTypeModel.load() if MODEL_PATH.exists() else None


def step_type(step: StepInput, lang: str) -> str:
    """The step type shown in the dashboard: the classifier for English, the
    opening marker (or development) otherwise."""
    model = default_model() if lang == "en" else None
    if model is None:
        return step.marker_type or DEVELOPMENT
    return model.predict(step)
