"""Retriever lexical BM25 para o corpus documental da Aliança."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover - dependência validada no fluxo de execução
    BM25Okapi = None

from sola_bot.retrieval.paths import chunks_path as runtime_chunks_path
from sola_bot.retrieval.retrieval_result import RetrievalResult
from sola_bot.retrieval.vector_retriever import DEFAULT_CHUNKS_PATH, DEFAULT_FILTERS


ROOT_DIR = Path(__file__).resolve().parents[3]
TOKEN_PATTERN = re.compile(r"[\wÀ-ÿ]+", flags=re.UNICODE)


class BM25RetrieverError(RuntimeError):
    """Erro da camada lexical BM25."""


def tokenize_for_bm25(text: str) -> list[str]:
    """
    Tokeniza texto para BM25 preservando termos doutrinários e acentos.

    A tokenização é intencionalmente simples: minúsculas, remoção de
    pontuação básica e separação por palavras. Não há remoção de stopwords
    nesta etapa, para evitar perda de termos confessionais relevantes.
    """
    return TOKEN_PATTERN.findall(text.lower())


class BM25Retriever:
    """Recupera chunks por busca lexical BM25 usando `rank-bm25`."""

    def __init__(
        self,
        chunks_path: str | None = None,
        text_field: str = "embedding_text",
    ) -> None:
        if BM25Okapi is None:
            raise BM25RetrieverError(
                "rank-bm25 não está instalado. Instale a dependência para usar BM25Okapi."
            )
        chunks_file = self._repo_path(chunks_path) if chunks_path else runtime_chunks_path()
        self.chunks_path = str(chunks_file)
        self.text_field = text_field
        self.chunks = self._load_chunks(chunks_file)

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Retorna os chunks mais relevantes pela rota lexical BM25."""
        if top_k < 1:
            raise BM25RetrieverError("top_k deve ser maior ou igual a 1.")
        filtered_chunks = [chunk for chunk in self.chunks if self._matches_filters(chunk, filters)]
        if not filtered_chunks:
            return []

        tokenized_corpus = [tokenize_for_bm25(str(chunk.get(self.text_field, ""))) for chunk in filtered_chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        query_tokens = tokenize_for_bm25(query)
        scores = bm25.get_scores(query_tokens)

        ranked = sorted(
            zip(filtered_chunks, scores, strict=True),
            key=lambda item: item[1],
            reverse=True,
        )[:top_k]
        return [self._build_result(chunk, float(score)) for chunk, score in ranked]

    def _load_chunks(self, chunks_path: str | Path) -> list[dict[str, Any]]:
        """Carrega chunks elegíveis para recuperação."""
        path = self._repo_path(chunks_path)
        if not path.exists():
            raise BM25RetrieverError(f"Arquivo de chunks não encontrado: {chunks_path}")

        chunks: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("embedding_eligible") is True:
                    chunks.append(row)
        return chunks

    def _matches_filters(self, chunk: dict[str, Any], filters: dict[str, Any] | None) -> bool:
        """Aplica filtros obrigatórios e filtros adicionais sobre metadados do chunk."""
        merged: dict[str, Any] = dict(DEFAULT_FILTERS)
        for key, value in (filters or {}).items():
            if value is None:
                continue
            if key in DEFAULT_FILTERS and value != DEFAULT_FILTERS[key]:
                continue
            merged[key] = value
        return all(chunk.get(key) == value for key, value in merged.items())

    def _build_result(self, chunk: dict[str, Any], score: float) -> RetrievalResult:
        """Converte um chunk JSONL em `RetrievalResult`."""
        metadata = {
            key: chunk.get(key)
            for key in (
                "chunk_id",
                "corpus_id",
                "retrieval_namespace",
                "document_id",
                "doc_id",
                "document",
                "document_title",
                "document_type",
                "source_category",
                "denomination",
                "tradition",
                "tradition_family",
                "tradition_branch",
                "language",
                "chunk_type",
                "content_role",
                "is_doctrinal",
                "document_structure_type",
                "section_title",
                "section_reference",
                "subsection_title",
                "chapter_title",
                "chapter_reference",
                "article_number",
                "paragraph_number",
                "paragraph_label",
                "paragraph_number_roman",
                "inciso",
                "alinea",
                "full_reference",
                "biblical_references",
                "page_start",
                "page_end",
                "source_path",
                "normalized_source",
                "text_hash",
            )
            if chunk.get(key) is not None
        }
        metadata["retrieval_source"] = "bm25"
        metadata["bm25_score"] = score
        return RetrievalResult(
            chunk_id=str(chunk.get("chunk_id", "")),
            document_id=str(chunk.get("document_id", "")),
            document=str(chunk.get("document", "")),
            chunk_type=str(chunk.get("chunk_type", "")),
            content_role=_nullable_string(chunk.get("content_role")),
            section_title=_nullable_string(chunk.get("section_title")),
            section_reference=_nullable_string(chunk.get("section_reference")),
            chapter_title=_nullable_string(chunk.get("chapter_title")),
            chapter_reference=_nullable_string(chunk.get("chapter_reference")),
            page_start=_nullable_int(chunk.get("page_start")),
            page_end=_nullable_int(chunk.get("page_end")),
            source_path=str(chunk.get("source_path", "")),
            text_hash=str(chunk.get("text_hash", "")),
            score=score,
            distance=None,
            text=str(chunk.get("text", "")),
            metadata=metadata,
        )

    @staticmethod
    def _repo_path(path: str | Path) -> Path:
        """Resolve caminhos relativos à raiz do repositório."""
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        return ROOT_DIR / candidate


def _nullable_string(value: Any) -> str | None:
    """Converte valores vazios para `None`."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _nullable_int(value: Any) -> int | None:
    """Converte valores de página para inteiro quando possível."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
