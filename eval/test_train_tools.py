"""The training-set tools: tag specs (eval/annotations.py) and the split's isolation."""

import pytest

from eval.annotations import AnnotationError, parse_tags
from eval.common import split, trace_ids


def test_tags_from_a_spec():
    assert parse_tags("0:planning, 4:development,9:verification") == {0: "planning", 4: "development", 9: "verification"}


@pytest.mark.parametrize("spec", ["4:development", "0:plan", "0:planning,0:development"])
def test_bad_tag_specs_are_refused(spec):
    with pytest.raises(AnnotationError):
        parse_tags(spec)


def test_training_traces_stay_out_of_the_evaluation_split():
    ids = trace_ids()
    assert len(ids) == 30 and not any(i.startswith("ds-") or i.split("-")[1].isdigit() for i in ids)
    dev, test = split(ids)
    assert len(dev) == 19 and len(test) == 11
