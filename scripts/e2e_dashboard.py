"""End-to-end check of traceability in the real dashboard (build step 3).

Plays a sample in a headless browser, then for every bubble:
1. clicks it and reads which character ranges the text pane highlights;
2. compares them with the term's spans from the miner, computed here
   independently (the miner is deterministic, so this is ground truth);
3. clicks the first highlighted mention and checks that its bubble is the
   one selected (the link in the other direction).

Needs the backend and the Vite dev server running (see README).

    python scripts/e2e_dashboard.py --sample login-es --channel chromium-headless-shell
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from medra.contracts import TextChunk  # noqa: E402
from medra.mining import TextMiner  # noqa: E402
from medra.sources import ReplaySource, load_trace  # noqa: E402


def expected_spans(sample: str) -> dict[str, list[tuple[int, int]]]:
    source = ReplaySource(load_trace(sample), "e2e", words_per_second=0)

    async def chunks() -> list[TextChunk]:
        return [c async for c in source.stream()]

    miner = TextMiner("e2e")
    final = [u for u in (miner.feed(c) for c in asyncio.run(chunks())) if u][-1]
    return {t.id: [tuple(s) for s in t.spans] for t in final.terms}


def merge(pieces: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Adjacent highlighted pieces (split where marks overlap) form one mention."""
    out: list[tuple[int, int]] = []
    for a, b in sorted(pieces):
        if out and out[-1][1] == a:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:5173/")
    parser.add_argument("--sample", default="login-es")
    parser.add_argument("--channel", default="chromium-headless-shell")
    args = parser.parse_args()
    truth = expected_spans(args.sample)

    failures = 0
    with sync_playwright() as p:
        page = p.chromium.launch(channel=args.channel).new_page(viewport={"width": 1440, "height": 900})
        page.goto(args.url)
        page.wait_for_selector(f"#sample option[value='{args.sample}']", state="attached")
        page.select_option("#sample", args.sample)
        page.select_option("#speed", "75")
        page.click("#start")
        page.wait_for_function("document.getElementById('status').dataset.state === 'done'", timeout=120_000)
        page.wait_for_timeout(1500)

        # Every paragraph block must show exactly the source text of its range.
        source = load_trace(args.sample).reasoning
        blocks = page.eval_on_selector_all(
            "#stream .para[data-seg]",
            """els => els.map(e => [Number(e.dataset.start), Number(e.dataset.end),
                [...e.childNodes].filter(n => !(n.classList && (n.classList.contains('pending')
                    || n.classList.contains('caret')))).map(n => n.textContent).join('')])""",
        )
        bad = [(a, b) for a, b, shown in blocks if shown != source[a:b]]
        failures += bool(bad)
        print(f"{args.sample}: {len(blocks)} paragraphs, "
              f"{'all match the source text' if not bad else f'MISMATCH in {bad}'}")

        ids = page.eval_on_selector_all("g.node", "els => els.map(e => e.dataset.id)")
        print(f"{args.sample}: {len(ids)} bubbles")
        for node_id in ids:
            bubble = f"g.node[data-id='{node_id}']"
            page.click(bubble)  # select
            pieces = page.eval_on_selector_all(
                ".m.hl", "els => els.map(e => [Number(e.dataset.start), Number(e.dataset.end)])"
            )
            got = merge([tuple(x) for x in pieces])
            want = sorted(truth[node_id])
            page.click(bubble)  # deselect

            # The other direction: clicking a mention selects its bubble. Where
            # mentions overlap (two n-grams), the longest one is chosen.
            first = page.locator(f".m[data-start='{want[0][0]}']").first
            ids_here = json.loads(first.get_attribute("data-ids") or "[]")
            first.click()
            selected = page.query_selector("g.node.sel")
            back = selected.get_attribute("data-id") if selected else None
            if back:
                page.click(f"g.node[data-id='{back}']")  # deselect for the next bubble

            ok = got == want and node_id in ids_here and back == ids_here[0]
            failures += not ok
            print(f"  {'ok' if ok else 'FAIL':4} {node_id!r}: {len(got)} mentions highlighted, "
                  f"{len(want)} expected; clicking its first mention selects {back!r}")
    print("all bubbles underline exactly their mentions" if not failures else f"{failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
