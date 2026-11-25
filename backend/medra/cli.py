"""Each layer as a command that reads and writes JSON Lines:

    medra-source replay login-es | medra-mine | medra-present > frames.jsonl
    medra-source deepseek "¿Cuántos primos hay menores que 50?" | medra-mine > mining.jsonl

Output is ASCII-escaped JSON (é -> \\u00e9) on purpose: Windows PowerShell
5.1 re-encodes text piped between programs (with the console code page, and
sometimes a byte-order mark) and would mangle accents otherwise. Any JSON
parser reads it back unchanged.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Iterable, Iterator

from pydantic import BaseModel

from medra.contracts import MiningUpdate, TextChunk

# Each command imports only its own layer (inside its function): the source
# and presenter commands should not pay for loading spaCy and scikit-learn.


def write_jsonl(model: BaseModel) -> None:
    sys.stdout.write(json.dumps(model.model_dump(mode="json"), ensure_ascii=True) + "\n")
    sys.stdout.flush()


def read_jsonl(lines: Iterable[str], model: type[BaseModel]) -> Iterator:
    for line in lines:
        # PowerShell may prepend a UTF-8 byte-order mark to piped input.
        line = line.lstrip("﻿")
        if line.strip():
            yield model.model_validate_json(line)


def source_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="medra-source", description="Layer 1: emit TextChunks.")
    sub = parser.add_subparsers(dest="kind", required=True)
    replay = sub.add_parser("replay", help="replay a sample trace (id or path to .json)")
    replay.add_argument("sample")
    replay.add_argument("--wps", type=float, default=0.0, help="words per second; 0 = no pacing")
    replay.add_argument("--chunking", choices=["word", "random"], default="word")
    replay.add_argument("--seed", type=int, default=0)
    replay.add_argument("--session-id", default="cli")
    paste = sub.add_parser("paste", help="replay any text file (split at </think> if present)")
    paste.add_argument("file")
    paste.add_argument("--wps", type=float, default=0.0, help="words per second; 0 = no pacing")
    paste.add_argument("--chunking", choices=["word", "random"], default="word")
    paste.add_argument("--seed", type=int, default=0)
    paste.add_argument("--session-id", default="cli")
    live = sub.add_parser("deepseek", help="ask DeepSeek live; uses the server settings (.env)")
    live.add_argument("prompt")
    live.add_argument("--session-id", default="cli")
    args = parser.parse_args(argv)
    from medra.sources import DeepSeekSource, PasteSource, ReplaySource, load_trace

    if args.kind == "replay":
        source = ReplaySource(
            load_trace(args.sample), args.session_id, words_per_second=args.wps, chunking=args.chunking, seed=args.seed
        )
    elif args.kind == "paste":
        with open(args.file, encoding="utf-8-sig") as f:
            text = f.read()
        source = PasteSource(text, args.session_id, words_per_second=args.wps, chunking=args.chunking, seed=args.seed)
    else:
        from medra.settings import get_settings

        s = get_settings()
        if not s.deepseek_api_key:
            sys.exit("DEEPSEEK_API_KEY is not set (.env or environment)")
        source = DeepSeekSource(args.prompt, args.session_id, api_key=s.deepseek_api_key, model=s.deepseek_model,
                                base_url=s.deepseek_url, max_tokens=s.max_tokens)

    async def run() -> None:
        async for chunk in source.stream():
            write_jsonl(chunk)

    asyncio.run(run())


def mine_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="medra-mine", description="Layer 2: TextChunks in, MiningUpdates out.")
    parser.add_argument("--miner", choices=["text", "stub"], default="text")
    args = parser.parse_args(argv)
    from medra.mining import Miner, make_miner

    miner: Miner | None = None
    for chunk in read_jsonl(sys.stdin, TextChunk):
        miner = miner or make_miner(args.miner, chunk.session_id)
        update = miner.feed(chunk)
        if update is not None:
            write_jsonl(update)


def present_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="medra-present", description="Layer 3: MiningUpdates in, ViewUpdates out.")
    parser.add_argument("--presenter", choices=["view", "stub"], default="view")
    args = parser.parse_args(argv)
    from medra.present import StubPresenter, ViewPresenter

    presenter = ViewPresenter() if args.presenter == "view" else StubPresenter()
    for update in read_jsonl(sys.stdin, MiningUpdate):
        view = presenter.present(update)
        if view is not None:
            write_jsonl(view)


def serve_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="medra-serve", description="Run the backend.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args(argv)
    import uvicorn

    uvicorn.run("medra.server:app", host=args.host, port=args.port, reload=args.reload)
