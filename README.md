# MeDRA

**Mapa de Despliegue del Razonamiento Agente**: a real-time dashboard that applies text mining
to a model's chain-of-thought while it streams.

The live text sits next to a concept map, a topic timeline and a step graph, and every bubble,
segment and topic links back to the words it came from. The mining (cleaning, lemmatisation,
n-grams, TF-IDF per segment, co-occurrence, segmentation, topic clustering and a step-type
classifier) runs sentence by sentence as the text arrives.

The system has four interchangeable layers:

1. **Source**: any text stream (an LLM API, pasted text, a recorded trace).
2. **Mining**: source-agnostic text mining that outputs metrics and term lists with offsets into the text.
3. **Presentation**: turns the metrics into visual decisions (bubble sizes, links, highlights).
4. **Dashboard**: the web frontend.

Final project for *Inteligencia Artificial en las Organizaciones* (UC3M, 2026/27), Grupo 1.

**Live version:** https://joejbaldwin.github.io/medra/. Recorded traces and pasted text work
without an account; the live DeepSeek source asks for an access code. The backend sleeps when
idle, so the first request after a pause waits while it starts.

## Repository layout

| Path | What |
|---|---|
| `backend/medra/sources/` | Layer 1: DeepSeek API, pasted text, recorded traces |
| `backend/medra/mining/` | Layer 2: cleaning, sentences, terms, segmentation, TF-IDF, co-occurrence, topics, step-type classifier (`models/step_types_en.json`) |
| `backend/medra/present/` | Layer 3: bubble selection and sizes, edges, topic colours, timeline, diffs |
| `backend/medra/server.py` | FastAPI server: REST + WebSocket, access codes |
| `backend/medra/contracts.py` | the data contracts between layers (snapshot in `docs/contracts/`) |
| `frontend/` | Layer 4: the dashboard (TypeScript + D3, Vite); `estudio.html` is the user-study page |
| `data/samples/` | recorded traces the dashboard can replay |
| `eval/` | annotated traces, metrics, segmenter tuning, classifier training, results (`eval/results/`) |
| `eval/train/` | the training traces of the step-type classifier |
| `scripts/` | Cloud Run deployment, browser checks of the dashboard, screenshots |

## Run locally

Needs Python 3.11+ and Node 20+. Commands start in the repo root; on macOS/Linux write
`.venv/bin/` instead of `.venv/Scripts/`.

```sh
# install (once)
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.lock
.venv/Scripts/python -m pip install -e "backend[dev]"
cd frontend && npm install && cd ..
```

```sh
# terminal 1: backend on http://127.0.0.1:8000
.venv/Scripts/medra-serve
```

```sh
# terminal 2: dashboard on http://localhost:5173
cd frontend && npm run dev
```

Open http://localhost:5173, pick a trace in **Traza** and press the send button. **+ Añadir
visualización** adds the concept map, the topic timeline or the step graph to an empty slot.

The **Fuente** menu picks where the text comes from:

| Fuente | What it does |
|---|---|
| Traza de ejemplo | replays a recorded trace from `data/samples/` |
| Pegar texto | replays pasted text (a `<think>…</think>` block is split off from the answer) |
| DeepSeek Flash | streams a live answer from the DeepSeek API; needs `DEEPSEEK_API_KEY` in `.env` (copy `.env.example`) |

The key is read only by the backend and is never sent to the browser or logged.

## Tests

```sh
cd backend && ../.venv/Scripts/python -m pytest && cd ..   # backend
.venv/Scripts/python -m pytest eval                         # metrics and annotation tools
cd frontend && npm test && cd ..                            # dashboard
```

## Reproduce the results

The results in `eval/results/` come from these commands, run from the repo root. Each output
file records the commit and date it was produced with. Every number is deterministic except
the timings of `eval.bench`, which depend on the machine.

```sh
.venv/Scripts/python -m pip install -e "backend[eval]"
.venv/Scripts/python -m eval.annotations --check   # the 30 evaluation annotations match their traces
.venv/Scripts/python -m eval.tune        # segmenter parameters: grid search on dev, scored on test
.venv/Scripts/python -m eval.steptypes   # step-type classifier: settings by grouped CV, test scores, learning curve
.venv/Scripts/python -m eval.run         # segmentation, concepts and topics against the baselines
.venv/Scripts/python -m eval.bench       # cost per update as the text grows
.venv/Scripts/python -m eval.figures     # the figures (PNG)
```

`eval/annotations/GUIDE.md` describes the annotation format and the step types.
