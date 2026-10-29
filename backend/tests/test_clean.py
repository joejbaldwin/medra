import pytest

from medra.mining.clean import mask


@pytest.mark.parametrize(
    "text",
    [
        "Code: ```py\nx = 1\n``` done.",
        "Inline `x.y` and $a^2$ here.",
        "Display $$\na = b. C\n$$ end",
        "Bracket \\[ T(n) = 1. X \\] and \\( y \\).",
        "<think>Hmm.</think> Ok.",
        "Costs $5 and $6, not maths.",
    ],
)
def test_masking_preserves_length(text):
    assert len(mask(text, final=True).text) == len(text)


def test_masks_code_maths_and_tags():
    text = "Use `foo.bar` then ```\nx = 1. Y\n``` and $x.y$ or \\[ z. W \\] <think>ok</think>"
    masked = mask(text, final=True).text
    for hidden in ("foo", "x = 1", "x.y", "z. W", "<think>", "</think>"):
        assert hidden not in masked
    assert "Use" in masked and "then" in masked and "ok" in masked


def test_currency_is_not_maths():
    text = "It costs $5 and $6 today."
    assert mask(text, final=True).text == text


def test_unclosed_block_holds_commit_until_closed():
    text = "Intro. ```\nx = 1. Y"
    m = mask(text, final=False)
    assert m.hold == text.index("```")
    # Once the stream ends, an unterminated block is still treated as code.
    assert "x = 1" not in mask(text, final=True).text


def test_inline_construct_ending_at_newline_is_literal():
    text = "A `tick without close\nNext line."
    m = mask(text, final=False)
    assert m.hold == len(text) and m.text == text


def test_partial_think_tag_at_the_end_holds():
    text = "Fine. <thi"
    assert mask(text, final=False).hold == text.index("<")


def test_mask_from_an_offset_matches_full_mask():
    text = "One. Two `code` three. ```\nblock\n``` four."
    start = text.index("Two")
    assert mask(text, start, final=True).text == mask(text, final=True).text[start:]
