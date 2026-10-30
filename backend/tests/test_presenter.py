"""Layer 3 rules (step 3): selection, hysteresis, sizing, edges, highlights, diffs."""

import asyncio

import pytest

from conftest import replay_chunks
from medra.contracts import Cooccurrence, MiningUpdate, Node, SegmentKeywords, Term, TermWeight
from medra.mining import TextMiner
from medra.pipeline import run_pipeline
from medra.present import ViewPresenter
from medra.present.edges import MAX_PER_NODE, select_edges
from medra.present.presenter import label_for
from medra.present.select import BubbleSelector, nested_words
from medra.present.sizing import R_MAX, R_MIN, radius
from medra.sources import ReplaySource, load_trace


def term(tid: str, count: int, spans=None, forms=None) -> Term:
    spans = spans or [(i * 10, i * 10 + len(tid)) for i in range(count)]
    return Term(id=tid, surface_forms=forms or [tid], count=count, df_segments=1, spans=spans, first_seen=spans[0][0])


def update(terms: list[Term], **kw) -> MiningUpdate:
    return MiningUpdate(session_id="t", seq=0, t=0, text_length=100, committed_upto=100, terms=terms, **kw)


def run(sample: str):
    miner, presenter = TextMiner("t"), ViewPresenter()
    mining, views = [], []
    for c in replay_chunks(sample, "random", 1):
        u = miner.feed(c)
        if u:
            mining.append(u)
            views.append(presenter.present(u))
    return miner, presenter, mining, views


# ---------------------------------------------------------------- selection


def test_word_inside_ngram_is_dropped():
    # "odd" appears 3 times, always inside "odd number"; "number" once outside.
    odd = term("odd", 3, spans=[(0, 3), (20, 23), (40, 43)])
    number = term("number", 4, spans=[(4, 10), (24, 30), (44, 50), (60, 66)])
    odd_number = term("odd number", 3, spans=[(0, 10), (20, 30), (40, 50)])
    assert nested_words([odd, number, odd_number]) == {"odd", "number"}  # 3/4 = 75% for number
    assert nested_words([odd, number, odd_number], share=0.8) == {"odd"}


def test_hysteresis_keeps_a_bubble_until_it_drops_past_the_margin():
    selector = BubbleSelector(top_k=2, margin=1)
    first = selector.select(update([term("a", 5), term("b", 4), term("c", 3)]))
    assert [t.id for t in first] == ["a", "b"]
    # c overtakes b by one: b is now rank 3 (< top_k + margin), so it stays.
    second = selector.select(update([term("a", 5), term("c", 5), term("b", 4)]))
    assert {t.id for t in second} == {"a", "b"}
    # b falls to rank 4: it leaves and c enters.
    third = selector.select(update([term("a", 6), term("c", 6), term("d", 6), term("b", 4)]))
    assert {t.id for t in third} == {"a", "c"}


def test_tfidf_breaks_ties_between_equally_frequent_terms():
    tfidf = [SegmentKeywords(segment_id=0, terms=[TermWeight(term_id="b", weight=0.9)])]
    shown = BubbleSelector(top_k=1).select(update([term("a", 3), term("b", 3)], tfidf=tfidf))
    assert [t.id for t in shown] == ["b"]


def test_label_prefers_a_form_equal_to_the_lemma():
    assert label_for(term("jwt", 2, forms=["JWT"])) == "JWT"
    assert label_for(term("campo", 2, forms=["campos", "campo"])) == "campo"
    assert label_for(term("campo", 2, forms=["campos"])) == "campo"


# ---------------------------------------------------------------- sizing and edges


def test_radius_scales_with_square_root_of_count():
    assert radius(9, 9) == R_MAX and radius(0, 9) == R_MIN
    # Area ~ count: a quarter of the count gives half of the extra radius.
    assert radius(1, 4) == pytest.approx(R_MIN + (R_MAX - R_MIN) / 2, abs=0.1)


def test_edges_need_shown_nodes_positive_pmi_and_cap_per_node():
    cooc = [Cooccurrence(a="hub", b=f"n{i}", count=5 - i, pmi=1.0) for i in range(5)]
    cooc += [Cooccurrence(a="x", b="y", count=9, pmi=-0.5), Cooccurrence(a="x", b="z", count=9, pmi=1.0)]
    shown = {"hub", "n0", "n1", "n2", "n3", "n4", "x", "y"}
    edges = select_edges(cooc, shown)
    assert [e.b for e in edges if e.a == "hub"] == ["n0", "n1", "n2"][:MAX_PER_NODE]  # strongest first
    assert not [e for e in edges if e.a == "x"]  # negative PMI, or z not shown
    assert all(e.width > 0 for e in edges)


# ---------------------------------------------------------------- highlights (the step-3 goal)


@pytest.mark.parametrize("sample", ["login-es", "odd-sum-en"])
def test_each_bubble_underlines_exactly_its_mentions(sample):
    text = load_trace(sample).reasoning
    _, presenter, mining, views = run(sample)
    final_terms = {t.id: t for t in mining[-1].terms}
    highlights = {}
    for v in views:
        for h in v.highlights:
            highlights[h.id] = h
        for key in v.removed.highlights:
            highlights.pop(key.split(":", 1)[1])
    shown = set(presenter.nodes.sent)
    assert set(highlights) == shown
    for node_id, h in highlights.items():
        assert h.spans == final_terms[node_id].spans
        for a, b in h.spans:
            assert text[a:b] in final_terms[node_id].surface_forms


def test_applying_diffs_rebuilds_the_presenters_state():
    _, presenter, _, views = run("odd-sum-en")
    nodes: dict[str, Node] = {}
    edges = {}
    for v in views:
        nodes.update({n.id: n for n in v.nodes})
        edges.update({e.id: e for e in v.edges})
        for i in v.removed.nodes:
            del nodes[i]
        for i in v.removed.edges:
            del edges[i]
    assert nodes == presenter.nodes.sent and edges == presenter.edges.sent
    assert all(e.a in nodes and e.b in nodes for e in edges.values())
    assert views[0].kind == "snapshot" and views[-1].final


def test_paragraph_labels_skip_words_nested_in_ngrams():
    _, _, _, views = run("odd-sum-en")
    labels = {p.segment_id: p.label for v in views for p in v.paragraphs}
    assert labels[0].split(" · ")[0] == "odd number"
    assert "odd ·" not in labels[0] and "number" != labels[0].split(" · ")[-1]


def test_ticker_reports_token_decisions():
    _, _, _, views = run("login-es")
    items = [t for v in views for t in v.ticker]
    assert {"term", "stopword", "pos"} <= {t.outcome for t in items}
    assert any(t.node_id == "contraseña" for t in items)


# ---------------------------------------------------------------- throttling


def stream(min_interval: float):
    source = ReplaySource(load_trace("login-es"), "t", words_per_second=0)

    async def collect():
        return [m async for m in run_pipeline("t", source, TextMiner("t"), ViewPresenter(), min_interval)]

    return asyncio.run(collect())


def test_throttle_keeps_the_final_state_and_carries_ticker_tokens():
    fast = [m.view for m in stream(0) if m.type == "view"]
    slow = [m.view for m in stream(3600) if m.type == "view"]
    assert len(slow) == 2 < len(fast)  # the first view, then the final one
    assert slow[-1].final and slow[-1].committed_upto == fast[-1].committed_upto
    assert slow[-1].ticker[-1] == fast[-1].ticker[-1]
