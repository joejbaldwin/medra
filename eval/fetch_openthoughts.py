"""Fetch a few short English traces from OpenThoughts-114k for the evaluation set.

    python -m eval.fetch_openthoughts

OpenThoughts-114k (Apache-2.0) holds DeepSeek-R1 reasoning for maths and code
problems. Rows are read one at a time from the Hugging Face datasets-server
API (no download of the full dataset), and saved as eval/traces/<id>.json in
the data/samples/ format. The rows were picked by hand among those with
300-1300 words of reasoning, to add another model's style to the set.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

TRACES_DIR = Path(__file__).parent / "traces"
API = "https://datasets-server.huggingface.co/rows?dataset=open-thoughts/OpenThoughts-114k&config=metadata&split=train"

# id: (row index in the train split, title)
ROWS = {
    "ot-mat-plums": (12, "Plums, apples and a pear"),
    "ot-mat-trail": (47, "Jitka's hike"),
    "ot-log-krakozyabrs": (84, "Horns and wings"),
    "ot-cod-yen": (100002, "Change from 1000-yen bills"),
}


def fetch(row: int) -> dict:
    with urllib.request.urlopen(f"{API}&offset={row}&length=1", timeout=60) as resp:
        data = json.load(resp)
    return data["rows"][0]["row"]


def main() -> None:
    TRACES_DIR.mkdir(exist_ok=True)
    for trace_id, (row, title) in ROWS.items():
        r = fetch(row)
        trace = {
            "id": trace_id,
            "title": title,
            "language": "en",
            "prompt": r["problem"].strip(),
            "reasoning": r["deepseek_reasoning"].strip(),
            "answer": r["deepseek_solution"].strip(),
            "origin": (f"OpenThoughts-114k (Apache-2.0), fila {row} de train (dominio {r['domain']}): razonamiento "
                       "de DeepSeek-R1; descargado con eval/fetch_openthoughts.py; sin editar."),
        }
        path = TRACES_DIR / f"{trace_id}.json"
        path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"{trace_id}: {len(trace['reasoning'].split())} words")


if __name__ == "__main__":
    main()
