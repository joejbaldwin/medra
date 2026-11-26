# Annotation guide

Each file is a reasoning trace with a `[[type]]` tag where each step starts. The front matter holds:

- `concepts:` 5-10 key terms, as written in the text (no generic words like "answer" or "step").
- `topics:` 2-5 groups of 3-8 related terms, each term in one group only.
- `status: corrected` once the file is final; only those files count in the results.

`python -m eval.annotations --check` checks every file.

## Rules

- Never change the text itself, only the tags (the checker compares it byte for byte).
- Put a tag right before the first word of a sentence, never inside one.
- Don't split one long calculation into several steps if its purpose doesn't change.
- `python -m eval.annotations --sentences <id>` shows how MeDRA numbers the sentences.
- Annotate without looking at MeDRA's output for that trace, so the reference does not copy the system.

## Step types

| Type | Use when the reasoning is... |
|---|---|
| `planning` | understanding the problem or deciding how to approach it |
| `development` | doing the work: calculating, deducing, writing code |
| `verification` | checking a result it already has (including re-solving another way to confirm) |
| `backtrack` | noticing a mistake and correcting it |
| `alternative` | trying a different approach, case or interpretation to make progress |
| `conclusion` | stating the result or deciding what to answer |
