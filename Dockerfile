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
ENV RAG_CORPUS_DIR=/app/corpus
ENV CHROMA_PERSIST_DIRECTORY=/app/corpus/indexes/chroma/alliance
ENV RAG_CHUNKS_PATH=/app/corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl
ENV CHROMA_COLLECTION_NAME=solabot_alliance_v1
ENV HF_HOME=/app/.cache/huggingface
ENV RERANKER_ENABLED=true
ENV RERANKER_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
ENV RERANKED_TOP_K=12
ENV HYBRID_CANDIDATE_K=16
ENV RERANKER_MAX_TEXT_CHARS=1800

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-runtime.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir -r requirements-runtime.txt
RUN python -c "import os; from sentence_transformers import CrossEncoder; CrossEncoder(os.environ['RERANKER_MODEL'])"

COPY config ./config
COPY scripts ./scripts
COPY src ./src
COPY --from=frontend /app/web/dist ./web/dist
COPY runtime_artifacts/solabot-runtime-corpus.tar.gz /tmp/solabot-runtime-corpus.tar.gz
RUN python -c "import tarfile; tarfile.open('/tmp/solabot-runtime-corpus.tar.gz').extractall('/app')" \
    && rm /tmp/solabot-runtime-corpus.tar.gz

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT}/api/health || exit 1

CMD ["python", "scripts/run_web_chat.py"]
