FROM node:20-alpine AS frontend

WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV RAG_CORPUS_DIR=/app/storage/corpus
ENV HF_HOME=/app/storage/huggingface

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-runtime.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir -r requirements-runtime.txt

COPY config ./config
COPY scripts ./scripts
COPY src ./src
COPY --from=frontend /app/web/dist ./web/dist

RUN mkdir -p /app/storage/corpus

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT}/api/health || exit 1

CMD ["python", "scripts/run_web_chat.py"]
