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

Requires Python 3.11+ and Node 20+.

```sh
# backend (from the repo root)
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.lock   # macOS/Linux: .venv/bin/python
.venv/Scripts/python -m pip install -e "backend[dev]"
.venv/Scripts/medra-serve                     # http://127.0.0.1:8000

# dashboard (second terminal)
cd frontend
npm install
npm run dev                                   # open http://localhost:5173
```

Pick a trace, press **Reproducir**: the text streams in on the right, split into segments
(«tramos») coloured by topic; on the left the bubbles grow and the topic timeline fills in.
The **Pasos** tab shows one node per segment, labelled with the discourse marker that opened it.

The **Fuente** menu picks where the text comes from:

| Source | What it does | Needs |
|---|---|---|
| Traza de ejemplo | replays a recorded trace from `data/samples/` | nothing |
| Pegar texto | replays text you paste (a `<think>…</think>` block is split off from the answer) | nothing |
| DeepSeek (en directo) | asks `deepseek-flash` and streams its reasoning, then its answer | `DEEPSEEK_API_KEY` |
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

## Screenshots

With the backend and dashboard running, `scripts/screenshots.py` replays a trace in a headless
browser and saves streaming and final captures (light and dark) to `screenshots/` (not committed);
`--select ID` adds one with that bubble selected, `--topic N` one with the N-th topic selected, and
`--step N` one of the steps view with the N-th step selected:

```sh
.venv/Scripts/python -m pip install -e "backend[figures]"
.venv/Scripts/python -m playwright install chromium-headless-shell
.venv/Scripts/python scripts/screenshots.py --prefix step4 --select contraseña --topic 1 --step 3 --channel chromium-headless-shell
```

`--source paste --paste-file FILE` captures pasted text instead, and `--source deepseek --prompt "..."`
a live run (each colour scheme is one API call, so add `--schemes light`).

## Contracts

The messages between layers are Pydantic models in [backend/medra/contracts.py](backend/medra/contracts.py),
frozen as schema v1 in [docs/contracts/v1.schema.json](docs/contracts/v1.schema.json) (currently 1.3;
minor versions only add fields with defaults). The dashboard's TypeScript types are generated from
that schema. After changing a contract, bump `SCHEMA_VERSION`, then:

```sh
cd backend && ../.venv/Scripts/python -m medra.schema ../docs/contracts/v1.schema.json
cd frontend && npm run gen:types
```
