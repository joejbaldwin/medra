"""Efficiency benchmark: cost per update as the text grows.

    python -m eval.bench                # ~30,000 words
    python -m eval.bench --words 10000

The evaluation traces are joined (and repeated if needed) into one long text
and streamed word by word, about the size of a DeepSeek streaming chunk,
through the same TextMiner and ViewPresenter the server uses. For every chunk
that commits a sentence (and so produces a MiningUpdate) the time of
miner.feed and of presenter.present is recorded against the words so far.

The miner rebuilds the snapshot (segments, TF-IDF, PMI, topics) from its
per-sentence counts on each update, so its cost grows with the text; the
question is whether it stays well below the time between sentences of a live
stream. The server also throttles views to at most 5 per second
(pipeline.MIN_VIEW_INTERVAL), which this benchmark does not do: here every
update is presented, the worst case.

Writes eval/results/bench.json and bench.md. Timings depend on the machine;
the report records it.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import time
from datetime import date

import numpy as np

from eval.common import RESULTS_DIR, get_trace, git_commit, trace_ids
from medra.contracts import TextChunk
from medra.mining.miner import TextMiner
from medra.present import ViewPresenter

BUCKET_WORDS = 5000


def long_text(target_words: int) -> str:
    parts, words = [], 0
    traces = [get_trace(t).reasoning for t in trace_ids()]
    while words < target_words:
        for text in traces:
            parts.append(text)
            words += len(text.split())
            if words >= target_words:
                break
    return "\n\n".join(parts)


def run(target_words: int) -> dict:
    text = long_text(target_words)
    chunks = re.findall(r"\S+\s*|\s+", text)
    miner = TextMiner("bench")
    presenter = ViewPresenter()
    rows = []  # (words so far, miner ms, presenter ms)
    words = 0
    started = time.perf_counter()
    for seq, piece in enumerate(chunks):
        words += bool(piece.strip())
        final = seq == len(chunks) - 1
        t0 = time.perf_counter()
        update = miner.feed(TextChunk(session_id="bench", seq=seq, channel="reasoning", text=piece, t=0.0, final=final))
        t1 = time.perf_counter()
        if update is not None:
            presenter.present(update)
            t2 = time.perf_counter()
            rows.append((words, (t1 - t0) * 1000, (t2 - t1) * 1000))
    total = time.perf_counter() - started

    buckets = []
    for lo in range(0, words, BUCKET_WORDS):
        sel = [r for r in rows if lo < r[0] <= lo + BUCKET_WORDS]
        if not sel:
            continue
        m = np.array([r[1] for r in sel])
        both = np.array([r[1] + r[2] for r in sel])
        buckets.append({"words": f"{lo + 1}-{lo + BUCKET_WORDS}", "updates": len(sel),
                        "miner_p50_ms": float(np.percentile(m, 50)), "miner_p95_ms": float(np.percentile(m, 95)),
                        "total_p50_ms": float(np.percentile(both, 50)), "total_p95_ms": float(np.percentile(both, 95))})
    return {
        "date": date.today().isoformat(),
        "commit": git_commit(),
        "machine": {"platform": platform.platform(), "processor": platform.processor(),
                    "python": platform.python_version()},
        "words": words,
        "chunks": len(chunks),
        "updates": len(rows),
        "seconds": round(total, 2),
        "words_per_second": round(words / total, 1),
        "sentences_per_second": round(len(rows) / total, 1),
        "buckets": buckets,
    }


def report(r: dict) -> str:
    lines = ["# Eficiencia de MeDRA", "",
             f"`python -m eval.bench`, {r['date']}, commit {r['commit']}. Máquina: {r['machine']['platform']}, "
             f"{r['machine']['processor'] or 'CPU desconocida'}, Python {r['machine']['python']}.", "",
             f"{r['words']} palabras en {r['chunks']} trozos de una palabra, {r['updates']} actualizaciones "
             f"(una por trozo que cierra al menos una frase). Minero + presentador en cada actualización (sin el "
             f"límite de 5 vistas/s del servidor): {r['seconds']} s en total, **{r['words_per_second']} palabras/s** "
             f"sostenidas de media.", "",
             "| Palabras ya recibidas | Actualizaciones | Minero p50 (ms) | Minero p95 (ms) | Total p50 (ms) "
             "| Total p95 (ms) |", "|---|---|---|---|---|---|"]
    for b in r["buckets"]:
        lines.append(f"| {b['words']} | {b['updates']} | {b['miner_p50_ms']:.1f} | {b['miner_p95_ms']:.1f} "
                     f"| {b['total_p50_ms']:.1f} | {b['total_p95_ms']:.1f} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Time the miner and presenter on a long streamed text.")
    parser.add_argument("--words", type=int, default=30000)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    result = run(args.words)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "bench.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    md = report(result)
    (RESULTS_DIR / "bench.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
