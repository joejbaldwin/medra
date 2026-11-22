import random

import pytest

from conftest import fixture_text
from medra.mining.clean import mask
from medra.mining.sentences import find_sentences


def split(text: str, final: bool = True) -> tuple[list[str], int]:
    spans, frontier = find_sentences(text, 0, len(text), final)
    return [text[a:b] for a, b in spans], frontier


def test_basic_and_pending_tail():
    sentences, frontier = split("Hola mundo. Esto sig", final=False)
    assert sentences == ["Hola mundo."] and frontier == len("Hola mundo.")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("¿Qué pasa? Nada. ¡Vale!", ["¿Qué pasa?", "Nada.", "¡Vale!"]),
        ("Use a language, e.g. Python. Then test.", ["Use a language, e.g. Python.", "Then test."]),
        ("It takes approx. two steps. Done.", ["It takes approx. two steps.", "Done."]),
        ("Dr. Knuth wrote it. Yes.", ["Dr. Knuth wrote it.", "Yes."]),
        ("Por ejemplo, p. ej. Madrid. Fin.", ["Por ejemplo, p. ej. Madrid.", "Fin."]),
        ("The value is 3.14 here. Next.", ["The value is 3.14 here.", "Next."]),
        ("Step one\nStep two\n\nStep three", ["Step one", "Step two", "Step three"]),
        ('He said "stop." Then left.', ['He said "stop."', "Then left."]),
        ("Is it 9? 9 it is.", ["Is it 9?", "9 it is."]),
        ("Hmm, no. Let me check.", ["Hmm, no.", "Let me check."]),
        # A list number does not end a sentence, unless the line ends after it.
        ("Clues:\n1. Ann is here.\n2. Ben does not own the cat.",
         ["Clues:", "1. Ann is here.", "2. Ben does not own the cat."]),
        ("The total is\n10.\nDone.", ["The total is", "10.", "Done."]),
        ("It has 3 sides. 4. Next one.", ["It has 3 sides.", "4. Next one."]),
    ],
)
def test_rules(text, expected):
    assert split(text)[0] == expected


def test_waits_for_the_next_character():
    # "3." might become "3.14"; "end.  " might be followed by a lowercase word.
    assert split("The value is 3.", final=False)[0] == []
    assert split("The end.  ", final=False)[0] == []
    assert split("The end.  ", final=True)[0] == ["The end."]


def committed_incrementally(text: str, cuts: list[int]) -> list[tuple[int, int]]:
    """Feed text in pieces the way the miner does: mask the uncommitted tail,
    split it, advance the frontier."""
    spans, start = [], 0
    for end in cuts + [len(text)]:
        final = end == len(text)
        region = mask(text[:end], start, final)
        limit = end if final else region.hold
        new, frontier = find_sentences(region.text, 0, limit - start, final)
        spans += [(start + a, start + b) for a, b in new]
        start += frontier
    return spans


@pytest.mark.parametrize("seed", range(20))
def test_boundaries_do_not_depend_on_chunking(seed):
    text = fixture_text("tricky-en.txt") + fixture_text("mixed-en-es.txt")
    batch = committed_incrementally(text, [])
    rng = random.Random(seed)
    cuts = sorted(rng.sample(range(1, len(text)), rng.randint(5, 80)))
    assert committed_incrementally(text, cuts) == batch
