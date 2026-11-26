# MeDRA backend container. Deployed on Google Cloud Run
# with scripts/deploy_cloudrun.py; runs anywhere Docker does.
#
#   docker build -t medra . && docker run -p 7860:7860 --env-file .env medra
#
# Only the backend and the sample traces go in the image; the dashboard is
# served by GitHub Pages. Secrets (DEEPSEEK_API_KEY, MEDRA_ACCESS_CODES) come
# from the host's secret store at run time, never from the image.
FROM python:3.12-slim

RUN useradd -m -u 1000 user
WORKDIR /app

# Dependencies first (pinned versions, including the spaCy md models), so a
# code change does not reinstall them.
COPY backend/requirements.lock backend/requirements.lock
RUN pip install --no-cache-dir -r backend/requirements.lock

COPY backend backend
COPY data/samples data/samples
# Editable install keeps the repo layout, so medra finds data/samples next to backend/.
RUN pip install --no-cache-dir --no-deps -e backend

USER user
ENV PYTHONUNBUFFERED=1 \
    # numpy's OpenBLAS would reserve a memory buffer per core (medra/__init__.py)
    OPENBLAS_NUM_THREADS=1
EXPOSE 7860
# Cloud Run sets PORT (8080); elsewhere the container listens on 7860.
CMD exec uvicorn medra.server:app --host 0.0.0.0 --port ${PORT:-7860} --proxy-headers --forwarded-allow-ips "*"
