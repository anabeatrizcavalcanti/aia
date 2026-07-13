"""Retriever híbrido com reranking neural."""

from __future__ import annotations

import os
from typing import Any

from sola_bot.retrieval.cross_encoder_reranker import (
    DEFAULT_MAX_TEXT_CHARS,
    DEFAULT_RERANKER_MODEL,
    CrossEncoderReranker,
)
from sola_bot.retrieval.hybrid_retriever import HybridRetriever
from sola_bot.retrieval.retrieval_result import RetrievalResult


class RerankedRetriever:
    """Encadeia HybridRetriever e CrossEncoderReranker."""

    def __init__(
        self,
        hybrid_candidate_k: int = 20,
        final_top_k: int = 5,
        reranker_model: str = DEFAULT_RERANKER_MODEL,
        max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
        include_metadata: bool = True,
        reranker: CrossEncoderReranker | None = None,
    ) -> None:
        self.hybrid_candidate_k = hybrid_candidate_k
        self.final_top_k = final_top_k
        self.reranker_model = os.getenv("RERANKER_MODEL", reranker_model).strip() or reranker_model
        self.max_text_chars = _int_env("RERANKER_MAX_TEXT_CHARS", max_text_chars)
        self.include_metadata = include_metadata
        self.hybrid_retriever = HybridRetriever(
            vector_candidate_k=hybrid_candidate_k,
            bm25_candidate_k=hybrid_candidate_k,
            final_top_k=hybrid_candidate_k,
        )
        self.reranker_enabled = _reranker_enabled()
        self.reranker = None
        if self.reranker_enabled:
            self.reranker = reranker or CrossEncoderReranker(
                model_name=self.reranker_model,
                max_text_chars=self.max_text_chars,
                include_metadata=include_metadata,
            )

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Recupera candidatos híbridos e reordena com Cross-Encoder."""
        final_top_k = top_k or self.final_top_k
        candidates = self.hybrid_retriever.retrieve(
            query=query,
            top_k=self.hybrid_candidate_k,
            filters=filters,
        )
        if self.reranker is None:
            return [_with_skipped_reranker_metadata(result) for result in candidates[:final_top_k]]
        return self.reranker.rerank(query=query, candidates=candidates, top_k=final_top_k)


def _reranker_enabled() -> bool:
    value = os.getenv("RERANKER_ENABLED", "true").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return max(1, parsed)


def _with_skipped_reranker_metadata(result: RetrievalResult) -> RetrievalResult:
    metadata = dict(result.metadata)
    metadata["reranker_provider"] = "disabled"
    metadata["reranker_skipped"] = True
    return result.__class__(
        chunk_id=result.chunk_id,
        document_id=result.document_id,
        document=result.document,
        chunk_type=result.chunk_type,
        content_role=result.content_role,
        section_title=result.section_title,
        section_reference=result.section_reference,
        chapter_title=result.chapter_title,
        chapter_reference=result.chapter_reference,
        page_start=result.page_start,
        page_end=result.page_end,
        source_path=result.source_path,
        text_hash=result.text_hash,
        score=result.score,
        distance=result.distance,
        text=result.text,
        metadata=metadata,
    )
