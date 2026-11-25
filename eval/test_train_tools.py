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


def test_step_type_split_is_80_20_over_every_annotated_trace():
    from eval.common import train_trace_ids
    from eval.steptypes import step_split

    ids = trace_ids() + train_trace_ids()
    train, test = step_split(ids)
    assert len(ids) == 302 and len(train) + len(test) == 302 and not set(train) & set(test)
    assert len(test) == 61  # 20% of each source: 29 of 144 DeepSeek, 32 of 158 OpenThoughts
    assert step_split(list(reversed(ids))) == (train, test)  # depends only on the ids and the seed
