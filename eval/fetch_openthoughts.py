"""Fetch English traces from OpenThoughts-114k.

    python -m eval.fetch_openthoughts                       # the evaluation traces (ROWS)
    python -m eval.fetch_openthoughts --scan 500 300        # list rows 500-799 of 300-1800 words
    python -m eval.fetch_openthoughts --peek 500 501 502    # look at rows, save nothing
    python -m eval.fetch_openthoughts --rows 500 731        # training traces -> eval/train/traces/ot-<row>.json

OpenThoughts-114k (Apache-2.0) holds DeepSeek-R1 reasoning for maths and code
problems. Rows are read one at a time from the Hugging Face datasets-server
API (no download of the full dataset), and saved as eval/traces/<id>.json in
the data/samples/ format. The rows were picked by hand among those with
300-1300 words of reasoning, to add another model's style to the set.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

from eval.common import TRAIN_TRACES_DIR

TRACES_DIR = Path(__file__).parent / "traces"
API = "https://datasets-server.huggingface.co/rows?dataset=open-thoughts/OpenThoughts-114k&config=metadata&split=train"

# id: (row index in the train split, title)
ROWS = {
    "ot-mat-plums": (12, "Plums, apples and a pear"),
    "ot-mat-trail": (47, "Jitka's hike"),
    "ot-log-krakozyabrs": (84, "Horns and wings"),
    "ot-cod-yen": (100002, "Change from 1000-yen bills"),
    # The "puzzle" domain is common-sense multiple choice, so the logic puzzles
    # come from the maths domain; 112008 adds a science (chemistry) calculation.
    "ot-log-calculator": (151, "A calculator that doubles and reverses"),
    "ot-log-board": (289, "Erasing numbers from a board"),
    "ot-cod-tasks": (100107, "Three tasks"),
    "ot-sci-enthalpy": (112008, "Dissolving sodium hydroxide"),
}


# Rows by domain (approximate): math ~0-89,999, code ~90,000-109,999,
# biology ~110,000, physics ~110,500-111,500, chemistry ~111,900-112,999,
# puzzle (common-sense multiple choice) from ~113,000.
DOMAINS = {"math": {"math"}, "code": {"code"}, "science": {"biology", "physics", "chemistry"},
           "biology": {"biology"}, "physics": {"physics"}, "chemistry": {"chemistry"}, "puzzle": {"puzzle"}}


def fetch_page(offset: int, length: int, tries: int = 4) -> list[tuple[int, dict]]:
    """Up to 100 consecutive rows as (row index, row); the public API is
    sometimes busy (5xx or timeouts), so retry."""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(f"{API}&offset={offset}&length={length}", timeout=60) as resp:
                return [(r["row_idx"], r["row"]) for r in json.load(resp)["rows"]]
        except (OSError, KeyError, ValueError):
            if attempt == tries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


def fetch(row: int) -> dict:
    return fetch_page(row, 1)[0][1]


def scan(start: int, count: int, min_words: int, max_words: int, domain: str | None) -> None:
    """List the rows in [start, start + count) whose reasoning has min-max words."""
    shown = 0
    for offset in range(start, start + count, 100):
        try:
            page = fetch_page(offset, min(100, start + count - offset))
        except (OSError, KeyError, ValueError) as exc:
            print(f"rows {offset}-{offset + 99}: could not fetch ({exc})")
            continue
        for row, r in page:
            n = words(r["deepseek_reasoning"])
            if min_words <= n <= max_words and (domain is None or r["domain"] in DOMAINS[domain]):
                shown += 1
                print(f"{row}\t{r['domain']}\t{n} words\t{' '.join(r['problem'].split())[:110]}")
    print(f"{shown} rows with {min_words}-{max_words} words in rows {start}-{start + count - 1}")


def to_trace(trace_id: str, row: int, r: dict, title: str) -> dict:
    return {
        "id": trace_id,
        "title": title,
        "language": "en",
        "prompt": r["problem"].strip(),
        "reasoning": r["deepseek_reasoning"].strip(),
        "answer": r["deepseek_solution"].strip(),
        "origin": (f"OpenThoughts-114k (Apache-2.0), fila {row} de train (dominio {r['domain']}): razonamiento "
                   "de DeepSeek-R1; descargado con eval/fetch_openthoughts.py; sin editar."),
    }


def save(trace: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{trace['id']}.json"
    path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def words(text: str) -> int:
    return len(text.split())


def peek(rows: list[int]) -> None:
    """One line per row: domain, reasoning words, start of the problem. Saves nothing."""
    for row in rows:
        try:
            r = fetch(row)
        except (OSError, KeyError, ValueError, IndexError) as exc:
            print(f"{row}: could not fetch ({exc})")
            continue
        problem = " ".join(r["problem"].split())[:110]
        print(f"{row}\t{r['domain']}\t{words(r['deepseek_reasoning'])} words\t{problem}")


def fetch_rows(rows: list[int], out: Path, min_words: int, max_words: int) -> None:
    """Save each row as <out>/ot-<row>.json if its reasoning has min-max words."""
    for row in rows:
        trace_id = f"ot-{row}"
        if (out / f"{trace_id}.json").exists():
            print(f"{trace_id}: already saved, skipped")
            continue
        try:
            r = fetch(row)
        except (OSError, KeyError, ValueError, IndexError) as exc:
            print(f"{trace_id}: could not fetch ({exc})")
            continue
        n = words(r["deepseek_reasoning"])
        if not min_words <= n <= max_words:
            print(f"{trace_id}: skipped, {n} words (allowed {min_words}-{max_words})")
            continue
        title = " ".join(r["problem"].split()[:8])
        save(to_trace(trace_id, row, r, title), out)
        print(f"{trace_id}: saved, {r['domain']}, {n} words")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch OpenThoughts-114k traces.")
    parser.add_argument("--scan", type=int, nargs=2, metavar=("START", "COUNT"),
                        help="list rows START..START+COUNT-1 within the word limits; save nothing")
    parser.add_argument("--domain", choices=sorted(DOMAINS), help="with --scan: only this domain")
    parser.add_argument("--peek", type=int, nargs="+", metavar="ROW", help="show rows (domain, words, problem); save nothing")
    parser.add_argument("--rows", type=int, nargs="+", metavar="ROW", help="save these rows as ot-<row> (training set)")
    parser.add_argument("--out", type=Path, default=TRAIN_TRACES_DIR, help="folder for --rows (default eval/train/traces)")
    parser.add_argument("--min-words", type=int, default=300)
    parser.add_argument("--max-words", type=int, default=1800)
    args = parser.parse_args()
    if args.scan:
        return scan(*args.scan, args.min_words, args.max_words, args.domain)
    if args.peek:
        return peek(args.peek)
    if args.rows:
        evaluation = {row for row, _ in ROWS.values()}
        if evaluation & set(args.rows):
            sys.exit(f"rows already in the evaluation set: {sorted(evaluation & set(args.rows))}")
        return fetch_rows(args.rows, args.out, args.min_words, args.max_words)
    # No options: the evaluation traces (ROWS), as first fetched.
    for trace_id, (row, title) in ROWS.items():
        if (TRACES_DIR / f"{trace_id}.json").exists():
            print(f"{trace_id}: already saved, skipped")
            continue
        trace = to_trace(trace_id, row, fetch(row), title)
        save(trace, TRACES_DIR)
        print(f"{trace_id}: {words(trace['reasoning'])} words")


if __name__ == "__main__":
    main()
