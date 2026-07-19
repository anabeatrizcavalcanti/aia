"""Caminhos configuraveis dos artefatos de retrieval."""

from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_DIR = ROOT_DIR / "corpus"
DEFAULT_COLLECTION_NAME = "aia_alliance_v1"
DEFAULT_QUERY_EMBEDDING_MODEL = "text-embedding-3-large"


def corpus_dir() -> Path:
    """Retorna o diretorio raiz do corpus usado em runtime."""
    configured = os.getenv("RAG_CORPUS_DIR", "").strip()
    if configured:
        return Path(configured)
    return DEFAULT_CORPUS_DIR


def chunks_path() -> Path:
    """Arquivo JSONL de chunks usado por BM25 e contextos hierarquicos."""
    configured = os.getenv("RAG_CHUNKS_PATH", "").strip()
    if configured:
        return _resolve_runtime_path(configured)
    return corpus_dir() / "processed" / "chunks" / "alliance" / "all_chunks_for_embeddings.jsonl"


def chroma_persist_directory() -> Path:
    """Diretorio persistido do ChromaDB."""
    configured = os.getenv("CHROMA_PERSIST_DIRECTORY", "").strip()
    if configured:
        path = _resolve_runtime_path(configured)
        if path.name == "chroma":
            return path / "alliance"
        return path
    return corpus_dir() / "indexes" / "chroma" / "alliance"


def chroma_collection_name() -> str:
    """Nome da collection ChromaDB em runtime."""
    return os.getenv("CHROMA_COLLECTION_NAME", DEFAULT_COLLECTION_NAME).strip() or DEFAULT_COLLECTION_NAME


def _resolve_runtime_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return ROOT_DIR / candidate
