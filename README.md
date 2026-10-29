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
