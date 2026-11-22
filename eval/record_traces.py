"""Record real reasoning traces from DeepSeek for the evaluation set.

    python -m eval.record_traces            # record every prompt not yet saved
    python -m eval.record_traces en-log-seats en-cod-intervals   # only these

Each trace is saved as eval/traces/<id>.json in the same format as
data/samples/, so the dashboard can replay it too. A trace is kept only if
its reasoning is in the intended language and long enough to segment; very long ones
are kept but flagged, since they are slow to annotate by hand.

This spends a little of the group's DeepSeek credit. The key is read from
.env like the server does and is never printed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import date
from pathlib import Path

from medra.mining.language import stopword_hits
from medra.settings import get_settings
from medra.sources import DeepSeekSource, SourceError

TRACES_DIR = Path(__file__).parent / "traces"
MIN_WORDS = 300
LONG_WORDS = 2000  # above this, flagged as slow to annotate
MAX_TOKENS = 6000  # enough room for the reasoning and the answer

# All prompts are in English. DeepSeek's thinking is in English even when
# asked in Spanish: 7 of 9 Spanish prompts gave English reasoning (the other 2
# were too short to keep), and a Spanish system message did not change it on
# deepseek-flash or deepseek-v4-pro (22/11/2026). The evaluation uses real
# chains of thought only, so it is English (build plan §8).

# id: (title, language, prompt). Medium-difficulty problems, so the reasoning
# has several steps (planning, checks, corrections) but stays annotatable.
PROMPTS: dict[str, tuple[str, str, str]] = {
    # Maths
    "en-mat-dice": ("Sum of three dice", "en",
        "I roll three ordinary six-sided dice. What is the probability that the sum is exactly 10? "
        "Check it in two different ways."),
    "en-mat-trains": ("Two trains passing", "en",
        "A train leaves Madrid for Barcelona at 9:00 at 120 km/h. Another leaves Barcelona for Madrid at 9:30 at "
        "100 km/h, but stops for 15 minutes in Zaragoza, 300 km from Barcelona. The total distance is 620 km. "
        "At what time and how far from Madrid do they meet?"),
    "en-mat-square": ("Perfect square", "en",
        "Find all positive integers n such that n^2 + 2n + 12 is a perfect square, and prove that there are no "
        "others. Then do the same for n^2 + 6n + 50."),
    "en-mat-clock": ("Clock hands", "en",
        "At exactly what times between 3:00 and 4:00 do the hands of a clock form a right angle?"),
    "en-mat-coins": ("Making change", "en",
        "In how many ways can you make 50 cents using pennies, nickels, dimes and quarters? And how many ways "
        "are there to make one dollar if half-dollars are also allowed? Double-check both counts."),
    "en-mat-semicircle": ("Rectangle in a semicircle", "en",
        "A rectangle is inscribed in a semicircle of radius 5, with one side on the diameter. What is its maximum "
        "area? Solve it with calculus and then check it another way."),
    # Code
    "en-cod-palindrome": ("Longest palindromic substring", "en",
        "Write a Python function that returns the longest palindromic substring of a string. Compare two "
        "approaches and explain the complexity of each."),
    "en-cod-search": ("Bug in a binary search", "en",
        "This Python code sometimes loops forever. Find the bug and fix it:\n\n"
        "def search(items, x):\n    lo, hi = 0, len(items) - 1\n    while lo < hi:\n        mid = (lo + hi) // 2\n"
        "        if items[mid] < x:\n            lo = mid\n        else:\n            hi = mid\n"
        "    return lo if items and items[lo] == x else -1\n"),
    "en-cod-lru": ("LRU cache", "en",
        "Design an LRU cache in Python with get and put in O(1) time, without using OrderedDict. Explain which "
        "data structures you use and why."),
    "en-cod-intervals": ("Merging intervals", "en",
        "Write a Python function that merges overlapping intervals in a list such as [[1,3],[2,6],[8,10],[15,18]]. "
        "Think about edge cases such as touching intervals and unsorted input."),
    # Logic
    "en-log-seats": ("Four friends in a row", "en",
        "Ana, Bruno, Carla and David sit on four chairs in a row. Bruno is not at either end. Carla is to the "
        "right of Ana, though not necessarily next to her. David does not sit next to Bruno. Ana is not in the "
        "leftmost chair. In what order do they sit? Is there only one solution?"),
    "en-log-knights": ("Knights and knaves", "en",
        "On an island, knights always tell the truth and knaves always lie. A says: \"B is a knave.\" B says: "
        "\"A and C are the same type.\" C says: \"I am a knight or B is.\" What is each of them?"),
    "en-log-pets": ("Three friends and their pets", "en",
        "Three friends, Alice, Ben and Chloe, each own a different pet (cat, dog, parrot) and live in houses "
        "numbered 1 to 3. The dog owner lives next to Alice. Ben does not own the cat. Chloe lives in house 3. "
        "The parrot owner lives in house 1. Who owns which pet and who lives where? Is the solution unique?"),
}


def words(text: str) -> int:
    return len(re.findall(r"\S+", text))


async def record(trace_id: str, title: str, language: str, prompt: str, model: str) -> dict:
    s = get_settings()
    source = DeepSeekSource(prompt, trace_id, api_key=s.deepseek_api_key, model=model,
                            base_url=s.deepseek_url, max_tokens=MAX_TOKENS)
    parts: dict[str, list[str]] = {"reasoning": [], "answer": []}
    async for chunk in source.stream():
        parts[chunk.channel].append(chunk.text)
    reasoning = "".join(parts["reasoning"]).strip()
    return {
        "id": trace_id,
        "title": title,
        "language": language,
        "prompt": prompt,
        "reasoning": reasoning,
        "answer": "".join(parts["answer"]).strip(),
        "origin": (f"Razonamiento real de DeepSeek ({model}, modo thinking), grabado el "
                   f"{date.today().isoformat()} con eval/record_traces.py; sin editar."),
        "meta": {"finish_reason": source.finish_reason, "usage": source.usage},
    }


def check(trace: dict) -> str | None:
    """Why the trace should be discarded, or None to keep it."""
    n = words(trace["reasoning"])
    if n < MIN_WORDS:
        return f"too short ({n} words)"
    if trace["meta"]["finish_reason"] != "stop":
        return f"did not finish (finish_reason={trace['meta']['finish_reason']})"
    hits = stopword_hits(trace["reasoning"])
    other = "en" if trace["language"] == "es" else "es"
    # The miner's own rule (language.py): at least twice the other language's
    # stopwords. Code can add a few false hits ("lo" as a variable name).
    if hits[trace["language"]] < 2 * hits[other]:
        return f"wrong language (stopword hits {hits})"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ids", nargs="*", help="prompt ids to record (default: those not yet saved)")
    parser.add_argument("--force", action="store_true", help="re-record even if the file exists")
    parser.add_argument("--model", default=None, help="DeepSeek model (default: MEDRA_DEEPSEEK_MODEL)")
    parser.add_argument("--discarded", type=Path, default=None, help="also save discarded traces in this folder")
    args = parser.parse_args()
    if not get_settings().deepseek_api_key:
        sys.exit("DEEPSEEK_API_KEY is not set (.env or environment)")
    unknown = set(args.ids) - set(PROMPTS)
    if unknown:
        sys.exit(f"unknown ids: {sorted(unknown)}")
    TRACES_DIR.mkdir(exist_ok=True)
    for trace_id in args.ids or list(PROMPTS):
        path = TRACES_DIR / f"{trace_id}.json"
        if path.exists() and not args.force:
            print(f"{trace_id}: already saved, skipped")
            continue
        try:
            trace = asyncio.run(record(trace_id, *PROMPTS[trace_id], model=args.model or get_settings().deepseek_model))
        except SourceError as exc:
            print(f"{trace_id}: FAILED: {exc}")
            continue
        n = words(trace["reasoning"])
        problem = check(trace)
        if problem:
            print(f"{trace_id}: discarded, {problem}")
            if args.discarded:
                args.discarded.mkdir(parents=True, exist_ok=True)
                (args.discarded / f"{trace_id}.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2),
                                                                 encoding="utf-8")
            continue
        path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        flag = " (long: slow to annotate)" if n > LONG_WORDS else ""
        print(f"{trace_id}: saved, {n} words, usage={trace['meta']['usage']}{flag}")


if __name__ == "__main__":
    main()
