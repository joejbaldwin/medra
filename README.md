# MeDRA

**Mapa de Despliegue del Razonamiento Agente**: a real-time dashboard that turns a
model's chain-of-thought into a visual map while the reasoning is still streaming.

Text mining (cleaning, lemmatisation, n-grams, TF-IDF per segment, co-occurrence,
segmentation and topic clustering) runs on the stream as it arrives. The dashboard
shows the live text next to a concept map, a timeline of topics and the steps the
model takes. Every bubble, segment and topic links back to the words it came from.

The system has four interchangeable layers:

1. **Source**: any text stream (an LLM API, pasted text, a recorded dataset).
2. **Mining**: source-agnostic text mining that outputs metrics and term lists with offsets into the text.
3. **Presentation**: turns the metrics into visual decisions (bubble sizes, links, highlights).
4. **Dashboard**: the web frontend.

Final project for *Inteligencia Artificial en las Organizaciones* (UC3M, 2026/27), Grupo 1.

## Run locally

Needs Python 3.11+ and Node 20+. All commands start in the repo root.

**1. Install (once)**

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.lock
.venv/Scripts/python -m pip install -e "backend[dev]"
cd frontend && npm install && cd ..
```

On macOS/Linux, write `.venv/bin/` instead of `.venv/Scripts/` here and below.

**2. Optional: live DeepSeek**

```sh
cp .env.example .env      # then set DEEPSEEK_API_KEY in .env
```

The recorded traces and pasted text work without a key.

**3. Start (two terminals, each time)**

```sh
# terminal 1: backend on http://127.0.0.1:8000
.venv/Scripts/medra-serve
```

```sh
# terminal 2: dashboard
cd frontend && npm run dev
```

**4. Open** http://localhost:5173 and press the purple send button.

The page opens in light mode with the chat on the right, two empty slots on the left, a blank
page 2 and the trace «Sum of the first 100 odd numbers» selected.

Pick a trace in **Traza** and press the round send button in the chat: the prompt appears as a
message, then the model's reasoning streams in below it, split into segments («tramos») coloured
by topic, followed by its answer. The windows on the left follow the text live. Click **+ Añadir
visualización** in an empty slot to add the concept map, the topic timeline or the step graph.
Drag a window by its handle (or focus the handle and use the arrow keys) to swap it with another
slot. **⤢** makes a visualization fill its column or its row (two slots; **⤡** shrinks it back),
**−** removes a window (the analysis is kept), and the chevron shrinks the chat to a quarter.
While a trace plays or a model answers, the send button becomes a square: press it to stop.
The **1 / 2 / +** selector switches between pages of windows for the same session.
**Estadísticas** in the header opens a popup with the current trace's text-mining figures (words,
sentences, segments, topics, concepts, co-occurrence links, lexical diversity, hedges, top concepts,
steps by type, language, and the last tokens the miner processed). How to read each view is in the
tooltip on its title.

The **Fuente** menu picks where the text comes from:

| Source | What it does | Needs |
|---|---|---|
| Traza de ejemplo | replays a recorded trace from `data/samples/` | nothing |
| Pegar texto | replays text you paste (a `<think>…</think>` block is split off from the answer) | nothing |
| DeepSeek Flash | asks `deepseek-flash` and streams its reasoning, then its answer; the menu shows the configured model's name (`MEDRA_DEEPSEEK_MODEL`) | `DEEPSEEK_API_KEY` |

Copy `.env.example` to `.env` and put the DeepSeek key there; it is read only by the backend and
never sent to the browser or logged. Only one DeepSeek session runs at a time, and
`MEDRA_LIVE_DISABLED=1` switches it off. On the deployed backend a DeepSeek
question also needs an access code (see [Deploy](#deploy)); locally it does not. Questions sent to DeepSeek leave this
machine, so don't type personal data.

Each layer is also a command reading and writing JSON Lines:

```sh
medra-source replay login-es --chunking random | medra-mine | medra-present > frames.jsonl
medra-source paste trace.txt | medra-mine | medra-present > frames.jsonl
medra-source deepseek "¿Cuántos primos hay menores que 50?" | medra-mine > metrics.jsonl
```

## Tests

```sh
cd backend && ../.venv/Scripts/python -m pytest      # backend
cd frontend && npm run typecheck && npm test         # dashboard
```

End to end, with the backend and dashboard running (needs Playwright, see below): plays a trace,
checks that every paragraph shows exactly the source text, and that clicking each bubble
highlights exactly its mentions (and clicking a mention selects the bubble):

```sh
.venv/Scripts/python scripts/e2e_dashboard.py --sample login-es
```

The dashboard's layout has its own check: it adds, removes, drags and moves windows by keyboard,
grows them to two slots and back, collapses the chat, switches pages, stops a running session,
opens the «Estadísticas» popup and the «Fuente» menu, and exercises the «Añadir visualización»
picker (search, filters, Escape, focus), using recorded and pasted text only:

```sh
.venv/Scripts/python scripts/ui_dashboard.py
```

## Screenshots

With the backend and dashboard running, `scripts/screenshots.py` replays a trace in a headless
browser and saves to `screenshots/` (not committed) the empty first page, the «Añadir
visualización» picker, and streaming and final captures (light and dark, with the concept map
and the topic timeline added); `--select ID` adds one with that bubble selected, `--topic N` one with the N-th topic
selected, and `--step N` one with the step graph added and the N-th step selected:

```sh
.venv/Scripts/python -m pip install -e "backend[figures]"
.venv/Scripts/python -m playwright install chromium-headless-shell
.venv/Scripts/python scripts/screenshots.py --prefix step6 --select contraseña --topic 1 --step 3 --channel chromium-headless-shell
```

`--source paste --paste-file FILE` captures pasted text instead, and `--source deepseek --prompt "..."`
a live run (each colour scheme is one API call, so add `--schemes light`).

## Evaluation

`eval/` measures the miner against hand annotations (build plan §8). Run from the repo root:

```sh
.venv/Scripts/python -m pip install -e "backend[eval]"   # matplotlib, pytest
.venv/Scripts/python -m eval.annotations --check          # every annotation matches its trace
.venv/Scripts/python -m eval.tune                         # grid search on dev, scored on test + LOOCV
.venv/Scripts/python -m eval.run                          # all metrics -> eval/results/results.md
.venv/Scripts/python -m eval.bench                        # ms per update on a 30,000-word stream
.venv/Scripts/python -m eval.figures                      # PNG figures for the report
.venv/Scripts/python -m pytest eval                       # the metrics' own tests
```

- **Data.** `eval/traces/`: 16 English reasoning traces, 12 recorded from DeepSeek in thinking
  mode (`eval/record_traces.py`) and 4 DeepSeek-R1 traces from OpenThoughts-114k
  (`eval/fetch_openthoughts.py`). `eval/annotations/<id>.md`: the same text with a `[[type]]` tag
  where each reasoning step starts, plus the key concepts and topics. `GUIDE.md` (Spanish)
  explains how to annotate. The drafts were written by an AI assistant and are corrected by the
  group; only files with `status: corrected` count. `--drafts` runs the scripts on the drafts as
  well, for testing the code, and writes to `eval/results/drafts/` (not committed).
- **Segmentation.** Pk and WindowDiff (lower is better) and boundary F1 (within one sentence)
  against baselines: fixed-size segments, a boundary at every blank line, at every discourse
  marker, and TextTiling.
- **Step types, concepts, topics.** Accuracy and macro-F1 of the step type at each reference
  boundary, P/R/F1 of the bubbles against the annotated concepts, and B-cubed F1 of the topics
  (Louvain vs agglomerative clustering). Agreement between annotators on traces annotated twice.
- **"Fine-tuning"** means tuning the segmenter's parameters (`SegParams` in
  `backend/medra/mining/segment.py`) by grid search on a fixed dev split (seed 0, stratified by
  source model). Results are reported once on test and with leave-one-out cross-validation. No
  model is trained.

## Deploy

The backend runs on Google Cloud Run and the dashboard on GitHub Pages.

**Backend.** The [Dockerfile](Dockerfile) holds only the backend and the sample traces. Try it
locally with `docker build -t medra . && docker run -p 7860:7860 --env-file .env medra`. To
publish it, you need the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) and a project
with billing on (the free tier covers this use):

```sh
gcloud auth login
.venv/Scripts/python scripts/deploy_cloudrun.py --project <project-id> --secrets   # first time
.venv/Scripts/python scripts/deploy_cloudrun.py --project <project-id>             # redeploys
```

`--secrets` copies `DEEPSEEK_API_KEY` and `MEDRA_DEPLOY_ACCESS_CODES` (`code:n,code:n`, where n is
DeepSeek sessions per UTC day for that code) from `.env` into Secret Manager. It never prints them.
The service sees the codes as `MEDRA_ACCESS_CODES`. The script runs one instance with 1 GiB of
memory, scales to zero when idle (so the first request after a pause waits a few seconds), and
allows browser calls only from `https://joejbaldwin.github.io`.

