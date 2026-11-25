"""Pick 150 OpenThoughts-114k rows for the step-type training set (eval/train/).

    python -m eval.pick_train_rows picked.json
    python -m eval.fetch_openthoughts --rows <the rows in picked.json>

Blocks of 100 rows are sampled (fixed seed) across each domain's range, rows
with 300-1800 words of reasoning are kept, sorted into kinds (logic puzzles
by keywords in the math domain; science = calculation problems), near
duplicates of the evaluation problems, the new DeepSeek problems and each
other are dropped, and within each kind the rows whose reasoning shows the
most variety (checks, alternatives, corrections per 1000 words) are taken.
Writes the chosen rows (and the number of candidates) as JSON to the path given.
Run on 25/11/2026: 248 blocks of 100 rows scanned, 8,148 candidates within the word
limits, 150 chosen (55 maths, 40 logic, 35 code, 20 science by this script's keywords);
the chosen rows are the ot-*.json files in eval/train/traces/.
"""

import json
import random
import re
import sys
from pathlib import Path

import yaml

from eval.common import TRACES_DIR
from eval.fetch_openthoughts import ROWS, fetch_page

TARGET = {"maths": 55, "logic": 40, "code": 35, "science": 20}
RANGES = {  # (first row, last row, blocks of 100 to sample)
    "math": (0, 89_900, 220),
    "code": (90_000, 109_900, 14),
    "science": (110_000, 112_900, 14),
}
MIN_WORDS, MAX_WORDS = 300, 1800

LOGIC = re.compile(
    r"\b(knights?|knaves?|liars?|truth[- ]?tellers?|tells? the truth|always lies|(?:is|are) lying|"
    r"(?:statements?|claims?) (?:is|are) (?:true|false)|sitting|seated|around a (?:round )?table|"
    r"weighings?|balance scale|counterfeit|fake coins?|hats?|logic puzzle|who (?:is|was|did|owns|stole|lives)|"
    r"tournament|played (?:each|against)|winning strategy|takes? turns|envelopes|each (?:boy|girl|friend) said)\b",
    re.I)
ESSAY = re.compile(r"^\s*(how|why|what are|what is the (role|effect|impact|mechanism)|explain|describe|discuss)\b", re.I)
VARIETY = re.compile(
    r"\b(wait|alternatively|another (way|approach)|let me (check|verify|double[- ]check|confirm)|"
    r"double[- ]check|mistake|that's (not right|wrong)|on second thought|hmm|but then|let's verify|"
    r"check(ing)?|verify|re-?examine|reconsider)\b", re.I)


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", text.lower()))


def similar(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(1, min(len(a), len(b)))


def kind_of(domain: str, problem: str) -> str | None:
    if domain == "math":
        return "logic" if LOGIC.search(problem) else "maths"
    if domain == "code":
        return "code"
    if domain in ("biology", "physics", "chemistry"):
        if ESSAY.search(problem) or not re.search(r"\d", problem):
            return None  # essay question, not a calculation
        return "science"
    return None


def main() -> None:
    out = Path(sys.argv[1])
    rng = random.Random(0)
    taken = {row for row, _ in ROWS.values()}
    avoid = [words(json.loads(p.read_text(encoding="utf-8"))["prompt"]) for p in TRACES_DIR.glob("*.json")]
    avoid += [words(str(x["prompt"])) for x in yaml.safe_load(Path("eval/train/prompts.yaml").read_text(encoding="utf-8"))]
    candidates = []
    for domain, (first, last, blocks) in RANGES.items():
        starts = rng.sample(range(first, last + 1, 100), blocks)
        for i, start in enumerate(sorted(starts)):
            try:
                page = fetch_page(start, 100)
            except Exception as exc:  # noqa: BLE001 - a busy API page is skipped
                print(f"{domain} {start}: failed ({exc})", flush=True)
                continue
            for row, r in page:
                reasoning = r["deepseek_reasoning"]
                n = len(reasoning.split())
                kind = kind_of(r["domain"], r["problem"])
                if row in taken or kind is None or not MIN_WORDS <= n <= MAX_WORDS:
                    continue
                candidates.append({
                    "row": row, "domain": r["domain"], "kind": kind, "words": n,
                    "variety": round(1000 * len(VARIETY.findall(reasoning)) / n, 2),
                    "problem": " ".join(r["problem"].split())[:400],
                })
            print(f"{domain}: block {i + 1}/{blocks} at {start}, {len(candidates)} candidates so far", flush=True)

    chosen: list[dict] = []
    seen: list[set[str]] = []
    for kind, n in TARGET.items():
        pool = sorted((c for c in candidates if c["kind"] == kind), key=lambda c: -c["variety"])
        picked = 0
        for c in pool:
            w = words(c["problem"])
            if any(similar(w, a) > 0.6 for a in avoid) or any(similar(w, s) > 0.6 for s in seen):
                continue
            chosen.append(c)
            seen.append(w)
            picked += 1
            if picked == n:
                break
        print(f"{kind}: {picked} of {n} (pool {len(pool)})", flush=True)
    out.write_text(json.dumps({"chosen": chosen, "candidates": len(candidates)}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
