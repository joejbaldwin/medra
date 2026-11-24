# Annotation guide

Your traces are the files with your name in `annotator:`. Each file is a reasoning trace with a `[[type]]` tag where each step starts.

## Correcting a draft (`<id>.md`)

1. Read the whole trace before changing anything.
2. Move, add or delete tags so each tag sits where the reasoning changes purpose (not just where it says "Wait").
3. Check each tag's type against the table below.
4. Fix `concepts:` (5-10 key terms, as written in the text, no generic words like "answer" or "step").
5. Fix `topics:` (2-5 groups of 3-8 related terms, each term in one group only).
6. Set `status: corrected`.
7. Run `python -m eval.annotations --check` and fix anything it reports, then commit and push.

The draft was written by an AI: don't trust it, and don't look at MeDRA's dashboard output for that trace while correcting.

## Rules

- Never change the text itself, only the tags (the checker compares it byte for byte).
- Put a tag right before the first word of a sentence, never inside one.
- Don't split one long calculation into several steps if its purpose doesn't change.
- `python -m eval.annotations --sentences <id>` shows how MeDRA numbers the sentences.

## Step types

| Type | Use when the reasoning is... |
|---|---|
| `planning` | understanding the problem or deciding how to approach it |
| `development` | doing the work: calculating, deducing, writing code |
| `verification` | checking a result it already has (including re-solving another way to confirm) |
| `backtrack` | noticing a mistake and correcting it |
| `alternative` | trying a different approach, case or interpretation to make progress |
| `conclusion` | stating the result or deciding what to answer |
