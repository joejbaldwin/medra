"""The layers as separate processes joined by pipes (JSON Lines)."""

import json
import subprocess
import sys


def cmd(func: str, *args: str) -> list[str]:
    return [sys.executable, "-c", f"import sys; from medra.cli import {func}; {func}(sys.argv[1:])", *args]


def test_source_mine_present_pipe():
    source = subprocess.Popen(cmd("source_main", "replay", "login-es", "--chunking", "random"), stdout=subprocess.PIPE)
    mine = subprocess.Popen(cmd("mine_main"), stdin=source.stdout, stdout=subprocess.PIPE)
    present = subprocess.run(cmd("present_main"), stdin=mine.stdout, capture_output=True, check=True)
    source.wait(), mine.wait()
    assert source.returncode == mine.returncode == 0

    raw = present.stdout.decode("ascii")  # ASCII-escaped on purpose (see cli.py)
    views = [json.loads(line) for line in raw.splitlines()]
    assert views[0]["kind"] == "snapshot" and views[-1]["final"]
    labels = {n["label"] for v in views for n in v["nodes"]}
    assert "sesión" in labels  # non-ASCII survives the pipe


def test_reader_ignores_powershell_bom():
    from medra.cli import read_jsonl
    from medra.contracts import TextChunk

    line = '﻿{"session_id": "s", "seq": 0, "channel": "reasoning", "text": "Hola", "t": 0}\n'
    assert [c.text for c in read_jsonl([line, "\n"], TextChunk)] == ["Hola"]
