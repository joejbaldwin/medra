# MeDRA

Panel en tiempo real que aplica minería de textos a la cadena de pensamiento (CoT) de un modelo
de lenguaje mientras se genera. Práctica final de *Inteligencia Artificial en las Organizaciones*
(UC3M, 2026/27), Grupo 1.

Hay dos formas de usarlo: ejecutarlo en local o abrir la web en directo.

## Opción 1: ejecutarlo en local

### Recursos necesarios

- Python 3.11 o superior.
- Node.js 20 o superior.
- Conexión a internet durante la instalación (se descargan las dependencias y los modelos de spaCy).
- Opcional: una clave de la API de DeepSeek, solo para la fuente DeepSeek.

### Instrucciones

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

## Opción 2: usar la web en directo (con DeepSeek)

No hace falta instalar nada ni tener clave de API.

1. Abrir https://joejbaldwin.github.io/medra/.
2. En **Fuente**, elegir **DeepSeek Flash**.
3. Escribir una pregunta, enviarla e introducir el código de acceso que facilita el grupo.

Si el servidor llevaba un rato inactivo, la primera petición tarda algo más mientras arranca.
