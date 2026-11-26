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
