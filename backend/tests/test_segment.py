"""Discourse markers, segmentation (TextTiling + markers) and topics."""

import random
from collections import Counter

import pytest

from medra.mining.markers import count_hedges, find_marker
from medra.mining.segment import (
    FROZEN_AFTER,
    MIN_SENTENCES,
    THRESHOLD,
    SentenceFeatures,
    boundaries,
    cosine,
    gap_scores,
)
from medra.mining.topics import MAX_TOPICS, TopicTracker, communities

# ---------------------------------------------------------------- markers


@pytest.mark.parametrize(
    "sentence,lang,expected",
    [
        ("Wait, let me check that with a small case.", "en", ("verification", "Wait, let me check")),
        ("Wait.", "en", ("backtrack", "Wait")),
        ("Alternatively, there is a pattern.", "en", ("alternative", "Alternatively")),
        ("So both approaches agree.", "en", ("conclusion", "So")),
        ("Hmm, so the answer is 9.", "en", ("conclusion", "Hmm, so the answer is")),
        ("The sum is so large.", "en", None),  # not sentence-initial
        ("Sorting first.", "en", None),  # "so" must be a whole word
        ("Espera, falta la seguridad.", "es", ("backtrack", "Espera")),
        ("No, espera, eso está mal.", "es", ("backtrack", "No, espera")),
        ("Primero los campos.", "es", ("planning", "Primero")),
        ("¿Y si usamos JWT?", "es", ("alternative", "Y si")),
        ("Vale, el usuario quiere una página.", "es", None),
    ],
)
def test_sentence_initial_markers(sentence, lang, expected):
    found = find_marker(sentence, lang)
    assert (found and (found.type, sentence[found.start : found.end])) == expected


def test_hedges_are_counted_as_whole_phrases():
    assert count_hedges("Maybe it works, I think. Perhaps not.", "en") == 3
    assert count_hedges("Quizá convenga. Podría usar JWT, tal vez.", "es") == 3
    assert count_hedges("The maybelline mightiness.", "en") == 0


# ---------------------------------------------------------------- segmentation


def feats(words: str, marker: str | None = None, para: bool = False) -> SentenceFeatures:
    return SentenceFeatures(words=Counter(words.split()), marker_type=marker, paragraph_break=para)


def test_cosine():
    assert cosine(Counter("a b".split()), Counter("a b".split())) == pytest.approx(1)
    assert cosine(Counter("a".split()), Counter("b".split())) == 0
    assert cosine(Counter(), Counter("a".split())) == 0


def test_a_change_of_vocabulary_is_a_boundary():
    sentences = [feats("login form email")] * 4 + [feats("hash server security")] * 4
    gaps = gap_scores(sentences)
    deepest = max(gaps, key=lambda g: g.depth)
    assert deepest.index == 4 and deepest.score >= THRESHOLD
    assert boundaries(gaps) == [0, 4]


def test_a_marker_and_a_paragraph_break_make_a_boundary_without_lexical_change():
    same = [feats("sum odd number")] * 6
    assert boundaries(gap_scores(same)) == [0]
    marked = same[:3] + [feats("sum odd number", marker="backtrack", para=True)] + same[4:]
    assert boundaries(gap_scores(marked)) == [0, 3]


def test_segments_have_a_minimum_length():
    sentences = [feats("a"), feats("b", "backtrack", True), feats("c", "backtrack", True), feats("d", "backtrack", True)]
    starts = boundaries(gap_scores(sentences))
    assert all(b - a >= MIN_SENTENCES for a, b in zip(starts, starts[1:]))


def test_boundaries_are_frozen_once_enough_sentences_follow():
    # Random features: the decision for every gap with FROZEN_AFTER sentences
    # after it must not change when more sentences arrive.
    rng = random.Random(0)
    vocab = "a b c d e f g h".split()
    markers = [None, None, None, "backtrack", "planning", "conclusion"]
    sentences = [
        feats(" ".join(rng.sample(vocab, 3)), rng.choice(markers), rng.random() < 0.3) for _ in range(80)
    ]
    final = boundaries(gap_scores(sentences))
    for n in range(1, len(sentences)):
        partial = boundaries(gap_scores(sentences[:n]))
        frozen = [b for b in partial if n - b >= FROZEN_AFTER]
        assert frozen == [b for b in final if n - b >= FROZEN_AFTER], n


# ---------------------------------------------------------------- topics


def test_communities_split_terms_used_in_different_places():
    sentence_terms = [["login", "form"], ["login", "email"], ["form", "email"]] * 2 + [
        ["hash", "server"],
        ["hash", "salt"],
        ["server", "salt"],
    ] * 2
    counts = Counter(t for s in sentence_terms for t in s)
    groups = communities(sentence_terms, counts)
    assert {frozenset(g) for g in groups} == {frozenset({"login", "form", "email"}), frozenset({"hash", "server", "salt"})}
    assert communities(sentence_terms, counts) == groups  # deterministic


def test_nested_pairs_are_not_evidence_of_a_topic():
    sentence_terms = [["odd", "odd number", "rare"], ["odd", "odd number"]]
    counts = {"odd": 2, "odd number": 2, "rare": 1}
    assert communities(sentence_terms, counts) == []  # the only edge between frequent terms is nested


def test_rare_terms_join_the_topic_they_occur_with():
    sentence_terms = [["login", "form"], ["login", "form"], [], ["hash", "server", "salt"], ["hash", "server"], []]
    counts = Counter(t for s in sentence_terms for t in s)
    counts["orphan"] = 1  # never co-occurs with anything
    groups = communities(sentence_terms, counts)
    assert {frozenset(g) for g in groups} == {frozenset({"login", "form"}), frozenset({"hash", "server", "salt"})}
    assert next(g for g in groups if "hash" in g)[-1] == "salt"  # rare terms sort after the frequent ones


def test_at_most_max_topics():
    # MAX_TOPICS + 3 unconnected pairs (an empty sentence keeps the 2-sentence
    # window from linking one pair to the next).
    sentence_terms = [s for i in range(MAX_TOPICS + 3) for s in ([[f"a{i}", f"b{i}"]] * 3 + [[]])]
    counts = Counter(t for s in sentence_terms for t in s)
    assert len(communities(sentence_terms, counts)) == MAX_TOPICS


def test_topic_ids_stay_stable_when_clusters_change():
    tracker = TopicTracker()
    first = dict(tracker.assign([["login", "form"], ["hash", "server"]]))
    assert first == {"t0": ["login", "form"], "t1": ["hash", "server"]}
    # Order flips and both groups grow: the ids follow the terms, not the order.
    second = dict(tracker.assign([["hash", "server", "salt"], ["login", "form", "email"]]))
    assert second == {"t1": ["hash", "server", "salt"], "t0": ["login", "form", "email"]}
    # A group with nothing in common gets a fresh id (ids are never reused).
    third = dict(tracker.assign([["jwt", "cookie"], ["login", "form", "email"]]))
    assert third == {"t2": ["jwt", "cookie"], "t0": ["login", "form", "email"]}
