"""Pipeline final de retrieval do corpus documental da Aliança."""

from __future__ import annotations

import os
from typing import Any

from sola_bot.retrieval.context_consolidator import (
    ContextConsolidator,
    classify_query_intent,
    query_mentions_denominational_scope,
)
from sola_bot.retrieval.final_context import RetrievalContextPackage
from sola_bot.retrieval.hierarchical_retriever import HierarchicalRetriever
from sola_bot.retrieval.reranked_retriever import RerankedRetriever


class RetrievalPipeline:
    """Integra recuperação hierárquica e consolidação final de contexto."""

    alliance_doctrinal_document_ids = ("confissao-fe-congregacional-alianca",)

    def __init__(
        self,
        final_context_top_k: int = 4,
        max_total_context_chars: int = 18000,
        max_context_chars_per_parent: int = 9000,
        hierarchical_retriever: HierarchicalRetriever | None = None,
        context_consolidator: ContextConsolidator | None = None,
    ) -> None:
        self.final_context_top_k = final_context_top_k
        self.max_total_context_chars = max_total_context_chars
        self.max_context_chars_per_parent = max_context_chars_per_parent
        anchor_candidate_k = _int_env("RERANKED_TOP_K", max(30, final_context_top_k * 8))
        hybrid_candidate_k = _int_env("HYBRID_CANDIDATE_K", max(40, final_context_top_k * 10))
        self.hierarchical_retriever = hierarchical_retriever or HierarchicalRetriever(
            reranked_top_k=anchor_candidate_k,
            reranked_retriever=RerankedRetriever(
                hybrid_candidate_k=hybrid_candidate_k,
                final_top_k=anchor_candidate_k,
            ),
        )
        self.context_consolidator = context_consolidator or ContextConsolidator(
            final_context_top_k=final_context_top_k,
            max_total_context_chars=max_total_context_chars,
            max_context_chars_per_parent=max_context_chars_per_parent,
        )

    def retrieve(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalContextPackage:
        """Executa o fluxo completo até o pacote final de contextos."""
        package = self._retrieve_once(query=query, filters=filters)
        return self._retry_when_source_type_is_missing(
            query=query,
            filters=filters,
            package=package,
        )

    def _retrieve_once(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalContextPackage:
        """Executa uma rodada de retrieval com filtros explícitos."""
        parent_contexts = self.hierarchical_retriever.retrieve(query=query, filters=filters)
        return self.context_consolidator.consolidate(
            query=query,
            parent_contexts=parent_contexts,
            filters=filters,
        )

    def _retry_when_source_type_is_missing(
        self,
        query: str,
        filters: dict[str, Any] | None,
        package: RetrievalContextPackage,
    ) -> RetrievalContextPackage:
        """Refaz a busca quando a pergunta pede uma natureza documental ausente no pacote final."""
        if filters and filters.get("source_category"):
            return package

        intent = classify_query_intent(query)
        priorities = {context.content_priority for context in package.contexts}
        retry_attempts: list[tuple[dict[str, Any], str]] = []

        if intent in {"normative", "mixed"} and "normative" not in priorities:
            retry_attempts.append(
                (
                    {"source_category": "denominational_normative_document"},
                    "missing_normative_context",
                )
            )
        elif intent == "doctrinal" and "doctrinal" not in priorities:
            if query_mentions_denominational_scope(query):
                retry_attempts.extend(
                    (
                        {"document_id": document_id},
                        "missing_alliance_doctrinal_context",
                    )
                    for document_id in self.alliance_doctrinal_document_ids
                )
            retry_attempts.append(
                (
                    {"source_category": "doctrinal_document"},
                    "missing_doctrinal_context",
                )
            )

        if not retry_attempts:
            return package

        for retry_filter, retry_reason in retry_attempts:
            retry_filters = dict(filters or {})
            retry_filters.update(retry_filter)
            retry_package = self._retrieve_once(query=query, filters=retry_filters)
            if not retry_package.contexts:
                continue

            retry_package.metadata["fallback_retry"] = {
                "reason": retry_reason,
                "filters": retry_filter,
                "initial_context_count": package.context_count,
                "initial_content_priorities": sorted(priorities),
            }
            return retry_package

        return package


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return max(1, parsed)