With access codes set, a DeepSeek question asks once per tab for a code (the `X-Access-Code`
header of `POST /sessions`). The answer is 401 for a wrong code and 429 when the code's daily
budget is used up. Recorded traces and pasted text never need a code. The counts are kept in
memory, so they also reset when the instance restarts. `MEDRA_MAX_TOKENS` caps the cost of each
session, and `MEDRA_LIVE_DISABLED=1` is the kill switch.

**Dashboard.** [.github/workflows/pages.yml](.github/workflows/pages.yml) builds `frontend/` and
publishes it on each push to `main` that touches the frontend. It reads the backend's URL from the
repository variable `MEDRA_BACKEND_URL` (*Settings → Secrets and variables → Actions →
Variables*). Turn on Pages under *Settings → Pages → Source: GitHub Actions*.

## Contracts

The messages between layers are Pydantic models in [backend/medra/contracts.py](backend/medra/contracts.py),
frozen as schema v1 in [docs/contracts/v1.schema.json](docs/contracts/v1.schema.json) (currently 1.5;
minor versions only add fields with defaults). The dashboard's TypeScript types are generated from
that schema. After changing a contract, bump `SCHEMA_VERSION`, then:

```sh
cd backend && ../.venv/Scripts/python -m medra.schema ../docs/contracts/v1.schema.json
cd frontend && npm run gen:types
```
