"""Capture dashboard screenshots for the memoria.

Needs the backend and the Vite dev server running (see README), and
Playwright (`pip install -e "backend[figures]"`). It drives the Microsoft
Edge already installed on Windows, so no browser download is needed; pass
--channel chrome (or chromium after `playwright install chromium`) elsewhere.

    python scripts/screenshots.py --prefix step1

Writes, into screenshots/ (gitignored):
    <prefix>-streaming-light.png   mid-stream: pending tail in grey, caret
    <prefix>-final-light.png       after the trace has finished
    <prefix>-final-dark.png        same, dark theme
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def start(page: Page, url: str, sample: str, speed: str) -> None:
    page.goto(url)
    page.wait_for_selector(f"#sample option[value='{sample}']", state="attached")
    page.select_option("#sample", sample)
    page.select_option("#speed", speed)
    page.click("#start")


def wait_finished(page: Page) -> None:
    page.wait_for_function("document.getElementById('status').dataset.state === 'done'", timeout=120_000)
    page.wait_for_timeout(2500)  # let the force layout settle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:5173/")
    parser.add_argument("--sample", default="login-es")
    parser.add_argument("--speed", default="15", help="words per second (value of the speed menu)")
    parser.add_argument("--prefix", default="dashboard")
    parser.add_argument("--channel", default="msedge")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "screenshots")
    args = parser.parse_args()
    args.out_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel)
        for scheme in ("light", "dark"):
            context = browser.new_context(
                viewport={"width": 1440, "height": 900}, device_scale_factor=2, color_scheme=scheme
            )
            page = context.new_page()
            start(page, args.url, args.sample, args.speed)
            if scheme == "light":
                # Mid-stream: enough committed text for bubbles, and an unfinished sentence showing.
                page.wait_for_function(
                    "document.getElementById('committed').textContent.length > 450"
                    " && document.getElementById('pending').textContent.length > 25",
                    timeout=60_000,
                )
                page.wait_for_timeout(300)
                page.screenshot(path=args.out_dir / f"{args.prefix}-streaming-{scheme}.png")
            wait_finished(page)
            page.screenshot(path=args.out_dir / f"{args.prefix}-final-{scheme}.png")
            context.close()
        browser.close()
    for f in sorted(args.out_dir.glob(f"{args.prefix}-*.png")):
        print(f)


if __name__ == "__main__":
    main()
