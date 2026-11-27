# MeDRA

Panel en tiempo real que aplica minería de textos a la cadena de pensamiento (CoT) de un modelo
de lenguaje mientras se genera. Práctica final de *Inteligencia Artificial en las Organizaciones*
(UC3M, 2026/27), Grupo 1.

## Instalación y ejecución

Hay dos formas de usarlo: ejecutarlo en local o abrir la web en directo.

### Opción 1: ejecutarlo en local

Recursos necesarios:

- Python 3.11 o superior.
- Node.js 20 o superior.
- Conexión a internet durante la instalación (se descargan las dependencias y los modelos de spaCy).
- Opcional: una clave de la API de DeepSeek, solo para la fuente DeepSeek.

Los comandos se ejecutan desde la carpeta raíz del proyecto. En macOS o Linux, escribir
`.venv/bin/` en lugar de `.venv/Scripts/`.

1. Instalar (solo la primera vez):

   ```sh
   python -m venv .venv
   .venv/Scripts/python -m pip install -r backend/requirements.lock
   .venv/Scripts/python -m pip install -e backend
   cd frontend && npm install && cd ..
   ```

2. Arrancar el servidor, en una terminal:

   ```sh
   .venv/Scripts/medra-serve
   ```

3. Arrancar el panel, en otra terminal:

   ```sh
   cd frontend
   npm run dev
   ```

4. Abrir http://localhost:5173, elegir una traza en **Traza** y pulsar el botón de enviar.
   Con **Añadir visualización** se añaden el mapa de conceptos, la línea de temas o los pasos
   del agente.

Sin clave funcionan las fuentes **Traza de ejemplo** y **Pegar texto**. Para usar DeepSeek en
local, copiar `.env.example` como `.env` y escribir la clave en `DEEPSEEK_API_KEY`.

### Opción 2: usar la web en directo (con DeepSeek)

No hace falta instalar nada ni tener clave de API.

1. Abrir https://joejbaldwin.github.io/medra/.
2. En **Fuente**, elegir **DeepSeek Flash**.
3. Escribir una pregunta y enviarla. La web pedirá un código de acceso: lo enviará Joe Baldwin
   (100483331@alumnos.uc3m.es) por Aula Global junto con la entrega.

Si el servidor llevaba un rato inactivo, la primera petición tarda algo más mientras arranca.

## Dependencias

Las versiones exactas están fijadas en `backend/requirements.lock` y `frontend/package-lock.json`.

| Parte | Dependencias |
|---|---|
| Servidor (Python) | FastAPI y Uvicorn (API y WebSocket), Pydantic (contratos de datos), httpx (API de DeepSeek), python-dotenv, PyYAML |
| Minería de textos (Python) | spaCy con los modelos `en_core_web_md` y `es_core_news_md`, scikit-learn (TF-IDF y regresión logística), NetworkX (grafo de coocurrencia y Louvain) |
| Evaluación (Python) | matplotlib (figuras), pytest |
| Panel (web) | TypeScript, D3, Vite, Vitest |

## Reproducir los resultados

Los resultados están en `eval/results/` y salen de estos comandos, tras la instalación de la
opción 1. Usan solo los datos del repositorio: no hace falta clave de API.

```sh
.venv/Scripts/python -m pip install -e "backend[eval]"   # añade matplotlib y pytest
.venv/Scripts/python -m eval.annotations --check   # comprueba que las anotaciones coinciden con sus trazas
.venv/Scripts/python -m eval.tune        # ajuste del segmentador en las trazas de desarrollo
.venv/Scripts/python -m eval.steptypes   # clasificador de tipo de paso: ajuste, prueba y curva de aprendizaje
.venv/Scripts/python -m eval.run         # segmentación, conceptos y temas frente a los baselines
.venv/Scripts/python -m eval.bench       # coste por actualización según crece el texto
.venv/Scripts/python -m eval.figures     # figuras (PNG)
```

| Resultado | Fichero en `eval/results/` |
|---|---|
| Segmentación (Pk, WindowDiff), conceptos y temas frente a los baselines | `results.md` |
| Ajuste del segmentador | `tune.md` |
| Tipo de paso: regresión logística frente a la regla de marcadores | `steptypes.md` |
| Latencia por actualización | `bench.md` |

Cada fichero indica la fecha y el commit con que se generó. Todos los números se repiten
exactamente al volver a ejecutar, salvo los tiempos de `eval.bench`, que dependen de la máquina.
`eval.steptypes` también vuelve a escribir el modelo que usa el panel
(`backend/medra/mining/models/step_types_en.json`).

## Datos

Todos los datos están incluidos en el repositorio.

| Datos | Carpeta | Origen |
|---|---|---|
| 30 trazas de evaluación | `eval/traces/` | 22 grabadas de la API de DeepSeek (`en-*`) y 8 de OpenThoughts-114k (`ot-*`) |
| 272 trazas de entrenamiento | `eval/train/traces/` | 122 grabadas de la API de DeepSeek (`ds-*`, preguntas en `eval/train/prompts.yaml`) y 150 de OpenThoughts-114k (`ot-*`) |
| Anotaciones (tramos, tipos de paso, conceptos y temas) | `eval/annotations/`, `eval/train/annotations/` | del grupo; formato y criterios en `eval/annotations/GUIDE.md` |
| Trazas de ejemplo del panel | `data/samples/` | copias de trazas de evaluación y dos trazas ilustrativas escritas por el grupo |

Cómo obtenerlos de nuevo:

- **OpenThoughts-114k** (`open-thoughts/OpenThoughts-114k` en Hugging Face, licencia Apache-2.0):
  `python -m eval.fetch_openthoughts` descarga las filas de evaluación y
  `python -m eval.fetch_openthoughts --rows ...` las de entrenamiento. Cada traza indica su
  fila en el campo `origin`.
- **DeepSeek**: `python -m eval.record_traces` vuelve a enviar las preguntas (necesita la clave
  en `.env`). El modelo no es determinista, así que las trazas nuevas no serían idénticas; por eso
  se incluyen las grabadas.

Licencias y protección de datos:

- Las trazas de OpenThoughts-114k se usan sin modificar, con su procedencia y licencia indicadas
  en cada fichero.
- Las trazas de DeepSeek son respuestas del modelo a problemas de matemáticas, lógica, código y
  ciencia escritos por el grupo, obtenidas con la cuenta de API del grupo. No contienen datos
  personales.
- Los resultados de la prueba con usuarios no se incluyen en el repositorio.
