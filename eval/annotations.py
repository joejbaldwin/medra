"""Hand annotations of the evaluation traces: format, loading and checks.

One file per trace, eval/annotations/<id>.md:

    ---
    trace: en-log-pets
    annotator: claude-draft
    status: draft            # draft | corrected
    concepts: [dog owner, house, parrot]
    topics:
      - [house, number, neighbour]
      - [pet, dog, cat, parrot]
    ---
    [[planning]]We need to find who owns which pet. ...

    [[verification]]Let me check the clues again. ...

The body is the trace's reasoning, unchanged, with a [[type]] tag where each
segment (step) starts. People can edit that in any text editor, unlike
character offsets. The checker removes the tags and requires the rest to equal
the trace byte for byte, then maps each tag to a sentence index using MeDRA's
own sentence splitter, so boundaries are compared sentence by sentence.

    python -m eval.annotations --check          # check every file
    python -m eval.annotations --sentences ID   # print a trace's numbered sentences
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from eval.common import ANNOTATIONS_DIR, mine, trace_ids

STEP_TYPES = ("planning", "development", "verification", "backtrack", "alternative", "conclusion")
STATUSES = ("draft", "corrected")
# Only the six type names count as tags, so "[[1,3],[2,6]]" in a trace is text.
TAG = re.compile(r"\[\[(" + "|".join(STEP_TYPES) + r")\]\]")
_FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


class AnnotationError(ValueError):
    pass


@dataclass(frozen=True)
class Annotation:
    trace_id: str
    annotator: str
    status: str
    starts: list[int]  # sentence indexes that start a segment; starts[0] == 0
    types: list[str]  # step type of each segment, same length as starts
    concepts: list[str]
    topics: list[list[str]]
    n_sentences: int
    path: Path


def annotation_files(directory: Path = ANNOTATIONS_DIR) -> list[Path]:
    """Annotation files: <trace id>.md, or <trace id>.<annotator>.md for a
    second, independent correction (used for inter-annotator agreement)."""
    return sorted(p for p in directory.glob("*.md") if p.name != "GUIDE.md")


def parse(path: Path) -> Annotation:
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = _FRONT.match(raw)
    if not m:
        raise AnnotationError("missing front matter (--- ... --- at the top)")
    meta = yaml.safe_load(m.group(1)) or {}
    body = raw[m.end():]
    if body.endswith("\n"):
        body = body[:-1]  # editors add a final newline; traces are stripped

    trace_id = meta.get("trace") or path.name.split(".")[0]
    if trace_id not in trace_ids():
        raise AnnotationError(f"no trace {trace_id!r} in eval/traces/")
    status = meta.get("status")
    if status not in STATUSES:
        raise AnnotationError(f"status must be one of {STATUSES}, not {status!r}")

    mined = mine(trace_id)
    text = mined.text
    tags = []  # (offset in the untagged text, type)
    pieces = []
    removed = 0
    last = 0
    for t in TAG.finditer(body):
        pieces.append(body[last:t.start()])
        tags.append((t.start() - removed, t.group(1)))
        removed += t.end() - t.start()
        last = t.end()
    pieces.append(body[last:])
    plain = "".join(pieces)
    if plain != text:
        raise AnnotationError("text differs from the trace: " + _first_difference(plain, text))
    if not tags:
        raise AnnotationError("no [[type]] tags")

    starts, types = [], []
    for offset, kind in tags:
        index = _sentence_at(mined.spans, text, offset)
        if starts and index <= starts[-1]:
            raise AnnotationError(f"two tags start the same sentence {index}: {_context(text, offset)}")
        starts.append(index)
        types.append(kind)
    if starts[0] != 0:
        raise AnnotationError("the text must start with a tag (the type of the first segment)")

    concepts = meta.get("concepts") or []
    topics = meta.get("topics") or []
    if not all(isinstance(c, str) for c in concepts):
        raise AnnotationError("concepts must be a list of strings")
    if not all(isinstance(t, list) and all(isinstance(w, str) for w in t) for t in topics):
        raise AnnotationError("topics must be a list of lists of strings")
    return Annotation(
        trace_id=trace_id,
        annotator=str(meta.get("annotator", "")),
        status=status,
        starts=starts,
        types=types,
        concepts=concepts,
        topics=topics,
        n_sentences=len(mined.spans),
        path=path,
    )


def _sentence_at(spans: list[tuple[int, int]], text: str, offset: int) -> int:
    """The sentence a tag at `offset` opens. The tag may sit in the whitespace
    before the sentence, but not inside it."""
    for i, (start, end) in enumerate(spans):
        if offset <= start:
            if text[offset:start].strip():
                break  # there is text between the tag and the sentence
            return i
        if offset < end:
            break  # inside sentence i
    raise AnnotationError(f"tag is not at the start of a sentence: {_context(text, offset)}")


def _context(text: str, offset: int) -> str:
    return repr(text[max(0, offset - 30):offset] + " <<TAG>> " + text[offset:offset + 30])


def _first_difference(a: str, b: str) -> str:
    i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return f"at character {i}: annotation has {a[i:i + 30]!r}, trace has {b[i:i + 30]!r}"


def write(trace_id: str, tags: dict[int, str], *, concepts: list[str], topics: list[list[str]],
          annotator: str, status: str = "draft", path: Path | None = None) -> Path:
    """Write an annotation file with a tag before each given sentence index."""
    mined = mine(trace_id)
    text = mined.text
    out = []
    last = 0
    for index in sorted(tags):
        start = mined.spans[index][0]
        out.append(text[last:start] + f"[[{tags[index]}]]")
        last = start
    out.append(text[last:])
    meta = {"trace": trace_id, "annotator": annotator, "status": status, "concepts": concepts, "topics": topics}
    front = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=None, width=110)
    path = path or ANNOTATIONS_DIR / f"{trace_id}.md"
    path.write_text(f"---\n{front}---\n" + "".join(out) + "\n", encoding="utf-8", newline="\n")
    parse(path)  # what was written must check
    return path


def load_all(status: str | None = None) -> list[Annotation]:
    """Primary annotations (<id>.md), optionally only those with this status."""
    found = [parse(p) for p in annotation_files() if p.name.count(".") == 1]
    return [a for a in found if status is None or a.status == status]


def main() -> None:
    parser = argparse.ArgumentParser(description="Check annotation files or print a trace's sentences.")
    parser.add_argument("--check", action="store_true", help="check every annotation file")
    parser.add_argument("--sentences", metavar="ID", help="print the numbered sentences of a trace")
    parser.add_argument("--blank", nargs=2, metavar=("ID", "NAME"),
                        help="create eval/annotations/ID.NAME.md with no tags but the first, for an independent "
                             "second annotation (inter-annotator agreement)")
    args = parser.parse_args()
    if args.blank:
        trace_id, name = args.blank
        path = ANNOTATIONS_DIR / f"{trace_id}.{name}.md"
        if path.exists():
            sys.exit(f"{path} already exists")
        write(trace_id, {0: "planning"}, concepts=[], topics=[], annotator=name, status="draft", path=path)
        print(f"created {path}")
        return
    if args.sentences:
        mined = mine(args.sentences)
        for i, (a, b) in enumerate(mined.spans):
            print(f"{i:3d} {mined.text[a:b]}")
        return
    failed = 0
    for path in annotation_files():
        try:
            a = parse(path)
        except AnnotationError as exc:
            failed += 1
            print(f"FAIL {path.name}: {exc}")
            continue
        print(f"ok   {path.name}: {a.status}, {len(a.starts)} segments in {a.n_sentences} sentences, "
              f"{len(a.concepts)} concepts, {len(a.topics)} topics ({a.annotator})")
    missing = sorted(set(trace_ids()) - {p.name.split(".")[0] for p in annotation_files()})
    if missing:
        print(f"not annotated yet: {', '.join(missing)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
