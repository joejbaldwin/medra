"""Capture dashboard screenshots for the memoria.

Needs the backend and the Vite dev server running (see README), and
Playwright (`pip install -e "backend[figures]"`). It drives the Microsoft
Edge already installed on Windows, so no browser download is needed; pass
--channel chrome (or chromium after `playwright install chromium`) elsewhere.

    python scripts/screenshots.py --prefix step1
    python scripts/screenshots.py --prefix step5-live --source deepseek --prompt "..." --schemes light

Writes, into screenshots/ (gitignored), as full-page captures:
    <prefix>-streaming-light.png   mid-stream: pending tail in grey, caret
    <prefix>-final-light.png       after the trace has finished
    <prefix>-final-dark.png        same, dark theme
    <prefix>-selected-light.png    with --select ID: that bubble clicked, its mentions highlighted
    <prefix>-topic-light.png       with --topic N: the N-th legend entry selected
    <prefix>-steps-light.png       with --step N: the steps view, the N-th step selected
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def start(page: Page, args: argparse.Namespace) -> None:
    page.goto(args.url)
    page.wait_for_selector("#source[data-loaded]", state="attached")  # GET /sources has answered
    page.wait_for_selector(f"#source option[value='{args.source}']:not([disabled])", state="attached")
    page.select_option("#source", args.source)
    if args.source == "replay":
        page.wait_for_selector(f"#sample option[value='{args.sample}']", state="attached")
        page.select_option("#sample", args.sample)
    elif args.source == "paste":
        page.fill("#paste-text", Path(args.paste_file).read_text(encoding="utf-8"))
    else:
        page.fill("#prompt-input", args.prompt)
    if args.source in ("replay", "paste"):
        page.select_option("#speed", args.speed)
    page.click("#start")


def wait_finished(page: Page) -> None:
    page.wait_for_function("document.getElementById('status').dataset.state === 'done'", timeout=120_000)
    page.wait_for_timeout(2500)  # let the force layout settle


def shot(page: Page, args: argparse.Namespace, name: str, scheme: str) -> None:
    page.screenshot(path=args.out_dir / f"{args.prefix}-{name}-{scheme}.png", full_page=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:5173/")
    parser.add_argument("--source", default="replay", choices=["replay", "paste", "deepseek", "ollama"])
    parser.add_argument("--sample", default="login-es")
    parser.add_argument("--paste-file", help="text file to paste (--source paste)")
    parser.add_argument("--prompt", help="question for a live model (--source deepseek/ollama); costs API credit")
    parser.add_argument("--schemes", default="light,dark", help="live runs cost a call each: use --schemes light")
    parser.add_argument("--speed", default="15", help="words per second (value of the speed menu)")
    parser.add_argument("--prefix", default="dashboard")
    parser.add_argument("--channel", default="msedge")
    parser.add_argument("--select", help="bubble id to click for a 'selected' capture")
    parser.add_argument("--topic", type=int, help="legend entry (1-based) to click for a 'topic' capture")
    parser.add_argument("--step", type=int, help="step (1-based) to click for a 'steps' capture")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "screenshots")
    args = parser.parse_args()
    args.out_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel)
        for scheme in args.schemes.split(","):
            context = browser.new_context(
                viewport={"width": 1440, "height": 900}, device_scale_factor=2, color_scheme=scheme
            )
            page = context.new_page()
            start(page, args)
            if scheme == "light":
                # Mid-stream: enough committed text for bubbles, and an unfinished sentence showing.
                # (A live model may finish first: then there is no streaming capture.)
                page.wait_for_function(
                    "(document.querySelectorAll('#stream .para[data-seg]').length >= 3"
                    " && (document.querySelector('#stream .pending')?.textContent.length ?? 0) > 25)"
                    " || ['done', 'error'].includes(document.getElementById('status').dataset.state)",
                    timeout=120_000,
                )
                if page.get_attribute("#status", "data-state") == "live":
                    page.wait_for_timeout(300)
                    shot(page, args, "streaming", scheme)
            wait_finished(page)
            shot(page, args, "final", scheme)
            if scheme == "light" and args.select:
                page.click(f"g.node[data-id='{args.select}']")
                page.mouse.move(0, 0)  # leave the bubble so the selection, not a hover, is shown
                page.wait_for_timeout(1200)  # smooth scroll to the first mention
                shot(page, args, "selected", scheme)
                page.click(f"g.node[data-id='{args.select}']")  # deselect
            if scheme == "light" and args.topic:
                page.click(f"#legend button:nth-child({args.topic})")
                page.mouse.move(0, 0)
                page.wait_for_timeout(1200)
                shot(page, args, "topic", scheme)
                page.click(f"#legend button:nth-child({args.topic})")
            if scheme == "light" and args.step:
                page.click("#tab-pasos")
                page.wait_for_timeout(300)
                page.click(f"g.s-node >> nth={args.step - 1}")
                page.mouse.move(0, 0)
                page.wait_for_timeout(1200)
                shot(page, args, "steps", scheme)
            context.close()
        browser.close()
    for f in sorted(args.out_dir.glob(f"{args.prefix}-*.png")):
        print(f)


if __name__ == "__main__":
    main()
