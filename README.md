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

Pick a trace, press **Reproducir**: the text streams in on the right and the bubbles grow on the left.

Each layer is also a command reading and writing JSON Lines:

```sh
medra-source replay login-es --chunking random | medra-mine | medra-present > frames.jsonl
```

## Tests

```sh
cd backend && ../.venv/Scripts/python -m pytest      # backend
cd frontend && npm run typecheck                     # dashboard
```

## Screenshots

With the backend and dashboard running, `scripts/screenshots.py` replays a trace in a headless
browser and saves streaming and final captures (light and dark) to `screenshots/` (not committed):

```sh
.venv/Scripts/python -m pip install -e "backend[figures]"
.venv/Scripts/python -m playwright install chromium-headless-shell
.venv/Scripts/python scripts/screenshots.py --prefix step1 --channel chromium-headless-shell
```

## Contracts

The messages between layers are Pydantic models in [backend/medra/contracts.py](backend/medra/contracts.py),
frozen as schema v1 in [docs/contracts/v1.schema.json](docs/contracts/v1.schema.json). The dashboard's
TypeScript types are generated from that schema. After changing a contract, bump `SCHEMA_VERSION`, then:

```sh
cd backend && ../.venv/Scripts/python -m medra.schema ../docs/contracts/v1.schema.json
cd frontend && npm run gen:types
```
