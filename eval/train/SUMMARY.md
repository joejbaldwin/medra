# Training annotation summary

All 272 supplied traces have a matching annotation. Each batch of 25 traces passed the cumulative training checker, as did the final batch of 22. The final check reported 272 files as `ok` and zero missing annotations. SHA-256 hashes matched the originals for all 272 trace files.

## Traces by source and kind

| Kind | Part A · OpenThoughts | Part B · DeepSeek | Total |
|---|---:|---:|---:|
| Maths | 68 | 44 | 112 |
| Logic | 27 | 32 | 59 |
| Code | 35 | 27 | 62 |
| Science | 20 | 19 | 39 |
| **Total** | **150** | **122** | **272** |

DeepSeek kinds come from the prompt IDs. OpenThoughts records 95 maths-domain rows, 35 code, 11 physics and 9 chemistry. For this report, the logic subset of the maths domain comprises deduction, weighing, arrangement, strategy and number puzzles. The maths/logic boundary is a judgement call. The following OpenThoughts row numbers were counted as logic.

136, 2278, 2753, 3766, 4145, 4195, 11930, 12748, 15056, 17424, 18862, 20926, 22021, 31097, 36579, 45534, 48195, 48760, 49041, 56445, 58197, 58911, 59317, 60387, 62654, 67601, 67655.

## Annotated steps

The follow-up review covered all 272 traces and changed step labels or boundaries in 127 files. First-time solutions and requested worked examples use `development`. Checks against an existing result use `verification`, and drafting the answer uses `conclusion`.

| Step type | Count |
|---|---:|
| planning | 460 |
| development | 885 |
| verification | 1,624 |
| backtrack | 142 |
| alternative | 718 |
| conclusion | 1,194 |
| **Total** | **5,023** |

## Rejections and uncertainties

All supplied files were retained. The saved OpenThoughts files record accepted row IDs only. The 170-entry DeepSeek prompt bank includes 48 IDs without a supplied recording. The available records do not establish a discard reason for each, or whether each was attempted.

| DeepSeek kind | Prompt numbers without a trace |
|---|---|
| Code | 05, 08, 09, 12, 15, 17, 18, 19, 21, 22, 24, 28, 30, 31, 34, 41, 42, 44 |
| Maths | 05, 06, 09, 14, 18, 23, 27, 30, 39, 42, 47 |
| Logic | 02, 12, 17, 19, 20, 23, 25, 27, 28, 30, 37, 38, 40, 41, 44, 46, 47, 50 |
| Science | 03 |

The labels describe what the model was doing, including guesses. For example, `ot-77694` refers to a missing bar graph and the trace guesses a ratio. In `ot-49041`, the trace repeatedly switches between “at least five” and “exactly five” weighings. These are limitations of the underlying answers. The annotations are AI judgements, with no independent human agreement measurement for this set.
