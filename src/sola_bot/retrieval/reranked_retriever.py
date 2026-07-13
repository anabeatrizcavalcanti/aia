"""Retriever híbrido com reranking neural."""

from __future__ import annotations

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
        self.reranker_model = reranker_model
        self.max_text_chars = max_text_chars
        self.include_metadata = include_metadata
        self.hybrid_retriever = HybridRetriever(
            vector_candidate_k=hybrid_candidate_k,
            bm25_candidate_k=hybrid_candidate_k,
            final_top_k=hybrid_candidate_k,
        )
        self.reranker = reranker or CrossEncoderReranker(
            model_name=reranker_model,
            max_text_chars=max_text_chars,
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
        return self.reranker.rerank(query=query, candidates=candidates, top_k=final_top_k)
