from conftest import replay_chunks
from medra.contracts import Node
from medra.mining import StubMiner
from medra.present import StubPresenter
from medra.present.stub import R_MAX, R_MIN, TOP_K


def run(sample: str = "login-es", seed: int = 0):
    miner, presenter = StubMiner("test"), StubPresenter()
    mining, views = [], []
    for c in replay_chunks(sample, "random", seed):
        update = miner.feed(c)
        if update:
            mining.append(update)
            views.append(presenter.present(update))
    return mining, views


def apply_diffs(views) -> dict[str, Node]:
    nodes: dict[str, Node] = {}
    for view in views:
        for node in view.nodes:
            nodes[node.id] = node
        for node_id in view.removed.nodes:
            del nodes[node_id]
    return nodes


def test_applying_diffs_rebuilds_the_full_view():
    mining, views = run()
    assert views[0].kind == "snapshot" and all(v.kind == "diff" for v in views[1:])
    expected = [t.id for t in mining[-1].terms[:TOP_K]]
    assert sorted(apply_diffs(views)) == sorted(expected)
    assert views[-1].final


def test_radius_follows_count():
    _, views = run()
    final = sorted(apply_diffs(views).values(), key=lambda n: -n.count)
    assert final[0].radius == R_MAX
    assert all(R_MIN <= n.radius <= R_MAX for n in final)
    assert all(a.radius >= b.radius for a, b in zip(final, final[1:]))


def test_diff_is_empty_when_nothing_changed():
    mining, _ = run()
    presenter = StubPresenter()
    presenter.present(mining[-1])
    again = presenter.present(mining[-1])
    assert again.nodes == [] and again.removed.nodes == [] and again.highlights == []
