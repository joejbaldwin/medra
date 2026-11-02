# MeDRA

**Mapa de Despliegue del Razonamiento Agente**: a real-time dashboard that turns a
model's chain-of-thought into a visual map while the reasoning is still streaming.

Text mining (cleaning, lemmatisation, n-grams, TF-IDF per segment, co-occurrence,
segmentation and topic clustering) runs on the stream as it arrives. The dashboard
shows the live text next to a concept map, a timeline of topics and the steps the
model takes. Every bubble, segment and topic links back to the words it came from.

The system has four interchangeable layers:

1. **Source**: any text stream (an LLM API, pasted text, a recorded dataset, a local model, transcription).
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
| Ollama (modelo local) | the same with a local reasoning model (`deepseek-r1:8b` by default) | Ollama running |

Copy `.env.example` to `.env` and put the DeepSeek key there; it is read only by the backend and
never sent to the browser or logged. Only one DeepSeek session runs at a time, and
`MEDRA_LIVE_DISABLED=1` switches off both live sources. Questions sent to DeepSeek leave this
machine, so don't type personal data.

Each layer is also a command reading and writing JSON Lines:

```sh
medra-source replay login-es --chunking random | medra-mine | medra-present > frames.jsonl
medra-source paste trace.txt | medra-mine | medra-present > frames.jsonl
medra-source deepseek "¿Cuántos primos hay menores que 50?" | medra-mine > metrics.jsonl
medra-source ollama "Is 91 prime?" | medra-mine > metrics.jsonl
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

## Contracts

The messages between layers are Pydantic models in [backend/medra/contracts.py](backend/medra/contracts.py),
frozen as schema v1 in [docs/contracts/v1.schema.json](docs/contracts/v1.schema.json) (currently 1.4;
minor versions only add fields with defaults). The dashboard's TypeScript types are generated from
that schema. After changing a contract, bump `SCHEMA_VERSION`, then:

```sh
cd backend && ../.venv/Scripts/python -m medra.schema ../docs/contracts/v1.schema.json
cd frontend && npm run gen:types
```
