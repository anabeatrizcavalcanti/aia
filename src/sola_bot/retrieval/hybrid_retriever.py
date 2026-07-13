"""Retriever híbrido para o corpus documental da Aliança."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from sola_bot.retrieval.bm25_retriever import BM25Retriever
from sola_bot.retrieval.retrieval_result import RetrievalResult
from sola_bot.retrieval.rrf import reciprocal_rank_fusion
from sola_bot.retrieval.vector_retriever import DEFAULT_FILTERS, VectorRetriever


class HybridRetriever:
    """Combina retrieval vetorial e lexical BM25 por Reciprocal Rank Fusion."""

    def __init__(
        self,
        vector_candidate_k: int = 20,
        bm25_candidate_k: int = 20,
        rrf_k: int = 60,
        final_top_k: int = 5,
        bm25_text_field: str = "embedding_text",
    ) -> None:
        self.vector_candidate_k = vector_candidate_k
        self.bm25_candidate_k = bm25_candidate_k
        self.rrf_k = rrf_k
        self.final_top_k = final_top_k
        self.bm25_text_field = bm25_text_field
        self.vector_retriever = VectorRetriever()
        self.bm25_retriever = BM25Retriever(text_field=bm25_text_field)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Recupera chunks usando vetorial + BM25 + RRF."""
        final_top_k = top_k or self.final_top_k
        merged_filters = self._merge_filters(filters)
        vector_results = self._tag_vector_results(
            self.vector_retriever.retrieve(
                query=query,
                top_k=self.vector_candidate_k,
                filters=merged_filters,
            )
        )
        bm25_results = self.bm25_retriever.retrieve(
            query=query,
            top_k=self.bm25_candidate_k,
            filters=merged_filters,
        )
        return reciprocal_rank_fusion(
            [vector_results, bm25_results],
            k=self.rrf_k,
            top_k=final_top_k,
        )

    def _merge_filters(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        """Combina filtros adicionais com o escopo padrão do corpus ativo."""
        merged: dict[str, Any] = dict(DEFAULT_FILTERS)
        for key, value in (filters or {}).items():
            if value is None:
                continue
            if key in DEFAULT_FILTERS and value != DEFAULT_FILTERS[key]:
                continue
            merged[key] = value
        return merged

    def _tag_vector_results(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Marca resultados vetoriais com metadados usados pelo RRF."""
        tagged: list[RetrievalResult] = []
        for result in results:
            metadata = dict(result.metadata)
            metadata["retrieval_source"] = "vector"
            metadata["vector_distance"] = result.distance
            metadata["vector_score"] = result.score
            tagged.append(replace(result, metadata=metadata))
        return tagged
