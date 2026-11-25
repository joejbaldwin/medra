# Training traces for the step-type classifier

Annotated traces used only to **train** the step-type classifier
(`backend/medra/mining/steptypes.py`, trained by `python -m eval.steptypes`). They are kept apart
from the 30 evaluation traces in `eval/traces/`, so the evaluation set and its dev/test split never
change and the test results stay comparable.

| Path | What |
|---|---|
| `traces/ot-<row>.json` | OpenThoughts-114k rows (DeepSeek-R1): `python -m eval.fetch_openthoughts --rows ...` |
| `traces/ds-<kind>-<n>.json` | DeepSeek traces of the problems in `prompts.yaml`: `python -m eval.record_traces --prompts eval/train/prompts.yaml` |
| `prompts.yaml` | the problems sent to DeepSeek: a list of `{id, title, prompt}` |
| `annotations/<id>.md` | the step tags, same format as `eval/annotations/` (concepts and topics optional) |

Useful commands:

```sh
python -m eval.fetch_openthoughts --scan 500 300            # rows 500-799 with 300-1800 words of reasoning
python -m eval.annotations --sentences ot-680              # numbered sentences, as MeDRA splits them
python -m eval.annotations --write ot-680 --tags "0:planning,5:development,40:verification"
python -m eval.annotations --check --train                 # check every training annotation
```

Step types and how to choose them: `eval/annotations/GUIDE.md`.
